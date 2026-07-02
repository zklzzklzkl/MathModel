from __future__ import annotations

import json
import re
import shlex
import subprocess
from importlib import metadata
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from .config import Settings
from .langgraph_state import MathModelGraphState
from .model_adapters import ModelAdapterError, get_model_adapter
from .phase_plan import PhasePlan
from .prompts import build_prompt
from .runner import run_audit
from .workspace import append_history, copy_workspace_for_run


try:  # Optional dependency: keep the base Control Center lightweight.
    from langgraph.graph import END, StateGraph

    _StateGraph = StateGraph
    _END = END
    _LANGGRAPH_IMPORT_ERROR: str | None = None
except Exception as exc:  # pragma: no cover - depends on optional package state
    _StateGraph = None
    _END = None
    _LANGGRAPH_IMPORT_ERROR = str(exc)


class LangGraphUnavailableError(RuntimeError):
    """Raised when the optional LangGraph runtime is not installed."""


class RevisionSandboxError(ValueError):
    """Raised when the Phase 5 revision sandbox encounters a controlled rejection."""


APPLY_ALLOWED_PATHS: dict[int, set[str]] = {
    1: {
        "reports/MODEL_CANDIDATES.md",
        "reports/MODEL_REVIEW_AI.md",
        "reports/FIGURE_PLAN.md",
        "reports/REFINEMENT_LOG.md",
    },
    4: {
        "reports/PAPER_SCORECARD.md",
        "reports/REVISION_ACTIONS.md",
        "reports/REFINEMENT_LOG.md",
    },
}

LANGGRAPH_INFRA_PATHS = {
    "reports/LANGGRAPH_RUN_REPORT.md",
    "reports/LANGGRAPH_PHASE_PLAN.json",
    "reports/LANGGRAPH_PHASE_PLAN.md",
    "reports/LANGGRAPH_RAW_MODEL_OUTPUT.md",
    "reports/LANGGRAPH_APPLY_DIFF.md",
    "reports/LANGGRAPH_CONTEST_GRAPH_REPORT.md",
    "reports/AGENT_RUNS.md",
}

SUPPORTED_MODES = {
    "dry_run",
    "llm_plan",
    "controlled_apply",
    "phase_execute",
    "contest_graph_v0",
    "contest_graph_v1",
    "contest_graph_v2",
    "contest_graph_v3",
}
HUMAN_MODEL_GATE = "reports/HUMAN_MODEL_REVIEW.md"
HUMAN_MODEL_APPROVAL_SIGNALS = (
    "approval",
    "approved",
    "adopt",
    "accepted",
    "confirm",
    "confirmed",
    "通过",
    "确认",
    "同意",
    "采用",
    "批准",
)
PHASE2_ALLOWED_OUTPUT_FILES = {
    "results/RESULTS_MANIFEST.json",
    "reports/EXPERIMENT_LOG.md",
    "reports/TEMPLATE_ADAPTATION_LOG.md",
    "reports/RESULTS_REPORT.md",
    "reports/FIGURE_PLAN.md",
    "reports/FIGURE_AUDIT.md",
    "reports/LANGGRAPH_RUN_REPORT.md",
    "reports/LANGGRAPH_PHASE_PLAN.json",
    "reports/LANGGRAPH_PHASE_PLAN.md",
    "reports/AGENT_RUNS.md",
    "reports/LANGGRAPH_CONTEST_GRAPH_REPORT.md",
}
PHASE2_ALLOWED_OUTPUT_DIRS = {"code", "code/outputs", "figures"}
PHASE2_FORBIDDEN_COMMANDS = {
    "rm",
    "del",
    "rmdir",
    "curl",
    "wget",
    "pip",
    "conda",
    "powershell",
    "pwsh",
    "bash",
    "sh",
    "cmd",
}
PHASE2_FORBIDDEN_TOKENS = {"|", ">", "<", "&&", "||", ";", "`"}
PHASE3_ALLOWED_FILES = {
    "paper/main.tex",
    "paper/main.typ",
    "paper/README.md",
    "reports/CLAIM_TRACE.md",
    "reports/METHOD_IMPLEMENTATION_MATRIX.md",
    "reports/PAPER_BUILD_REPORT.md",
    "reports/FIGURE_AUDIT.md",
    "reports/LANGGRAPH_RUN_REPORT.md",
    "reports/LANGGRAPH_PHASE_PLAN.json",
    "reports/LANGGRAPH_PHASE_PLAN.md",
    "reports/AGENT_RUNS.md",
    "reports/LANGGRAPH_CONTEST_GRAPH_REPORT.md",
}
PHASE3_REQUIRED_REPORTS = {
    "reports/CLAIM_TRACE.md",
    "reports/METHOD_IMPLEMENTATION_MATRIX.md",
    "reports/PAPER_BUILD_REPORT.md",
}
PHASE5_ALLOWED_FILES = {
    "paper/main.tex",
    "paper/main.typ",
    "paper/README.md",
    "reports/CLAIM_TRACE.md",
    "reports/METHOD_IMPLEMENTATION_MATRIX.md",
    "reports/PAPER_BUILD_REPORT.md",
    "reports/REVISION_STATUS.md",
    "reports/REFINEMENT_LOG.md",
}
PHASE5_FORBIDDEN_PREFIXES = {
    "source/",
    "code/",
    "figures/",
    "results/",
}
PHASE5_FORBIDDEN_EXACT = {
    "reports/HUMAN_MODEL_REVIEW.md",
    "reports/MODELING_DECISION.md",
    "reports/VERIFY_REPORT.md",
}
PHASE5_REQUIRED_REPORTS = {
    "reports/REVISION_STATUS.md",
    "reports/REFINEMENT_LOG.md",
}


def _is_apply_mode(mode: str) -> bool:
    return mode in {"controlled_apply", "phase_execute"}


def _is_contest_graph_mode(mode: str) -> bool:
    return mode in {"contest_graph_v0", "contest_graph_v1", "contest_graph_v2", "contest_graph_v3"}


def langgraph_available() -> bool:
    return _StateGraph is not None


def langgraph_status() -> dict[str, Any]:
    if not langgraph_available():
        return {
            "available": False,
            "version": None,
            "import_error": _LANGGRAPH_IMPORT_ERROR or "langgraph is not installed",
            "note": "Install optional dependencies with: pip install -r app/backend/requirements-langgraph.txt",
        }
    try:
        version = metadata.version("langgraph")
    except metadata.PackageNotFoundError:  # pragma: no cover - unusual import state
        version = "unknown"
    return {
        "available": True,
        "version": version,
        "import_error": None,
        "note": "LangGraph Phase Runner is available. Supported modes: dry_run, llm_plan, controlled_apply, phase_execute, contest_graph_v0, contest_graph_v1, contest_graph_v2, contest_graph_v3.",
    }


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def assert_run_workspace_allowed(state: MathModelGraphState) -> None:
    source = Path(state["source_workspace"]).resolve()
    run = Path(state["run_workspace"]).resolve()
    allowed_runs_root = source / "runs"
    if run == source:
        return
    if _is_relative_to(run, allowed_runs_root):
        return
    raise ValueError("LangGraph run workspace must be the source workspace or a copied workspace under source/runs.")


def allowed_apply_paths(phase: int) -> set[str]:
    return set(APPLY_ALLOWED_PATHS.get(phase, set()))


def validate_apply_path(workspace: Path, relative_path: str, phase: int) -> Path:
    if not relative_path or not isinstance(relative_path, str):
        raise ValueError("Apply path must be a non-empty relative path.")
    raw = Path(relative_path)
    if raw.is_absolute():
        raise ValueError(f"Apply path must be relative: {relative_path}")
    if any(part == ".." for part in raw.parts):
        raise ValueError(f"Apply path must not contain '..': {relative_path}")
    normalized = raw.as_posix()
    if normalized not in allowed_apply_paths(phase):
        raise ValueError(f"Apply path is not allowed for phase {phase}: {normalized}")
    workspace = workspace.resolve()
    target = (workspace / raw).resolve()
    if not _is_relative_to(target, workspace):
        raise ValueError(f"Apply path escapes run workspace: {relative_path}")
    return target


def check_human_model_gate(workspace: Path) -> dict[str, Any]:
    gate_path = workspace / HUMAN_MODEL_GATE
    exists = gate_path.is_file()
    content = gate_path.read_text(encoding="utf-8", errors="replace") if exists else ""
    lower = content.lower()
    matched = next((signal for signal in HUMAN_MODEL_APPROVAL_SIGNALS if signal in lower or signal in content), None)
    return {
        "gate_file": HUMAN_MODEL_GATE,
        "path": str(gate_path),
        "exists": exists,
        "approved": bool(matched),
        "approval_signal": matched,
        "reason": "Human model review approval found." if matched else "Human model review approval is missing.",
    }


def _normalize_relative_path(relative_path: str) -> str:
    if not relative_path or not isinstance(relative_path, str):
        raise ValueError("Path must be a non-empty relative path.")
    raw = Path(relative_path)
    if raw.is_absolute():
        raise ValueError(f"Path must be relative: {relative_path}")
    if any(part == ".." for part in raw.parts):
        raise ValueError(f"Path must not contain '..': {relative_path}")
    return raw.as_posix()


def _is_phase2_allowed_path(relative_path: str) -> bool:
    normalized = _normalize_relative_path(relative_path)
    if normalized in PHASE2_ALLOWED_OUTPUT_FILES:
        return True
    return any(normalized == prefix or normalized.startswith(f"{prefix}/") for prefix in PHASE2_ALLOWED_OUTPUT_DIRS)


def validate_phase2_path(workspace: Path, relative_path: str) -> Path:
    normalized = _normalize_relative_path(relative_path)
    if not _is_phase2_allowed_path(normalized):
        raise ValueError(f"Phase 2 sandbox path is not allowed: {normalized}")
    workspace = workspace.resolve()
    target = (workspace / normalized).resolve()
    if not _is_relative_to(target, workspace):
        raise ValueError(f"Phase 2 sandbox path escapes run workspace: {normalized}")
    return target


def _validate_phase2_script_path(workspace: Path, relative_path: str) -> Path:
    normalized = _normalize_relative_path(relative_path)
    if not (normalized.startswith("code/") or normalized.startswith("tests/")):
        raise ValueError(f"Python script must live under code/ or tests/: {normalized}")
    if not normalized.endswith(".py"):
        raise ValueError(f"Python script must be a .py file: {normalized}")
    target = (workspace.resolve() / normalized).resolve()
    if not _is_relative_to(target, workspace.resolve()):
        raise ValueError(f"Python script escapes run workspace: {normalized}")
    if not target.is_file():
        raise ValueError(f"Python script does not exist: {normalized}")
    return target


def _split_command(command: str) -> list[str]:
    if not command or not isinstance(command, str):
        raise ValueError("Command must be a non-empty string.")
    if any(token in command for token in PHASE2_FORBIDDEN_TOKENS):
        raise ValueError(f"Command contains forbidden shell metacharacters: {command}")
    try:
        parts = shlex.split(command, posix=True)
    except ValueError as exc:
        raise ValueError(f"Command cannot be parsed safely: {command}") from exc
    if not parts:
        raise ValueError("Command must not be empty.")
    lower_parts = [part.lower() for part in parts]
    if lower_parts[0] in PHASE2_FORBIDDEN_COMMANDS:
        raise ValueError(f"Command is forbidden in Phase 2 sandbox: {parts[0]}")
    if lower_parts[0] == "powershell" and any(part.lower() in {"-enc", "-encodedcommand"} for part in parts[1:]):
        raise ValueError("Encoded PowerShell commands are forbidden.")
    if any(part.lower() in {"install", "download"} for part in parts) and lower_parts[0] in {"pip", "conda"}:
        raise ValueError("Package installation commands are forbidden.")
    return parts


