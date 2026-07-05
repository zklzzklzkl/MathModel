export type StudioProject = {
  id: string;
  name: string;
  domain: string;
  contest: string;
  workspace_path: string;
  template_id?: string | null;
  status: string;
};

export type StudioRun = {
  id: string;
  project_id: string;
  driver: string;
  status: string;
  current_stage: string;
  workspace_path: string;
};

export type RunEvent = {
  id: number;
  run_id: string;
  stage: string;
  type: string;
  severity: "info" | "warning" | "error" | string;
  message: string;
  artifacts: string[];
  created_at: string;
};

export type ArtifactIndexItem = {
  id: string;
  project_id: string;
  run_id?: string | null;
  path: string;
  type: string;
  size: number;
  updated_at: string;
};

export type ArtifactRead = {
  path: string;
  type: string;
  size: number;
  truncated: boolean;
  content: string;
};

export type GateArtifactPreview = {
  path: string;
  type: string;
  size: number;
  truncated: boolean;
  content: string;
};

export type Gate = {
  id: string;
  run_id: string;
  type: string;
  status: string;
  title: string;
  artifacts: string[];
  artifact_previews?: GateArtifactPreview[];
};

export type TemplatePack = {
  id: string;
  name: string;
  contest: string;
  language: string;
  engine: string;
  main_file: string;
  description: string;
  required_files: string[];
  preview_file: string;
  warnings: string[];
};

export type StageModelConfig = {
  stage: string;
  label: string;
  provider: string;
  model: string;
  temperature: number;
  max_tokens: number;
  timeout_sec: number;
  retry_count: number;
  context_budget: number;
  parallel_agents: number;
};

export type ModelConfig = {
  preset: string;
  providers: Array<{ id: string; label: string; enabled: boolean; api_key_status: string }>;
  stages: StageModelConfig[];
};

const API_BASE = process.env.NEXT_PUBLIC_MATHMODEL_API_BASE ?? "http://127.0.0.1:8000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers =
    init?.body instanceof FormData
      ? init.headers
      : { "Content-Type": "application/json", ...((init?.headers as Record<string, string> | undefined) ?? {}) };
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      detail = response.statusText;
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export function templateDownloadUrl(templateId: string): string {
  return `${API_BASE}/api/templates/${templateId}/download`;
}
