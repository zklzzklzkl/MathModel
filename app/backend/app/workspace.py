from __future__ import annotations

import base64
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from .config import Settings
from .models import ArtifactItem, PhaseSummary, WorkspaceItem


PHASES: list[dict[str, Any]] = [
    {
        "id": 0,
        "name": "题面与数据建档",
        "skill": "mm-problem-intake",
        "gate": "reports/INTAKE_GATE.md",
        "artifacts": ["PROBLEM_BRIEF.md", "DATA_AUDIT.md", "reports/INTAKE_GATE.md"],
    },
    {
        "id": 1,
        "name": "建模策略与人工闸门",
        "skill": "mm-model-strategy",
        "gate": "reports/HUMAN_MODEL_REVIEW.md",
        "artifacts": [
            "reports/MODEL_CANDIDATES.md",
            "reports/MODEL_REVIEW_AI.md",
            "reports/HUMAN_MODEL_REVIEW.md",
            "reports/MODELING_DECISION.md",
            "reports/ANALYSIS_MODELING_REPORT.md",
            "reports/ANALYSIS_GATE.md",
        ],
    },
    {
        "id": 2,
        "name": "实验与可视化",
        "skill": "mm-data-experiment",
        "gate": "results/RESULTS_MANIFEST.json",
        "artifacts": [
            "code",
            "figures",
            "reports/EXPERIMENT_LOG.md",
            "reports/RESULTS_REPORT.md",
            "reports/FIGURE_PLAN.md",
            "reports/FIGURE_AUDIT.md",
            "results/RESULTS_MANIFEST.json",
        ],
    },
    {
        "id": 3,
        "name": "论文构建与证据追踪",
        "skill": "mm-paper-build",
        "gate": "reports/CLAIM_TRACE.md",
        "artifacts": [
            "paper",
            "reports/CLAIM_TRACE.md",
            "reports/PAPER_BUILD_REPORT.md",
            "reports/METHOD_IMPLEMENTATION_MATRIX.md",
        ],
    },
    {
        "id": 4,
        "name": "竞赛评分审查",
        "skill": "mm-contest-review",
        "gate": "reports/PAPER_SCORECARD.md",
        "artifacts": ["reports/PAPER_SCORECARD.md", "reports/REVISION_ACTIONS.md"],
    },
    {
        "id": 5,
        "name": "修订集成",
        "skill": "mm-revision-integrator",
        "gate": "reports/REVISION_STATUS.md",
        "artifacts": ["reports/REVISION_ACTIONS.md", "reports/REVISION_STATUS.md"],
    },
    {
        "id": 6,
        "name": "最终验收",
        "skill": "mm-final-verify",
        "gate": "reports/VERIFY_REPORT.md",
        "artifacts": ["reports/VERIFY_REPORT.md", "results/RESULTS_MANIFEST.json", "paper"],
    },
]

REQUIRED_ARTIFACTS = sorted({item for phase in PHASES for item in phase["artifacts"]})


def encode_workspace_id(path: Path) -> str:
    raw = str(path.resolve()).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_workspace_id(workspace_id: str) -> Path:
    padding = "=" * (-len(workspace_id) % 4)
    try:
        raw = base64.urlsafe_b64decode(workspace_id + padding)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid workspace id") from exc
    return Path(raw.decode("utf-8")).resolve()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def ensure_allowed(path: Path, settings: Settings) -> Path:
    resolved = path.resolve()
    roots = [settings.mathmodel_root, settings.workspace_root, settings.examples_root]
    if not any(_is_relative_to(resolved, root) for root in roots):
        raise HTTPException(status_code=403, detail="Path is outside allowed roots")
    return resolved


def workspace_from_id(workspace_id: str, settings: Settings) -> Path:
    path = ensure_allowed(decode_workspace_id(workspace_id), settings)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")
    return path


def is_v2_workspace(path: Path) -> bool:
    return (
        path.is_dir()
        and (path / "reports").is_dir()
        and ((path / "WORKFLOW_STATE.md").is_file() or (path / "PROBLEM_BRIEF.md").is_file())
    )


def _mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def workspace_item(path: Path, settings: Settings, source: str | None = None) -> WorkspaceItem:
    resolved = path.resolve()
    if source is None:
        if _is_relative_to(resolved, settings.workspace_root):
            source = "workspace_root"
        elif _is_relative_to(resolved, settings.examples_root):
            source = "examples"
        else:
            source = "other"
    return WorkspaceItem(
        id=encode_workspace_id(resolved),
        name=resolved.name,
        path=str(resolved),
        source=source,  # type: ignore[arg-type]
        updated_at=_mtime(resolved),
        has_v2_shape=is_v2_workspace(resolved),
    )


