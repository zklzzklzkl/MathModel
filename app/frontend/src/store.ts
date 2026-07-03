import { defineStore } from "pinia";
import { computed, ref } from "vue";
import {
  api,
  type ArtifactItem,
  type ArtifactReadResponse,
  type BenchmarkResponse,
  type CreateWorkspacePayload,
  type HarnessInfo,
  type HealthResponse,
  type LangGraphMode,
  type LangGraphRunRequest,
  type LangGraphRunResponse,
  type LangGraphStatusResponse,
  type PrepareHarnessResponse,
  type PromptResponse,
  type RevisionTask,
  type RunHistoryEntry,
  type SourceUploadResponse,
  type WorkspaceItem,
  type WorkspaceSummary,
} from "./api";

export const useControlStore = defineStore("control", () => {
  const health = ref<HealthResponse | null>(null);
  const workspaces = ref<WorkspaceItem[]>([]);
  const selectedWorkspaceId = ref<string>("");
  const summary = ref<WorkspaceSummary | null>(null);
  const artifacts = ref<ArtifactItem[]>([]);
  const selectedArtifact = ref<ArtifactReadResponse | null>(null);
  const benchmark = ref<BenchmarkResponse | null>(null);
  const prompt = ref<PromptResponse | null>(null);
  const history = ref<RunHistoryEntry[]>([]);
  const revisionTasks = ref<RevisionTask[]>([]);
  const harnesses = ref<HarnessInfo[]>([]);
  const preparedRun = ref<PrepareHarnessResponse | null>(null);
  const uploadResult = ref<SourceUploadResponse | null>(null);
  const loading = ref(false);
  const error = ref<string>("");

  // LangGraph Runtime state
  const langGraphStatus = ref<LangGraphStatusResponse | null>(null);
  const langGraphRun = ref<LangGraphRunResponse | null>(null);
  const langGraphRunning = ref(false);
  const selectedLangGraphMode = ref<LangGraphMode>("contest_graph_v3");
  const selectedLangGraphPhase = ref(1);
  const selectedProvider = ref("none");
  const selectedModel = ref("");
  const langGraphCopyWorkspace = ref(true);
  const langGraphRunName = ref("");
  const langGraphTemperature = ref(0.2);
  const langGraphMaxTokens = ref(4096);

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
      harnesses.value = await api.harnesses();
      workspaces.value = await api.workspaces();
      if (!selectedWorkspaceId.value && workspaces.value.length > 0) {
        const preferred = workspaces.value.find((item) => item.name.includes("V2.6")) ?? workspaces.value[0];
        selectedWorkspaceId.value = preferred.id;
      }
      await refreshWorkspace();
    });
    // Load LangGraph status separately — don't break init if unavailable
    loadLangGraphStatus();
  }

  async function refreshWorkspace() {
    if (!selectedWorkspaceId.value) return;
    const id = selectedWorkspaceId.value;
    const [summaryResult, artifactsResult, historyResult] = await Promise.all([
      api.summary(id),
      api.artifacts(id),
      api.history(id),
    ]);
    summary.value = summaryResult;
    artifacts.value = artifactsResult;
    history.value = historyResult;
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

  async function createWorkspace(payload: CreateWorkspacePayload) {
    await run(async () => {
      const response = await api.createWorkspace(payload);
      workspaces.value = await api.workspaces();
      selectedWorkspaceId.value = response.workspace.id;
      selectedArtifact.value = null;
      await refreshWorkspace();
    });
  }

  async function uploadSource(files: FileList | File[]) {
    if (!selectedWorkspaceId.value) return;
    uploadResult.value = await run(() => api.uploadSource(selectedWorkspaceId.value, files));
    await refreshWorkspace();
  }

  async function generateRevisionTasks() {
    if (!selectedWorkspaceId.value) return;
    const result = await run(() => api.revisionTasks(selectedWorkspaceId.value));
    revisionTasks.value = result?.tasks ?? [];
    await refreshWorkspace();
  }

  async function loadBenchmark() {
    benchmark.value = await run(api.benchmark2022C);
  }

  async function generatePrompt(phase: number, harness: string) {
    if (!selectedWorkspaceId.value) return;
    prompt.value = await run(() => api.prompt(selectedWorkspaceId.value, phase, harness));
    await refreshWorkspace();
  }

  async function prepareHarness(phase: number, harness: string, copyWorkspace = true, runName?: string) {
    if (!selectedWorkspaceId.value) return;
    preparedRun.value = await run(() =>
      api.prepareHarness(selectedWorkspaceId.value, phase, harness, copyWorkspace, runName),
    );
    if (preparedRun.value) {
      prompt.value = {
        phase: preparedRun.value.phase,
        harness: preparedRun.value.harness,
        prompt: preparedRun.value.prompt,
      };
    }
    await refreshWorkspace();
  }

  // ---- LangGraph Runtime actions ----

  async function loadLangGraphStatus() {
    langGraphStatus.value = await run(api.langGraphStatus);
  }

  async function runLangGraph() {
    if (!selectedWorkspaceId.value) return;
    langGraphRunning.value = true;
    try {
      const payload: LangGraphRunRequest = {
        phase: selectedLangGraphPhase.value,
        mode: selectedLangGraphMode.value,
        provider: selectedProvider.value,
        model: selectedModel.value.trim() || null,
        copy_workspace: langGraphCopyWorkspace.value,
        run_name: langGraphRunName.value.trim() || null,
        temperature: langGraphTemperature.value,
        max_tokens: langGraphMaxTokens.value,
      };
      langGraphRun.value = await api.runLangGraph(selectedWorkspaceId.value, payload);
      await refreshWorkspace();
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err);
    } finally {
      langGraphRunning.value = false;
    }
  }

  function openLangGraphArtifact(path: string | null | undefined) {
    if (path) openArtifact(path);
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
    history,
    revisionTasks,
    harnesses,
    preparedRun,
    uploadResult,
    loading,
    error,
    initialize,
    refreshWorkspace,
    selectWorkspace,
    openArtifact,
    runAudit,
    createWorkspace,
    uploadSource,
    generateRevisionTasks,
    loadBenchmark,
    generatePrompt,
    prepareHarness,
    // LangGraph Runtime
    langGraphStatus,
    langGraphRun,
    langGraphRunning,
    selectedLangGraphMode,
    selectedLangGraphPhase,
    selectedProvider,
    selectedModel,
    langGraphCopyWorkspace,
    langGraphRunName,
    langGraphTemperature,
    langGraphMaxTokens,
    loadLangGraphStatus,
    runLangGraph,
    openLangGraphArtifact,
  };
});
