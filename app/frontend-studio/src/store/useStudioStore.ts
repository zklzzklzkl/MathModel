"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  apiFetch,
  type ArtifactIndexItem,
  type ArtifactRead,
  type Gate,
  type ModelConfig,
  type RunEvent,
  type StageModelConfig,
  type StudioProject,
  type StudioRun,
  type TemplatePack,
} from "@/lib/api";

/* ------------------------------------------------------------------ */
/*  Shared constants (mirrored from page.tsx so pages stay standalone) */
/* ------------------------------------------------------------------ */

export const domains = [
  { id: "math_modeling", label: "数学建模竞赛" },
  { id: "statistics", label: "统计建模" },
  { id: "data_analysis", label: "数据分析" },
  { id: "paper_writing", label: "论文写作" },
  { id: "homework", label: "课程作业" },
  { id: "research", label: "科研 / 毕业设计" },
] as const;

export const navItems = ["首页", "项目", "运行", "结果", "模板库", "模型设置", "质量检查"] as const;

export const timeline = [
  ["problem_intake", "题面建档"],
  ["model_strategy", "建模策略"],
  ["human_gate", "人工确认"],
  ["code_generation", "代码实验"],
  ["paper_writing", "论文构建"],
  ["contest_review", "竞赛评审"],
  ["revision", "修订"],
  ["final_verify", "最终验收"],
] as const;

export const qualityItems = [
  ["HUMAN_MODEL_REVIEW", "建模路线人工确认"],
  ["CLAIM_TRACE", "声明证据追踪"],
  ["METHOD_IMPLEMENTATION_MATRIX", "方法实现矩阵"],
  ["FIGURE_AUDIT", "图表审计"],
  ["PAPER_SCORECARD", "竞赛评分"],
  ["REVISION_ACTIONS", "修订任务"],
  ["VERIFY_REPORT", "最终验收"],
] as const;

export const runtimeDrivers = [
  ["local", "LocalWorkflowDriver"],
  ["langgraph", "LangGraphDriver"],
  ["codex", "CodexDriver"],
  ["claude-code", "ClaudeCodeDriver"],
  ["cloud", "CloudDriver"],
] as const;

/* ------------------------------------------------------------------ */
/*  Store shape                                                       */
/* ------------------------------------------------------------------ */

export type ToastMessage = {
  id: string;
  severity: "info" | "success" | "warning" | "error";
  message: string;
  createdAt: number;
};

type StudioState = {
  /* -- nav -- */
  activeNav: string;
  setActiveNav: (nav: string) => void;

  /* -- project -- */
  selectedDomain: string;
  setSelectedDomain: (domain: string) => void;
  projectName: string;
  setProjectName: (name: string) => void;
  contest: string;
  setContest: (c: string) => void;
  project: StudioProject | null;
  setProject: (p: StudioProject | null) => void;
  artifacts: ArtifactIndexItem[];
  selectedArtifactPath: string;
  artifactPreview: ArtifactRead | null;

  /* -- run -- */
  driver: string;
  setDriver: (d: string) => void;
  run: StudioRun | null;
  setRun: (r: StudioRun | null) => void;
  events: RunEvent[];
  gate: Gate | null;
  selectedRoute: string;
  setSelectedRoute: (r: string) => void;
  humanNotes: string;
  setHumanNotes: (n: string) => void;

  /* -- templates -- */
  templates: TemplatePack[];
  setTemplates: (t: TemplatePack[]) => void;

  /* -- model config -- */
  modelConfig: ModelConfig | null;
  setModelConfig: (c: ModelConfig | null) => void;

  /* -- ui -- */
  message: string;
  setMessage: (m: string) => void;
  busy: boolean;
  setBusy: (b: boolean) => void;
  developerMode: boolean;
  setDeveloperMode: (d: boolean) => void;
  toasts: ToastMessage[];
  addToast: (severity: ToastMessage["severity"], message: string) => void;
  dismissToast: (id: string) => void;

  /* -- derived helpers -- */
  currentDomain: () => { id: string; label: string };
  currentStage: () => string;

  /* -- actions -- */
  refreshStudioData: () => Promise<void>;
  createProject: (uploadFile: File | null) => Promise<void>;
  startRun: () => Promise<void>;
  refreshRun: (runId?: string) => Promise<void>;
  submitGate: (decision: string) => Promise<void>;
  cancelRun: () => Promise<void>;
  refreshArtifacts: (projectId?: string) => Promise<void>;
  readArtifactPath: (path: string, projectId?: string) => Promise<void>;
  updateStageConfig: (stage: StageModelConfig, patch: Partial<StageModelConfig>) => Promise<void>;
};