def validate_phase2_commands(workspace: Path, commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    for index, item in enumerate(commands, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Command item {index} must be an object.")
        command_id = str(item.get("id") or f"C{index}")
        purpose = str(item.get("purpose") or "")
        command = str(item.get("command") or "")
        expected_outputs = item.get("expected_outputs", [])
        if not purpose:
            raise ValueError(f"Command {command_id} purpose is required.")
        if not isinstance(expected_outputs, list):
            raise ValueError(f"Command {command_id} expected_outputs must be a list.")
        parts = _split_command(command)
        lower = parts[0].lower()
        run_args: list[str]
        if lower == "python":
            if len(parts) == 4 and parts[1] == "-m" and parts[2] == "py_compile":
                script = _validate_phase2_script_path(workspace, parts[3])
                run_args = ["python", "-m", "py_compile", _relative_or_absolute(script, workspace)]
            elif len(parts) == 2:
                script = _validate_phase2_script_path(workspace, parts[1])
                run_args = ["python", _relative_or_absolute(script, workspace)]
            else:
                raise ValueError(f"Only 'python <script>.py' and 'python -m py_compile <script>.py' are allowed: {command}")
        elif lower == "pytest":
            if not parts[1:]:
                raise ValueError("pytest must be scoped to a workspace tests path.")
            for arg in parts[1:]:
                if arg.startswith("-"):
                    continue
                normalized = _normalize_relative_path(arg)
                if not (normalized == "tests" or normalized.startswith("tests/")):
                    raise ValueError(f"pytest target must stay under tests/: {normalized}")
            run_args = parts
        else:
            raise ValueError(f"Only python and scoped pytest commands are allowed in Phase 2 sandbox: {parts[0]}")
        normalized_outputs = []
        for output in expected_outputs:
            normalized = _normalize_relative_path(str(output))
            validate_phase2_path(workspace, normalized)
            normalized_outputs.append(normalized)
        validated.append(
            {
                "id": command_id,
                "purpose": purpose,
                "command": command,
                "args": run_args,
                "expected_outputs": normalized_outputs,
                "status": "VALIDATED",
            }
        )
    return validated


def validate_phase3_path(workspace: Path, relative_path: str) -> Path:
    normalized = _normalize_relative_path(relative_path)
    if normalized not in PHASE3_ALLOWED_FILES:
        raise ValueError(f"Phase 3 paper sandbox path is not allowed: {normalized}")
    workspace = workspace.resolve()
    target = (workspace / normalized).resolve()
    if not _is_relative_to(target, workspace):
        raise ValueError(f"Phase 3 paper sandbox path escapes run workspace: {normalized}")
    return target


def validate_phase5_path(workspace: Path, relative_path: str) -> Path:
    normalized = _normalize_relative_path(relative_path)
    allowed = PHASE5_ALLOWED_FILES | LANGGRAPH_INFRA_PATHS
    if normalized not in allowed:
        raise ValueError(f"Phase 5 revision sandbox path is not allowed: {normalized}")
    for prefix in PHASE5_FORBIDDEN_PREFIXES:
        if normalized == prefix.rstrip("/") or normalized.startswith(prefix):
            raise ValueError(f"Phase 5 revision sandbox path is forbidden: {normalized}")
    if normalized in PHASE5_FORBIDDEN_EXACT:
        raise ValueError(f"Phase 5 revision sandbox path is forbidden: {normalized}")
    workspace = workspace.resolve()
    target = (workspace / normalized).resolve()
    if not _is_relative_to(target, workspace):
        raise ValueError(f"Phase 5 revision sandbox path escapes run workspace: {normalized}")
    return target


def _require_text_columns(content: str, required: list[str], path: str) -> None:
    lower = content.lower()
    missing = [item for item in required if item.lower() not in lower]
    if missing:
        raise ValueError(f"{path} is missing required fields: {', '.join(missing)}")


def _validate_paper_draft_content(path: str, content: str) -> None:
    if path not in {"paper/main.tex", "paper/main.typ"}:
        return
    required = [
        "摘要",
        "问题重述",
        "符号说明",
        "模型假设",
        "模型建立",
        "求解",
        "实验结果",
        "优缺点",
        "参考文献",
        "AI生成",
        "待人工确认",
    ]
    _require_text_columns(content, required, path)


def validate_phase3_writes(workspace: Path, writes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(writes, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Phase 3 write item {index} must be an object.")
        path = _normalize_relative_path(str(item.get("path") or ""))
        purpose = str(item.get("purpose") or "")
        content = item.get("content")
        if not purpose:
            raise ValueError(f"Phase 3 write {path} purpose is required.")
        if not isinstance(content, str) or not content:
            raise ValueError(f"Phase 3 write {path} content must be a non-empty string.")
        validate_phase3_path(workspace, path)
        if path == "reports/CLAIM_TRACE.md":
            _require_text_columns(
                content,
                [
                    "claim_id",
                    "paper_section",
                    "claim_text",
                    "evidence_source",
                    "source_quality",
                    "supporting_artifact",
                    "risk_note",
                    "status",
                ],
                path,
            )
        if path == "reports/METHOD_IMPLEMENTATION_MATRIX.md":
            _require_text_columns(
                content,
                [
                    "method",
                    "implementation_file",
                    "input_data",
                    "output_artifacts",
                    "validation_status",
                    "related_claims",
                    "known_gaps",
                ],
                path,
            )
        if path == "reports/PAPER_BUILD_REPORT.md":
            _require_text_columns(
                content,
                [
                    "generated paper files",
                    "used result artifacts",
                    "missing artifacts",
                    "claims generated",
                    "unresolved risks",
                    "next human actions",
                ],
                path,
            )
        _validate_paper_draft_content(path, content)
        seen.add(path)
        validated.append({"path": path, "purpose": purpose, "content": content, "status": "VALIDATED"})
    paper_present = bool({"paper/main.tex", "paper/main.typ", "paper/README.md"} & seen)
    if validated and not paper_present:
        raise ValueError("Phase 3 paper sandbox requires at least one paper draft file.")
    return validated


def _audit_summary(audit: dict[str, Any]) -> dict[str, Any]:
    result = audit.get("result", {})
    if not isinstance(result, dict):
        result = {}
    summary = result.get("summary", {})
    return {
        "status": result.get("status", "UNKNOWN"),
        "worst_severity": result.get("worst_severity", "NONE"),
        "issue_count": len(result.get("issues", []) if isinstance(result.get("issues"), list) else []),
        "summary": summary if isinstance(summary, dict) else {},
        "returncode": audit.get("returncode"),
    }


def _workspace_file_snapshot(workspace: Path) -> dict[str, bytes]:
    snapshot: dict[str, bytes] = {}
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        try:
            relative = path.resolve().relative_to(workspace.resolve()).as_posix()
        except ValueError:
            continue
        try:
            snapshot[relative] = path.read_bytes()
        except OSError:
            continue
    return snapshot


def _changed_files_since(workspace: Path, before: dict[str, bytes]) -> list[str]:
    changed: list[str] = []
    seen: set[str] = set()
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        try:
            relative = path.resolve().relative_to(workspace.resolve()).as_posix()
            content = path.read_bytes()
        except (OSError, ValueError):
            continue
        seen.add(relative)
        if before.get(relative) != content:
            changed.append(relative)
    for relative in before:
        if relative not in seen:
            changed.append(relative)
    return sorted(set(changed))


def _restore_workspace_snapshot(workspace: Path, before: dict[str, bytes]) -> None:
    current = _workspace_file_snapshot(workspace)
    for relative in current:
        if relative not in before:
            target = (workspace / relative).resolve()
            if _is_relative_to(target, workspace):
                target.unlink(missing_ok=True)
    for relative, content in before.items():
        target = (workspace / relative).resolve()
        if _is_relative_to(target, workspace):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)


def _stdout_summary(text: str, limit: int = 1200) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n")
    return text if len(text) <= limit else text[:limit] + "\n...[truncated]"


def _relative_or_absolute(path: Path, workspace: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _write_text_tracked(state: MathModelGraphState, path: Path, text: str) -> None:
    run_workspace = Path(state["run_workspace"])
    existed = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    relative = _relative_or_absolute(path, run_workspace)
    target = state["updated_files"] if existed else state["created_files"]
    if relative not in target:
        target.append(relative)


def ensure_results_manifest(state: MathModelGraphState) -> bool:
    manifest = Path(state["run_workspace"]) / "results" / "RESULTS_MANIFEST.json"
    if manifest.is_file():
        return False
    empty = {"metrics": [], "tables": [], "figures": [], "scripts": []}
    _write_text_tracked(state, manifest, json.dumps(empty, ensure_ascii=False, indent=2) + "\n")
    return True


def write_experiment_log(state: MathModelGraphState, command_results: list[dict[str, Any]], generated_files: list[str]) -> Path:
    sections = ["# LangGraph Phase 2 Experiment Log", ""]
    for item in command_results:
        sections.extend(
            [
                f"## {item.get('id', '')}: {item.get('purpose', '')}",
                "",
                f"- Command: `{item.get('command', '')}`",
                f"- Working directory: `{state['run_workspace']}`",
                f"- Return code: {item.get('returncode')}",
                f"- Status: {item.get('status')}",
                "",
                "### stdout",
                "",
                "```text",
                item.get("stdout", "") or "",
                "```",
                "",
                "### stderr",
                "",
                "```text",
                item.get("stderr", "") or "",
                "```",
                "",
            ]
        )
    sections.extend(
        [
            "## Generated or Updated Files",
            "",
            *(f"- {path}" for path in generated_files),
            "",
            f"- manifest_created_empty: {state.get('manifest_created_empty', False)}",
            "",
        ]
    )
    target = Path(state["run_workspace"]) / "reports" / "EXPERIMENT_LOG.md"
    validate_phase2_path(Path(state["run_workspace"]), "reports/EXPERIMENT_LOG.md")
    _write_text_tracked(state, target, "\n".join(sections))
    return target


def _append_phase2_agent_run(state: MathModelGraphState) -> None:
    commands = ", ".join(item.get("id", "") for item in state.get("sandbox_commands", [])) or "none"
    entry = f"""## LangGraph Phase 2 Sandbox

- Mode: {state['mode']}
- Provider: {state['provider']}
- Model: {state['model'] or 'none'}
- Status: {state.get('sandbox_status') or state.get('status')}
- Commands: {commands}
- manifest_created_empty: {state.get('manifest_created_empty', False)}
- Stop reason: {state.get('stop_reason') or 'none'}
"""
    _write_langgraph_file(state, "reports/AGENT_RUNS.md", _existing_agent_runs(state) + entry + "\n")


def _append_phase2_history(state: MathModelGraphState) -> dict[str, Any]:
    return append_history(
        Path(state["source_workspace"]),
        {
            "event": "langgraph_phase2_sandbox",
            "phase": 2,
            "harness": "LangGraph",
            "source_workspace": state["source_workspace"],
            "run_workspace": state["run_workspace"],
            "prompt_path": state.get("prompt_path"),
            "status_after": state.get("sandbox_status") or state.get("status"),
            "note": state.get("stop_reason"),
        },
    )


def _result_artifact_status(workspace: Path) -> dict[str, Any]:
    manifest_path = workspace / "results" / "RESULTS_MANIFEST.json"
    status = {
        "manifest_path": "results/RESULTS_MANIFEST.json",
        "manifest_exists": manifest_path.is_file(),
        "manifest_empty": True,
        "used_result_artifacts": [],
        "missing_artifacts": [],
        "risk_note": "",
    }
    if not manifest_path.is_file():
        status["missing_artifacts"].append("results/RESULTS_MANIFEST.json")
        status["risk_note"] = "manifest missing or empty; paper draft must not fabricate results."
    else:
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            data = {}
            status["missing_artifacts"].append("results/RESULTS_MANIFEST.json: invalid json")
        collections = [
            data.get("metrics", []),
            data.get("tables", []),
            data.get("figures", []),
            data.get("scripts", []),
        ] if isinstance(data, dict) else []
        status["manifest_empty"] = not any(bool(item) for item in collections if isinstance(item, list))
        if status["manifest_empty"]:
            status["risk_note"] = "manifest missing or empty; paper draft must not fabricate results."
        else:
            status["used_result_artifacts"].append("results/RESULTS_MANIFEST.json")
    for artifact in ["reports/RESULTS_REPORT.md", "reports/FIGURE_PLAN.md", "reports/FIGURE_AUDIT.md"]:
        if (workspace / artifact).is_file():
            status["used_result_artifacts"].append(artifact)
        else:
            status["missing_artifacts"].append(artifact)
    return status


def _paper_readme_skeleton(result_status: dict[str, Any]) -> str:
    risk = result_status.get("risk_note") or "Human review required before treating this draft as final."
    return f"""# Paper Draft Sandbox

This is an AI generated draft workspace note.

## Existing results

{', '.join(result_status.get('used_result_artifacts', [])) or 'No verified result artifacts available.'}

## Missing results

{', '.join(result_status.get('missing_artifacts', [])) or 'None detected by sandbox.'}

## Human confirmation required

- Check every claim against `reports/CLAIM_TRACE.md`.
- Run Phase 4 contest review before any final verification.

## Risk

{risk}
"""


def ensure_claim_trace(state: MathModelGraphState, result_status: dict[str, Any]) -> Path:
    path = Path(state["run_workspace"]) / "reports" / "CLAIM_TRACE.md"
    if path.is_file():
        state["claim_trace_path"] = str(path)
        return path
    content = """| claim_id | paper_section | claim_text | evidence_source | source_quality | supporting_artifact | risk_note | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C-DRAFT-001 | 求解与实验结果 | 结果内容待人工确认 | local artifacts | B | reports/RESULTS_REPORT.md | manifest missing or empty; do not fabricate metrics | DRAFT_RISK |
"""
    _write_text_tracked(state, path, content)
    state["claim_trace_path"] = str(path)
    return path


def ensure_method_implementation_matrix(state: MathModelGraphState, result_status: dict[str, Any]) -> Path:
    path = Path(state["run_workspace"]) / "reports" / "METHOD_IMPLEMENTATION_MATRIX.md"
    if path.is_file():
        state["method_matrix_path"] = str(path)
        return path
    content = """| method | implementation_file | input_data | output_artifacts | validation_status | related_claims | known_gaps |
| --- | --- | --- | --- | --- | --- | --- |
| draft-method | code/solve.py | source data | results/RESULTS_MANIFEST.json | DRAFT_RISK | C-DRAFT-001 | Human must confirm implementation and evidence |
"""
    _write_text_tracked(state, path, content)
    state["method_matrix_path"] = str(path)
    return path


def write_paper_build_report(state: MathModelGraphState, result_status: dict[str, Any], written: list[str]) -> Path:
    path = Path(state["run_workspace"]) / "reports" / "PAPER_BUILD_REPORT.md"
    if path.is_file():
        state["paper_build_report_path"] = str(path)
        return path
    generated = "\n".join(f"- {item}" for item in written if item.startswith("paper/")) or "- paper/README.md"
    used = "\n".join(f"- {item}" for item in result_status.get("used_result_artifacts", [])) or "- none"
    missing = "\n".join(f"- {item}" for item in result_status.get("missing_artifacts", [])) or "- none"
    content = f"""# Paper Build Report

## generated paper files
{generated}

## used result artifacts
{used}

## missing artifacts
{missing}

## claims generated
- C-DRAFT-001

## unresolved risks
- {result_status.get('risk_note') or 'Human review required before treating this draft as final.'}

## next human actions
- Review paper draft and evidence trace.
- Run Phase 4 contest review.
- Do not claim final PASS from this draft.
"""
    _write_text_tracked(state, path, content)
    state["paper_build_report_path"] = str(path)
    return path


def _append_phase3_agent_run(state: MathModelGraphState) -> None:
    written = ", ".join(state.get("paper_files_written", [])) or "none"
    entry = f"""## LangGraph Phase 3 Paper Sandbox

- Mode: {state['mode']}
- Provider: {state['provider']}
- Model: {state['model'] or 'none'}
- Status: {state.get('paper_sandbox_status') or state.get('status')}
- Paper files written: {written}
- Claim trace: {state.get('claim_trace_path') or 'none'}
- Method matrix: {state.get('method_matrix_path') or 'none'}
- Paper build report: {state.get('paper_build_report_path') or 'none'}
- Stop reason: {state.get('stop_reason') or 'none'}
"""
    _write_langgraph_file(state, "reports/AGENT_RUNS.md", _existing_agent_runs(state) + entry + "\n")


def _append_phase3_history(state: MathModelGraphState) -> dict[str, Any]:
    return append_history(
        Path(state["source_workspace"]),
        {
            "event": "langgraph_phase3_paper_sandbox",
            "phase": 3,
            "harness": "LangGraph",
            "source_workspace": state["source_workspace"],
            "run_workspace": state["run_workspace"],
            "prompt_path": state.get("prompt_path"),
            "status_after": state.get("paper_sandbox_status") or state.get("status"),
            "note": state.get("stop_reason"),
        },
    )


def summarize_phase3_outputs(state: MathModelGraphState) -> dict[str, Any]:
    return {
        "paper_sandbox_status": state.get("paper_sandbox_status"),
        "paper_files_written": list(state.get("paper_files_written", [])),
        "claim_trace_path": state.get("claim_trace_path"),
        "method_matrix_path": state.get("method_matrix_path"),
        "paper_build_report_path": state.get("paper_build_report_path"),
        "paper_sandbox_error": state.get("paper_sandbox_error"),
    }


def run_phase3_paper_sandbox(state: MathModelGraphState) -> dict[str, Any]:
    assert_run_workspace_allowed(state)
    run_workspace = Path(state["run_workspace"]).resolve()
    source_workspace = Path(state["source_workspace"]).resolve()
    allowed_root = source_workspace / "runs"
    if run_workspace == source_workspace or not _is_relative_to(run_workspace, allowed_root):
        raise ValueError("Phase 3 paper sandbox may only run inside a copied run workspace.")
    plan = state.get("phase_plan") or {}
    writes = plan.get("file_writes", []) if isinstance(plan, dict) else []
    state["paper_files_written"] = []
    state["paper_sandbox_error"] = None
    state["claim_trace_path"] = None
    state["method_matrix_path"] = None
    state["paper_build_report_path"] = None
    result_status = _result_artifact_status(run_workspace)
    try:
        validated = validate_phase3_writes(run_workspace, writes) if writes else []
    except ValueError as exc:
        state["paper_sandbox_status"] = "PAPER_SANDBOX_REJECTED"
        state["status"] = "PAPER_SANDBOX_REJECTED"
        state["paper_sandbox_error"] = str(exc)
        state["stop_reason"] = str(exc)
        state["needs_human"] = True
        _append_phase3_agent_run(state)
        state["history"] = _append_phase3_history(state)
        return summarize_phase3_outputs(state) | {"paper_files_rejected": [{"reason": str(exc)}]}

    before = _workspace_file_snapshot(run_workspace)
    try:
        for item in validated:
            target = validate_phase3_path(run_workspace, item["path"])
            _write_text_tracked(state, target, item["content"])
            if item["path"] not in state["paper_files_written"]:
                state["paper_files_written"].append(item["path"])
        if not validated:
            readme = Path(state["run_workspace"]) / "paper" / "README.md"
            _write_text_tracked(state, readme, _paper_readme_skeleton(result_status))
            state["paper_files_written"].append("paper/README.md")
        ensure_claim_trace(state, result_status)
        ensure_method_implementation_matrix(state, result_status)
        write_paper_build_report(state, result_status, state["paper_files_written"])
    except Exception as exc:
        _restore_workspace_snapshot(run_workspace, before)
        state["paper_files_written"] = []
        state["paper_sandbox_status"] = "PAPER_SANDBOX_ROLLED_BACK"
        state["status"] = "PAPER_SANDBOX_ROLLED_BACK"
        state["paper_sandbox_error"] = str(exc)
        state["stop_reason"] = f"Phase 3 paper sandbox failed and rolled back: {exc}"
        state["needs_human"] = True
        return summarize_phase3_outputs(state)

    changed = _changed_files_since(run_workspace, before)
    forbidden_changes = [path for path in changed if path not in PHASE3_ALLOWED_FILES]
    if forbidden_changes:
        _restore_workspace_snapshot(run_workspace, before)
        state["paper_files_written"] = []
        state["paper_sandbox_status"] = "PAPER_SANDBOX_REJECTED"
        state["status"] = "PAPER_SANDBOX_REJECTED"
        state["paper_sandbox_error"] = "Phase 3 sandbox attempted forbidden writes: " + ", ".join(forbidden_changes)
        state["stop_reason"] = state["paper_sandbox_error"]
        state["needs_human"] = True
        return summarize_phase3_outputs(state)

    for required in PHASE3_REQUIRED_REPORTS:
        if required not in state["paper_files_written"] and (run_workspace / required).is_file():
            state["paper_files_written"].append(required)
    state["paper_sandbox_status"] = "PAPER_SANDBOX_SUCCEEDED"
    state["status"] = "PAPER_SANDBOX_SUCCEEDED"
    state["stop_reason"] = "Phase 3 paper draft sandbox completed. Phase 4 contest review is still required."
    state["needs_human"] = True
    _append_phase3_agent_run(state)
    state["history"] = _append_phase3_history(state)
    return summarize_phase3_outputs(state) | {"result_artifact_status": result_status}


# ---------------------------------------------------------------------------
# Phase 5 Revision Integrator Sandbox
# ---------------------------------------------------------------------------


def validate_phase5_writes(workspace: Path, writes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(writes, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Phase 5 write item {index} must be an object.")
        path = _normalize_relative_path(str(item.get("path") or ""))
        purpose = str(item.get("purpose") or "")
        content = item.get("content")
        if not purpose:
            raise ValueError(f"Phase 5 write {path} purpose is required.")
        if not isinstance(content, str) or not content:
            raise ValueError(f"Phase 5 write {path} content must be a non-empty string.")
        validate_phase5_path(workspace, path)
        if path == "reports/CLAIM_TRACE.md":
            _require_text_columns(
                content,
                [
                    "claim_id",
                    "paper_section",
                    "claim_text",
                    "evidence_source",
                    "source_quality",
                    "supporting_artifact",
                    "risk_note",
                    "status",
                ],
                path,
            )
        if path == "reports/METHOD_IMPLEMENTATION_MATRIX.md":
            _require_text_columns(
                content,
                [
                    "method",
                    "implementation_file",
                    "input_data",
                    "output_artifacts",
                    "validation_status",
                    "related_claims",
                    "known_gaps",
                ],
                path,
            )
        if path == "reports/PAPER_BUILD_REPORT.md":
            _require_text_columns(
                content,
                [
                    "generated paper files",
                    "used result artifacts",
                    "missing artifacts",
                    "claims generated",
                    "unresolved risks",
                    "next human actions",
                ],
                path,
            )
        if path == "reports/REVISION_STATUS.md":
            _require_text_columns(
                content,
                [
                    "revision_actions_exists",
                    "blocker_high_count",
                    "unresolved_blocker_high",
                    "next_action",
                ],
                path,
            )
        seen.add(path)
        validated.append({"path": path, "purpose": purpose, "content": content, "status": "VALIDATED"})
    if validated:
        if not any(item["path"].startswith("paper/") for item in validated) and not any(
            item["path"] == "reports/REVISION_STATUS.md" for item in validated
        ):
            raise ValueError("Phase 5 revision sandbox requires at least one paper file or REVISION_STATUS.md.")
    return validated


def parse_revision_actions(run_workspace: Path) -> dict[str, Any]:
    path = run_workspace / "reports" / "REVISION_ACTIONS.md"
    if not path.is_file():
        return {
            "exists": False,
            "path": str(path),
            "blocker_high_count": 0,
            "items": [],
            "raw": "",
        }
    raw = path.read_text(encoding="utf-8", errors="replace")
    lower = raw.lower()
    items: list[dict[str, str]] = []
    blocker_high_count = 0
    for severity in ("blocker", "high"):
        if severity in lower:
            count = lower.count(severity)
            blocker_high_count += count
            for _ in range(count):
                items.append({"severity": severity.upper(), "detected": True})
    return {
        "exists": True,
        "path": str(path),
        "blocker_high_count": blocker_high_count,
        "items": items,
        "raw": raw[:2000],
    }


def write_revision_status(state: MathModelGraphState, actions: dict[str, Any], sandbox_status: str) -> Path:
    path = Path(state["run_workspace"]) / "reports" / "REVISION_STATUS.md"
    if actions["exists"]:
        unresolved = actions["blocker_high_count"] > 0
        status_text = "blocker_high_unresolved" if unresolved else "blocker_high_resolved_or_absent"
        content = (
            f"# Revision Status\n\n"
            f"- revision_actions_exists: true\n"
            f"- blocker_high_count: {actions['blocker_high_count']}\n"
            f"- unresolved_blocker_high: {str(unresolved).lower()}\n"
            f"- sandbox_status: {sandbox_status}\n"
            f"- next_action: "
            f"{'Human reviewer must confirm whether BLOCKER/HIGH issues are resolved.' if unresolved else 'Proceed to Phase 6 audit-only; human review still required.'}\n"
        )
    else:
        content = (
            "# Revision Status\n\n"
            "- revision_actions_exists: false\n"
            "- blocker_high_count: 0\n"
            "- unresolved_blocker_high: false\n"
            f"- sandbox_status: {sandbox_status}\n"
            "- next_action: No revision actions file was found. Proceed to Phase 6 audit-only; human review still required.\n"
        )
    _write_text_tracked(state, path, content)
    state["revision_status_path"] = str(path)
    if "reports/REVISION_STATUS.md" not in state.get("revision_files_written", []):
        revision_list = state.setdefault("revision_files_written", [])
        revision_list.append("reports/REVISION_STATUS.md")
    return path


def summarize_revision_outputs(state: MathModelGraphState) -> dict[str, Any]:
    return {
        "revision_sandbox_status": state.get("revision_sandbox_status"),
        "revision_files_written": list(state.get("revision_files_written", [])),
        "revision_status_path": state.get("revision_status_path"),
        "revision_sandbox_error": state.get("revision_sandbox_error"),
    }


def _append_phase5_agent_run(state: MathModelGraphState) -> None:
    written = ", ".join(state.get("revision_files_written", [])) or "none"
    entry = f"""## LangGraph Phase 5 Revision Sandbox

- Mode: {state['mode']}
- Provider: {state['provider']}
- Model: {state['model'] or 'none'}
- Status: {state.get('revision_sandbox_status') or state.get('status')}
- Revision files written: {written}
- Revision status path: {state.get('revision_status_path') or 'none'}
- Revision sandbox error: {state.get('revision_sandbox_error') or 'none'}
- Stop reason: {state.get('stop_reason') or 'none'}
"""
    _write_langgraph_file(state, "reports/AGENT_RUNS.md", _existing_agent_runs(state) + entry + "\n")


def _append_phase5_history(state: MathModelGraphState) -> dict[str, Any]:
    return append_history(
        Path(state["source_workspace"]),
        {
            "event": "langgraph_phase5_revision_sandbox",
            "phase": 5,
            "harness": "LangGraph",
            "source_workspace": state["source_workspace"],
            "run_workspace": state["run_workspace"],
            "prompt_path": state.get("prompt_path"),
            "status_after": state.get("revision_sandbox_status") or state.get("status"),
            "note": state.get("stop_reason"),
        },
    )


def run_phase5_revision_sandbox(state: MathModelGraphState) -> dict[str, Any]:
    assert_run_workspace_allowed(state)
    run_workspace = Path(state["run_workspace"]).resolve()
    source_workspace = Path(state["source_workspace"]).resolve()
    allowed_root = source_workspace / "runs"
    if run_workspace == source_workspace or not _is_relative_to(run_workspace, allowed_root):
        raise ValueError("Phase 5 revision sandbox may only run inside a copied run workspace.")
    plan = state.get("phase_plan") or {}
    writes = plan.get("file_writes", []) if isinstance(plan, dict) else []
    state["revision_files_written"] = []
    state["revision_sandbox_error"] = None
    state["revision_status_path"] = None

    actions = parse_revision_actions(run_workspace)

    if not actions["exists"]:
        write_revision_status(state, actions, "NO_REVISION_ACTIONS")
        state["revision_sandbox_status"] = "NO_REVISION_ACTIONS"
        state["status"] = "NO_REVISION_ACTIONS"
        state["stop_reason"] = "No REVISION_ACTIONS.md found; revision status written, no paper changes applied."
        state["needs_human"] = True
        state["contest_status"] = "NO_REVISION_ACTIONS"
        _append_phase5_agent_run(state)
        state["history"] = _append_phase5_history(state)
        return summarize_revision_outputs(state)

    try:
        validated = validate_phase5_writes(run_workspace, writes) if writes else []
    except ValueError as exc:
        state["revision_sandbox_status"] = "REVISION_SANDBOX_REJECTED"
        state["status"] = "REVISION_SANDBOX_REJECTED"
        state["revision_sandbox_error"] = str(exc)
        state["stop_reason"] = str(exc)
        state["needs_human"] = True
        _append_phase5_agent_run(state)
        state["history"] = _append_phase5_history(state)
        return summarize_revision_outputs(state) | {"revision_files_rejected": [{"reason": str(exc)}]}

    before = _workspace_file_snapshot(run_workspace)
    try:
        for item in validated:
            target = validate_phase5_path(run_workspace, item["path"])
            _write_text_tracked(state, target, item["content"])
            if item["path"] not in state["revision_files_written"]:
                state["revision_files_written"].append(item["path"])
        write_revision_status(state, actions, "REVISION_SANDBOX_SUCCEEDED")
    except Exception as exc:
        _restore_workspace_snapshot(run_workspace, before)
        state["revision_files_written"] = []
        state["revision_sandbox_status"] = "REVISION_SANDBOX_ROLLED_BACK"
        state["status"] = "REVISION_SANDBOX_ROLLED_BACK"
        state["revision_sandbox_error"] = str(exc)
        state["stop_reason"] = f"Phase 5 revision sandbox failed and rolled back: {exc}"
        state["needs_human"] = True
        _append_phase5_agent_run(state)
        state["history"] = _append_phase5_history(state)
        return summarize_revision_outputs(state)

    if "reports/REVISION_STATUS.md" not in state["revision_files_written"]:
        state["revision_files_written"].append("reports/REVISION_STATUS.md")

    changed = _changed_files_since(run_workspace, before)
    allowed = PHASE5_ALLOWED_FILES | LANGGRAPH_INFRA_PATHS
    forbidden_changes = [path for path in changed if path not in allowed]
    if forbidden_changes:
        _restore_workspace_snapshot(run_workspace, before)
        state["revision_files_written"] = []
        state["revision_sandbox_status"] = "REVISION_SANDBOX_REJECTED"
        state["status"] = "REVISION_SANDBOX_REJECTED"
        state["revision_sandbox_error"] = "Phase 5 sandbox attempted forbidden writes: " + ", ".join(forbidden_changes)
        state["stop_reason"] = state["revision_sandbox_error"]
        state["needs_human"] = True
        _append_phase5_agent_run(state)
        state["history"] = _append_phase5_history(state)
        return summarize_revision_outputs(state)

    state["revision_sandbox_status"] = "REVISION_SANDBOX_SUCCEEDED"
    state["status"] = "REVISION_SANDBOX_SUCCEEDED"

    if actions["blocker_high_count"] > 0:
        state["contest_status"] = "REVISION_REQUIRED"
        state["stop_reason"] = (
            f"Phase 5 revision sandbox completed, but {actions['blocker_high_count']} "
            "BLOCKER/HIGH issues remain unresolved. Phase 6 audit-only is still required."
        )
    else:
        state["contest_status"] = "READY_FOR_FINAL_AUDIT"
        state["stop_reason"] = (
            "Phase 5 revision sandbox completed with no unresolved BLOCKER/HIGH. "
            "Phase 6 audit-only will not write VERIFY_REPORT.md."
        )
    state["needs_human"] = True

    _append_phase5_agent_run(state)
    state["history"] = _append_phase5_history(state)
    return summarize_revision_outputs(state)


def run_phase2_sandbox_executor(settings: Settings, state: MathModelGraphState) -> dict[str, Any]:
    assert_run_workspace_allowed(state)
    run_workspace = Path(state["run_workspace"]).resolve()
    source_workspace = Path(state["source_workspace"]).resolve()
    allowed_root = source_workspace / "runs"
    if run_workspace == source_workspace or not _is_relative_to(run_workspace, allowed_root):
        raise ValueError("Phase 2 sandbox may only run inside a copied run workspace.")
    plan = state.get("phase_plan") or {}
    commands = plan.get("commands", []) if isinstance(plan, dict) else []
    state["sandbox_commands"] = []
    state["manifest_created_empty"] = False
    if not commands:
        state["sandbox_status"] = "PHASE2_PLAN_ONLY"
        state["status"] = "PHASE2_PLAN_ONLY"
        state["stop_reason"] = "Phase 2 plan did not include sandbox commands; no experiment commands were executed."
        return {
            "sandbox_status": state["sandbox_status"],
            "sandbox_commands": [],
            "manifest_created_empty": False,
            "generated_files": [],
        }
    try:
        validated = validate_phase2_commands(run_workspace, commands)
    except ValueError as exc:
        rejected = []
        for item in commands if isinstance(commands, list) else []:
            rejected.append(
                {
                    "id": item.get("id", "UNKNOWN") if isinstance(item, dict) else "UNKNOWN",
                    "purpose": item.get("purpose", "") if isinstance(item, dict) else "",
                    "command": item.get("command", "") if isinstance(item, dict) else "",
                    "status": "REJECTED",
                    "reason": str(exc),
                }
            )
        state["sandbox_commands"] = rejected
        state["sandbox_status"] = "SANDBOX_COMMAND_REJECTED"
        state["status"] = "SANDBOX_COMMAND_REJECTED"
        state["stop_reason"] = str(exc)
        state["needs_human"] = True
        _append_phase2_agent_run(state)
        state["history"] = _append_phase2_history(state)
        return {
            "sandbox_status": state["sandbox_status"],
            "sandbox_commands": rejected,
            "manifest_created_empty": False,
            "generated_files": [],
        }

    before = _workspace_file_snapshot(run_workspace)
    command_results: list[dict[str, Any]] = []
    for item in validated:
        args = list(item["args"])
        if args[0] == "python":
            args[0] = settings.python_executable
        elif args[0].lower() == "pytest":
            args = [settings.python_executable, "-m", "pytest", *args[1:]]
        completed = subprocess.run(
            args,
            cwd=run_workspace,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            timeout=120,
        )
        result = {
            "id": item["id"],
            "purpose": item["purpose"],
            "command": item["command"],
            "returncode": completed.returncode,
            "stdout": _stdout_summary(completed.stdout),
            "stderr": _stdout_summary(completed.stderr),
            "expected_outputs": item["expected_outputs"],
            "status": "SUCCEEDED" if completed.returncode == 0 else "FAILED",
        }
        command_results.append(result)
        if completed.returncode != 0:
            break

    manifest_created_empty = ensure_results_manifest(state)
    state["manifest_created_empty"] = manifest_created_empty
    changed = _changed_files_since(run_workspace, before)
    forbidden_changes = [path for path in changed if not _is_phase2_allowed_path(path)]
    if forbidden_changes:
        _restore_workspace_snapshot(run_workspace, before)
        state["sandbox_commands"] = command_results
        state["sandbox_status"] = "SANDBOX_WRITE_VIOLATION"
        state["status"] = "SANDBOX_WRITE_VIOLATION"
        state["stop_reason"] = "Phase 2 sandbox attempted forbidden writes: " + ", ".join(forbidden_changes)
        state["needs_human"] = True
        _append_phase2_agent_run(state)
        state["history"] = _append_phase2_history(state)
        return {
            "sandbox_status": state["sandbox_status"],
            "sandbox_commands": command_results,
            "manifest_created_empty": manifest_created_empty,
            "generated_files": changed,
            "forbidden_changes": forbidden_changes,
        }

    write_experiment_log(state, command_results, changed)
    _append_phase2_agent_run(state)
    failed = next((item for item in command_results if item["status"] != "SUCCEEDED"), None)
    state["sandbox_commands"] = command_results
    state["sandbox_status"] = "SANDBOX_FAILED" if failed else "SANDBOX_SUCCEEDED"
    state["status"] = state["sandbox_status"]
    state["stop_reason"] = (
        f"Phase 2 sandbox command failed: {failed['command']}" if failed else "Phase 2 sandbox completed safely."
    )
    state["needs_human"] = True
    state["history"] = _append_phase2_history(state)
    return {
        "sandbox_status": state["sandbox_status"],
        "sandbox_commands": command_results,
        "manifest_created_empty": manifest_created_empty,
        "generated_files": _changed_files_since(run_workspace, before),
    }


def _assert_allowed_langgraph_write(state: MathModelGraphState, path: Path) -> None:
    run_workspace = Path(state["run_workspace"]).resolve()
    target = path.resolve()
    if not _is_relative_to(target, run_workspace):
        raise ValueError("LangGraph output path escapes run workspace.")
    relative = target.relative_to(run_workspace).as_posix()
    allowed = {f"CONTROL_LANGGRAPH_PHASE_{state['phase']}.md", *LANGGRAPH_INFRA_PATHS}
    if relative not in allowed:
        raise ValueError(f"LangGraph runner is not allowed to write: {relative}")


def _write_langgraph_file(state: MathModelGraphState, relative: str, text: str) -> Path:
    path = Path(state["run_workspace"]) / relative
    _assert_allowed_langgraph_write(state, path)
    _write_text_tracked(state, path, text)
    return path


def pre_audit_node(settings: Settings) -> Callable[[MathModelGraphState], MathModelGraphState]:
    def node(state: MathModelGraphState) -> MathModelGraphState:
        assert_run_workspace_allowed(state)
        audit = run_audit(settings, Path(state["run_workspace"]))
        state["pre_audit"] = audit.get("result", {})
        state["issues"] = list(state["pre_audit"].get("issues", [])) if isinstance(state["pre_audit"], dict) else []
        state["status"] = "pre_audit_complete"
        return state

    return node


def build_prompt_node() -> Callable[[MathModelGraphState], MathModelGraphState]:
    def node(state: MathModelGraphState) -> MathModelGraphState:
        assert_run_workspace_allowed(state)
        run_workspace = Path(state["run_workspace"])
        prompt = build_prompt(run_workspace, state["phase"], "Manual", issues=state.get("issues", []))
        if state["mode"] in {"llm_plan", "controlled_apply", "phase_execute"}:
            prompt = _llm_plan_prompt(prompt, state["phase"])
        if _is_apply_mode(state["mode"]):
            prompt = _controlled_apply_prompt(prompt, state["phase"])
        prompt_path = _write_langgraph_file(state, f"CONTROL_LANGGRAPH_PHASE_{state['phase']}.md", prompt)
        state["prompt"] = prompt
        state["prompt_path"] = str(prompt_path)
        state["status"] = "prompt_built"
        return state

    return node


def provider_plan_node() -> Callable[[MathModelGraphState], MathModelGraphState]:
    def node(state: MathModelGraphState) -> MathModelGraphState:
        if state["mode"] == "dry_run":
            state["needs_human"] = True
            state["status"] = "provider_skipped"
            state["stop_reason"] = (
                "Dry-run only: prompt generated and audits recorded; no provider was called, "
                "no Bash was executed, and no paper/code content was modified."
            )
            return state
        if state["mode"] == "controlled_apply":
            existing_plan = Path(state["run_workspace"]) / "reports" / "LANGGRAPH_PHASE_PLAN.json"
            if existing_plan.is_file():
                state["raw_model_output"] = existing_plan.read_text(encoding="utf-8", errors="replace")
                state["plan_source"] = "existing_plan"
                state["status"] = "existing_plan_loaded"
                return state
        if state["mode"] not in {"llm_plan", "controlled_apply", "phase_execute"}:
            raise ValueError(
                "LangGraph Phase Runner supports mode='dry_run', mode='llm_plan', "
                "mode='controlled_apply', or mode='phase_execute'."
            )
        adapter = get_model_adapter(state["provider"])
        state["raw_model_output"] = adapter.generate(
            state["prompt"],
            model=state["model"],
            temperature=state["temperature"],
            max_tokens=state["max_tokens"],
        )
        state["provider"] = adapter.provider
        state["plan_source"] = "provider"
        state["status"] = "provider_plan_complete"
        return state

    return node


def validate_plan_node() -> Callable[[MathModelGraphState], MathModelGraphState]:
    def node(state: MathModelGraphState) -> MathModelGraphState:
        if state["mode"] not in {"llm_plan", "controlled_apply", "phase_execute"}:
            return state
        raw = state.get("raw_model_output") or ""
        try:
            data = json.loads(_extract_json(raw))
            plan = _validate_phase_plan(data)
            if plan.phase != state["phase"]:
                raise ValueError(f"Plan phase {plan.phase} does not match requested phase {state['phase']}.")
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            state["phase_plan"] = None
            state["provider_error"] = f"PLAN_PARSE_FAILED: {exc}"
            state["status"] = "PLAN_PARSE_FAILED"
            state["stop_reason"] = "Provider output could not be parsed as a valid PhasePlan JSON document."
            state["needs_human"] = True
            return state
        state["phase_plan"] = plan.to_dict()
        state["provider_error"] = None
        state["status"] = "PLAN_READY"
        state["stop_reason"] = (
            "LLM plan generated and validated. No Bash was executed and no paper/code/figures/results files "
            "were modified."
        )
        state["needs_human"] = True
        return state

    return node


def write_plan_node() -> Callable[[MathModelGraphState], MathModelGraphState]:
    def node(state: MathModelGraphState) -> MathModelGraphState:
        if state["mode"] not in {"llm_plan", "controlled_apply", "phase_execute"}:
            return state
        if state.get("phase_plan") is None:
            raw = state.get("raw_model_output") or ""
            raw_path = _write_langgraph_file(
                state,
                "reports/LANGGRAPH_RAW_MODEL_OUTPUT.md",
                f"# LangGraph Raw Model Output\n\n```text\n{raw}\n```\n",
            )
            state["raw_output_path"] = str(raw_path)
            return state
        plan_json = json.dumps(state["phase_plan"], ensure_ascii=False, indent=2)
        plan_path = _write_langgraph_file(state, "reports/LANGGRAPH_PHASE_PLAN.json", plan_json + "\n")
        plan_markdown_path = _write_langgraph_file(
            state,
            "reports/LANGGRAPH_PHASE_PLAN.md",
            _phase_plan_markdown(state["phase_plan"]),
        )
        state["plan_path"] = str(plan_path)
        state["plan_markdown_path"] = str(plan_markdown_path)
        state["raw_output_path"] = None
        return state

    return node


def apply_router_node() -> Callable[[MathModelGraphState], MathModelGraphState]:
    def node(state: MathModelGraphState) -> MathModelGraphState:
        if not _is_apply_mode(state["mode"]):
            return state
        if state["phase"] not in APPLY_ALLOWED_PATHS:
            raise ValueError("controlled_apply only supports phase 1 and phase 4.")
        if state.get("phase_plan") is None:
            state["files_planned"] = []
            state["files_rejected"] = [{"path": "", "reason": state.get("provider_error") or "phase plan is missing"}]
            state["status"] = "APPLY_REJECTED"
            state["needs_human"] = True
            return state
        writes = state.get("phase_plan", {}).get("file_writes", [])
        state["files_planned"] = [str(item.get("path", "")) for item in writes if isinstance(item, dict)]
        if not writes:
            state["status"] = "APPLY_PLAN_ONLY"
            state["stop_reason"] = "Validated phase plan did not include file_writes; no controlled files were written."
            state["needs_human"] = True
            return state
        rejected: list[dict[str, Any]] = []
        run_workspace = Path(state["run_workspace"])
        for item in writes:
            if not isinstance(item, dict):
                rejected.append({"path": "", "reason": "file_writes item must be an object"})
                continue
            path = str(item.get("path", ""))
            content = item.get("content")
            purpose = item.get("purpose")
            if not isinstance(content, str) or not content:
                rejected.append({"path": path, "reason": "content must be a non-empty string"})
                continue
            if not isinstance(purpose, str) or not purpose:
                rejected.append({"path": path, "reason": "purpose must be a non-empty string"})
                continue
            try:
                validate_apply_path(run_workspace, path, state["phase"])
            except ValueError as exc:
                rejected.append({"path": path, "reason": str(exc)})
        state["files_rejected"] = rejected
        if rejected:
            state["status"] = "APPLY_REJECTED"
            state["stop_reason"] = "At least one planned write failed the controlled-apply allowlist; no core files were written."
            state["needs_human"] = True
            return state
        state["status"] = "APPLY_READY_TO_WRITE"
        return state

    return node


def controlled_write_node() -> Callable[[MathModelGraphState], MathModelGraphState]:
    def node(state: MathModelGraphState) -> MathModelGraphState:
        if not _is_apply_mode(state["mode"]):
            return state
        if state["status"] in {"APPLY_REJECTED", "APPLY_PLAN_ONLY"}:
            return state
        writes = state.get("phase_plan", {}).get("file_writes", [])
        run_workspace = Path(state["run_workspace"])
        backups: dict[Path, tuple[bool, str]] = {}
        written_paths: list[Path] = []
        try:
            for item in writes:
                target = validate_apply_path(run_workspace, str(item["path"]), state["phase"])
                backups[target] = (target.exists(), target.read_text(encoding="utf-8", errors="replace") if target.exists() else "")
                _write_text_tracked(state, target, str(item["content"]))
                written_paths.append(target)
                relative = _relative_or_absolute(target, run_workspace)
                if relative not in state["files_written"]:
                    state["files_written"].append(relative)
        except Exception as exc:
            for path, (existed, content) in backups.items():
                if existed:
                    path.write_text(content, encoding="utf-8", newline="\n")
                elif path.exists():
                    path.unlink()
            state["files_written"] = []
            state["apply_error"] = str(exc)
            state["status"] = "APPLY_ROLLED_BACK"
            state["stop_reason"] = f"Controlled apply failed and rolled back: {exc}"
            state["needs_human"] = True
            return state
        state["status"] = "APPLY_WRITTEN"
        state["stop_reason"] = _controlled_apply_stop_reason(state)
        state["needs_human"] = True
        return state

    return node


def post_audit_node(settings: Settings) -> Callable[[MathModelGraphState], MathModelGraphState]:
    def node(state: MathModelGraphState) -> MathModelGraphState:
        assert_run_workspace_allowed(state)
        audit = run_audit(settings, Path(state["run_workspace"]))
        state["post_audit"] = audit.get("result", {})
        if _is_apply_mode(state["mode"]):
            if state["status"] in {"APPLY_REJECTED", "APPLY_PLAN_ONLY", "APPLY_ROLLED_BACK"}:
                return state
            if _audit_has_high_or_blocker(state["post_audit"]):
                state["status"] = "APPLY_NEEDS_REVIEW"
                state["stop_reason"] = "Controlled files were written, but post-audit still reports HIGH/BLOCKER issues."
            else:
                state["status"] = "APPLY_READY_FOR_HUMAN_REVIEW"
                state["stop_reason"] = _controlled_apply_stop_reason(state)
            state["needs_human"] = True
            return state
        state["status"] = "post_audit_complete"
        return state

    return node


def _report_markdown(state: MathModelGraphState) -> str:
    pre = _audit_summary({"result": state.get("pre_audit", {}), "returncode": None})
    post = _audit_summary({"result": state.get("post_audit", {}), "returncode": None})
    model = state["model"] or "none"
    prompt_path = state["prompt_path"] or "not generated"
    plan_path = state.get("plan_path") or "not generated"
    plan_markdown_path = state.get("plan_markdown_path") or "not generated"
    raw_output_path = state.get("raw_output_path") or "not generated"
    apply_diff_path = state.get("apply_diff_path") or "not generated"
    provider_error = state.get("provider_error") or "none"
    apply_error = state.get("apply_error") or "none"
    files_planned = "\n".join(f"- {item}" for item in state.get("files_planned", [])) or "- none"
    files_written = "\n".join(f"- {item}" for item in state.get("files_written", [])) or "- none"
    files_rejected = "\n".join(
        f"- {item.get('path', '')}: {item.get('reason', '')}" for item in state.get("files_rejected", [])
    ) or "- none"
    created = "\n".join(f"- {item}" for item in state["created_files"]) or "- none"
    updated = "\n".join(f"- {item}" for item in state["updated_files"]) or "- none"
    next_action = _next_recommended_action(state)
    return f"""# LangGraph Run Report

## Run

- Phase: {state['phase']}
- Mode: {state['mode']}
- Provider: {state['provider']}
- Model: {model}
- Status: {state['status']}
- Source workspace: `{state['source_workspace']}`
- Run workspace: `{state['run_workspace']}`
- Prompt path: `{prompt_path}`
- Plan JSON path: `{plan_path}`
- Plan Markdown path: `{plan_markdown_path}`
- Raw output path: `{raw_output_path}`
- Apply diff path: `{apply_diff_path}`
- Provider error: {provider_error}
- Apply error: {apply_error}

## Pre Audit

- Status: {pre['status']}
- Worst severity: {pre['worst_severity']}
- Issue count: {pre['issue_count']}

## Post Audit

- Status: {post['status']}
- Worst severity: {post['worst_severity']}
- Issue count: {post['issue_count']}

## File Changes

Files planned:
{files_planned}

Files written:
{files_written}

Files rejected:
{files_rejected}

Created files:
{created}

Updated files:
{updated}

## Stop Reason

{state['stop_reason'] or 'none'}

## Next Recommended Action

{next_action}
"""


def write_report_node() -> Callable[[MathModelGraphState], MathModelGraphState]:
    def node(state: MathModelGraphState) -> MathModelGraphState:
        assert_run_workspace_allowed(state)
        if _is_apply_mode(state["mode"]):
            apply_diff_path = _write_langgraph_file(
                state,
                "reports/LANGGRAPH_APPLY_DIFF.md",
                _apply_diff_markdown(state),
            )
            state["apply_diff_path"] = str(apply_diff_path)
            _append_agent_runs(state)
        report_path = _write_langgraph_file(state, "reports/LANGGRAPH_RUN_REPORT.md", _report_markdown(state))
        state["report_path"] = str(report_path)
        if not _is_apply_mode(state["mode"]):
            state["status"] = "report_written"
        return state

    return node


def append_history_node() -> Callable[[MathModelGraphState], MathModelGraphState]:
    def node(state: MathModelGraphState) -> MathModelGraphState:
        event = {
            "dry_run": "langgraph_phase_dry_run",
            "llm_plan": "langgraph_phase_llm_plan",
            "controlled_apply": "langgraph_phase_controlled_apply",
            "phase_execute": "langgraph_phase_execute",
        }.get(state["mode"], "langgraph_phase")
        final_status = _final_status(state)
        history = append_history(
            Path(state["source_workspace"]),
            {
                "event": event,
                "phase": state["phase"],
                "harness": "LangGraph",
                "source_workspace": state["source_workspace"],
                "run_workspace": state["run_workspace"],
                "prompt_path": state["prompt_path"],
                "status_before": str(state.get("pre_audit", {}).get("status", "UNKNOWN")),
                "status_after": str(state.get("post_audit", {}).get("status", "UNKNOWN")),
                "files_planned": state.get("files_planned", []),
                "files_written": state.get("files_written", []),
                "files_rejected": state.get("files_rejected", []),
                "note": state.get("provider_error") or state["stop_reason"],
            },
        )
        state["history"] = history
        state["status"] = final_status
        return state

    return node


def _llm_plan_prompt(base_prompt: str, phase: int) -> str:
    return f"""{base_prompt}

LangGraph llm_plan provider instructions:
- Output strict JSON only. Do not wrap the JSON in Markdown fences.
- Generate a structured PhasePlan for Phase {phase}; do not write or apply any workspace changes.
- Do not propose edits to paper/, code/, figures/, results/, or V2 core reports as an automatic action.
- Preserve HUMAN_MODEL_REVIEW.md and all V2 human gates.
- Include these top-level fields exactly: phase, phase_name, summary, required_inputs, required_outputs,
  planned_steps, rag_queries, source_quality_requirements, human_gates, risk_register, expected_artifacts,
  do_not_do, next_action.
- planned_steps items require: id, title, description, reads, writes, checks, requires_human.
- rag_queries items require: library, query, core_only, reason.
- risk_register items require: severity, risk, mitigation.
- human_gates items require: gate_file, required, reason.
"""


def _controlled_apply_prompt(base_prompt: str, phase: int) -> str:
    allowed = "\n".join(f"- {item}" for item in sorted(allowed_apply_paths(phase))) or "- none"
    return f"""{base_prompt}

Controlled apply instructions:
- You may include optional `file_writes`, but every path must be in this phase allowlist:
{allowed}
- Never write HUMAN_MODEL_REVIEW.md, MODELING_DECISION.md, VERIFY_REPORT.md, paper/, code/, figures/, results/, or source/.
- If you are not certain the content is safe, omit `file_writes`; the runner will produce a plan-only result.
- `file_writes` items require: path, purpose, content.
- Phase 1 must stop for human review after MODEL_CANDIDATES.md and related draft reports.
- Phase 4 must stop for human review after scorecard and revision actions.
"""


def _extract_json(raw: str) -> str:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def _validate_phase_plan(data: dict[str, Any]) -> PhasePlan:
    if hasattr(PhasePlan, "model_validate"):
        return PhasePlan.model_validate(data)
    return PhasePlan.parse_obj(data)


def _phase_plan_markdown(plan: dict[str, Any]) -> str:
    steps = "\n".join(
        f"- `{step.get('id', '')}` {step.get('title', '')}: {step.get('description', '')}"
        for step in plan.get("planned_steps", [])
    ) or "- none"
    risks = "\n".join(
        f"- [{risk.get('severity', 'INFO')}] {risk.get('risk', '')} -> {risk.get('mitigation', '')}"
        for risk in plan.get("risk_register", [])
    ) or "- none"
    gates = "\n".join(
        f"- {gate.get('gate_file', '')}: {gate.get('reason', '')}"
        for gate in plan.get("human_gates", [])
    ) or "- none"
    outputs = "\n".join(f"- {item}" for item in plan.get("expected_artifacts", [])) or "- none"
    do_not_do = "\n".join(f"- {item}" for item in plan.get("do_not_do", [])) or "- none"
    return f"""# LangGraph Phase Plan

## Summary

- Phase: {plan.get('phase')}
- Phase name: {plan.get('phase_name')}
- Summary: {plan.get('summary')}

## Planned Steps

{steps}

## Human Gates

{gates}

## Risks

{risks}

## Expected Artifacts

{outputs}

## Do Not Do

{do_not_do}

## Next Action

{plan.get('next_action')}
"""


def _next_recommended_action(state: MathModelGraphState) -> str:
    if state["mode"] == "dry_run":
        return (
            f"Copy `CONTROL_LANGGRAPH_PHASE_{state['phase']}.md` into Manual/Codex/Claude Code/OpenCode. "
            "Keep human gates and `audit_v2_run.py` as the source of completion truth."
        )
    if _is_apply_mode(state["mode"]):
        if state["status"] == "APPLY_PLAN_ONLY":
            return "Review the plan manually. No file_writes were present, so no controlled reports were written."
        if state["status"] == "APPLY_REJECTED":
            return "Fix rejected file_writes and rerun the phase executor. No core files were written."
        if state["status"] == "APPLY_ROLLED_BACK":
            return "Inspect the apply error and rerun after fixing the write failure. Partial writes were rolled back."
        if state["phase"] == 1:
            return (
                "Human must review `reports/MODEL_CANDIDATES.md`. Do not enter data-experiment until "
                "`reports/HUMAN_MODEL_REVIEW.md` and `reports/MODELING_DECISION.md` are created manually."
            )
        if state["phase"] == 4:
            return "Human must review `reports/PAPER_SCORECARD.md` and `reports/REVISION_ACTIONS.md` before revision."
        return "Human review is required before any downstream phase."
    if state.get("phase_plan") is None:
        return (
            "Inspect `reports/LANGGRAPH_RAW_MODEL_OUTPUT.md`, fix provider output formatting, and rerun llm_plan. "
            "Do not apply any changes from an invalid plan."
        )
    return (
        "Review `reports/LANGGRAPH_PHASE_PLAN.md` manually, then run the relevant V2 skill or harness. "
        "This plan is advisory and does not bypass human gates."
    )


def _final_status(state: MathModelGraphState) -> str:
    if state["mode"] == "dry_run":
        return "dry_run_complete"
    if _is_apply_mode(state["mode"]):
        return state["status"]
    if state.get("phase_plan") is None:
        return "PLAN_PARSE_FAILED"
    return "PLAN_READY"


def _audit_has_high_or_blocker(audit: dict[str, Any]) -> bool:
    issues = audit.get("issues", []) if isinstance(audit, dict) else []
    if not isinstance(issues, list):
        return False
    return any(str(item.get("severity", "")).upper() in {"HIGH", "BLOCKER"} for item in issues if isinstance(item, dict))


def _controlled_apply_stop_reason(state: MathModelGraphState) -> str:
    if state["phase"] == 1:
        return (
            "Controlled apply wrote Phase 1 draft reports only. HUMAN_MODEL_REVIEW.md and MODELING_DECISION.md "
            "remain manual gates."
        )
    if state["phase"] == 4:
        return "Controlled apply wrote Phase 4 review reports only. Revision remains a human-reviewed next step."
    return "Controlled apply completed with human review required."


def _append_agent_runs(state: MathModelGraphState) -> None:
    planned = ", ".join(state.get("files_planned", [])) or "none"
    written = ", ".join(state.get("files_written", [])) or "none"
    rejected = "; ".join(
        f"{item.get('path', '')}: {item.get('reason', '')}" for item in state.get("files_rejected", [])
    ) or "none"
    entry = f"""## LangGraph Run

- Mode: {state['mode']}
- Provider: {state['provider']}
- Model: {state['model'] or 'none'}
- Phase: {state['phase']}
- Status: {state['status']}
- Files planned: {planned}
- Files written: {written}
- Files rejected: {rejected}
- Pre audit: {state.get('pre_audit', {}).get('status', 'UNKNOWN')}
- Post audit: {state.get('post_audit', {}).get('status', 'UNKNOWN')}
- Stop reason: {state.get('stop_reason') or 'none'}
- Next action: {_next_recommended_action(state)}
"""
    target = _write_langgraph_file(state, "reports/AGENT_RUNS.md", _existing_agent_runs(state) + entry + "\n")
    if str(target):
        return


def _apply_diff_markdown(state: MathModelGraphState) -> str:
    pre = _audit_summary({"result": state.get("pre_audit", {}), "returncode": None})
    post = _audit_summary({"result": state.get("post_audit", {}), "returncode": None})
    files_planned = "\n".join(f"- {item}" for item in state.get("files_planned", [])) or "- none"
    files_written = "\n".join(f"- {item}" for item in state.get("files_written", [])) or "- none"
    files_rejected = "\n".join(
        f"- {item.get('path', '')}: {item.get('reason', '')}" for item in state.get("files_rejected", [])
    ) or "- none"
    rollback = "yes" if state.get("status") == "APPLY_ROLLED_BACK" else "no"
    return f"""# LangGraph Apply Diff

## Run

- Phase: {state['phase']}
- Mode: {state['mode']}
- Provider: {state['provider']}
- Model: {state['model'] or 'none'}
- Status: {state['status']}
- Rollback status: {rollback}

## Files Planned

{files_planned}

## Files Written

{files_written}

## Files Rejected

{files_rejected}

## Pre Audit

- Status: {pre['status']}
- Worst severity: {pre['worst_severity']}
- Issue count: {pre['issue_count']}

## Post Audit

- Status: {post['status']}
- Worst severity: {post['worst_severity']}
- Issue count: {post['issue_count']}

## Next Human Action

{_next_recommended_action(state)}
"""


def _existing_agent_runs(state: MathModelGraphState) -> str:
    path = Path(state["run_workspace"]) / "reports" / "AGENT_RUNS.md"
    if not path.is_file():
        return "# Agent Runs\n\n"
    text = path.read_text(encoding="utf-8", errors="replace")
    return text if text.endswith("\n") else text + "\n"


def _build_graph(settings: Settings) -> Any:
    if _StateGraph is None or _END is None:
        raise LangGraphUnavailableError(
            "LangGraph is not installed. Install with: pip install -r app/backend/requirements-langgraph.txt"
        )
    graph = _StateGraph(MathModelGraphState)
    graph.add_node("pre_audit_node", pre_audit_node(settings))
    graph.add_node("build_prompt_node", build_prompt_node())
    graph.add_node("provider_plan_node", provider_plan_node())
    graph.add_node("validate_plan_node", validate_plan_node())
    graph.add_node("write_plan_node", write_plan_node())
    graph.add_node("apply_router_node", apply_router_node())
    graph.add_node("controlled_write_node", controlled_write_node())
    graph.add_node("post_audit_node", post_audit_node(settings))
    graph.add_node("write_report_node", write_report_node())
    graph.add_node("append_history_node", append_history_node())
    graph.set_entry_point("pre_audit_node")
    graph.add_edge("pre_audit_node", "build_prompt_node")
    graph.add_edge("build_prompt_node", "provider_plan_node")
    graph.add_edge("provider_plan_node", "validate_plan_node")
    graph.add_edge("validate_plan_node", "write_plan_node")
    graph.add_edge("write_plan_node", "apply_router_node")
    graph.add_edge("apply_router_node", "controlled_write_node")
    graph.add_edge("controlled_write_node", "post_audit_node")
    graph.add_edge("post_audit_node", "write_report_node")
    graph.add_edge("write_report_node", "append_history_node")
    graph.add_edge("append_history_node", _END)
    return graph.compile()


def _initial_state(
    *,
    source_workspace: Path,
    run_workspace: Path,
    phase: int,
    mode: str,
    provider: str,
    model: str | None,
    temperature: float,
    max_tokens: int,
) -> MathModelGraphState:
    return {
        "source_workspace": str(source_workspace),
        "run_workspace": str(run_workspace),
        "phase": phase,
        "mode": mode,
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "prompt": "",
        "prompt_path": None,
        "pre_audit": {},
        "post_audit": {},
        "issues": [],
        "created_files": [],
        "updated_files": [],
        "needs_human": False,
        "status": "initialized",
        "stop_reason": None,
        "report_path": None,
        "phase_plan": None,
        "raw_model_output": None,
        "provider_error": None,
        "plan_path": None,
        "plan_markdown_path": None,
        "raw_output_path": None,
        "apply_diff_path": None,
        "files_planned": [],
        "files_written": [],
        "files_rejected": [],
        "apply_error": None,
        "plan_source": None,
        "sandbox_commands": [],
        "sandbox_status": None,
        "manifest_created_empty": False,
        "paper_sandbox_status": None,
        "paper_files_written": [],
        "claim_trace_path": None,
        "method_matrix_path": None,
        "paper_build_report_path": None,
        "paper_sandbox_error": None,
        "history": None,
    }


def _run_phase_in_workspace(
    *,
    settings: Settings,
    source_workspace: Path,
    run_workspace: Path,
    phase: int,
    mode: str,
    provider: str,
    model: str | None,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    state = _initial_state(
        source_workspace=source_workspace,
        run_workspace=run_workspace,
        phase=phase,
        mode=mode,
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    assert_run_workspace_allowed(state)
    return dict(_build_graph(settings).invoke(state))


def _contest_phase_mode(phase: int) -> str:
    if phase in {1, 4}:
        return "phase_execute"
    return "llm_plan"


def _phase_result_summary(result: dict[str, Any], *, strategy: str) -> dict[str, Any]:
    summary = {
        "phase": int(result.get("phase", -1)),
        "mode": result.get("mode"),
        "strategy": strategy,
        "status": result.get("status"),
        "prompt_path": result.get("prompt_path"),
        "report_path": result.get("report_path"),
        "plan_path": result.get("plan_path"),
        "apply_diff_path": result.get("apply_diff_path"),
        "provider_error": result.get("provider_error"),
        "files_planned": list(result.get("files_planned", [])),
        "files_written": list(result.get("files_written", [])),
        "files_rejected": list(result.get("files_rejected", [])),
        "pre_audit": _audit_summary({"result": result.get("pre_audit", {}), "returncode": None}),
        "post_audit": _audit_summary({"result": result.get("post_audit", {}), "returncode": None}),
        "stop_reason": result.get("stop_reason"),
    }
    if "sandbox_status" in result:
        summary["sandbox_status"] = result.get("sandbox_status")
        summary["sandbox_commands"] = list(result.get("sandbox_commands", []))
        summary["manifest_created_empty"] = bool(result.get("manifest_created_empty", False))
    if "paper_sandbox_status" in result:
        summary["paper_sandbox_status"] = result.get("paper_sandbox_status")
        summary["paper_files_written"] = list(result.get("paper_files_written", []))
        summary["claim_trace_path"] = result.get("claim_trace_path")
        summary["method_matrix_path"] = result.get("method_matrix_path")
        summary["paper_build_report_path"] = result.get("paper_build_report_path")
        summary["paper_sandbox_error"] = result.get("paper_sandbox_error")
    if "revision_sandbox_status" in result:
        summary["revision_sandbox_status"] = result.get("revision_sandbox_status")
        summary["revision_files_written"] = list(result.get("revision_files_written", []))
        summary["revision_status_path"] = result.get("revision_status_path")
        summary["revision_sandbox_error"] = result.get("revision_sandbox_error")
    return summary


def _merge_file_tracking(target: dict[str, Any], result: dict[str, Any]) -> None:
    for key in ("created_files", "updated_files"):
        bucket = target.setdefault(key, [])
        for item in result.get(key, []):
            if item not in bucket:
                bucket.append(item)
    for key in ("files_planned", "files_written"):
        bucket = target.setdefault(key, [])
        for item in result.get(key, []):
            if item not in bucket:
                bucket.append(item)
    rejected = target.setdefault("files_rejected", [])
    for item in result.get("files_rejected", []):
        if item not in rejected:
            rejected.append(item)
    if result.get("sandbox_commands"):
        target["sandbox_commands"] = list(result.get("sandbox_commands", []))
    if result.get("sandbox_status"):
        target["sandbox_status"] = result.get("sandbox_status")
    if result.get("manifest_created_empty"):
        target["manifest_created_empty"] = bool(result.get("manifest_created_empty"))
    if result.get("paper_sandbox_status"):
        target["paper_sandbox_status"] = result.get("paper_sandbox_status")
    if result.get("paper_files_written"):
        bucket = target.setdefault("paper_files_written", [])
        for item in result.get("paper_files_written", []):
            if item not in bucket:
                bucket.append(item)
    for key in ("claim_trace_path", "method_matrix_path", "paper_build_report_path", "paper_sandbox_error"):
        if result.get(key):
            target[key] = result.get(key)
    if result.get("revision_sandbox_status"):
        target["revision_sandbox_status"] = result.get("revision_sandbox_status")
    if result.get("revision_files_written"):
        bucket = target.setdefault("revision_files_written", [])
        for item in result.get("revision_files_written", []):
            if item not in bucket:
                bucket.append(item)
    for key in ("revision_status_path", "revision_sandbox_error"):
        if result.get(key):
            target[key] = result.get(key)


def _contest_graph_report_markdown(state: MathModelGraphState) -> str:
    phase_lines = []
    for item in state.get("phase_results", []):
        written = ", ".join(item.get("files_written", [])) or "none"
        rejected = "; ".join(
            f"{entry.get('path', '')}: {entry.get('reason', '')}" for entry in item.get("files_rejected", [])
        ) or "none"
        phase_lines.append(
            "\n".join(
                [
                    f"### Phase {item.get('phase')}",
                    "",
                    f"- Strategy: {item.get('strategy')}",
                    f"- Mode: {item.get('mode')}",
                    f"- Status: {item.get('status')}",
                    f"- Sandbox status: {item.get('sandbox_status', 'n/a')}",
                    f"- Paper sandbox status: {item.get('paper_sandbox_status', 'n/a')}",
                    f"- manifest_created_empty: {item.get('manifest_created_empty', False)}",
                    f"- Files written: {written}",
                    f"- Paper files written: {', '.join(item.get('paper_files_written', [])) or 'none'}",
                    f"- Files rejected: {rejected}",
                    f"- Post-audit worst severity: {item.get('post_audit', {}).get('worst_severity', 'UNKNOWN')}",
                ]
            )
        )
    phases = "\n\n".join(phase_lines) or "No phase executed."
    gate = state.get("human_gate", {})
    final_audit = _audit_summary({"result": state.get("final_audit", {}), "returncode": None})
    return f"""# LangGraph Contest Graph Report

## Run

- Mode: {state['mode']}
- Provider: {state['provider']}
- Model: {state['model'] or 'none'}
- Contest status: {state.get('contest_status') or state.get('status')}
- Source workspace: `{state['source_workspace']}`
- Run workspace: `{state['run_workspace']}`
- Completed phases: {', '.join(str(item) for item in state.get('completed_phases', [])) or 'none'}
- Paused at: {state.get('paused_at') or 'none'}
- Stop reason: {state.get('stop_reason') or 'none'}

## Human Gate

- Required now: {state.get('human_gate_required', False)}
- Gate file: {state.get('human_gate_file') or HUMAN_MODEL_GATE}
- Exists: {gate.get('exists', False)}
- Approved: {gate.get('approved', False)}
- Approval signal: {gate.get('approval_signal') or 'none'}

## Phase Results

{phases}

## Final Audit

- Status: {final_audit['status']}
- Worst severity: {final_audit['worst_severity']}
- Issue count: {final_audit['issue_count']}

## Next Recommended Action

{_contest_next_action(state)}
"""


def _contest_next_action(state: MathModelGraphState) -> str:
    if state.get("contest_status") == "WAITING_FOR_HUMAN_MODEL_REVIEW":
        return (
            "Human must review Phase 1 model candidates and manually create/approve "
            "`reports/HUMAN_MODEL_REVIEW.md` before entering Phase 2. Do not write "
            "`reports/MODELING_DECISION.md` automatically."
        )
    if str(state.get("contest_status", "")).startswith("CONTEST_GRAPH_FAILED"):
        return "Inspect the failed phase report and rerun after manual repair. Do not continue automatically."
    return (
        "Review all generated LangGraph plans and Phase 1/4 draft reports manually. "
        "Phase 6 was audit-only and does not write `reports/VERIFY_REPORT.md` or claim final PASS."
    )


def _write_contest_graph_report(state: MathModelGraphState) -> Path:
    path = _write_langgraph_file(
        state,
        "reports/LANGGRAPH_CONTEST_GRAPH_REPORT.md",
        _contest_graph_report_markdown(state),
    )
    state["graph_report_path"] = str(path)
    state["report_path"] = str(path)
    return path


def _audit_only_phase6(settings: Settings, state: MathModelGraphState) -> dict[str, Any]:
    audit = run_audit(settings, Path(state["run_workspace"]))
    result = {
        "phase": 6,
        "mode": "audit_only",
        "strategy": "final_verify_audit_only",
        "status": "AUDIT_RECORDED",
        "prompt_path": None,
        "report_path": None,
        "plan_path": None,
        "apply_diff_path": None,
        "provider_error": None,
        "files_planned": [],
        "files_written": [],
        "files_rejected": [],
        "pre_audit": audit.get("result", {}),
        "post_audit": audit.get("result", {}),
        "stop_reason": "Phase 6 v0 is audit-only; VERIFY_REPORT.md is not written and final PASS is not claimed.",
    }
    state["final_audit"] = audit.get("result", {})
    return result


def run_contest_graph_v0(
    *,
    settings: Settings,
    source_workspace: Path,
    requested_phase: int,
    provider: str,
    model: str | None,
    copy_workspace: bool,
    run_name: str | None,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    source_workspace = source_workspace.resolve()
    if not source_workspace.is_dir():
        raise ValueError(f"Source workspace does not exist: {source_workspace}")
    run_workspace = (
        copy_workspace_for_run(source_workspace, run_name or "langgraph-contest-graph-v0")
        if copy_workspace
        else source_workspace
    ).resolve()

    state = _initial_state(
        source_workspace=source_workspace,
        run_workspace=run_workspace,
        phase=requested_phase,
        mode="contest_graph_v0",
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    state["contest_graph_steps"] = []
    state["phase_results"] = []
    state["completed_phases"] = []
    state["paused_at"] = None
    state["human_gate_required"] = False
    state["human_gate_file"] = HUMAN_MODEL_GATE
    state["contest_status"] = "RUNNING"
    state["final_audit"] = {}
    state["graph_report_path"] = None
    assert_run_workspace_allowed(state)

    for phase in range(0, 6):
        phase_mode = _contest_phase_mode(phase)
        strategy = "phase_execute_allowlisted_reports" if phase_mode == "phase_execute" else "llm_plan_only"
        state["current_phase"] = phase
        try:
            result = _run_phase_in_workspace(
                settings=settings,
                source_workspace=source_workspace,
                run_workspace=run_workspace,
                phase=phase,
                mode=phase_mode,
                provider=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            state["contest_status"] = f"CONTEST_GRAPH_FAILED_PHASE_{phase}"
            state["status"] = state["contest_status"]
            state["stop_reason"] = str(exc)
            state["needs_human"] = True
            break
        summary = _phase_result_summary(result, strategy=strategy)
        state["phase_results"].append(summary)
        state["contest_graph_steps"].append(summary)
        state["completed_phases"].append(phase)
        state["pre_audit"] = result.get("pre_audit", state.get("pre_audit", {}))
        state["post_audit"] = result.get("post_audit", state.get("post_audit", {}))
        state["issues"] = list(result.get("issues", []))
        state["prompt_path"] = result.get("prompt_path")
        _merge_file_tracking(state, result)

        if result.get("status") == "PLAN_PARSE_FAILED" or result.get("provider_error"):
            state["contest_status"] = f"CONTEST_GRAPH_FAILED_PHASE_{phase}"
            state["status"] = state["contest_status"]
            state["stop_reason"] = result.get("provider_error") or result.get("stop_reason")
            state["needs_human"] = True
            break

        if phase == 1:
            gate = check_human_model_gate(run_workspace)
            state["human_gate"] = gate
            if not gate["approved"]:
                state["contest_status"] = "WAITING_FOR_HUMAN_MODEL_REVIEW"
                state["status"] = "WAITING_FOR_HUMAN_MODEL_REVIEW"
                state["paused_at"] = "phase_1_human_gate"
                state["human_gate_required"] = True
                state["human_gate_file"] = HUMAN_MODEL_GATE
                state["needs_human"] = True
                state["stop_reason"] = "Phase 1 completed, but HUMAN_MODEL_REVIEW.md is missing or lacks approval."
                break
    else:
        phase6 = _audit_only_phase6(settings, state)
        summary = _phase_result_summary(phase6, strategy="audit_only")
        state["phase_results"].append(summary)
        state["contest_graph_steps"].append(summary)
        state["completed_phases"].append(6)
        state["post_audit"] = phase6["post_audit"]
        state["issues"] = list(phase6["post_audit"].get("issues", [])) if isinstance(phase6["post_audit"], dict) else []
        state["contest_status"] = "CONTEST_GRAPH_REVIEW_READY"
        state["status"] = "CONTEST_GRAPH_REVIEW_READY"
        state["needs_human"] = True
        state["stop_reason"] = "Contest graph v0 completed safe orchestration through Phase 6 audit-only."

    if "human_gate" not in state:
        state["human_gate"] = check_human_model_gate(run_workspace)
    if not state.get("final_audit"):
        state["final_audit"] = state.get("post_audit", {})

    _write_contest_graph_report(state)
    history = append_history(
        source_workspace,
        {
            "event": "langgraph_contest_graph_v0",
            "phase": None,
            "harness": "LangGraph",
            "source_workspace": str(source_workspace),
            "run_workspace": str(run_workspace),
            "prompt_path": state.get("prompt_path"),
            "status_before": str(state.get("pre_audit", {}).get("status", "UNKNOWN")),
            "status_after": str(state.get("post_audit", {}).get("status", "UNKNOWN")),
            "note": state.get("stop_reason"),
        },
    )
    state["history"] = history
    return dict(state)


def _phase2_sandbox_phase(
    *,
    settings: Settings,
    source_workspace: Path,
    run_workspace: Path,
    provider: str,
    model: str | None,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    plan_result = _run_phase_in_workspace(
        settings=settings,
        source_workspace=source_workspace,
        run_workspace=run_workspace,
        phase=2,
        mode="llm_plan",
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if plan_result.get("phase_plan") is None or plan_result.get("provider_error"):
        return plan_result
    sandbox_state = _initial_state(
        source_workspace=source_workspace,
        run_workspace=run_workspace,
        phase=2,
        mode="contest_graph_v1",
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    sandbox_state["prompt_path"] = plan_result.get("prompt_path")
    sandbox_state["plan_path"] = plan_result.get("plan_path")
    sandbox_state["plan_markdown_path"] = plan_result.get("plan_markdown_path")
    sandbox_state["phase_plan"] = plan_result.get("phase_plan")
    sandbox_result = run_phase2_sandbox_executor(settings, sandbox_state)
    audit = run_audit(settings, run_workspace)
    merged = dict(plan_result)
    merged.update(
        {
            "mode": "phase2_sandbox",
            "status": sandbox_result["sandbox_status"],
            "sandbox_status": sandbox_result["sandbox_status"],
            "sandbox_commands": sandbox_result["sandbox_commands"],
            "manifest_created_empty": sandbox_result["manifest_created_empty"],
            "generated_files": sandbox_result.get("generated_files", []),
            "post_audit": audit.get("result", {}),
            "issues": list(audit.get("result", {}).get("issues", [])),
            "stop_reason": sandbox_state.get("stop_reason"),
            "created_files": list(dict.fromkeys(plan_result.get("created_files", []) + sandbox_state.get("created_files", []))),
            "updated_files": list(dict.fromkeys(plan_result.get("updated_files", []) + sandbox_state.get("updated_files", []))),
        }
    )
    return merged


def run_contest_graph_v1(
    *,
    settings: Settings,
    source_workspace: Path,
    requested_phase: int,
    provider: str,
    model: str | None,
    copy_workspace: bool,
    run_name: str | None,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    source_workspace = source_workspace.resolve()
    if not source_workspace.is_dir():
        raise ValueError(f"Source workspace does not exist: {source_workspace}")
    run_workspace = (
        copy_workspace_for_run(source_workspace, run_name or "langgraph-contest-graph-v1")
        if copy_workspace
        else source_workspace
    ).resolve()

    state = _initial_state(
        source_workspace=source_workspace,
        run_workspace=run_workspace,
        phase=requested_phase,
        mode="contest_graph_v1",
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    state["contest_graph_steps"] = []
    state["phase_results"] = []
    state["completed_phases"] = []
    state["paused_at"] = None
    state["human_gate_required"] = False
    state["human_gate_file"] = HUMAN_MODEL_GATE
    state["contest_status"] = "RUNNING"
    state["final_audit"] = {}
    state["graph_report_path"] = None
    state["sandbox_commands"] = []
    state["sandbox_status"] = None
    state["manifest_created_empty"] = False
    assert_run_workspace_allowed(state)

    for phase in range(0, 6):
        state["current_phase"] = phase
        try:
            if phase == 2:
                result = _phase2_sandbox_phase(
                    settings=settings,
                    source_workspace=source_workspace,
                    run_workspace=run_workspace,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                strategy = "phase2_sandbox_executor"
            else:
                phase_mode = _contest_phase_mode(phase)
                strategy = "phase_execute_allowlisted_reports" if phase_mode == "phase_execute" else "llm_plan_only"
                result = _run_phase_in_workspace(
                    settings=settings,
                    source_workspace=source_workspace,
                    run_workspace=run_workspace,
                    phase=phase,
                    mode=phase_mode,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
        except Exception as exc:
            state["contest_status"] = f"CONTEST_GRAPH_FAILED_PHASE_{phase}"
            state["status"] = state["contest_status"]
            state["stop_reason"] = str(exc)
            state["needs_human"] = True
            break
        summary = _phase_result_summary(result, strategy=strategy)
        state["phase_results"].append(summary)
        state["contest_graph_steps"].append(summary)
        state["completed_phases"].append(phase)
        state["pre_audit"] = result.get("pre_audit", state.get("pre_audit", {}))
        state["post_audit"] = result.get("post_audit", state.get("post_audit", {}))
        state["issues"] = list(result.get("issues", []))
        state["prompt_path"] = result.get("prompt_path")
        _merge_file_tracking(state, result)

        if result.get("status") == "PLAN_PARSE_FAILED" or result.get("provider_error"):
            state["contest_status"] = f"CONTEST_GRAPH_FAILED_PHASE_{phase}"
            state["status"] = state["contest_status"]
            state["stop_reason"] = result.get("provider_error") or result.get("stop_reason")
            state["needs_human"] = True
            break

        if phase == 1:
            gate = check_human_model_gate(run_workspace)
            state["human_gate"] = gate
            if not gate["approved"]:
                state["contest_status"] = "WAITING_FOR_HUMAN_MODEL_REVIEW"
                state["status"] = "WAITING_FOR_HUMAN_MODEL_REVIEW"
                state["paused_at"] = "phase_1_human_gate"
                state["human_gate_required"] = True
                state["human_gate_file"] = HUMAN_MODEL_GATE
                state["needs_human"] = True
                state["stop_reason"] = "Phase 1 completed, but HUMAN_MODEL_REVIEW.md is missing or lacks approval."
                break

        if phase == 2:
            sandbox_status = str(result.get("sandbox_status", ""))
            if sandbox_status != "SANDBOX_SUCCEEDED":
                state["contest_status"] = sandbox_status or "PHASE2_SANDBOX_FAILED"
                state["status"] = state["contest_status"]
                state["paused_at"] = "phase_2_sandbox"
                state["needs_human"] = True
                state["stop_reason"] = result.get("stop_reason") or "Phase 2 sandbox did not complete successfully."
                break
            if _audit_has_high_or_blocker(result.get("post_audit", {})):
                state["contest_status"] = "PHASE2_AUDIT_NEEDS_REVIEW"
                state["status"] = "PHASE2_AUDIT_NEEDS_REVIEW"
                state["paused_at"] = "phase_2_audit"
                state["needs_human"] = True
                state["stop_reason"] = "Phase 2 sandbox completed, but post-audit reports HIGH/BLOCKER issues."
                break
    else:
        phase6 = _audit_only_phase6(settings, state)
        summary = _phase_result_summary(phase6, strategy="audit_only")
        state["phase_results"].append(summary)
        state["contest_graph_steps"].append(summary)
        state["completed_phases"].append(6)
        state["post_audit"] = phase6["post_audit"]
        state["issues"] = list(phase6["post_audit"].get("issues", [])) if isinstance(phase6["post_audit"], dict) else []
        state["contest_status"] = "CONTEST_GRAPH_REVIEW_READY"
        state["status"] = "CONTEST_GRAPH_REVIEW_READY"
        state["needs_human"] = True
        state["stop_reason"] = "Contest graph v1 completed safe orchestration through Phase 6 audit-only."

    if "human_gate" not in state:
        state["human_gate"] = check_human_model_gate(run_workspace)
    if not state.get("final_audit"):
        state["final_audit"] = state.get("post_audit", {})

    _write_contest_graph_report(state)
    history = append_history(
        source_workspace,
        {
            "event": "langgraph_contest_graph_v1",
            "phase": None,
            "harness": "LangGraph",
            "source_workspace": str(source_workspace),
            "run_workspace": str(run_workspace),
            "prompt_path": state.get("prompt_path"),
            "status_before": str(state.get("pre_audit", {}).get("status", "UNKNOWN")),
            "status_after": str(state.get("post_audit", {}).get("status", "UNKNOWN")),
            "note": state.get("stop_reason"),
        },
    )
    state["history"] = history
    return dict(state)


def _phase3_paper_phase(
    *,
    settings: Settings,
    source_workspace: Path,
    run_workspace: Path,
    provider: str,
    model: str | None,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    plan_result = _run_phase_in_workspace(
        settings=settings,
        source_workspace=source_workspace,
        run_workspace=run_workspace,
        phase=3,
        mode="llm_plan",
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if plan_result.get("phase_plan") is None or plan_result.get("provider_error"):
        return plan_result
    paper_state = _initial_state(
        source_workspace=source_workspace,
        run_workspace=run_workspace,
        phase=3,
        mode="contest_graph_v2",
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    paper_state["prompt_path"] = plan_result.get("prompt_path")
    paper_state["plan_path"] = plan_result.get("plan_path")
    paper_state["plan_markdown_path"] = plan_result.get("plan_markdown_path")
    paper_state["phase_plan"] = plan_result.get("phase_plan")
    paper_result = run_phase3_paper_sandbox(paper_state)
    audit = run_audit(settings, run_workspace)
    merged = dict(plan_result)
    merged.update(
        {
            "mode": "phase3_paper_sandbox",
            "status": paper_result["paper_sandbox_status"],
            "paper_sandbox_status": paper_result["paper_sandbox_status"],
            "paper_files_written": paper_result.get("paper_files_written", []),
            "claim_trace_path": paper_result.get("claim_trace_path"),
            "method_matrix_path": paper_result.get("method_matrix_path"),
            "paper_build_report_path": paper_result.get("paper_build_report_path"),
            "paper_sandbox_error": paper_result.get("paper_sandbox_error"),
            "post_audit": audit.get("result", {}),
            "issues": list(audit.get("result", {}).get("issues", [])),
            "stop_reason": paper_state.get("stop_reason"),
            "created_files": list(dict.fromkeys(plan_result.get("created_files", []) + paper_state.get("created_files", []))),
            "updated_files": list(dict.fromkeys(plan_result.get("updated_files", []) + paper_state.get("updated_files", []))),
        }
    )
    return merged


def run_contest_graph_v2(
    *,
    settings: Settings,
    source_workspace: Path,
    requested_phase: int,
    provider: str,
    model: str | None,
    copy_workspace: bool,
    run_name: str | None,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    source_workspace = source_workspace.resolve()
    if not source_workspace.is_dir():
        raise ValueError(f"Source workspace does not exist: {source_workspace}")
    run_workspace = (
        copy_workspace_for_run(source_workspace, run_name or "langgraph-contest-graph-v2")
        if copy_workspace
        else source_workspace
    ).resolve()

    state = _initial_state(
        source_workspace=source_workspace,
        run_workspace=run_workspace,
        phase=requested_phase,
        mode="contest_graph_v2",
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    state["contest_graph_steps"] = []
    state["phase_results"] = []
    state["completed_phases"] = []
    state["paused_at"] = None
    state["human_gate_required"] = False
    state["human_gate_file"] = HUMAN_MODEL_GATE
    state["contest_status"] = "RUNNING"
    state["final_audit"] = {}
    state["graph_report_path"] = None
    state["sandbox_commands"] = []
    state["sandbox_status"] = None
    state["manifest_created_empty"] = False
    state["paper_sandbox_status"] = None
    state["paper_files_written"] = []
    state["claim_trace_path"] = None
    state["method_matrix_path"] = None
    state["paper_build_report_path"] = None
    state["paper_sandbox_error"] = None
    assert_run_workspace_allowed(state)

    for phase in range(0, 6):
        state["current_phase"] = phase
        try:
            if phase == 2:
                result = _phase2_sandbox_phase(
                    settings=settings,
                    source_workspace=source_workspace,
                    run_workspace=run_workspace,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                strategy = "phase2_sandbox_executor"
            elif phase == 3:
                result = _phase3_paper_phase(
                    settings=settings,
                    source_workspace=source_workspace,
                    run_workspace=run_workspace,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                strategy = "phase3_paper_sandbox"
            else:
                phase_mode = _contest_phase_mode(phase)
                strategy = "phase_execute_allowlisted_reports" if phase_mode == "phase_execute" else "llm_plan_only"
                result = _run_phase_in_workspace(
                    settings=settings,
                    source_workspace=source_workspace,
                    run_workspace=run_workspace,
                    phase=phase,
                    mode=phase_mode,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
        except Exception as exc:
            state["contest_status"] = f"CONTEST_GRAPH_FAILED_PHASE_{phase}"
            state["status"] = state["contest_status"]
            state["stop_reason"] = str(exc)
            state["needs_human"] = True
            break
        summary = _phase_result_summary(result, strategy=strategy)
        state["phase_results"].append(summary)
        state["contest_graph_steps"].append(summary)
        state["completed_phases"].append(phase)
        state["pre_audit"] = result.get("pre_audit", state.get("pre_audit", {}))
        state["post_audit"] = result.get("post_audit", state.get("post_audit", {}))
        state["issues"] = list(result.get("issues", []))
        state["prompt_path"] = result.get("prompt_path")
        _merge_file_tracking(state, result)

        if result.get("status") == "PLAN_PARSE_FAILED" or result.get("provider_error"):
            state["contest_status"] = f"CONTEST_GRAPH_FAILED_PHASE_{phase}"
            state["status"] = state["contest_status"]
            state["stop_reason"] = result.get("provider_error") or result.get("stop_reason")
            state["needs_human"] = True
            break

        if phase == 1:
            gate = check_human_model_gate(run_workspace)
            state["human_gate"] = gate
            if not gate["approved"]:
                state["contest_status"] = "WAITING_FOR_HUMAN_MODEL_REVIEW"
                state["status"] = "WAITING_FOR_HUMAN_MODEL_REVIEW"
                state["paused_at"] = "phase_1_human_gate"
                state["human_gate_required"] = True
                state["human_gate_file"] = HUMAN_MODEL_GATE
                state["needs_human"] = True
                state["stop_reason"] = "Phase 1 completed, but HUMAN_MODEL_REVIEW.md is missing or lacks approval."
                break

        if phase == 2:
            sandbox_status = str(result.get("sandbox_status", ""))
            if sandbox_status != "SANDBOX_SUCCEEDED":
                state["contest_status"] = sandbox_status or "PHASE2_SANDBOX_FAILED"
                state["status"] = state["contest_status"]
                state["paused_at"] = "phase_2_sandbox"
                state["needs_human"] = True
                state["stop_reason"] = result.get("stop_reason") or "Phase 2 sandbox did not complete successfully."
                break
            if _audit_has_high_or_blocker(result.get("post_audit", {})):
                state["contest_status"] = "PHASE2_AUDIT_NEEDS_REVIEW"
                state["status"] = "PHASE2_AUDIT_NEEDS_REVIEW"
                state["paused_at"] = "phase_2_audit"
                state["needs_human"] = True
                state["stop_reason"] = "Phase 2 sandbox completed, but post-audit reports HIGH/BLOCKER issues."
                break

        if phase == 3:
            paper_status = str(result.get("paper_sandbox_status", ""))
            if paper_status != "PAPER_SANDBOX_SUCCEEDED":
                state["contest_status"] = paper_status or "PHASE3_PAPER_SANDBOX_FAILED"
                state["status"] = state["contest_status"]
                state["paused_at"] = "phase_3_paper_sandbox"
                state["needs_human"] = True
                state["stop_reason"] = result.get("stop_reason") or "Phase 3 paper sandbox did not complete successfully."
                break

        if phase == 4 and _audit_has_high_or_blocker(result.get("post_audit", {})):
            state["contest_status"] = "REVISION_REQUIRED"
            state["status"] = "REVISION_REQUIRED"
            state["paused_at"] = "phase_4_review"
            state["needs_human"] = True
            state["stop_reason"] = "Phase 4 review found HIGH/BLOCKER issues; revision is required."
            break
    else:
        phase6 = _audit_only_phase6(settings, state)
        summary = _phase_result_summary(phase6, strategy="audit_only")
        state["phase_results"].append(summary)
        state["contest_graph_steps"].append(summary)
        state["completed_phases"].append(6)
        state["post_audit"] = phase6["post_audit"]
        state["issues"] = list(phase6["post_audit"].get("issues", [])) if isinstance(phase6["post_audit"], dict) else []
        state["contest_status"] = "CONTEST_GRAPH_REVIEW_READY"
        state["status"] = "CONTEST_GRAPH_REVIEW_READY"
        state["needs_human"] = True
        state["stop_reason"] = "Contest graph v2 completed safe orchestration through Phase 6 audit-only."

    if "human_gate" not in state:
        state["human_gate"] = check_human_model_gate(run_workspace)
    if not state.get("final_audit"):
        state["final_audit"] = state.get("post_audit", {})

    _write_contest_graph_report(state)
    history = append_history(
        source_workspace,
        {
            "event": "langgraph_contest_graph_v2",
            "phase": None,
            "harness": "LangGraph",
            "source_workspace": str(source_workspace),
            "run_workspace": str(run_workspace),
            "prompt_path": state.get("prompt_path"),
            "status_before": str(state.get("pre_audit", {}).get("status", "UNKNOWN")),
            "status_after": str(state.get("post_audit", {}).get("status", "UNKNOWN")),
            "note": state.get("stop_reason"),
        },
    )
    state["history"] = history
    return dict(state)


def _phase5_revision_phase(
    *,
    settings: Settings,
    source_workspace: Path,
    run_workspace: Path,
    provider: str,
    model: str | None,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    plan_result = _run_phase_in_workspace(
        settings=settings,
        source_workspace=source_workspace,
        run_workspace=run_workspace,
        phase=5,
        mode="llm_plan",
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if plan_result.get("phase_plan") is None or plan_result.get("provider_error"):
        return plan_result
    revision_state = _initial_state(
        source_workspace=source_workspace,
        run_workspace=run_workspace,
        phase=5,
        mode="contest_graph_v3",
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    revision_state["prompt_path"] = plan_result.get("prompt_path")
    revision_state["plan_path"] = plan_result.get("plan_path")
    revision_state["plan_markdown_path"] = plan_result.get("plan_markdown_path")
    revision_state["phase_plan"] = plan_result.get("phase_plan")
    revision_result = run_phase5_revision_sandbox(revision_state)
    audit = run_audit(settings, run_workspace)
    merged = dict(plan_result)
    merged.update(
        {
            "mode": "phase5_revision_sandbox",
            "status": revision_result["revision_sandbox_status"],
            "revision_sandbox_status": revision_result["revision_sandbox_status"],
            "revision_files_written": revision_result.get("revision_files_written", []),
            "revision_status_path": revision_result.get("revision_status_path"),
            "revision_sandbox_error": revision_result.get("revision_sandbox_error"),
            "contest_status": revision_state.get("contest_status"),
            "post_audit": audit.get("result", {}),
            "issues": list(audit.get("result", {}).get("issues", [])),
            "stop_reason": revision_state.get("stop_reason"),
            "created_files": list(dict.fromkeys(plan_result.get("created_files", []) + revision_state.get("created_files", []))),
            "updated_files": list(dict.fromkeys(plan_result.get("updated_files", []) + revision_state.get("updated_files", []))),
        }
    )
    return merged


def run_contest_graph_v3(
    *,
    settings: Settings,
    source_workspace: Path,
    requested_phase: int,
    provider: str,
    model: str | None,
    copy_workspace: bool,
    run_name: str | None,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    source_workspace = source_workspace.resolve()
    if not source_workspace.is_dir():
        raise ValueError(f"Source workspace does not exist: {source_workspace}")
    run_workspace = (
        copy_workspace_for_run(source_workspace, run_name or "langgraph-contest-graph-v3")
        if copy_workspace
        else source_workspace
    ).resolve()

    state = _initial_state(
        source_workspace=source_workspace,
        run_workspace=run_workspace,
        phase=requested_phase,
        mode="contest_graph_v3",
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    state["contest_graph_steps"] = []
    state["phase_results"] = []
    state["completed_phases"] = []
    state["paused_at"] = None
    state["human_gate_required"] = False
    state["human_gate_file"] = HUMAN_MODEL_GATE
    state["contest_status"] = "RUNNING"
    state["final_audit"] = {}
    state["graph_report_path"] = None
    state["sandbox_commands"] = []
    state["sandbox_status"] = None
    state["manifest_created_empty"] = False
    state["paper_sandbox_status"] = None
    state["paper_files_written"] = []
    state["claim_trace_path"] = None
    state["method_matrix_path"] = None
    state["paper_build_report_path"] = None
    state["paper_sandbox_error"] = None
    state["revision_sandbox_status"] = None
    state["revision_files_written"] = []
    state["revision_status_path"] = None
    state["revision_sandbox_error"] = None
    assert_run_workspace_allowed(state)

    for phase in range(0, 6):
        state["current_phase"] = phase
        try:
            if phase == 2:
                result = _phase2_sandbox_phase(
                    settings=settings,
                    source_workspace=source_workspace,
                    run_workspace=run_workspace,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                strategy = "phase2_sandbox_executor"
            elif phase == 3:
                result = _phase3_paper_phase(
                    settings=settings,
                    source_workspace=source_workspace,
                    run_workspace=run_workspace,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                strategy = "phase3_paper_sandbox"
            elif phase == 5:
                result = _phase5_revision_phase(
                    settings=settings,
                    source_workspace=source_workspace,
                    run_workspace=run_workspace,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                strategy = "phase5_revision_sandbox"
            else:
                phase_mode = _contest_phase_mode(phase)
                strategy = "phase_execute_allowlisted_reports" if phase_mode == "phase_execute" else "llm_plan_only"
                result = _run_phase_in_workspace(
                    settings=settings,
                    source_workspace=source_workspace,
                    run_workspace=run_workspace,
                    phase=phase,
                    mode=phase_mode,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
        except Exception as exc:
            state["contest_status"] = f"CONTEST_GRAPH_FAILED_PHASE_{phase}"
            state["status"] = state["contest_status"]
            state["stop_reason"] = str(exc)
            state["needs_human"] = True
            break
        summary = _phase_result_summary(result, strategy=strategy)
        state["phase_results"].append(summary)
        state["contest_graph_steps"].append(summary)
        state["completed_phases"].append(phase)
        state["pre_audit"] = result.get("pre_audit", state.get("pre_audit", {}))
        state["post_audit"] = result.get("post_audit", state.get("post_audit", {}))
        state["issues"] = list(result.get("issues", []))
        state["prompt_path"] = result.get("prompt_path")
        _merge_file_tracking(state, result)

        if result.get("status") == "PLAN_PARSE_FAILED" or result.get("provider_error"):
            state["contest_status"] = f"CONTEST_GRAPH_FAILED_PHASE_{phase}"
            state["status"] = state["contest_status"]
            state["stop_reason"] = result.get("provider_error") or result.get("stop_reason")
            state["needs_human"] = True
            break

        if phase == 1:
            gate = check_human_model_gate(run_workspace)
            state["human_gate"] = gate
            if not gate["approved"]:
                state["contest_status"] = "WAITING_FOR_HUMAN_MODEL_REVIEW"
                state["status"] = "WAITING_FOR_HUMAN_MODEL_REVIEW"
                state["paused_at"] = "phase_1_human_gate"
                state["human_gate_required"] = True
                state["human_gate_file"] = HUMAN_MODEL_GATE
                state["needs_human"] = True
                state["stop_reason"] = "Phase 1 completed, but HUMAN_MODEL_REVIEW.md is missing or lacks approval."
                break

        if phase == 2:
            sandbox_status = str(result.get("sandbox_status", ""))
            if sandbox_status != "SANDBOX_SUCCEEDED":
                state["contest_status"] = sandbox_status or "PHASE2_SANDBOX_FAILED"
                state["status"] = state["contest_status"]
                state["paused_at"] = "phase_2_sandbox"
                state["needs_human"] = True
                state["stop_reason"] = result.get("stop_reason") or "Phase 2 sandbox did not complete successfully."
                break
            if _audit_has_high_or_blocker(result.get("post_audit", {})):
                state["contest_status"] = "PHASE2_AUDIT_NEEDS_REVIEW"
                state["status"] = "PHASE2_AUDIT_NEEDS_REVIEW"
                state["paused_at"] = "phase_2_audit"
                state["needs_human"] = True
                state["stop_reason"] = "Phase 2 sandbox completed, but post-audit reports HIGH/BLOCKER issues."
                break

        if phase == 3:
            paper_status = str(result.get("paper_sandbox_status", ""))
            if paper_status != "PAPER_SANDBOX_SUCCEEDED":
                state["contest_status"] = paper_status or "PHASE3_PAPER_SANDBOX_FAILED"
                state["status"] = state["contest_status"]
                state["paused_at"] = "phase_3_paper_sandbox"
                state["needs_human"] = True
                state["stop_reason"] = result.get("stop_reason") or "Phase 3 paper sandbox did not complete successfully."
                break

        if phase == 4 and _audit_has_high_or_blocker(result.get("post_audit", {})):
            state["contest_status"] = "REVISION_REQUIRED"
            state["status"] = "REVISION_REQUIRED"
            state["paused_at"] = "phase_4_review"
            state["needs_human"] = True
            state["stop_reason"] = "Phase 4 review found HIGH/BLOCKER issues; revision is required."
            break

        if phase == 5:
            revision_status = str(result.get("revision_sandbox_status", ""))
            state["contest_status"] = result.get("contest_status") or state.get("contest_status") or revision_status
            if revision_status in {"REVISION_SANDBOX_REJECTED", "REVISION_SANDBOX_ROLLED_BACK"}:
                state["status"] = state["contest_status"]
                state["paused_at"] = "phase_5_revision_sandbox"
                state["needs_human"] = True
                state["stop_reason"] = result.get("stop_reason") or "Phase 5 revision sandbox encountered a fatal error."
                break
    else:
        phase6 = _audit_only_phase6(settings, state)
        summary = _phase_result_summary(phase6, strategy="audit_only")
        state["phase_results"].append(summary)
        state["contest_graph_steps"].append(summary)
        state["completed_phases"].append(6)
        state["post_audit"] = phase6["post_audit"]
        state["issues"] = list(phase6["post_audit"].get("issues", [])) if isinstance(phase6["post_audit"], dict) else []
        if not state.get("contest_status") or state.get("contest_status") == "RUNNING":
            state["contest_status"] = "CONTEST_GRAPH_REVIEW_READY"
        state["status"] = state["contest_status"]
        state["needs_human"] = True
        state["stop_reason"] = "Contest graph v3 completed safe orchestration through Phase 6 audit-only. VERIFY_REPORT.md was not written."

    if "human_gate" not in state:
        state["human_gate"] = check_human_model_gate(run_workspace)
    if not state.get("final_audit"):
        state["final_audit"] = state.get("post_audit", {})

    _write_contest_graph_report(state)
    history = append_history(
        source_workspace,
        {
            "event": "langgraph_contest_graph_v3",
            "phase": None,
            "harness": "LangGraph",
            "source_workspace": str(source_workspace),
            "run_workspace": str(run_workspace),
            "prompt_path": state.get("prompt_path"),
            "status_before": str(state.get("pre_audit", {}).get("status", "UNKNOWN")),
            "status_after": str(state.get("post_audit", {}).get("status", "UNKNOWN")),
            "note": state.get("stop_reason"),
        },
    )
    state["history"] = history
    return dict(state)


def run_langgraph_phase(
    *,
    settings: Settings,
    source_workspace: Path,
    phase: int,
    mode: str = "dry_run",
    provider: str = "none",
    model: str | None = None,
    copy_workspace: bool = True,
    run_name: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    if not langgraph_available():
        raise LangGraphUnavailableError(
            "LangGraph is not installed. Install with: pip install -r app/backend/requirements-langgraph.txt"
        )
    if mode not in SUPPORTED_MODES:
        raise ValueError(
            "LangGraph Phase Runner supports mode='dry_run', mode='llm_plan', "
            "mode='controlled_apply', mode='phase_execute', mode='contest_graph_v0', mode='contest_graph_v1', "
            "or mode='contest_graph_v3'."
        )
    if _is_contest_graph_mode(mode):
        if mode == "contest_graph_v3":
            return run_contest_graph_v3(
                settings=settings,
                source_workspace=source_workspace,
                requested_phase=phase,
                provider=provider,
                model=model,
                copy_workspace=copy_workspace,
                run_name=run_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        if mode == "contest_graph_v2":
            return run_contest_graph_v2(
                settings=settings,
                source_workspace=source_workspace,
                requested_phase=phase,
                provider=provider,
                model=model,
                copy_workspace=copy_workspace,
                run_name=run_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        if mode == "contest_graph_v1":
            return run_contest_graph_v1(
                settings=settings,
                source_workspace=source_workspace,
                requested_phase=phase,
                provider=provider,
                model=model,
                copy_workspace=copy_workspace,
                run_name=run_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        return run_contest_graph_v0(
            settings=settings,
            source_workspace=source_workspace,
            requested_phase=phase,
            provider=provider,
            model=model,
            copy_workspace=copy_workspace,
            run_name=run_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    if mode == "controlled_apply" and phase not in APPLY_ALLOWED_PATHS:
        raise ValueError("controlled_apply only supports phase 1 and phase 4.")
    if mode == "phase_execute" and phase not in APPLY_ALLOWED_PATHS:
        raise ValueError("PHASE_NOT_SUPPORTED: phase_execute only supports phase 1 and phase 4.")
    if phase < 0 or phase > 6:
        raise ValueError("phase must be between 0 and 6.")

    source_workspace = source_workspace.resolve()
    if not source_workspace.is_dir():
        raise ValueError(f"Source workspace does not exist: {source_workspace}")
    run_workspace = (
        copy_workspace_for_run(source_workspace, run_name or f"langgraph-phase-{phase}")
        if copy_workspace
        else source_workspace
    ).resolve()

    return _run_phase_in_workspace(
        settings=settings,
        source_workspace=source_workspace,
        run_workspace=run_workspace,
        phase=phase,
        mode=mode,
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