def discover_workspaces(settings: Settings) -> list[WorkspaceItem]:
    candidates: dict[str, WorkspaceItem] = {}
    for root, source in ((settings.workspace_root, "workspace_root"), (settings.examples_root, "examples")):
        if not root.exists():
            continue
        for item in sorted(root.rglob("*")):
            if is_v2_workspace(item):
                candidates[str(item.resolve())] = workspace_item(item, settings, source)
    return sorted(candidates.values(), key=lambda item: (item.source, item.name.lower()))


def artifact_type(path: Path) -> str:
    if path.is_dir():
        return "directory"
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".json":
        return "json"
    if suffix in {".txt", ".log", ".py", ".typ", ".tex", ".csv"}:
        return "text"
    if suffix in {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp"}:
        return "image"
    if suffix == ".pdf":
        return "pdf"
    return "binary"


def artifact_item(workspace: Path, relative: str, required: bool = False) -> ArtifactItem:
    target = (workspace / relative).resolve()
    exists = target.exists()
    stat = target.stat() if exists else None
    return ArtifactItem(
        path=relative.replace("\\", "/"),
        exists=exists,
        type=artifact_type(target) if exists else "missing",
        size=stat.st_size if stat and target.is_file() else None,
        updated_at=_mtime(target),
        required=required,
    )


def list_artifacts(workspace: Path) -> list[ArtifactItem]:
    items: dict[str, ArtifactItem] = {}
    for relative in REQUIRED_ARTIFACTS:
        items[relative] = artifact_item(workspace, relative, required=True)
    for folder in ("source", "code", "figures", "paper", "reports", "results"):
        base = workspace / folder
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_dir():
                continue
            relative = path.relative_to(workspace).as_posix()
            items.setdefault(relative, artifact_item(workspace, relative, required=False))
    return sorted(items.values(), key=lambda item: (not item.required, item.path.lower()))


def safe_artifact_path(workspace: Path, relative: str) -> Path:
    if not relative:
        raise HTTPException(status_code=400, detail="Artifact path is required")
    target = (workspace / relative).resolve()
    if not _is_relative_to(target, workspace):
        raise HTTPException(status_code=403, detail="Artifact path escapes workspace")
    return target


def read_json(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def gate_status(workspace: Path, gate: str) -> tuple[str, str]:
    path = workspace / gate
    if not path.exists():
        return "MISSING", "bad"
    if path.suffix.lower() == ".json":
        data = read_json(path)
        if isinstance(data, list):
            return "LEGACY", "warn"
        if isinstance(data, dict):
            return "READY", "good"
        return "INVALID", "bad"
    text = read_text(path)
    normalized = text.lower()
    if re.search(r"\bpass\b", text, re.IGNORECASE) and "fail" not in normalized:
        return "PASS", "good"
    if "fail" in normalized or "blocker" in normalized:
        return "FAIL", "bad"
    if "conditional_pass" in normalized or "high" in normalized or "pending" in normalized:
        return "PENDING", "warn"
    return "READY", "info"


def build_phase_summaries(workspace: Path) -> list[PhaseSummary]:
    phases: list[PhaseSummary] = []
    for phase in PHASES:
        status, status_class = gate_status(workspace, phase["gate"])
        phases.append(
            PhaseSummary(
                id=phase["id"],
                name=phase["name"],
                skill=phase["skill"],
                gate=phase["gate"],
                status=status,
                status_class=status_class,
                artifacts=phase["artifacts"],
            )
        )
    return phases


def manifest_summary(workspace: Path) -> dict[str, Any]:
    path = workspace / "results" / "RESULTS_MANIFEST.json"
    data = read_json(path)
    if isinstance(data, dict):
        return {
            "schema": "object",
            "metrics": len(data.get("metrics", []) if isinstance(data.get("metrics"), list) else []),
            "tables": len(data.get("tables", []) if isinstance(data.get("tables"), list) else []),
            "figures": len(data.get("figures", []) if isinstance(data.get("figures"), list) else []),
            "scripts": len(data.get("scripts", []) if isinstance(data.get("scripts"), list) else []),
        }
    if isinstance(data, list):
        return {"schema": "legacy_list", "metrics": len(data), "tables": 0, "figures": 0, "scripts": 0}
    return {"schema": "missing_or_invalid", "metrics": 0, "tables": 0, "figures": 0, "scripts": 0}


def paper_summary(workspace: Path) -> dict[str, Any]:
    paper = workspace / "paper"
    pdfs = sorted(paper.glob("*.pdf")) if paper.is_dir() else []
    return {
        "exists": paper.is_dir(),
        "pdf_count": len(pdfs),
        "pdfs": [item.name for item in pdfs],
    }


def copy_workspace_for_run(workspace: Path, name: str | None = None) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", name or workspace.name).strip("-") or "run"
    destination = workspace / "runs" / f"{stamp}-{safe_name}"
    ignore = shutil.ignore_patterns("runs", ".venv", "__pycache__", ".pytest_cache", "node_modules")
    shutil.copytree(workspace, destination, ignore=ignore)
    return destination
