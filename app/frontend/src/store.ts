import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { api, type ArtifactItem, type ArtifactReadResponse, type BenchmarkResponse, type HealthResponse, type PromptResponse, type WorkspaceItem, type WorkspaceSummary } from "./api";

export const useControlStore = defineStore("control", () => {
  const health = ref<HealthResponse | null>(null);
  const workspaces = ref<WorkspaceItem[]>([]);
  const selectedWorkspaceId = ref<string>("");
  const summary = ref<WorkspaceSummary | null>(null);
  const artifacts = ref<ArtifactItem[]>([]);
  const selectedArtifact = ref<ArtifactReadResponse | null>(null);
  const benchmark = ref<BenchmarkResponse | null>(null);
  const prompt = ref<PromptResponse | null>(null);
  const loading = ref(false);
  const error = ref<string>("");

  const selectedWorkspace = computed(() =>
    workspaces.value.find((item) => item.id === selectedWorkspaceId.value) ?? null,
  );

  async function run<T>(operation: () => Promise<T>): Promise<T | null> {
    loading.value = true;
    error.value = "";
    try {
      return await operation();
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err);
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function initialize() {
    await run(async () => {
      health.value = await api.health();
      workspaces.value = await api.workspaces();
      if (!selectedWorkspaceId.value && workspaces.value.length > 0) {
        const preferred = workspaces.value.find((item) => item.name.includes("V2.3")) ?? workspaces.value[0];
        selectedWorkspaceId.value = preferred.id;
      }
      await refreshWorkspace();
    });
  }

  async function refreshWorkspace() {
    if (!selectedWorkspaceId.value) return;
    const id = selectedWorkspaceId.value;
    const [summaryResult, artifactsResult] = await Promise.all([api.summary(id), api.artifacts(id)]);
    summary.value = summaryResult;
    artifacts.value = artifactsResult;
    if (!selectedArtifact.value && artifactsResult.length > 0) {
      await openArtifact(artifactsResult[0].path);
    }
  }

  async function selectWorkspace(id: string) {
    selectedWorkspaceId.value = id;
    selectedArtifact.value = null;
    prompt.value = null;
    await run(refreshWorkspace);
  }

  async function openArtifact(path: string) {
    if (!selectedWorkspaceId.value) return;
    selectedArtifact.value = await api.artifact(selectedWorkspaceId.value, path);
  }

  async function runAudit() {
    if (!selectedWorkspaceId.value) return;
    await run(async () => {
      await api.audit(selectedWorkspaceId.value);
      await refreshWorkspace();
    });
  }

  async function loadBenchmark() {
    benchmark.value = await run(api.benchmark2022C);
  }

  async function generatePrompt(phase: number, harness: string) {
    if (!selectedWorkspaceId.value) return;
    prompt.value = await run(() => api.prompt(selectedWorkspaceId.value, phase, harness));
  }

  return {
    health,
    workspaces,
    selectedWorkspaceId,
    selectedWorkspace,
    summary,
    artifacts,
    selectedArtifact,
    benchmark,
    prompt,
    loading,
    error,
    initialize,
    refreshWorkspace,
    selectWorkspace,
    openArtifact,
    runAudit,
    loadBenchmark,
    generatePrompt,
  };
});
