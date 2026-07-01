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
  health: () => request<HealthResponse>("/api/health"),
  workspaces: () => request<WorkspaceItem[]>("/api/workspaces"),
  createWorkspace: (payload: CreateWorkspacePayload) =>
    request("/api/workspaces", { method: "POST", body: JSON.stringify(payload) }),
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
};
