import { defineStore } from "pinia";
import { computed, ref } from "vue";
import {
  api,
  type ArtifactItem,
  type ArtifactReadResponse,
  type BenchmarkReportItem,
  type BenchmarkReportReadResponse,
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
  type RunArtifactItem,
  type RunArtifactReadResponse,
  type RunHistoryEntry,
  type RunWorkspaceItem,
  type SafeLangGraphBenchmarkRequest,
  type SourceUploadResponse,
  type WorkspaceItem,
  type WorkspaceSummary,
} from "./api";

export function isRunWorkspacePath(path?: string | null) {
  if (!path) return false;
  return /[\\/]runs[\\/]/.test(path.replace(/\s+/g, ""));
}

const PHASE_EXECUTE_SUPPORTED = new Set([1, 4]);

function canPhaseExecute(phase: number) {
  return PHASE_EXECUTE_SUPPORTED.has(phase);
}

function friendlyError(message: string) {
  if (message.includes("PHASE_NOT_SUPPORTED") && message.includes("phase_execute")) {
    return "当前阶段暂不支持单阶段执行。phase_execute 目前只支持 P1 建模策略与 P4 竞赛评分审查；其它阶段请使用 Dry Run 或 Run Recommended Graph。";
  }
  return message;
}

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

  // Benchmark Report Browser state
  const benchmarkReports = ref<BenchmarkReportItem[]>([]);
  const selectedBenchmarkReportId = ref("");
  const selectedBenchmarkReport = ref<BenchmarkReportReadResponse | null>(null);
  const benchmarkReportLoading = ref(false);
  const benchmarkCategoryFilter = ref("all");
  const benchmarkProviderFilter = ref("all");

  // Run workspace browser state
  const runWorkspaces = ref<RunWorkspaceItem[]>([]);
  const selectedRunWorkspaceId = ref("");
  const runArtifacts = ref<RunArtifactItem[]>([]);
  const selectedRunArtifact = ref<RunArtifactReadResponse | null>(null);
  const runArtifactQuery = ref("");
  const safeBenchmarkRunning = ref(false);
  const safeBenchmarkResult = ref<LangGraphRunResponse | null>(null);

  const selectedWorkspace = computed(() =>
    workspaces.value.find((item) => item.id === selectedWorkspaceId.value) ?? null,
  );
  const selectedIsRunWorkspace = computed(() => isRunWorkspacePath(selectedWorkspace.value?.path));

  async function run<T>(operation: () => Promise<T>): Promise<T | null> {
    loading.value = true;
    error.value = "";
    try {
      return await operation();
    } catch (err) {
      error.value = friendlyError(err instanceof Error ? err.message : String(err));
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
        const sourceWorkspaces = workspaces.value.filter((item) => !isRunWorkspacePath(item.path));
        const preferred =
          sourceWorkspaces.find((item) => item.name.includes("V2.7") || item.name.includes("V2.6")) ??
          sourceWorkspaces[0] ??
          workspaces.value[0];
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
    if (selectedIsRunWorkspace.value) {
      error.value = "Run workspace is read-only result context. Select a source workspace to run again.";
      return;
    }
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
      error.value = friendlyError(err instanceof Error ? err.message : String(err));
    } finally {
      langGraphRunning.value = false;
    }
  }

  async function runLangGraphPayload(payload: LangGraphRunRequest) {
    if (!selectedWorkspaceId.value) return null;
    if (selectedIsRunWorkspace.value) {
      error.value = "Run workspace is read-only result context. Select a source workspace to run again.";
      return null;
    }
    langGraphRunning.value = true;
    error.value = "";
    try {
      langGraphRun.value = await api.runLangGraph(selectedWorkspaceId.value, payload);
      await refreshWorkspace();
      await loadRunWorkspaces();
      return langGraphRun.value;
    } catch (err) {
      error.value = friendlyError(err instanceof Error ? err.message : String(err));
      return null;
    } finally {
      langGraphRunning.value = false;
    }
  }

  async function runRecommendedGraph() {
    selectedLangGraphMode.value = "contest_graph_v3";
    selectedLangGraphPhase.value = 1;
    selectedProvider.value = "none";
    selectedModel.value = "";
    langGraphCopyWorkspace.value = true;
    langGraphRunName.value = "ui-recommended-contest-graph-v3";
    langGraphTemperature.value = 0.2;
    langGraphMaxTokens.value = 4096;
    return runLangGraphPayload({
      phase: 1,
      mode: "contest_graph_v3",
      provider: "none",
      model: null,
      copy_workspace: true,
      run_name: "ui-recommended-contest-graph-v3",
      temperature: 0.2,
      max_tokens: 4096,
    });
  }

  async function runCurrentSkill(phase: number) {
    if (!canPhaseExecute(phase)) {
      error.value = `当前 Runtime 暂不支持 P${phase} 单阶段执行；请使用 Dry Run 或 Run Recommended Graph。`;
      return null;
    }
    selectedLangGraphMode.value = "phase_execute";
    selectedLangGraphPhase.value = phase;
    selectedProvider.value = "none";
    selectedModel.value = "";
    langGraphCopyWorkspace.value = true;
    langGraphRunName.value = `ui-phase-${phase}`;
    langGraphTemperature.value = 0.2;
    langGraphMaxTokens.value = 4096;
    return runLangGraphPayload({
      phase,
      mode: "phase_execute",
      provider: "none",
      model: null,
      copy_workspace: true,
      run_name: `ui-phase-${phase}`,
      temperature: 0.2,
      max_tokens: 4096,
    });
  }

  async function dryRunSkill(phase: number) {
    selectedLangGraphMode.value = "dry_run";
    selectedLangGraphPhase.value = phase;
    selectedProvider.value = "none";
    selectedModel.value = "";
    langGraphCopyWorkspace.value = true;
    langGraphRunName.value = `ui-dry-run-phase-${phase}`;
    langGraphTemperature.value = 0.2;
    langGraphMaxTokens.value = 4096;
    return runLangGraphPayload({
      phase,
      mode: "dry_run",
      provider: "none",
      model: null,
      copy_workspace: true,
      run_name: `ui-dry-run-phase-${phase}`,
      temperature: 0.2,
      max_tokens: 4096,
    });
  }

  function openLangGraphArtifact(path: string | null | undefined) {
    if (path) openArtifact(path);
  }

  // ---- Benchmark Report Browser actions ----

  async function loadBenchmarkReports() {
    benchmarkReportLoading.value = true;
    try {
      benchmarkReports.value = await api.benchmarkReports();
      if (!selectedBenchmarkReportId.value && benchmarkReports.value.length > 0) {
        await openBenchmarkReport(benchmarkReports.value[0].id);
      }
    } catch (err) {
      error.value = friendlyError(err instanceof Error ? err.message : String(err));
    } finally {
      benchmarkReportLoading.value = false;
    }
  }

  async function openBenchmarkReport(id: string) {
    selectedBenchmarkReportId.value = id;
    selectedBenchmarkReport.value = await api.benchmarkReport(id);
  }

  // ---- Run workspace browser actions ----

  async function loadRunWorkspaces() {
    if (!selectedWorkspaceId.value) return;
    try {
      runWorkspaces.value = await api.runs(selectedWorkspaceId.value);
    } catch {
      runWorkspaces.value = [];
    }
  }

  async function selectRunWorkspace(id: string) {
    selectedRunWorkspaceId.value = id;
    selectedRunArtifact.value = null;
    if (selectedWorkspaceId.value) {
      try {
        runArtifacts.value = await api.runArtifacts(selectedWorkspaceId.value, id);
      } catch {
        runArtifacts.value = [];
      }
    }
  }

  async function loadRunArtifacts() {
    if (!selectedWorkspaceId.value || !selectedRunWorkspaceId.value) return;
    try {
      runArtifacts.value = await api.runArtifacts(selectedWorkspaceId.value, selectedRunWorkspaceId.value);
    } catch {
      runArtifacts.value = [];
    }
  }

  async function openRunArtifact(path: string) {
    if (!selectedWorkspaceId.value || !selectedRunWorkspaceId.value) return;
    try {
      selectedRunArtifact.value = await api.runArtifact(selectedWorkspaceId.value, selectedRunWorkspaceId.value, path);
    } catch (err) {
      error.value = friendlyError(err instanceof Error ? err.message : String(err));
    }
  }

  async function runSafeLangGraphBenchmark() {
    if (!selectedWorkspaceId.value) return;
    if (selectedIsRunWorkspace.value) {
      error.value = "Run workspace is read-only result context. Select a source workspace to run again.";
      return;
    }
    safeBenchmarkRunning.value = true;
    try {
      const payload: SafeLangGraphBenchmarkRequest = {
        mode: "contest_graph_v3",
        provider: "none",
        copy_workspace: true,
        run_name: "safe-ui-benchmark-contest-graph-v3",
      };
      safeBenchmarkResult.value = await api.safeLangGraphBenchmark(selectedWorkspaceId.value, payload);
      await refreshWorkspace();
      await loadRunWorkspaces();
    } catch (err) {
      error.value = friendlyError(err instanceof Error ? err.message : String(err));
    } finally {
      safeBenchmarkRunning.value = false;
    }
  }

  return {
    health,
    workspaces,
    selectedWorkspaceId,
    selectedWorkspace,
    selectedIsRunWorkspace,
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
    runRecommendedGraph,
    runCurrentSkill,
    dryRunSkill,
    openLangGraphArtifact,
    // Benchmark Report Browser
    benchmarkReports,
    selectedBenchmarkReportId,
    selectedBenchmarkReport,
    benchmarkReportLoading,
    benchmarkCategoryFilter,
    benchmarkProviderFilter,
    loadBenchmarkReports,
    openBenchmarkReport,
    // Run workspace browser
    runWorkspaces,
    selectedRunWorkspaceId,
    runArtifacts,
    selectedRunArtifact,
    runArtifactQuery,
    safeBenchmarkRunning,
    safeBenchmarkResult,
    loadRunWorkspaces,
    selectRunWorkspace,
    loadRunArtifacts,
    openRunArtifact,
    runSafeLangGraphBenchmark,
  };
});
