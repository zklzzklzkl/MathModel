const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export interface ScriptStatus {
  path: string;
  exists: boolean;
}

export interface HealthResponse {
  ok: boolean;
  python: string;
  mathmodel_root: string;
  workspace_root: string;
  examples_root: string;
  scripts: Record<string, ScriptStatus>;
}

export interface WorkspaceItem {
  id: string;
  name: string;
  path: string;
  source: "workspace_root" | "examples" | "other";
  updated_at: string | null;
  has_v2_shape: boolean;
}

export interface PhaseSummary {
  id: number;
  name: string;
  skill: string;
  gate: string;
  status: string;
  status_class: "good" | "warn" | "bad" | "info" | string;
  artifacts: string[];
  inputs: string[];
  outputs: string[];
  missing_inputs: string[];
  missing_outputs: string[];
  ready: boolean;
  next_action: string;
}

export interface ArtifactItem {
  path: string;
  exists: boolean;
  type: string;
  size: number | null;
  updated_at: string | null;
  required: boolean;
}

export interface ArtifactReadResponse {
  path: string;
  exists: boolean;
  type: string;
  content: string | null;
  data: unknown;
  absolute_path: string | null;
}

export interface WorkspaceSummary {
  workspace: WorkspaceItem;
  status: string;
  worst_severity: string;
  phases: PhaseSummary[];
  required_missing: string[];
  manifest: Record<string, unknown>;
  paper: Record<string, unknown>;
  issues: Array<Record<string, unknown>>;
  recommendations: Array<Record<string, unknown>>;
}

export interface AuditResponse {
  result: Record<string, unknown>;
  stdout: string;
  stderr: string;
  returncode: number;
}

export interface BenchmarkResponse {
  results: Array<Record<string, unknown>>;
  stdout: string;
  stderr: string;
  returncode: number;
}

export interface PromptResponse {
  phase: number;
  harness: string;
  prompt: string;
}

export interface CreateWorkspacePayload {
  path?: string;
  name?: string;
  contest: string;
  engine: string;
  language: string;
  subproblems: string;
  figure_backend: string;
  nature: "enabled" | "unavailable" | "not_requested";
  force?: boolean;
}

export interface CreateWorkspaceResponse {
  workspace: WorkspaceItem;
  created: string[];
  skipped: string[];
  stdout: string;
  stderr: string;
}

export interface RunHistoryEntry {
  timestamp: string;
  event: string;
  phase: number | null;
  harness: string | null;
  status_before: string | null;
  status_after: string | null;
  source_workspace: string | null;
  run_workspace: string | null;
  prompt_path: string | null;
  note: string | null;
}

export interface RevisionTask {
  id: string;
  severity: string;
  phase: number;
  artifact: string;
  issue_code: string;
  title: string;
  action: string;
}

export interface RevisionTasksResponse {
  tasks: RevisionTask[];
  written_path: string | null;
}

export interface SourceUploadResponse {
  saved: string[];
  skipped: string[];
}

export interface HarnessInfo {
  id: "Manual" | "Codex" | "Claude Code" | "OpenCode";
  label: string;
  managed: boolean;
  available: boolean;
  note: string;
}

export interface PrepareHarnessResponse {
  harness: string;
  phase: number;
  source_workspace: string;
  run_workspace: string;
  copied: boolean;
  prompt: string;
  prompt_path: string | null;
  command_preview: string;
  history: RunHistoryEntry;
}

// ---------------------------------------------------------------------------
// LangGraph Runtime types
// ---------------------------------------------------------------------------

export type LangGraphMode =
  | "dry_run"
  | "llm_plan"
  | "controlled_apply"
  | "phase_execute"
  | "contest_graph_v0"
  | "contest_graph_v1"
  | "contest_graph_v2"
  | "contest_graph_v3";

export interface LangGraphStatusResponse {
  available: boolean;
  version: string | null;
  import_error: string | null;
  note: string;
}

export interface LangGraphRunRequest {
  phase: number;
  mode: LangGraphMode;
  provider: string;
  model?: string | null;
  copy_workspace: boolean;
  run_name?: string | null;
  temperature: number;
  max_tokens: number;
}

export interface LangGraphRunResponse {
  available: boolean;
  source_workspace: string;
  run_workspace: string;
  phase: number;
  mode: string;
  provider: string;
  model: string | null;
  status: string;
  prompt_path: string | null;
  report_path: string | null;
  pre_audit: Record<string, unknown>;
  post_audit: Record<string, unknown>;
  issues: Array<Record<string, unknown>>;
  history: Record<string, unknown> | null;
  phase_plan: Record<string, unknown> | null;
  provider_error: string | null;
  plan_path: string | null;
  plan_markdown_path: string | null;
  raw_output_path: string | null;
  apply_diff_path: string | null;
  files_planned: string[];
  files_written: string[];
  files_rejected: unknown[];
  needs_human: boolean;
  contest_status: string | null;
  completed_phases: number[];
  paused_at: string | null;
  human_gate_required: boolean;
  human_gate_file: string | null;
  graph_report_path: string | null;
  phase_results: Array<Record<string, unknown>>;
  final_audit: Record<string, unknown>;
  sandbox_commands: Array<Record<string, unknown>>;
  sandbox_status: string | null;
  manifest_created_empty: boolean;
  paper_sandbox_status: string | null;
  paper_files_written: string[];
  claim_trace_path: string | null;
  method_matrix_path: string | null;
  paper_build_report_path: string | null;
  revision_sandbox_status: string | null;
  revision_files_written: string[];
  revision_status_path: string | null;
}

