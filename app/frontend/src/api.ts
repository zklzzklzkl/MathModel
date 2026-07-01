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
};