let toastCounter = 0;

export const useStudioStore = create<StudioState>()(
  persist(
    (set, get) => ({
      /* -- nav -- */
      activeNav: "首页",
      setActiveNav: (nav) => set({ activeNav: nav }),

      /* -- project -- */
      selectedDomain: "math_modeling",
      setSelectedDomain: (domain) => set({ selectedDomain: domain }),
      projectName: "2026 国赛 C 题",
      setProjectName: (name) => set({ projectName: name }),
      contest: "CUMCM",
      setContest: (c) => set({ contest: c }),
      project: null,
      setProject: (p) => set({ project: p }),
      artifacts: [],
      selectedArtifactPath: "",
      artifactPreview: null,

      /* -- run -- */
      driver: "local",
      setDriver: (d) => set({ driver: d }),
      run: null,
      setRun: (r) => set({ run: r }),
      events: [],
      gate: null,
      selectedRoute: "方案 A",
      setSelectedRoute: (r) => set({ selectedRoute: r }),
      humanNotes: "",
      setHumanNotes: (n) => set({ humanNotes: n }),

      /* -- templates -- */
      templates: [],
      setTemplates: (t) => set({ templates: t }),

      /* -- model config -- */
      modelConfig: null,
      setModelConfig: (c) => set({ modelConfig: c }),

      /* -- ui -- */
      message: "等待创建项目",
      setMessage: (m) => set({ message: m }),
      busy: false,
      setBusy: (b) => set({ busy: b }),
      developerMode: false,
      setDeveloperMode: (d) => set({ developerMode: d }),
      toasts: [],
      addToast: (severity, message) => {
        const id = `toast_${++toastCounter}`;
        set((s) => ({
          toasts: [...s.toasts, { id, severity, message, createdAt: Date.now() }],
        }));
      },
      dismissToast: (id) => {
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
      },

      /* -- derived -- */
      currentDomain: () => domains.find((d) => d.id === get().selectedDomain) ?? domains[0],
      currentStage: () => get().run?.current_stage ?? "project_created",

      /* -- actions -- */
      refreshStudioData: async () => {
        try {
          const [models, templateResult] = await Promise.all([
            apiFetch<ModelConfig>("/api/models/config"),
            apiFetch<{ templates: TemplatePack[] }>("/api/templates"),
          ]);
          set({ modelConfig: models, templates: templateResult.templates });
        } catch (error) {
          set({ message: error instanceof Error ? error.message : "无法连接 Studio API" });
        }
      },

      createProject: async (uploadFile) => {
        const { projectName, selectedDomain, contest, templates } = get();
        set({ busy: true });
        try {
          const created = await apiFetch<StudioProject>("/api/projects", {
            method: "POST",
            body: JSON.stringify({
              name: projectName,
              domain: selectedDomain,
              contest,
              template_id: templates[0]?.id,
            }),
          });
          set({ project: created, message: "项目已创建" });
          if (uploadFile) {
            const form = new FormData();
            form.append("files", uploadFile);
            await apiFetch(`/api/projects/${created.id}/files`, { method: "POST", body: form });
            set({ message: "项目已创建，资料已上传" });
          }
          await get().refreshArtifacts(created.id);
        } catch (error) {
          set({ message: error instanceof Error ? error.message : "项目创建失败" });
        } finally {
          set({ busy: false });
        }
      },

      startRun: async () => {
        const { project, driver } = get();
        if (!project) {
          set({ message: "请先创建项目" });
          return;
        }
        set({ busy: true });
        try {
          const created = await apiFetch<StudioRun>("/api/runs", {
            method: "POST",
            body: JSON.stringify({ project_id: project.id, driver }),
          });
          set({ run: created });
          await get().refreshRun(created.id);
          set({ message: "运行已启动，等待当前闸门处理" });
        } catch (error) {
          set({ message: error instanceof Error ? error.message : "运行启动失败" });
        } finally {
          set({ busy: false });
        }
      },

      refreshRun: async (runId) => {
        const id = runId ?? get().run?.id;
        if (!id) return;
        const [eventResult, gateResult] = await Promise.all([
          apiFetch<{ events: RunEvent[] }>(`/api/runs/${id}/events`),
          apiFetch<Gate>(`/api/gates/${id}/current`).catch(() => null),
        ]);
        set({ events: eventResult.events, gate: gateResult });
      },

      submitGate: async (decision) => {
        const { run, gate, selectedRoute, humanNotes, project } = get();
        if (!run || !gate) return;
        set({ busy: true });
        try {
          await apiFetch(`/api/gates/${run.id}/${gate.id}/submit`, {
            method: "POST",
            body: JSON.stringify({
              decision,
              selected_route: selectedRoute,
              human_notes: humanNotes || "Studio V3 HumanGateModal 提交。",
              ai_notes: "",
            }),
          });
          const updatedRun = await apiFetch<StudioRun>(`/api/runs/${run.id}/resume`, { method: "POST", body: "{}" });
          set({ run: updatedRun });
          await get().refreshRun(run.id);
          if (project) {
            await get().refreshArtifacts(project.id);
            await get().readArtifactPath("reports/MODELING_DECISION.md", project.id);
          }
          set({ message: "人工闸门已提交" });
        } catch (error) {
          set({ message: error instanceof Error ? error.message : "人工闸门提交失败" });
        } finally {
          set({ busy: false });
        }
      },

      cancelRun: async () => {
        const { run } = get();
        if (!run) return;
        const canceled = await apiFetch<StudioRun>(`/api/runs/${run.id}/cancel`, { method: "POST", body: "{}" });
        set({ run: canceled, message: "运行已取消" });
      },

      refreshArtifacts: async (projectId) => {
        const id = projectId ?? get().project?.id;
        if (!id) return;
        const result = await apiFetch<{ files: ArtifactIndexItem[] }>(`/api/projects/${id}/files`);
        const { selectedArtifactPath } = get();
        const preferred =
          result.files.find((item) => item.path === selectedArtifactPath) ??
          result.files.find((item) => item.path === "reports/MODELING_DECISION.md") ??
          result.files.find((item) => item.type === "report") ??
          result.files[0];
        set({ artifacts: result.files });
        if (preferred) {
          await get().readArtifactPath(preferred.path, id);
        }
      },

      readArtifactPath: async (path, projectId) => {
        const id = projectId ?? get().project?.id;
        if (!id) return;
        const artifact = await apiFetch<ArtifactRead>(
          `/api/projects/${id}/artifacts/read?path=${encodeURIComponent(path)}`,
        );
        set({ selectedArtifactPath: path, artifactPreview: artifact });
      },

      updateStageConfig: async (stage, patch) => {
        const { modelConfig } = get();
        if (!modelConfig) return;
        const updated = await apiFetch<ModelConfig>("/api/models/config", {
          method: "PUT",
          body: JSON.stringify({
            ...modelConfig,
            stages: modelConfig.stages.map((item) => (item.stage === stage.stage ? { ...item, ...patch } : item)),
          }),
        });
        set({ modelConfig: updated });
      },
    }),
    {
      name: "mathmodel-studio-v3",
      partialize: (state) => ({
        selectedDomain: state.selectedDomain,
        driver: state.driver,
        developerMode: state.developerMode,
        activeNav: state.activeNav,
      }),
    },
  ),
);
