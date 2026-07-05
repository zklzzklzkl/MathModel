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
    archived: bool = False


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


class WorkspaceActionResponse(BaseModel):
    ok: bool
    action: str
    source: str
    destination: str | None = None
    workspace: WorkspaceItem | None = None
    message: str


class RunDeleteRequest(BaseModel):
    permanent: bool = False
    confirm_name: str | None = None


class RunDeleteResponse(BaseModel):
    ok: bool
    action: str
    run_id: str
    run_name: str
    source: str
    destination: str | None = None
    message: str


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


class ActivityMessage(BaseModel):
    id: str
    kind: str
    title: str
    body: str
    severity: str = "INFO"
    phase: int | None = None
    status: str | None = None
    artifacts: list[str] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: str | None = None


class WorkspaceActivityResponse(BaseModel):
    workspace: WorkspaceItem
    summary_status: str
    worst_severity: str
    primary_blocker: dict[str, Any] | None = None
    recommended_action: dict[str, Any]
    messages: list[ActivityMessage]


class HumanGateSummaryResponse(BaseModel):
    workspace: WorkspaceItem
    gate_file: str
    exists: bool
    approved: bool
    approval_signal: str | None = None
    summary: str
    model_candidates_excerpt: str = ""
    model_review_excerpt: str = ""
    figure_plan_excerpt: str = ""
    risks: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)


class HumanGateChatRequest(BaseModel):
    question: str
    context: str | None = None


class HumanGateChatResponse(BaseModel):
    answer: str
    suggested_review_note: str
    follow_up_questions: list[str] = Field(default_factory=list)


class HumanGateReviewRequest(BaseModel):
    decision: Literal["approved", "needs_revision", "rejected"]
    human_notes: str
    ai_notes: str | None = None


class HumanGateReviewResponse(BaseModel):
    ok: bool
    decision: str
    written_path: str
    approved: bool
    history: dict[str, Any]


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


class LangGraphStatusResponse(BaseModel):
    available: bool
    version: str | None = None
    import_error: str | None = None
    note: str


class LangGraphRunRequest(BaseModel):
    phase: int = Field(ge=0, le=6)
    mode: Literal[
        "dry_run",
        "llm_plan",
        "controlled_apply",
        "phase_execute",
        "contest_graph_v0",
        "contest_graph_v1",
        "contest_graph_v2",
        "contest_graph_v3",
    ] = "dry_run"
    provider: str = "none"
    model: str | None = None
    copy_workspace: bool = True
    run_name: str | None = None
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=512, le=32768)


class LangGraphRunResponse(BaseModel):
    available: bool
    source_workspace: str
    run_workspace: str
    phase: int
    mode: str
    provider: str
    model: str | None = None
    status: str
    prompt_path: str | None = None
    report_path: str | None = None
    pre_audit: dict[str, Any]
    post_audit: dict[str, Any]
    issues: list[dict[str, Any]]
    history: dict[str, Any] | None = None
    phase_plan: dict[str, Any] | None = None
    provider_error: str | None = None
    plan_path: str | None = None
    plan_markdown_path: str | None = None
    raw_output_path: str | None = None
    json_preprocess_report_path: str | None = None
    apply_diff_path: str | None = None
    files_planned: list[str] = Field(default_factory=list)
    files_written: list[str] = Field(default_factory=list)
    files_rejected: list[Any] = Field(default_factory=list)
    needs_human: bool = False
    contest_status: str | None = None
    completed_phases: list[int] = Field(default_factory=list)
    paused_at: str | None = None
    human_gate_required: bool = False
    human_gate_file: str | None = None
    graph_report_path: str | None = None
    phase_results: list[dict[str, Any]] = Field(default_factory=list)
    final_audit: dict[str, Any] = Field(default_factory=dict)
    sandbox_commands: list[dict[str, Any]] = Field(default_factory=list)
    sandbox_status: str | None = None
    manifest_created_empty: bool = False
    paper_sandbox_status: str | None = None
    paper_files_written: list[str] = Field(default_factory=list)
    claim_trace_path: str | None = None
    method_matrix_path: str | None = None
    paper_build_report_path: str | None = None
    revision_sandbox_status: str | None = None
    revision_files_written: list[str] = Field(default_factory=list)
    revision_status_path: str | None = None


# ---------------------------------------------------------------------------
# Benchmark Report Browser models
# ---------------------------------------------------------------------------

class BenchmarkReportItem(BaseModel):
    id: str
    title: str
    path: str
    type: Literal["markdown", "json"]
    category: str
    provider: str | None = None
    mode: str | None = None
    workspace: str | None = None
    updated_at: str | None = None
    size: int | None = None


class BenchmarkReportReadResponse(BaseModel):
    id: str
    title: str
    path: str
    type: Literal["markdown", "json"]
    category: str
    content: str
    data: Any | None = None
    summary: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Run workspace browser models
# ---------------------------------------------------------------------------

class RunWorkspaceItem(BaseModel):
    id: str
    name: str
    path: str
    updated_at: str | None = None
    has_langgraph_report: bool = False
    has_agent_runs: bool = False
    has_phase_plan: bool = False


class RunArtifactItem(BaseModel):
    path: str
    exists: bool
    type: str
    size: int | None = None
    updated_at: str | None = None
    required: bool = False


class RunArtifactReadResponse(BaseModel):
    path: str
    exists: bool
    type: str
    content: str | None = None
    data: Any | None = None
    absolute_path: str | None = None


class SafeLangGraphBenchmarkRequest(BaseModel):
    mode: Literal["contest_graph_v3"] = "contest_graph_v3"
    provider: Literal["none"] = "none"
    copy_workspace: bool = True
    run_name: str | None = None
