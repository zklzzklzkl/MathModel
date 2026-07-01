from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ScriptStatus(BaseModel):
    path: str
    exists: bool


class HealthResponse(BaseModel):
    ok: bool
    python: str
    mathmodel_root: str
    workspace_root: str
    examples_root: str
    scripts: dict[str, ScriptStatus]


class WorkspaceItem(BaseModel):
    id: str
    name: str
    path: str
    source: Literal["workspace_root", "examples", "other"]
    updated_at: str | None = None
    has_v2_shape: bool = False


class CreateWorkspaceRequest(BaseModel):
    path: str | None = None
    name: str | None = None
    contest: str = "待确认"
    engine: str = "LaTeX"
    language: str = "中文"
    subproblems: str = "待确认"
    figure_backend: str = "待确认"
    nature: Literal["enabled", "unavailable", "not_requested"] = "not_requested"
    force: bool = False


class CreateWorkspaceResponse(BaseModel):
    workspace: WorkspaceItem
    created: list[str]
    skipped: list[str]
    stdout: str
    stderr: str


class ArtifactItem(BaseModel):
    path: str
    exists: bool
    type: str
    size: int | None = None
    updated_at: str | None = None
    required: bool = False


class ArtifactReadResponse(BaseModel):
    path: str
    exists: bool
    type: str
    content: str | None = None
    data: Any | None = None
    absolute_path: str | None = None


class PhaseSummary(BaseModel):
    id: int
    name: str
    skill: str
    gate: str
    status: str
    status_class: str
    artifacts: list[str]
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    missing_outputs: list[str] = Field(default_factory=list)
    ready: bool = False
    next_action: str = ""


class Recommendation(BaseModel):
    severity: str
    title: str
    detail: str
    phase: int | None = None
    artifact: str | None = None


class WorkspaceSummary(BaseModel):
    workspace: WorkspaceItem
    status: str
    worst_severity: str
    phases: list[PhaseSummary]
    required_missing: list[str]
    manifest: dict[str, Any]
    paper: dict[str, Any]
    issues: list[dict[str, Any]]
    recommendations: list[Recommendation] = Field(default_factory=list)


class AuditResponse(BaseModel):
    result: dict[str, Any]
    stdout: str
    stderr: str
    returncode: int


class BenchmarkResponse(BaseModel):
    results: list[dict[str, Any]]
    stdout: str
    stderr: str
    returncode: int


class PromptRequest(BaseModel):
    phase: int = Field(ge=0, le=6)
    harness: Literal["Manual", "Codex", "Claude Code", "OpenCode"] = "Manual"


class PromptResponse(BaseModel):
    phase: int
    harness: str
    prompt: str


class CopyRunRequest(BaseModel):
    name: str | None = None


class CopyRunResponse(BaseModel):
    source: str
    destination: str
    workspace: WorkspaceItem


class RunHistoryEntry(BaseModel):
    timestamp: str
    event: str
    phase: int | None = None
    harness: str | None = None
    status_before: str | None = None
    status_after: str | None = None
    source_workspace: str | None = None
    run_workspace: str | None = None
    prompt_path: str | None = None
    note: str | None = None


class RevisionTask(BaseModel):
    id: str
    severity: str
    phase: int
    artifact: str
    issue_code: str
    title: str
    action: str


class RevisionTasksResponse(BaseModel):
    tasks: list[RevisionTask]
    written_path: str | None = None


class SourceUploadResponse(BaseModel):
    saved: list[str]
    skipped: list[str]


class HarnessInfo(BaseModel):
    id: Literal["Manual", "Codex", "Claude Code", "OpenCode"]
    label: str
    managed: bool
    available: bool
    note: str


class PrepareHarnessRequest(BaseModel):
    phase: int = Field(ge=0, le=6)
    harness: Literal["Manual", "Codex", "Claude Code", "OpenCode"] = "Manual"
    copy_workspace: bool = True
    run_name: str | None = None


class PrepareHarnessResponse(BaseModel):
    harness: str
    phase: int
    source_workspace: str
    run_workspace: str
    copied: bool
    prompt: str
    prompt_path: str | None = None
    command_preview: str
    history: RunHistoryEntry
