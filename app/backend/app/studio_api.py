from __future__ import annotations

import asyncio
import io
import json
import os
import re
import shutil
import sqlite3
import ssl
import threading
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen
from urllib.error import URLError

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import Response, StreamingResponse

from .config import Settings, get_settings as default_get_settings


router = APIRouter()

_settings_provider: Callable[[], Settings] = default_get_settings


def set_settings_provider(provider: Callable[[], Settings]) -> None:
    global _settings_provider
    _settings_provider = provider


def settings() -> Settings:
    return _settings_provider()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str, fallback: str = "project") -> str:
    cleaned = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", value.strip())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-_")
    return cleaned[:48] or fallback


def db_path() -> Path:
    env = os.environ.get("MATHMODEL_STUDIO_DB")
    if env:
        return Path(env).resolve()
    return settings().mathmodel_root / "app" / "backend" / ".local" / "studio-v3.sqlite3"


def template_root() -> Path:
    env = os.environ.get("MATHMODEL_TEMPLATE_PACK_ROOT")
    if env:
        return Path(env).resolve()
    return settings().mathmodel_root / "template_packs"


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            domain TEXT NOT NULL,
            contest TEXT NOT NULL DEFAULT '',
            workspace_path TEXT NOT NULL,
            template_id TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            driver TEXT NOT NULL,
            status TEXT NOT NULL,
            current_stage TEXT NOT NULL,
            workspace_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS run_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            artifacts TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS gates (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            title TEXT NOT NULL,
            artifacts TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS artifacts (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            run_id TEXT,
            path TEXT NOT NULL,
            type TEXT NOT NULL,
            size INTEGER NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(project_id, path)
        );
        CREATE TABLE IF NOT EXISTS template_packs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            contest TEXT NOT NULL,
            language TEXT NOT NULL,
            engine TEXT NOT NULL,
            main_file TEXT NOT NULL,
            description TEXT NOT NULL,
            required_files TEXT NOT NULL,
            preview_file TEXT NOT NULL,
            root_path TEXT NOT NULL,
            warnings TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS studio_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def row_to_project(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "domain": row["domain"],
        "contest": row["contest"],
        "workspace_path": row["workspace_path"],
        "template_id": row["template_id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def row_to_run(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "driver": row["driver"],
        "status": row["status"],
        "current_stage": row["current_stage"],
        "workspace_path": row["workspace_path"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def row_to_event(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "run_id": row["run_id"],
        "stage": row["stage"],
        "type": row["type"],
        "severity": row["severity"],
        "message": row["message"],
        "artifacts": json.loads(row["artifacts"]),
        "created_at": row["created_at"],
    }


def row_to_gate(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "run_id": row["run_id"],
        "type": row["type"],
        "status": row["status"],
        "title": row["title"],
        "artifacts": json.loads(row["artifacts"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def row_to_gate_with_previews(row: sqlite3.Row, workspace: Path) -> dict[str, Any]:
    gate = row_to_gate(row)
    max_preview_bytes = 512 * 1024
    resolved_workspace = workspace.resolve()
    previews = []
    for relative_path in gate["artifacts"]:
        target = (workspace / relative_path).resolve()
        if not target.is_relative_to(resolved_workspace):
            continue
        if not target.is_file():
            continue
        size = target.stat().st_size
        raw = target.read_bytes()[:max_preview_bytes]
        previews.append(
            {
                "path": relative_path,
                "type": artifact_type_for(relative_path),
                "size": size,
                "truncated": size > max_preview_bytes,
                "content": raw.decode("utf-8", errors="replace"),
            }
        )
    gate["artifact_previews"] = previews
    return gate


def row_to_artifact(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "run_id": row["run_id"],
        "path": row["path"],
        "type": row["type"],
        "size": row["size"],
        "updated_at": row["updated_at"],
    }


def row_to_template(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "contest": row["contest"],
        "language": row["language"],
        "engine": row["engine"],
        "main_file": row["main_file"],
        "description": row["description"],
        "required_files": json.loads(row["required_files"]),
        "preview_file": row["preview_file"],
        "root_path": row["root_path"],
        "warnings": json.loads(row["warnings"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def project_workspace(project_id: str, name: str) -> Path:
    return (settings().workspace_root / f"{slugify(name)}-{project_id[:8]}").resolve()


def ensure_v2_workspace_skeleton(workspace: Path, name: str, contest: str) -> None:
    for relative in ("reports", "results", "code", "figures", "paper", "source"):
        (workspace / relative).mkdir(parents=True, exist_ok=True)
    defaults = {
        "plan.md": f"# {name}\n\nContest: {contest or '待确认'}\n",
        "todo.md": "# Todo\n\n- [ ] Phase 0 intake\n",
        "WORKFLOW_STATE.md": "# Workflow State\n\ncurrent_phase: project_created\n",
        "PROBLEM_BRIEF.md": "# Problem Brief\n\n待上传题面与附件。\n",
        "DATA_AUDIT.md": "# Data Audit\n\n待上传数据。\n",
    }
    for relative, content in defaults.items():
        target = workspace / relative
        if not target.exists():
            target.write_text(content, encoding="utf-8")


def ensure_human_gate_artifacts(workspace: Path) -> list[str]:
    reports = workspace / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    files = {
        "MODEL_CANDIDATES.md": (
            "# Model Candidates\n\n"
            "## Route A\n\n"
            "推荐优先完成可解释模型和稳健性分析。\n\n"
            "- 可解释性强\n- 计算成本低\n- 易于调试\n\n"
            "## Route B (备选)\n\n"
            "深度学习方法，精度更高但可解释性较弱。\n"
        ),
        "MODEL_REVIEW_AI.md": (
            "# AI Model Review\n\n"
            "## Risk Assessment\n\n"
            "- risk: Route A 可能在极端数据下鲁棒性不足\n"
            "- risk: Route B 需要大量计算资源\n"
            "- 建议补充灵敏度分析\n\n"
            "## Recommendations\n\n"
            "优先 Route A，保留 Route B 作为修订备选。\n"
        ),
        "FIGURE_PLAN.md": (
            "# Figure Plan\n\n"
            "## Planned Figures\n\n"
            "- figure: 技术路线图\n"
            "- figure: 子问题求解流程图\n"
            "- figure: 模型结构图\n"
            "- figure: 数据处理流程图\n"
            "- figure: 结果对比图\n"
        ),
    }
    paths = []
    for filename, content in files.items():
        target = reports / filename
        if not target.exists():
            target.write_text(content, encoding="utf-8")
        paths.append(f"reports/{filename}")
    return paths


def artifact_type_for(relative_path: str) -> str:
    top = relative_path.split("/", 1)[0]
    return {
        "source": "source",
        "reports": "report",
        "results": "result",
        "code": "code",
        "figures": "figure",
        "paper": "paper",
    }.get(top, "workspace")


def upsert_artifact(
    conn: sqlite3.Connection,
    *,
    project_id: str,
    run_id: str | None,
    relative_path: str,
    size: int,
) -> None:
    artifact_id = f"art_{uuid.uuid5(uuid.NAMESPACE_URL, project_id + ':' + relative_path).hex[:16]}"
    conn.execute(
        """
        INSERT INTO artifacts(id, project_id, run_id, path, type, size, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_id, path) DO UPDATE SET
            run_id = excluded.run_id,
            type = excluded.type,
            size = excluded.size,
            updated_at = excluded.updated_at
        """,
        (
            artifact_id,
            project_id,
            run_id,
            relative_path,
            artifact_type_for(relative_path),
            size,
            utc_now(),
        ),
    )


def index_workspace_artifacts(conn: sqlite3.Connection, project: sqlite3.Row) -> list[dict[str, Any]]:
    workspace = Path(project["workspace_path"])
    seen: set[str] = set()
    if workspace.exists():
        for path in workspace.rglob("*"):
            if path.is_file():
                relative_path = path.relative_to(workspace).as_posix()
                seen.add(relative_path)
                upsert_artifact(
                    conn,
                    project_id=project["id"],
                    run_id=None,
                    relative_path=relative_path,
                    size=path.stat().st_size,
                )
    existing = conn.execute("SELECT path FROM artifacts WHERE project_id = ?", (project["id"],)).fetchall()
    for row in existing:
        if row["path"] not in seen:
            conn.execute("DELETE FROM artifacts WHERE project_id = ? AND path = ?", (project["id"], row["path"]))
    rows = conn.execute(
        "SELECT * FROM artifacts WHERE project_id = ? ORDER BY path",
        (project["id"],),
    ).fetchall()
    return [row_to_artifact(row) for row in rows]


def normalize_workspace_path(value: str) -> str:
    normalized = str(value or "").replace("\\", "/").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Artifact path is required.")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
        raise HTTPException(status_code=400, detail="Artifact path must be relative to the project workspace.")
    parts = tuple(part for part in normalized.split("/") if part and part != ".")
    if not parts or ".." in parts:
        raise HTTPException(status_code=400, detail="Artifact path must stay inside the project workspace.")
    return "/".join(parts)


_last_event_id: dict[str, int] = {}
_run_updated_at: dict[str, float] = {}


def _touch_run(run_id: str) -> None:
    _run_updated_at[run_id] = time.time()


def insert_event(
    conn: sqlite3.Connection,
    run_id: str,
    *,
    stage: str,
    event_type: str,
    severity: str,
    message: str,
    artifacts: list[str] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO run_events(run_id, stage, type, severity, message, artifacts, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, stage, event_type, severity, message, json.dumps(artifacts or [], ensure_ascii=False), utc_now()),
    )
    _touch_run(run_id)


class RuntimeDriver:
    id = "local"

    def start(self, conn: sqlite3.Connection, run: dict[str, Any], project: dict[str, Any]) -> None:
        raise NotImplementedError


_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="studio-driver")

DOMAIN_PHASES: dict[str, list[int]] = {
    "math_modeling": [0, 1, 2, 3, 4, 5, 6],
    "statistics": [0, 1, 2, 3, 4, 5, 6],
    "data_analysis": [0, 2, 4, 6],
    "paper_writing": [0, 1, 3, 4, 5, 6],
    "homework": [0, 1, 2, 3, 6],
    "research": [0, 1, 2, 3, 4, 5, 6],
}

PHASE_LABELS: dict[int, tuple[str, str]] = {
    0: ("problem_intake", "题面建档"),
    1: ("model_strategy", "建模策略"),
    2: ("code_generation", "代码实验"),
    3: ("paper_writing", "论文构建"),
    4: ("contest_review", "竞赛评审"),
    5: ("revision", "修订"),
    6: ("final_verify", "最终验收"),
}


def _langgraph_worker(
    run_id: str,
    workspace_path: str,
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    domain: str = "math_modeling",
) -> None:
    """Execute run_contest_graph_v3 in a background thread and emit granular RunEvents."""
    allowed_phases = DOMAIN_PHASES.get(domain, [0, 1, 2, 3, 4, 5, 6])

    try:
        from .langgraph_runner import run_contest_graph_v3

        s = settings()
        conn = connect()
        try:
            label = PHASE_LABELS.get(0, ("phase_0", "Phase 0"))
            insert_event(
                conn,
                run_id,
                stage=label[0],
                event_type="step_start",
                severity="info",
                message=f"[{domain}] {label[1]} 开始 — 允许阶段: {allowed_phases}",
                artifacts=[],
            )
            conn.commit()
        finally:
            conn.close()

        result = run_contest_graph_v3(
            settings=s,
            source_workspace=Path(workspace_path),
            requested_phase=1,
            provider=provider,
            model=model or None,
            copy_workspace=False,
            run_name=None,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Emit per-phase events with detail
        conn = connect()
        try:
            phase_results = result.get("phase_results") or []
            contest_status = result.get("contest_status", "UNKNOWN")
            completed_phases = result.get("completed_phases") or []

            for entry in phase_results:
                ph = entry.get("phase", -1)
                if ph not in allowed_phases and ph >= 0:
                    continue
                label = PHASE_LABELS.get(ph, (f"phase_{ph}", f"Phase {ph}"))
                strategy = entry.get("strategy", "")
                created_files: list[str] = []
                if isinstance(entry.get("created_files"), list):
                    created_files = entry["created_files"]
                elif isinstance(entry.get("files_written"), list):
                    created_files = entry["files_written"]

                insert_event(
                    conn,
                    run_id,
                    stage=label[0],
                    event_type="step_complete",
                    severity="info",
                    message=f"{label[1]} 完成 ({strategy})" if strategy else f"{label[1]} 完成",
                    artifacts=created_files,
                )

            # Pause on Human Gate
            if "WAITING_FOR_HUMAN" in str(contest_status):
                status = "paused"
                insert_event(
                    conn,
                    run_id,
                    stage="model_strategy",
                    event_type="human_gate_required",
                    severity="warning",
                    message="Phase 1 完成，等待人工审核建模路线。",
                    artifacts=["reports/MODEL_CANDIDATES.md", "reports/MODEL_REVIEW_AI.md", "reports/FIGURE_PLAN.md"],
                )
            elif "FAILED" in str(contest_status):
                status = "canceled"
                insert_event(
                    conn,
                    run_id,
                    stage="runtime",
                    event_type="step_error",
                    severity="error",
                    message=f"LangGraph 运行失败: {result.get('stop_reason', contest_status)}",
                    artifacts=[],
                )
            else:
                status = "completed"
                insert_event(
                    conn,
                    run_id,
                    stage="final_verify",
                    event_type="step_complete",
                    severity="info",
                    message=f"全部阶段完成 (完成 {len(completed_phases)} 个阶段，领域: {domain})",
                    artifacts=[],
                )

            conn.execute("UPDATE runs SET status = ?, updated_at = ? WHERE id = ?", (status, utc_now(), run_id))
            conn.commit()
            _touch_run(run_id)
        finally:
            conn.close()

    except ImportError:
        conn = connect()
        try:
            insert_event(
                conn,
                run_id,
                stage="runtime",
                event_type="step_error",
                severity="error",
                message="LangGraph 未安装，无法执行。请安装 langgraph 包。",
                artifacts=[],
            )
            conn.execute("UPDATE runs SET status = ?, updated_at = ? WHERE id = ?", ("canceled", utc_now(), run_id))
            conn.commit()
            _touch_run(run_id)
        finally:
            conn.close()
    except Exception as exc:
        conn = connect()
        try:
            insert_event(
                conn,
                run_id,
                stage="runtime",
                event_type="step_error",
                severity="error",
                message=f"LangGraph 执行异常: {exc}",
                artifacts=[],
            )
            conn.execute("UPDATE runs SET status = ?, updated_at = ? WHERE id = ?", ("canceled", utc_now(), run_id))
            conn.commit()
            _touch_run(run_id)
        finally:
            conn.close()


class LocalWorkflowDriver(RuntimeDriver):
    id = "local"

    def start(self, conn: sqlite3.Connection, run: dict[str, Any], project: dict[str, Any]) -> None:
        workspace = Path(run["workspace_path"])
        gate_artifacts = ensure_human_gate_artifacts(workspace)
        insert_event(
            conn,
            run["id"],
            stage="intake",
            event_type="run_started",
            severity="info",
            message="本地工作流已创建，等待资料上传与题面建档。",
            artifacts=["PROBLEM_BRIEF.md", "DATA_AUDIT.md"],
        )
        insert_event(
            conn,
            run["id"],
            stage="model_strategy",
            event_type="human_gate_required",
            severity="warning",
            message="已进入建模路线确认点，等待人工审核。",
            artifacts=gate_artifacts,
        )


class LangGraphDriver(LocalWorkflowDriver):
    id = "langgraph"

    def start(self, conn: sqlite3.Connection, run: dict[str, Any], project: dict[str, Any]) -> None:
        insert_event(
            conn,
            run["id"],
            stage="runtime",
            event_type="driver_selected",
            severity="info",
            message="已选择 LangGraphDriver；LangGraph 作为内部运行驱动，不暴露底层 mode 给普通用户。",
            artifacts=[],
        )
        # Emit stub events first (same as local driver), then launch real execution
        super().start(conn, run, project)

        # Read model config for the model_strategy stage
        model_config = load_model_config(conn)
        strategy_stage = next(
            (s for s in model_config["stages"] if s["stage"] == "model_strategy"),
            None,
        )
        provider = strategy_stage["provider"] if strategy_stage else "none"
        model = strategy_stage.get("model", "") if strategy_stage else ""
        temperature = strategy_stage.get("temperature", 0.5) if strategy_stage else 0.5
        max_tokens = strategy_stage.get("max_tokens", 8192) if strategy_stage else 8192

        if provider == "none":
            insert_event(
                conn,
                run["id"],
                stage="runtime",
                event_type="driver_fallback",
                severity="warning",
                message="Provider 为 none，跳过真实 LLM 调用。设定模型配置中的 provider 以启用 LangGraph 执行。",
                artifacts=[],
            )
            return

        _executor.submit(
            _langgraph_worker,
            run["id"],
            run["workspace_path"],
            provider,
            model,
            temperature,
            max_tokens,
            project.get("domain", "math_modeling"),
        )


DRIVERS: dict[str, RuntimeDriver] = {
    "local": LocalWorkflowDriver(),
    "langgraph": LangGraphDriver(),
    "codex": LocalWorkflowDriver(),
    "claude-code": LocalWorkflowDriver(),
    "cloud": LocalWorkflowDriver(),
}


STAGE_DEFAULTS = [
    ("problem_intake", "题面解析模型", 0.2, 4096, 300, 1, 16000, 2),
    ("model_strategy", "建模策略模型", 0.5, 8192, 600, 1, 24000, 3),
    ("code_generation", "代码生成模型", 0.15, 8192, 900, 2, 24000, 1),
    ("debug", "调试模型", 0.05, 8192, 900, 3, 20000, 1),
    ("result_analysis", "结果分析模型", 0.2, 4096, 300, 1, 16000, 1),
    ("paper_writing", "论文写作模型", 0.45, 12000, 900, 1, 32000, 1),
    ("contest_review", "竞赛评审模型", 0.2, 8192, 600, 1, 24000, 3),
    ("final_verify", "最终验收模型", 0.1, 4096, 300, 1, 16000, 1),
]


def default_model_config() -> dict[str, Any]:
    return {
        "preset": "balanced",
        "providers": [
            {"id": "none", "label": "安全预演", "enabled": True, "api_key_status": "not_required"},
            {"id": "deepseek", "label": "DeepSeek", "enabled": True, "api_key_status": "unknown"},
            {"id": "openai-compatible", "label": "OpenAI-compatible", "enabled": True, "api_key_status": "unknown"},
            {"id": "claude", "label": "Claude", "enabled": False, "api_key_status": "unknown"},
            {"id": "codex", "label": "Codex", "enabled": False, "api_key_status": "external"},
        ],
        "stages": [
            {
                "stage": stage,
                "label": label,
                "provider": "none",
                "model": "",
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout_sec": timeout_sec,
                "retry_count": retry_count,
                "context_budget": context_budget,
                "parallel_agents": parallel_agents,
            }
            for stage, label, temperature, max_tokens, timeout_sec, retry_count, context_budget, parallel_agents in STAGE_DEFAULTS
        ],
    }


def merge_model_config(payload: dict[str, Any]) -> dict[str, Any]:
    current = default_model_config()
    if payload.get("preset"):
        current["preset"] = payload["preset"]
    if isinstance(payload.get("providers"), list):
        current["providers"] = payload["providers"]
    stage_map = {stage["stage"]: stage for stage in current["stages"]}
    for item in payload.get("stages") or []:
        stage = item.get("stage")
        if stage not in stage_map:
            continue
        stage_map[stage].update({k: v for k, v in item.items() if k in stage_map[stage]})
    current["stages"] = list(stage_map.values())
    return current


def load_model_config(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT value FROM studio_config WHERE key = 'model_config'").fetchone()
    if not row:
        return default_model_config()
    try:
        return merge_model_config(json.loads(row["value"]))
    except (json.JSONDecodeError, TypeError):
        return default_model_config()


def save_model_config(conn: sqlite3.Connection, config: dict[str, Any]) -> dict[str, Any]:
    merged = merge_model_config(config)
    conn.execute(
        """
        INSERT INTO studio_config(key, value, updated_at)
        VALUES ('model_config', ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """,
        (json.dumps(merged, ensure_ascii=False), utc_now()),
    )
    conn.commit()
    return merged


@router.post("/api/projects")
def create_project(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or "Untitled Project")
    domain = str(payload.get("domain") or "math_modeling")
    contest = str(payload.get("contest") or "")
    project_id = f"proj_{uuid.uuid4().hex[:12]}"
    now = utc_now()
    workspace = project_workspace(project_id, name)
    ensure_v2_workspace_skeleton(workspace, name, contest)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO projects(id, name, domain, contest, workspace_path, template_id, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, name, domain, contest, str(workspace), payload.get("template_id"), "active", now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return row_to_project(row)


@router.get("/api/projects")
def list_projects() -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
    return {"projects": [row_to_project(row) for row in rows]}


@router.post("/api/projects/{project_id}/files")
async def upload_project_files(project_id: str, files: list[UploadFile] = File(...)) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found.")
    source = Path(row["workspace_path"]) / "source"
    source.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for file in files:
        safe_name = slugify(Path(file.filename or "upload.bin").stem, "upload") + Path(file.filename or "").suffix
        target = source / safe_name
        target.write_bytes(await file.read())
        relative_path = f"source/{safe_name}"
        saved.append(relative_path)
    with connect() as conn:
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        for relative_path in saved:
            target = Path(project["workspace_path"]) / relative_path
            upsert_artifact(
                conn,
                project_id=project_id,
                run_id=None,
                relative_path=relative_path,
                size=target.stat().st_size,
            )
        conn.commit()
    return {"saved": saved, "skipped": []}


@router.get("/api/projects/{project_id}/files")
def list_project_files(project_id: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found.")
    with connect() as conn:
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        files = index_workspace_artifacts(conn, project)
        conn.commit()
    return {"files": files}


@router.get("/api/projects/{project_id}/artifacts/read")
def read_project_artifact(project_id: str, path: str = Query(...)) -> dict[str, Any]:
    relative_path = normalize_workspace_path(path)
    with connect() as conn:
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")
        workspace = Path(project["workspace_path"]).resolve()
        target = (workspace / relative_path).resolve()
        if not target.is_relative_to(workspace):
            raise HTTPException(status_code=400, detail="Artifact path must stay inside the project workspace.")
        if not target.is_file():
            raise HTTPException(status_code=404, detail="Artifact not found.")
        size = target.stat().st_size
        upsert_artifact(conn, project_id=project_id, run_id=None, relative_path=relative_path, size=size)
        conn.commit()
    max_preview_bytes = 512 * 1024
    raw = target.read_bytes()[:max_preview_bytes]
    return {
        "path": relative_path,
        "type": artifact_type_for(relative_path),
        "size": size,
        "truncated": size > max_preview_bytes,
        "content": raw.decode("utf-8", errors="replace"),
    }


QUALITY_ARTIFACTS = [
    ("HUMAN_MODEL_REVIEW", "reports/HUMAN_MODEL_REVIEW.md"),
    ("CLAIM_TRACE", "reports/CLAIM_TRACE.md"),
    ("METHOD_IMPLEMENTATION_MATRIX", "reports/METHOD_IMPLEMENTATION_MATRIX.md"),
    ("FIGURE_AUDIT", "reports/FIGURE_AUDIT.md"),
    ("PAPER_SCORECARD", "reports/PAPER_SCORECARD.md"),
    ("REVISION_ACTIONS", "reports/REVISION_ACTIONS.md"),
    ("VERIFY_REPORT", "reports/VERIFY_REPORT.md"),
]


@router.get("/api/projects/{project_id}/quality")
def get_project_quality(project_id: str) -> dict[str, Any]:
    with connect() as conn:
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    workspace = Path(project["workspace_path"])
    items = []
    for key, relative_path in QUALITY_ARTIFACTS:
        target = workspace / relative_path
        status = "missing"
        preview = ""
        if target.is_file():
            status = "present"
            try:
                preview = target.read_text(encoding="utf-8", errors="replace")[:2048]
            except Exception:
                preview = "(binary or unreadable)"
        # Check for PASS/FAIL indicators
        if "PASS" in preview.upper() and "FAIL" not in preview.upper():
            status = "pass"
        elif "FAIL" in preview.upper() or "BLOCKER" in preview:
            status = "fail"
        items.append({"id": key, "path": relative_path, "status": status, "preview": preview})
    return {"project_id": project_id, "items": items}


@router.post("/api/runs")
def create_run(payload: dict[str, Any]) -> dict[str, Any]:
    project_id = str(payload.get("project_id") or "")
    driver_id = str(payload.get("driver") or "local")
    with connect() as conn:
        project_row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not project_row:
            raise HTTPException(status_code=404, detail="Project not found.")
        if driver_id not in DRIVERS:
            raise HTTPException(status_code=400, detail=f"Unsupported driver: {driver_id}")
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        now = utc_now()
        workspace = Path(project_row["workspace_path"])
        artifact_paths = ensure_human_gate_artifacts(workspace)
        conn.execute(
            """
            INSERT INTO runs(id, project_id, driver, status, current_stage, workspace_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, project_id, driver_id, "paused", "model_strategy", project_row["workspace_path"], now, now),
        )
        conn.execute(
            """
            INSERT INTO gates(id, run_id, type, status, title, artifacts, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"gate_{uuid.uuid4().hex[:10]}",
                run_id,
                "human_model_review",
                "required",
                "模型路线确认",
                json.dumps(artifact_paths, ensure_ascii=False),
                now,
                now,
            ),
        )
        run_row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        DRIVERS[driver_id].start(conn, row_to_run(run_row), row_to_project(project_row))
        conn.commit()
        run_row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    return row_to_run(run_row)


@router.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Run not found.")
    return row_to_run(row)


@router.post("/api/runs/{run_id}/resume")
def resume_run(run_id: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Run not found.")
        now = utc_now()
        conn.execute("UPDATE runs SET status = ?, updated_at = ? WHERE id = ?", ("running", now, run_id))
        insert_event(conn, run_id, stage=row["current_stage"], event_type="run_resumed", severity="info", message="运行已继续。")
        conn.commit()
        updated = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    return row_to_run(updated)


@router.post("/api/runs/{run_id}/cancel")
def cancel_run(run_id: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Run not found.")
        now = utc_now()
        conn.execute("UPDATE runs SET status = ?, updated_at = ? WHERE id = ?", ("canceled", now, run_id))
        insert_event(conn, run_id, stage=row["current_stage"], event_type="run_canceled", severity="warning", message="运行已取消。")
        conn.commit()
        updated = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    return row_to_run(updated)


@router.get("/api/runs/{run_id}/events")
def list_run_events(run_id: str) -> dict[str, Any]:
    with connect() as conn:
        run = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found.")
        rows = conn.execute("SELECT * FROM run_events WHERE run_id = ? ORDER BY id", (run_id,)).fetchall()
    return {"events": [row_to_event(row) for row in rows]}


def _new_events_since(conn: sqlite3.Connection, run_id: str, since_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM run_events WHERE run_id = ? AND id > ? ORDER BY id",
        (run_id, since_id),
    ).fetchall()
    return [row_to_event(row) for row in rows]


@router.get("/api/runs/{run_id}/events/stream")
async def stream_run_events(run_id: str, request: Request, replay_only: bool = Query(False)) -> StreamingResponse:
    with connect() as conn:
        run = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found.")
        rows = conn.execute("SELECT * FROM run_events WHERE run_id = ? ORDER BY id", (run_id,)).fetchall()
    events = [row_to_event(row) for row in rows]
    last_sent_id = events[-1]["id"] if events else 0
    last_known_ts = _run_updated_at.get(run_id, 0)

    async def event_stream():
        nonlocal last_sent_id, last_known_ts
        for event in events:
            if await request.is_disconnected():
                return
            yield f"event: run_event\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield f"event: ready\ndata: {json.dumps({'run_id': run_id, 'event_count': len(events)}, ensure_ascii=False)}\n\n"

        if replay_only:
            return

        await asyncio.sleep(0)
        heartbeat_interval = 15
        last_heartbeat = time.time()
        poll_start = time.time()
        max_poll_sec = 300
        while True:
            if await request.is_disconnected():
                return
            if time.time() - poll_start > max_poll_sec:
                yield f"event: timeout\ndata: {json.dumps({'run_id': run_id, 'message': 'stream timeout'}, ensure_ascii=False)}\n\n"
                return

            current_ts = _run_updated_at.get(run_id, 0)
            if current_ts > last_known_ts:
                last_known_ts = current_ts
                with connect() as conn:
                    new_events = _new_events_since(conn, run_id, last_sent_id)
                for event in new_events:
                    if await request.is_disconnected():
                        return
                    last_sent_id = event["id"]
                    yield f"event: run_event\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"

            with connect() as conn:
                r = conn.execute("SELECT status FROM runs WHERE id = ?", (run_id,)).fetchone()
            if r and r["status"] in ("completed", "canceled"):
                yield f"event: done\ndata: {json.dumps({'run_id': run_id, 'status': r['status']}, ensure_ascii=False)}\n\n"
                return

            now = time.time()
            if now - last_heartbeat >= heartbeat_interval:
                last_heartbeat = now
                yield f": heartbeat\n\n"

            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/api/gates/{run_id}/current")
def current_gate(run_id: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM gates WHERE run_id = ? AND status = 'required' ORDER BY created_at LIMIT 1",
            (run_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No required gate for this run.")
        run = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found.")
        workspace = Path(run["workspace_path"])
        return row_to_gate_with_previews(row, workspace)


@router.post("/api/gates/{run_id}/{gate_id}/submit")
def submit_gate(run_id: str, gate_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    with connect() as conn:
        run = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        gate = conn.execute("SELECT * FROM gates WHERE id = ? AND run_id = ?", (gate_id, run_id)).fetchone()
        if not run or not gate:
            raise HTTPException(status_code=404, detail="Gate not found.")
        workspace = Path(run["workspace_path"])
        reports = workspace / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        decision = str(payload.get("decision") or "needs_revision")
        selected_route = str(payload.get("selected_route") or "")
        human_notes = str(payload.get("human_notes") or "")
        ai_notes = str(payload.get("ai_notes") or "")
        review_text = "\n".join(
            [
                "# Human Model Review",
                "",
                "## Decision",
                decision,
                "",
                "## Selected Route",
                selected_route or "待确认",
                "",
                "## Human Notes",
                human_notes,
                "",
                "## AI Notes",
                ai_notes,
                "",
            ]
        )
        decision_text = "\n".join(
            [
                "# Modeling Decision",
                "",
                f"- decision: {decision}",
                f"- selected_route: {selected_route or '待确认'}",
                "",
                "## Notes",
                human_notes,
                "",
            ]
        )
        (reports / "HUMAN_MODEL_REVIEW.md").write_text(review_text, encoding="utf-8")
        (reports / "MODELING_DECISION.md").write_text(decision_text, encoding="utf-8")
        now = utc_now()
        gate_status = "approved" if decision == "approved" else "submitted"
        conn.execute("UPDATE gates SET status = ?, updated_at = ? WHERE id = ?", (gate_status, now, gate_id))
        conn.execute("UPDATE runs SET status = ?, updated_at = ? WHERE id = ?", ("running" if decision == "approved" else "paused", now, run_id))
        insert_event(
            conn,
            run_id,
            stage="model_strategy",
            event_type="human_gate_submitted",
            severity="info" if decision == "approved" else "warning",
            message=f"人工闸门已提交：{decision}",
            artifacts=["reports/HUMAN_MODEL_REVIEW.md", "reports/MODELING_DECISION.md"],
        )
        conn.commit()
    return {"ok": True, "decision": decision, "approved": decision == "approved"}


@router.get("/api/models/config")
def get_model_config() -> dict[str, Any]:
    with connect() as conn:
        return load_model_config(conn)


@router.put("/api/models/config")
def put_model_config(payload: dict[str, Any]) -> dict[str, Any]:
    with connect() as conn:
        return save_model_config(conn, payload)


PROVIDER_ENDPOINTS: dict[str, str] = {
    "deepseek": "https://api.deepseek.com/v1/models",
    "openai-compatible": "",
    "claude": "https://api.anthropic.com/v1/models",
}


@router.post("/api/models/test-connection")
def test_model_connection(payload: dict[str, Any]) -> dict[str, Any]:
    provider = str(payload.get("provider") or "none")
    if provider == "none":
        return {"ok": True, "provider": provider, "message": "安全预演不需要 API Key。", "latency_ms": 0}

    endpoint = PROVIDER_ENDPOINTS.get(provider)
    if not endpoint and provider != "openai-compatible":
        return {"ok": False, "provider": provider, "message": f"未知 provider: {provider}", "latency_ms": 0}

    # For openai-compatible, try the base URL from config
    if provider == "openai-compatible":
        base_url = str(payload.get("base_url") or "")
        if not base_url:
            return {"ok": False, "provider": provider, "message": "OpenAI-compatible 需要提供 base_url。", "latency_ms": 0}
        endpoint = base_url.rstrip("/") + "/v1/models"
    else:
        endpoint = PROVIDER_ENDPOINTS[provider]

    key_name = "MATHMODEL_LLM_API_KEY"
    api_key = os.environ.get(key_name)
    if not api_key:
        return {"ok": False, "provider": provider, "message": f"{key_name} 未设置。", "latency_ms": 0}

    try:
        ctx = ssl.create_default_context()
        start = time.perf_counter()
        req = Request(endpoint)
        if provider == "claude":
            req.add_header("x-api-key", api_key)
            req.add_header("anthropic-version", "2023-06-01")
        else:
            req.add_header("Authorization", f"Bearer {api_key}")
        with urlopen(req, timeout=10, context=ctx) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            elapsed_ms = round((time.perf_counter() - start) * 1000)
        data = json.loads(body)
        models = []
        if isinstance(data.get("data"), list):
            models = [item.get("id", "") for item in data["data"][:10]]
        return {
            "ok": True,
            "provider": provider,
            "message": f"连接成功，{len(models)} 个模型可用",
            "latency_ms": elapsed_ms,
            "models": models,
        }
    except URLError as exc:
        return {"ok": False, "provider": provider, "message": f"连接失败: {exc.reason}", "latency_ms": 0}
    except Exception as exc:
        return {"ok": False, "provider": provider, "message": f"连接失败: {exc}", "latency_ms": 0}


@router.get("/api/dev/diagnostics")
def dev_diagnostics() -> dict[str, Any]:
    """Developer-mode diagnostics endpoint."""
    s = settings()
    info: dict[str, Any] = {
        "mathmodel_root": str(s.mathmodel_root),
        "workspace_root": str(s.workspace_root),
        "db_path": str(db_path()),
        "template_root": str(template_root()),
        "python": s.python_executable,
    }

    try:
        from .langgraph_runner import _LANGGRAPH_IMPORT_ERROR, SUPPORTED_MODES

        info["langgraph"] = {
            "available": _LANGGRAPH_IMPORT_ERROR is None,
            "error": _LANGGRAPH_IMPORT_ERROR,
            "supported_modes": sorted(SUPPORTED_MODES),
        }
    except ImportError:
        info["langgraph"] = {"available": False, "error": "langgraph_runner import failed"}

    prompts_dir = s.mathmodel_root / "skills" / "_references"
    info["prompt_templates"] = (
        [p.name for p in sorted(prompts_dir.glob("*.md"))] if prompts_dir.is_dir() else []
    )

    return info


@router.post("/api/chat")
async def studio_chat(payload: dict[str, Any]) -> StreamingResponse:
    """General AI chat with workspace context, returns SSE stream."""
    message = str(payload.get("message") or "")
    ctx = payload.get("context") or {}

    if not message.strip():
        raise HTTPException(status_code=400, detail="Message is required.")

    # Build system prompt from context
    system_parts = ["你是一位数学建模、统计分析和科研写作的 AI 助手。"]
    if ctx.get("projectName"):
        system_parts.append(f"当前项目: {ctx['projectName']}")
    if ctx.get("domain"):
        system_parts.append(f"领域: {ctx['domain']}")
    if ctx.get("runStage"):
        system_parts.append(f"当前阶段: {ctx['runStage']}")
    system_prompt = "\n".join(system_parts)

    # Read model config
    with connect() as conn:
        config = load_model_config(conn)
    strategy_stage = next((s for s in config["stages"] if s["stage"] == "model_strategy"), None)
    provider = strategy_stage["provider"] if strategy_stage else "none"
    model = strategy_stage.get("model", "") if strategy_stage else ""
    temperature = strategy_stage.get("temperature", 0.5) if strategy_stage else 0.5
    max_tokens = strategy_stage.get("max_tokens", 4096) if strategy_stage else 4096

    if provider == "none":
        async def no_provider_stream():
            yield f"data: {json.dumps({'content': '[安全预演模式] Provider 为 none，无法发送聊天请求。请在模型设置中配置 provider。', 'done': True}, ensure_ascii=False)}\n\n"
        return StreamingResponse(no_provider_stream(), media_type="text/event-stream")

    api_key = os.environ.get("MATHMODEL_LLM_API_KEY")
    if not api_key:
        async def no_key_stream():
            yield f"data: {json.dumps({'content': 'MATHMODEL_LLM_API_KEY 未设置。', 'done': True}, ensure_ascii=False)}\n\n"
        return StreamingResponse(no_key_stream(), media_type="text/event-stream")

    async def chat_stream():
        try:
            from .model_adapters import get_model_adapter
            adapter = get_model_adapter(provider)
            full_prompt = f"{system_prompt}\n\n用户: {message}\n\n助手:"
            accumulated = ""
            async for chunk in adapter.stream_chat(
                model=model or None,
                prompt=full_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
            ):
                accumulated += chunk
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
        except ImportError:
            yield f"data: {json.dumps({'content': 'model_adapters 未安装或 provider 不支持流式聊天。', 'done': True}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'content': f'聊天出错: {exc}', 'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(chat_stream(), media_type="text/event-stream")


def safe_zip_members(archive: zipfile.ZipFile) -> list[str]:
    names = []
    for info in archive.infolist():
        name = normalize_template_path(info.filename, field="zip member")
        if not name.endswith("/"):
            names.append(name)
    return names


def normalize_template_path(value: str, field: str) -> str:
    name = str(value).replace("\\", "/").strip()
    if not name:
        raise HTTPException(status_code=400, detail=f"Template metadata contains unsafe {field}.")
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        raise HTTPException(status_code=400, detail=f"Template metadata contains unsafe {field}.")
    parts = tuple(part for part in name.split("/") if part and part != ".")
    if not parts or ".." in parts:
        raise HTTPException(status_code=400, detail=f"Template metadata contains unsafe {field}.")
    return "/".join(parts) + ("/" if name.endswith("/") else "")


def assert_no_traversal(value: str, field: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return raw
    normalized = raw.replace("\\", "/")
    parts = tuple(part for part in normalized.split("/") if part and part != ".")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized) or ".." in parts:
        raise HTTPException(status_code=400, detail=f"Template metadata contains unsafe {field}.")
    return raw


def template_metadata_from_zip(archive: zipfile.ZipFile, names: list[str]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if "template.json" in names:
        try:
            metadata = json.loads(archive.read("template.json").decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise HTTPException(status_code=400, detail="template.json is invalid.") from exc
    main_file = metadata.get("main_file")
    if not main_file:
        if "main.tex" in names:
            main_file = "main.tex"
        elif "main.typ" in names:
            main_file = "main.typ"
    else:
        main_file = normalize_template_path(str(main_file), field="main_file")
    if not main_file or main_file not in names:
        raise HTTPException(status_code=400, detail="Template ZIP must contain main.tex or main.typ.")
    if Path(main_file).name not in {"main.tex", "main.typ"}:
        raise HTTPException(status_code=400, detail="Template ZIP must contain main.tex or main.typ.")
    template_id = slugify(assert_no_traversal(str(metadata.get("id") or Path(main_file).stem), "id"), "template")
    contest = slugify(assert_no_traversal(str(metadata.get("contest") or "default"), "contest"), "default")
    required_raw = metadata.get("required_files") or [main_file]
    if not isinstance(required_raw, list):
        raise HTTPException(status_code=400, detail="template.json required_files must be a list.")
    required = [normalize_template_path(str(item), field="required_files") for item in required_raw]
    preview_file = ""
    if metadata.get("preview_file"):
        preview_file = normalize_template_path(str(metadata["preview_file"]), field="preview_file")
    warnings = [f"missing required file: {item}" for item in required if item not in names]
    if preview_file and preview_file not in names:
        warnings.append(f"missing preview file: {preview_file}")
    if Path(main_file).suffix.lower() == ".tex" and not any(name.endswith((".cls", ".sty")) for name in names):
        warnings.append("LaTeX template has no cls/sty file.")
    return {
        "id": template_id,
        "name": str(metadata.get("name") or template_id),
        "contest": contest,
        "language": str(metadata.get("language") or "zh"),
        "engine": str(metadata.get("engine") or ("latex" if main_file.endswith(".tex") else "typst")),
        "main_file": main_file,
        "description": str(metadata.get("description") or ""),
        "required_files": required,
        "preview_file": preview_file,
        "warnings": warnings,
    }


def extract_template_zip(archive: zipfile.ZipFile, root: Path) -> None:
    resolved_root = root.resolve()
    for info in archive.infolist():
        name = normalize_template_path(info.filename, field="zip member")
        if name.endswith("/"):
            continue
        target = (resolved_root / name).resolve()
        if not target.is_relative_to(resolved_root):
            raise HTTPException(status_code=400, detail="Template ZIP contains unsafe paths.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(info) as source, target.open("wb") as destination:
            shutil.copyfileobj(source, destination)


def save_template_pack(conn: sqlite3.Connection, metadata: dict[str, Any], root: Path) -> sqlite3.Row:
    now = utc_now()
    conn.execute(
        """
        INSERT INTO template_packs(
            id, name, contest, language, engine, main_file, description,
            required_files, preview_file, root_path, warnings, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            contest = excluded.contest,
            language = excluded.language,
            engine = excluded.engine,
            main_file = excluded.main_file,
            description = excluded.description,
            required_files = excluded.required_files,
            preview_file = excluded.preview_file,
            root_path = excluded.root_path,
            warnings = excluded.warnings,
            updated_at = excluded.updated_at
        """,
        (
            metadata["id"],
            metadata["name"],
            metadata["contest"],
            metadata["language"],
            metadata["engine"],
            metadata["main_file"],
            metadata["description"],
            json.dumps(metadata["required_files"], ensure_ascii=False),
            metadata["preview_file"],
            str(root),
            json.dumps(metadata["warnings"], ensure_ascii=False),
            now,
            now,
        ),
    )
    return conn.execute("SELECT * FROM template_packs WHERE id = ?", (metadata["id"],)).fetchone()


def builtin_template_metadata(language: str, pack_dir: Path) -> dict[str, Any] | None:
    main_tex = pack_dir / "main.tex"
    main_typ = pack_dir / "main.typ"
    if main_tex.is_file():
        main_file = "main.tex"
        engine = "latex"
    elif main_typ.is_file():
        main_file = "main.typ"
        engine = "typst"
    else:
        return None
    contest = slugify(pack_dir.name.removesuffix("-latex"), "default")
    template_id = slugify(f"{language}-{pack_dir.name}", "template")
    required_files = sorted(
        path.name
        for path in pack_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".tex", ".typ", ".cls", ".sty", ".bib"}
    )
    if main_file not in required_files:
        required_files.insert(0, main_file)
    warnings: list[str] = []
    if engine == "latex" and not any((pack_dir / name).suffix.lower() in {".cls", ".sty"} for name in required_files):
        warnings.append("LaTeX template has no cls/sty file.")
    return {
        "id": template_id,
        "name": f"{language.upper()} {pack_dir.name}",
        "contest": contest,
        "language": language,
        "engine": engine,
        "main_file": main_file,
        "description": f"Built-in template imported from skills/5writing/templates/{language}/{pack_dir.name}.",
        "required_files": required_files,
        "preview_file": "",
        "warnings": warnings,
    }


@router.get("/api/templates")
def list_templates() -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM template_packs ORDER BY contest, name").fetchall()
    return {"templates": [row_to_template(row) for row in rows]}


@router.post("/api/templates/upload")
async def upload_template(file: UploadFile = File(...)) -> dict[str, Any]:
    raw = await file.read()
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Template upload must be a ZIP file.") from exc
    with archive:
        names = safe_zip_members(archive)
        metadata = template_metadata_from_zip(archive, names)
        base_root = template_root().resolve()
        root = (base_root / metadata["contest"] / metadata["id"]).resolve()
        if not root.is_relative_to(base_root):
            raise HTTPException(status_code=400, detail="Template metadata contains unsafe root path.")
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True, exist_ok=True)
        extract_template_zip(archive, root)
    with connect() as conn:
        row = save_template_pack(conn, metadata, root)
        conn.commit()
    return row_to_template(row)


@router.post("/api/templates/import-builtin")
def import_builtin_templates() -> dict[str, Any]:
    source_root = settings().mathmodel_root / "skills" / "5writing" / "templates"
    if not source_root.is_dir():
        raise HTTPException(status_code=404, detail="Built-in template source directory not found.")
    base_root = template_root().resolve()
    imported: list[dict[str, Any]] = []
    with connect() as conn:
        for language_dir in sorted(path for path in source_root.iterdir() if path.is_dir()):
            language = slugify(language_dir.name, "unknown")
            for pack_dir in sorted(path for path in language_dir.iterdir() if path.is_dir()):
                metadata = builtin_template_metadata(language, pack_dir)
                if metadata is None:
                    continue
                root = (base_root / metadata["contest"] / metadata["id"]).resolve()
                if not root.is_relative_to(base_root):
                    raise HTTPException(status_code=400, detail="Built-in template target is unsafe.")
                if root.exists():
                    shutil.rmtree(root)
                shutil.copytree(pack_dir, root)
                row = save_template_pack(conn, metadata, root)
                imported.append(row_to_template(row))
        conn.commit()
    return {"imported_count": len(imported), "templates": imported}


def get_template_row(template_id: str) -> sqlite3.Row:
    with connect() as conn:
        row = conn.execute("SELECT * FROM template_packs WHERE id = ?", (template_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Template not found.")
    return row


@router.get("/api/templates/{template_id}/preview")
def preview_template(template_id: str) -> dict[str, Any]:
    row = get_template_row(template_id)
    root = Path(row["root_path"])
    preview = row["preview_file"]
    target = root / preview if preview else root / row["main_file"]
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Template preview file not found.")
    if target.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"}:
        return {"id": template_id, "type": target.suffix.lower().lstrip("."), "path": str(target), "content": None}
    return {"id": template_id, "type": "text", "path": str(target), "content": target.read_text(encoding="utf-8", errors="replace")}


@router.get("/api/templates/{template_id}/download")
def download_template(template_id: str) -> Response:
    row = get_template_row(template_id)
    root = Path(row["root_path"])
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in root.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(root).as_posix())
    payload.seek(0)
    return Response(
        content=payload.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{template_id}.zip"'},
    )


@router.delete("/api/templates/{template_id}")
def delete_template(template_id: str) -> dict[str, Any]:
    row = get_template_row(template_id)
    root = Path(row["root_path"])
    if root.exists():
        shutil.rmtree(root)
    with connect() as conn:
        conn.execute("DELETE FROM template_packs WHERE id = ?", (template_id,))
        conn.commit()
    return {"ok": True, "id": template_id}
