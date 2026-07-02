from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import get_settings
from .harness import harnesses, prepare_harness_run
from .langgraph_runner import LangGraphUnavailableError, langgraph_status, run_langgraph_phase
from .model_adapters import ModelAdapterError
from .models import (
    ArtifactReadResponse,
    AuditResponse,
    BenchmarkResponse,
    CopyRunRequest,
    CopyRunResponse,
    CreateWorkspaceRequest,
    CreateWorkspaceResponse,
    HarnessInfo,
    PrepareHarnessRequest,
    PrepareHarnessResponse,
    HealthResponse,
    LangGraphRunRequest,
    LangGraphRunResponse,
    LangGraphStatusResponse,
    PromptRequest,
    PromptResponse,
    Recommendation,
    RevisionTask,
    RevisionTasksResponse,
    RunHistoryEntry,
    SourceUploadResponse,
    ScriptStatus,
    WorkspaceSummary,
)
from .prompts import build_prompt
from .runner import run_audit, run_benchmark, run_scaffold
from .workspace import (
    artifact_type,
    append_history,
    build_phase_summaries,
    copy_workspace_for_run,
    discover_workspaces,
    encode_workspace_id,
    ensure_allowed,
    list_artifacts,
    manifest_summary,
    paper_summary,
    read_history,
    read_json,
    read_text,
    safe_artifact_path,
    sanitize_filename,
    workspace_from_id,
    workspace_item,
)


