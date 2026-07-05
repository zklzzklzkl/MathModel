from __future__ import annotations

from typing import NotRequired, TypedDict


class MathModelGraphState(TypedDict):
    source_workspace: str
    run_workspace: str
    phase: int
    mode: str
    provider: str
    model: str | None
    temperature: float
    max_tokens: int
    prompt: str
    prompt_path: str | None
    pre_audit: dict
    post_audit: dict
    issues: list[dict]
    created_files: list[str]
    updated_files: list[str]
    needs_human: bool
    status: str
    stop_reason: str | None
    report_path: str | None
    phase_plan: dict | None
    raw_model_output: str | None
    provider_error: str | None
    plan_path: str | None
    plan_markdown_path: str | None
    raw_output_path: str | None
    json_preprocess_report: NotRequired[dict | None]
    json_preprocess_report_path: NotRequired[str | None]
    apply_diff_path: str | None
    files_planned: list[str]
    files_written: list[str]
    files_rejected: list[dict]
    apply_error: str | None
    plan_source: str | None
    contest_graph_steps: NotRequired[list[dict]]
    current_phase: NotRequired[int | None]
    completed_phases: NotRequired[list[int]]
    paused_at: NotRequired[str | None]
    human_gate_required: NotRequired[bool]
    human_gate_file: NotRequired[str | None]
    contest_status: NotRequired[str | None]
    final_audit: NotRequired[dict]
    graph_report_path: NotRequired[str | None]
    phase_results: NotRequired[list[dict]]
    sandbox_commands: NotRequired[list[dict]]
    sandbox_status: NotRequired[str | None]
    manifest_created_empty: NotRequired[bool]
    paper_sandbox_status: NotRequired[str | None]
    paper_files_written: NotRequired[list[str]]
    claim_trace_path: NotRequired[str | None]
    method_matrix_path: NotRequired[str | None]
    paper_build_report_path: NotRequired[str | None]
    paper_sandbox_error: NotRequired[str | None]
    revision_sandbox_status: NotRequired[str | None]
    revision_files_written: NotRequired[list[str]]
    revision_status_path: NotRequired[str | None]
    revision_sandbox_error: NotRequired[str | None]
    history: NotRequired[dict | None]
