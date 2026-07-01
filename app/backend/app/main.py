from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .models import (
    ArtifactReadResponse,
    AuditResponse,
    BenchmarkResponse,
    CopyRunRequest,
    CopyRunResponse,
    CreateWorkspaceRequest,
    CreateWorkspaceResponse,
    HealthResponse,
    PromptRequest,
    PromptResponse,
    ScriptStatus,
    WorkspaceSummary,
)
from .prompts import build_prompt
from .runner import run_audit, run_benchmark, run_scaffold
from .workspace import (
    artifact_type,
    build_phase_summaries,
    copy_workspace_for_run,
    discover_workspaces,
    encode_workspace_id,
    ensure_allowed,
    list_artifacts,
    manifest_summary,
    paper_summary,
    read_json,
    read_text,
    safe_artifact_path,
    workspace_from_id,
    workspace_item,
)


app = FastAPI(title="MathModel Control Center", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/api/workspaces/{workspace_id}/audit", response_model=AuditResponse)
def audit_workspace(workspace_id: str) -> AuditResponse:
    workspace = workspace_from_id(workspace_id, get_settings())
    return AuditResponse(**run_audit(get_settings(), workspace))


@app.get("/api/benchmark/2022C", response_model=BenchmarkResponse)
def benchmark_2022c() -> BenchmarkResponse:
    return BenchmarkResponse(**run_benchmark(get_settings()))


@app.post("/api/workspaces/{workspace_id}/prompt", response_model=PromptResponse)
def prompt_workspace(workspace_id: str, payload: PromptRequest) -> PromptResponse:
    workspace = workspace_from_id(workspace_id, get_settings())
    return PromptResponse(
        phase=payload.phase,
        harness=payload.harness,
        prompt=build_prompt(workspace, payload.phase, payload.harness),
    )


@app.post("/api/workspaces/{workspace_id}/runs/copy", response_model=CopyRunResponse)
def copy_run_workspace(workspace_id: str, payload: CopyRunRequest) -> CopyRunResponse:
    settings = get_settings()
    workspace = workspace_from_id(workspace_id, settings)
    destination = copy_workspace_for_run(workspace, payload.name)
    return CopyRunResponse(
        source=str(workspace),
        destination=str(destination),
        workspace=workspace_item(destination, settings),
    )


@app.get("/api/debug/encode")
def debug_encode(path: str) -> dict[str, str]:
    settings = get_settings()
    resolved = ensure_allowed(Path(path), settings)
    return {"id": encode_workspace_id(resolved), "path": str(resolved)}