// ---------------------------------------------------------------------------
// Benchmark Report Browser types
// ---------------------------------------------------------------------------

export interface BenchmarkReportItem {
  id: string;
  title: string;
  path: string;
  type: "markdown" | "json";
  category: string;
  provider: string | null;
  mode: string | null;
  workspace: string | null;
  updated_at: string | null;
  size: number | null;
}

export interface BenchmarkReportReadResponse {
  id: string;
  title: string;
  path: string;
  type: "markdown" | "json";
  category: string;
  provider: string | null;
  mode: string | null;
  workspace: string | null;
  content: string;
  data: unknown | null;
  summary: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Run workspace browser types
// ---------------------------------------------------------------------------

export interface RunWorkspaceItem {
  id: string;
  name: string;
  path: string;
  updated_at: string | null;
  has_langgraph_report: boolean;
  has_agent_runs: boolean;
  has_phase_plan: boolean;
}

export interface RunArtifactItem {
  path: string;
  exists: boolean;
  type: string;
  size: number | null;
  updated_at: string | null;
  required: boolean;
}

export interface RunArtifactReadResponse {
  path: string;
  exists: boolean;
  type: string;
  content: string | null;
  data: unknown;
  absolute_path: string | null;
}

export interface SafeLangGraphBenchmarkRequest {
  mode: "contest_graph_v3";
  provider: "none";
  copy_workspace: true;
  run_name?: string | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // keep status text
    }
    throw new Error(`${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  base: API_BASE,
  health: () => request<HealthResponse>("/api/health"),
  rawUrl: (id: string, path: string) => `${API_BASE}/api/workspaces/${id}/raw?path=${encodeURIComponent(path)}`,
  harnesses: () => request<HarnessInfo[]>("/api/harnesses"),
  workspaces: () => request<WorkspaceItem[]>("/api/workspaces"),
  createWorkspace: (payload: CreateWorkspacePayload) =>
    request<CreateWorkspaceResponse>("/api/workspaces", { method: "POST", body: JSON.stringify(payload) }),
  summary: (id: string) => request<WorkspaceSummary>(`/api/workspaces/${id}/summary`),
  artifacts: (id: string) => request<ArtifactItem[]>(`/api/workspaces/${id}/artifacts`),
  artifact: (id: string, path: string) =>
    request<ArtifactReadResponse>(`/api/workspaces/${id}/artifact?path=${encodeURIComponent(path)}`),
  audit: (id: string) => request<AuditResponse>(`/api/workspaces/${id}/audit`, { method: "POST" }),
  benchmark2022C: () => request<BenchmarkResponse>("/api/benchmark/2022C"),
  prompt: (id: string, phase: number, harness: string) =>
    request<PromptResponse>(`/api/workspaces/${id}/prompt`, {
      method: "POST",
      body: JSON.stringify({ phase, harness }),
    }),
  copyRun: (id: string, name?: string) =>
    request(`/api/workspaces/${id}/runs/copy`, {
      method: "POST",
      body: JSON.stringify({ name }),
    }),
  history: (id: string) => request<RunHistoryEntry[]>(`/api/workspaces/${id}/runs/history`),
  revisionTasks: (id: string) =>
    request<RevisionTasksResponse>(`/api/workspaces/${id}/revision-tasks`, { method: "POST" }),
  prepareHarness: (id: string, phase: number, harness: string, copyWorkspace = true, runName?: string) =>
    request<PrepareHarnessResponse>(`/api/workspaces/${id}/harness/prepare`, {
      method: "POST",
      body: JSON.stringify({ phase, harness, copy_workspace: copyWorkspace, run_name: runName }),
    }),
  uploadSource: async (id: string, files: FileList | File[]) => {
    const form = new FormData();
    Array.from(files).forEach((file) => form.append("files", file));
    const response = await fetch(`${API_BASE}/api/workspaces/${id}/source-files`, {
      method: "POST",
      body: form,
    });
    if (!response.ok) {
      throw new Error(`${response.status}: ${response.statusText}`);
    }
    return response.json() as Promise<SourceUploadResponse>;
  },

  // LangGraph Runtime
  langGraphStatus: () => request<LangGraphStatusResponse>("/api/langgraph/status"),

  runLangGraph: (id: string, payload: LangGraphRunRequest) =>
    request<LangGraphRunResponse>(`/api/workspaces/${id}/langgraph/run`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Benchmark Report Browser
  benchmarkReports: () => request<BenchmarkReportItem[]>("/api/benchmark-reports"),

  benchmarkReport: (id: string) =>
    request<BenchmarkReportReadResponse>(`/api/benchmark-reports/${encodeURIComponent(id)}`),

  // Run Workspace Browser
  runs: (id: string) =>
    request<RunWorkspaceItem[]>(`/api/workspaces/${id}/runs`),

  runArtifacts: (id: string, runId: string) =>
    request<RunArtifactItem[]>(`/api/workspaces/${id}/runs/${encodeURIComponent(runId)}/artifacts`),

  runArtifact: (id: string, runId: string, path: string) =>
    request<RunArtifactReadResponse>(
      `/api/workspaces/${id}/runs/${encodeURIComponent(runId)}/artifact?path=${encodeURIComponent(path)}`,
    ),

  runRawUrl: (id: string, runId: string, path: string) =>
    `${API_BASE}/api/workspaces/${id}/runs/${encodeURIComponent(runId)}/raw?path=${encodeURIComponent(path)}`,

  safeLangGraphBenchmark: (id: string, payload: SafeLangGraphBenchmarkRequest) =>
    request<LangGraphRunResponse>(`/api/workspaces/${id}/benchmarks/langgraph-safe`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