app = FastAPI(title="MathModel Control Center", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ISSUE_PHASE_MAP = {
    "manifest": 2,
    "figure": 2,
    "png": 2,
    "pillow": 2,
    "audit": 3,
    "claim": 3,
    "score": 4,
    "revision": 5,
    "verify": 6,
}


def issue_phase(code: str) -> int:
    lower = code.lower()
    for key, phase in ISSUE_PHASE_MAP.items():
        if key in lower:
            return phase
    return 6


def issue_artifact(issue: dict[str, Any]) -> str:
    evidence = str(issue.get("evidence", ""))
    if evidence.startswith("results/") or evidence.startswith("reports/") or evidence.startswith("paper/"):
        return evidence.split(",", 1)[0]
    code = str(issue.get("code", ""))
    if "manifest" in code:
        return "results/RESULTS_MANIFEST.json"
    if "figure_audit" in code:
        return "reports/FIGURE_AUDIT.md"
    if "claim" in code:
        return "reports/CLAIM_TRACE.md"
    if "score" in code:
        return "reports/PAPER_SCORECARD.md"
    return "reports/VERIFY_REPORT.md"


def build_recommendations(result: dict[str, Any], missing: list[str]) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
    for issue in list(result.get("issues", []))[:6]:
        code = str(issue.get("code", "issue"))
        phase = issue_phase(code)
        recommendations.append(
            Recommendation(
                severity=str(issue.get("severity", "INFO")),
                title=code,
                detail=str(issue.get("message", issue.get("evidence", ""))),
                phase=phase,
                artifact=issue_artifact(issue),
            )
        )
    for path in missing[:4]:
        recommendations.append(
            Recommendation(
                severity="HIGH",
                title=f"missing:{path}",
                detail="Required V2 artifact is missing or not generated yet.",
                phase=None,
                artifact=path,
            )
        )
    if not recommendations:
        recommendations.append(
            Recommendation(
                severity="INFO",
                title="ready-for-next-audit",
                detail="No immediate issue found by current summary. Run audit before claiming PASS.",
            )
        )
    return recommendations


def build_revision_tasks(result: dict[str, Any]) -> list[RevisionTask]:
    tasks: list[RevisionTask] = []
    for index, issue in enumerate(result.get("issues", []), start=1):
        severity = str(issue.get("severity", "INFO"))
        if severity not in {"BLOCKER", "HIGH", "MEDIUM", "LOW"}:
            severity = "INFO"
        code = str(issue.get("code", f"issue-{index}"))
        phase = issue_phase(code)
        artifact = issue_artifact(issue)
        tasks.append(
            RevisionTask(
                id=f"RT-{index:03d}",
                severity=severity,
                phase=phase,
                artifact=artifact,
                issue_code=code,
                title=str(issue.get("message", code)),
                action=f"Phase {phase}: repair `{artifact}` for `{code}`, then rerun audit_v2_run.py.",
            )
        )
    return tasks


def revision_tasks_markdown(tasks: list[RevisionTask]) -> str:
    lines = [
        "# Control Center Revision Tasks",
        "",
        "| ID | Severity | Phase | Artifact | Issue | Action |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for task in tasks:
        lines.append(
            f"| {task.id} | {task.severity} | {task.phase} | {task.artifact} | {task.issue_code} | {task.action} |"
        )
    return "\n".join(lines) + "\n"


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    scripts = {
        "audit": ScriptStatus(path=str(settings.audit_script), exists=settings.audit_script.is_file()),
        "benchmark": ScriptStatus(path=str(settings.benchmark_script), exists=settings.benchmark_script.is_file()),
        "scaffold": ScriptStatus(path=str(settings.scaffold_script), exists=settings.scaffold_script.is_file()),
    }
    return HealthResponse(
        ok=all(item.exists for item in scripts.values()),
        python=platform.python_version(),
        mathmodel_root=str(settings.mathmodel_root),
        workspace_root=str(settings.workspace_root),
        examples_root=str(settings.examples_root),
        scripts=scripts,
    )


@app.get("/api/langgraph/status", response_model=LangGraphStatusResponse)
def get_langgraph_status() -> LangGraphStatusResponse:
    return LangGraphStatusResponse(**langgraph_status())


@app.get("/api/workspaces")
def get_workspaces() -> list[Any]:
    return discover_workspaces(get_settings())


@app.post("/api/workspaces", response_model=CreateWorkspaceResponse)
def create_workspace(payload: CreateWorkspaceRequest) -> CreateWorkspaceResponse:
    settings = get_settings()
    if payload.path:
        workspace = Path(payload.path)
    elif payload.name:
        workspace = settings.workspace_root / payload.name
    else:
        raise HTTPException(status_code=400, detail="Either path or name is required")
    workspace = ensure_allowed(workspace, settings)
    result = run_scaffold(settings, workspace, payload)
    parsed = result["parsed"]
    append_history(
        Path(parsed["workspace"]),
        {
            "event": "workspace_created",
            "note": f"Created by Control Center with contest={payload.contest}, engine={payload.engine}.",
        },
    )
    return CreateWorkspaceResponse(
        workspace=workspace_item(Path(parsed["workspace"]), settings),
        created=parsed.get("created", []),
        skipped=parsed.get("skipped", []),
        stdout=result["stdout"],
        stderr=result["stderr"],
    )


@app.get("/api/workspaces/{workspace_id}/summary", response_model=WorkspaceSummary)
def get_workspace_summary(workspace_id: str) -> WorkspaceSummary:
    settings = get_settings()
    workspace = workspace_from_id(workspace_id, settings)
    audit = run_audit(settings, workspace, nature="auto")
    result = audit["result"]
    required_missing = [item.path for item in list_artifacts(workspace) if item.required and not item.exists]
    return WorkspaceSummary(
        workspace=workspace_item(workspace, settings),
        status=str(result.get("status", "UNKNOWN")),
        worst_severity=str(result.get("worst_severity", "NONE")),
        phases=build_phase_summaries(workspace),
        required_missing=required_missing,
        manifest=manifest_summary(workspace),
        paper=paper_summary(workspace),
        issues=list(result.get("issues", [])),
        recommendations=build_recommendations(result, required_missing),
    )


@app.get("/api/workspaces/{workspace_id}/artifacts")
def get_workspace_artifacts(workspace_id: str) -> list[Any]:
    workspace = workspace_from_id(workspace_id, get_settings())
    return list_artifacts(workspace)


@app.get("/api/workspaces/{workspace_id}/artifact", response_model=ArtifactReadResponse)
def get_workspace_artifact(workspace_id: str, path: str = Query(...)) -> ArtifactReadResponse:
    workspace = workspace_from_id(workspace_id, get_settings())
    target = safe_artifact_path(workspace, path)
    if not target.exists():
        return ArtifactReadResponse(path=path, exists=False, type="missing")
    kind = artifact_type(target)
    if kind == "json":
        return ArtifactReadResponse(
            path=path,
            exists=True,
            type=kind,
            content=json.dumps(read_json(target), ensure_ascii=False, indent=2),
            data=read_json(target),
            absolute_path=str(target),
        )
    if kind in {"markdown", "text"}:
        return ArtifactReadResponse(path=path, exists=True, type=kind, content=read_text(target), absolute_path=str(target))
    return ArtifactReadResponse(path=path, exists=True, type=kind, absolute_path=str(target))


@app.get("/api/workspaces/{workspace_id}/raw")
def get_workspace_raw(workspace_id: str, path: str = Query(...)) -> FileResponse:
    workspace = workspace_from_id(workspace_id, get_settings())
    target = safe_artifact_path(workspace, path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(target))


@app.post("/api/workspaces/{workspace_id}/audit", response_model=AuditResponse)
def audit_workspace(workspace_id: str) -> AuditResponse:
    workspace = workspace_from_id(workspace_id, get_settings())
    before = run_audit(get_settings(), workspace)
    append_history(
        workspace,
        {
            "event": "audit",
            "status_after": str(before["result"].get("status", "UNKNOWN")),
            "note": f"Worst severity: {before['result'].get('worst_severity', 'NONE')}",
        },
    )
    return AuditResponse(**before)


@app.get("/api/benchmark/2022C", response_model=BenchmarkResponse)
def benchmark_2022c() -> BenchmarkResponse:
    return BenchmarkResponse(**run_benchmark(get_settings()))


@app.post("/api/workspaces/{workspace_id}/prompt", response_model=PromptResponse)
def prompt_workspace(workspace_id: str, payload: PromptRequest) -> PromptResponse:
    workspace = workspace_from_id(workspace_id, get_settings())
    audit = run_audit(get_settings(), workspace)
    prompt = build_prompt(workspace, payload.phase, payload.harness, issues=list(audit["result"].get("issues", [])))
    append_history(
        workspace,
        {
            "event": "prompt_generated",
            "phase": payload.phase,
            "harness": payload.harness,
            "status_before": str(audit["result"].get("status", "UNKNOWN")),
            "note": "Generated portable phase prompt.",
        },
    )
    return PromptResponse(
        phase=payload.phase,
        harness=payload.harness,
        prompt=prompt,
    )


@app.post("/api/workspaces/{workspace_id}/runs/copy", response_model=CopyRunResponse)
def copy_run_workspace(workspace_id: str, payload: CopyRunRequest) -> CopyRunResponse:
    settings = get_settings()
    workspace = workspace_from_id(workspace_id, settings)
    destination = copy_workspace_for_run(workspace, payload.name)
    append_history(
        workspace,
        {
            "event": "workspace_copied",
            "source_workspace": str(workspace),
            "run_workspace": str(destination),
            "note": "Created safe copied run workspace.",
        },
    )
    return CopyRunResponse(
        source=str(workspace),
        destination=str(destination),
        workspace=workspace_item(destination, settings),
    )


@app.get("/api/workspaces/{workspace_id}/runs/history", response_model=list[RunHistoryEntry])
def run_history(workspace_id: str) -> list[RunHistoryEntry]:
    workspace = workspace_from_id(workspace_id, get_settings())
    return [RunHistoryEntry(**item) for item in read_history(workspace)]


@app.post("/api/workspaces/{workspace_id}/revision-tasks", response_model=RevisionTasksResponse)
def revision_tasks(workspace_id: str) -> RevisionTasksResponse:
    workspace = workspace_from_id(workspace_id, get_settings())
    audit = run_audit(get_settings(), workspace)
    tasks = build_revision_tasks(audit["result"])
    target = workspace / "reports" / "REVISION_ACTIONS_CONTROL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(revision_tasks_markdown(tasks), encoding="utf-8")
    append_history(
        workspace,
        {
            "event": "revision_tasks_generated",
            "status_before": str(audit["result"].get("status", "UNKNOWN")),
            "note": f"Generated {len(tasks)} revision tasks.",
        },
    )
    return RevisionTasksResponse(tasks=tasks, written_path=str(target))


@app.post("/api/workspaces/{workspace_id}/source-files", response_model=SourceUploadResponse)
async def upload_source_files(workspace_id: str, files: list[UploadFile] = File(...)) -> SourceUploadResponse:
    workspace = workspace_from_id(workspace_id, get_settings())
    source = workspace / "source"
    source.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    skipped: list[str] = []
    for upload in files:
        filename = sanitize_filename(upload.filename or "")
        content = await upload.read()
        if not content:
            skipped.append(filename)
            continue
        target = source / filename
        target.write_bytes(content)
        saved.append(target.relative_to(workspace).as_posix())
    append_history(
        workspace,
        {
            "event": "source_uploaded",
            "note": f"Saved {len(saved)} source files.",
        },
    )
    return SourceUploadResponse(saved=saved, skipped=skipped)


@app.get("/api/harnesses", response_model=list[HarnessInfo])
def get_harnesses() -> list[HarnessInfo]:
    return harnesses()


@app.post("/api/workspaces/{workspace_id}/harness/prepare", response_model=PrepareHarnessResponse)
def prepare_harness(workspace_id: str, payload: PrepareHarnessRequest) -> PrepareHarnessResponse:
    workspace = workspace_from_id(workspace_id, get_settings())
    audit = run_audit(get_settings(), workspace)
    return PrepareHarnessResponse(
        **prepare_harness_run(
            workspace,
            payload.phase,
            payload.harness,
            copy_first=payload.copy_workspace,
            run_name=payload.run_name,
            issues=list(audit["result"].get("issues", [])),
        )
    )


@app.post("/api/workspaces/{workspace_id}/langgraph/run", response_model=LangGraphRunResponse)
def run_langgraph(workspace_id: str, payload: LangGraphRunRequest) -> LangGraphRunResponse:
    settings = get_settings()
    workspace = workspace_from_id(workspace_id, settings)
    try:
        result = run_langgraph_phase(
            settings=settings,
            source_workspace=workspace,
            phase=payload.phase,
            mode=payload.mode,
            provider=payload.provider,
            model=payload.model,
            copy_workspace=payload.copy_workspace,
            run_name=payload.run_name,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        )
    except LangGraphUnavailableError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ModelAdapterError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return LangGraphRunResponse(
        available=True,
        source_workspace=str(result["source_workspace"]),
        run_workspace=str(result["run_workspace"]),
        phase=int(result["phase"]),
        mode=str(result["mode"]),
        provider=str(result["provider"]),
        model=result.get("model"),
        status=str(result.get("status", "unknown")),
        prompt_path=result.get("prompt_path"),
        report_path=result.get("report_path"),
        pre_audit=result.get("pre_audit", {}),
        post_audit=result.get("post_audit", {}),
        issues=list(result.get("issues", [])),
        history=result.get("history"),
        phase_plan=result.get("phase_plan"),
        provider_error=result.get("provider_error"),
        plan_path=result.get("plan_path"),
        plan_markdown_path=result.get("plan_markdown_path"),
        raw_output_path=result.get("raw_output_path"),
        apply_diff_path=result.get("apply_diff_path"),
        files_planned=list(result.get("files_planned", [])),
        files_written=list(result.get("files_written", [])),
        files_rejected=list(result.get("files_rejected", [])),
        needs_human=bool(result.get("needs_human", False)),
        contest_status=result.get("contest_status"),
        completed_phases=list(result.get("completed_phases", [])),
        paused_at=result.get("paused_at"),
        human_gate_required=bool(result.get("human_gate_required", False)),
        human_gate_file=result.get("human_gate_file"),
        graph_report_path=result.get("graph_report_path"),
        phase_results=list(result.get("phase_results", [])),
        final_audit=result.get("final_audit", {}),
        sandbox_commands=list(result.get("sandbox_commands", [])),
        sandbox_status=result.get("sandbox_status"),
        manifest_created_empty=bool(result.get("manifest_created_empty", False)),
        paper_sandbox_status=result.get("paper_sandbox_status"),
        paper_files_written=list(result.get("paper_files_written", [])),
        claim_trace_path=result.get("claim_trace_path"),
        method_matrix_path=result.get("method_matrix_path"),
        paper_build_report_path=result.get("paper_build_report_path"),
        revision_sandbox_status=result.get("revision_sandbox_status"),
        revision_files_written=list(result.get("revision_files_written", [])),
        revision_status_path=result.get("revision_status_path"),
    )


@app.get("/api/debug/encode")
def debug_encode(path: str) -> dict[str, str]:
    settings = get_settings()
    resolved = ensure_allowed(Path(path), settings)
    return {"id": encode_workspace_id(resolved), "path": str(resolved)}
