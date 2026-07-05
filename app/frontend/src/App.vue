<!-- Legacy Control Center: frozen for V3. New product work lives in app/frontend-studio. -->
<template>
  <div class="cc-shell">
    <aside class="cc-sidebar">
      <div class="brand-block">
        <strong>MathModel</strong>
        <span>Control Center v3</span>
      </div>

      <nav class="simple-nav">
        <button :class="{ active: view === 'home' }" @click="view = 'home'"><MessageCircle :size="17" />开始</button>
        <button :class="{ active: view === 'workspaces' }" @click="openWorkspaceManager"><FolderOpen :size="17" />工作区</button>
        <button :class="{ active: view === 'settings' }" @click="view = 'settings'"><Settings :size="17" />设置</button>
      </nav>

      <section class="workspace-picker">
        <label>当前工作区</label>
        <select v-model="store.selectedWorkspaceId" @change="selectWorkspace">
          <option v-for="workspace in activeWorkspaces" :key="workspace.id" :value="workspace.id">
            {{ workspace.name }}
          </option>
        </select>
        <small :title="store.selectedWorkspace?.path ?? ''">{{ shortWorkspacePath(store.selectedWorkspace?.path ?? '') }}</small>
      </section>

      <section class="runtime-card">
        <label>运行方式</label>
        <select v-model="store.selectedProvider">
          <option value="none">安全预演，不调用 API</option>
          <option value="deepseek">DeepSeek</option>
          <option value="openai-compatible">OpenAI-compatible</option>
        </select>
        <input v-if="store.selectedProvider !== 'none'" v-model="store.selectedModel" placeholder="模型名，例如 deepseek-chat" />
        <button class="primary full" :disabled="!canRun" @click="runRecommended">
          <PlayCircle :size="17" />{{ store.langGraphRunning ? "运行中..." : "开始推荐流程" }}
        </button>
        <small>默认运行现有 `contest_graph_v3`，不会跳过人工审核。</small>
      </section>
    </aside>

    <main class="cc-main">
      <header class="hero-strip">
        <div>
          <p class="eyebrow">像聊天一样跑完整建模流程</p>
          <h1>{{ heroTitle }}</h1>
          <p>{{ heroSubtitle }}</p>
        </div>
        <div class="hero-actions">
          <button @click="store.initialize"><RefreshCw :size="16" />刷新</button>
          <button @click="store.runAudit"><ShieldCheck :size="16" />审计</button>
          <button class="primary" :disabled="!canRun" @click="runRecommended"><PlayCircle :size="16" />运行</button>
        </div>
      </header>

      <div v-if="store.error" class="notice bad">{{ store.error }}</div>
      <div v-if="store.selectedIsRunWorkspace" class="notice warn">当前是运行副本，只适合查看结果。请切回 Source 工作区再运行。</div>
      <div v-if="store.loading" class="notice info">正在读取本地工作区...</div>

      <section v-if="view === 'home'" class="workspace-console">
        <div class="chat-column">
          <div class="status-composer">
            <div>
              <span :class="['status-dot', statusTone(store.activity?.worst_severity)]"></span>
              <strong>{{ humanStatus(store.activity?.summary_status ?? store.summary?.status ?? 'UNKNOWN') }}</strong>
              <small>最高风险：{{ store.activity?.worst_severity ?? store.summary?.worst_severity ?? 'UNKNOWN' }}</small>
            </div>
            <button class="primary" :disabled="!canRun" @click="runRecommended">
              <PlayCircle :size="16" />{{ store.langGraphRunning ? "运行中..." : "运行推荐流程" }}
            </button>
          </div>

          <article v-if="primaryBlocker" class="priority-card">
            <span :class="['badge', statusTone(primaryBlocker.severity)]">{{ primaryBlocker.severity }}</span>
            <div>
              <h2>{{ primaryBlocker.title }}</h2>
              <p>{{ primaryBlocker.detail }}</p>
              <button v-if="primaryBlocker.artifact" @click="openArtifact(String(primaryBlocker.artifact))">查看相关文件</button>
            </div>
          </article>

          <div class="chat-stream">
            <article v-for="message in store.activityMessages" :key="message.id" :class="['chat-message', message.kind]">
              <div class="avatar">{{ message.kind === 'history' ? '历' : message.kind === 'recommendation' ? '建' : '状' }}</div>
              <div class="bubble">
                <div class="bubble-head">
                  <strong>{{ message.title }}</strong>
                  <span :class="['badge', statusTone(message.severity)]">{{ message.severity }}</span>
                </div>
                <p>{{ message.body }}</p>
                <div v-if="message.artifacts.length" class="artifact-chips">
                  <button v-for="artifact in message.artifacts" :key="artifact" @click="openArtifact(artifact)">
                    {{ pathLabel(artifact) }}
                  </button>
                </div>
              </div>
            </article>
          </div>

          <details class="all-issues">
            <summary>查看全部审计问题与阶段状态</summary>
            <div class="issue-grid">
              <article v-for="phase in store.summary?.phases ?? []" :key="phase.id" class="phase-card">
                <span>P{{ phase.id }}</span>
                <strong>{{ phase.name }}</strong>
                <small>{{ phase.next_action }}</small>
                <em :class="statusTone(phase.status)">{{ phase.status }}</em>
              </article>
            </div>
            <div class="issue-list">
              <button v-for="issue in groupedIssues" :key="issue.key" @click="issue.artifact && openArtifact(issue.artifact)">
                <span :class="['badge', statusTone(issue.severity)]">{{ issue.severity }}</span>
                <strong>{{ issue.title }}<em v-if="issue.count > 1"> × {{ issue.count }}</em></strong>
                <small>{{ issue.detail }}</small>
              </button>
            </div>
          </details>

          <section class="human-gate-card">
            <div class="section-head">
              <div>
                <p class="eyebrow">人工审核</p>
                <h2>模型路线确认</h2>
              </div>
              <button @click="openHumanGate">打开审核对话</button>
            </div>
            <p>{{ store.humanGateSummary?.summary ?? "当流程停在 Human Gate 时，这里会汇总候选模型、风险和建议问题。" }}</p>
            <div v-if="store.humanGateSummary?.risks.length" class="risk-pills">
              <span v-for="risk in store.humanGateSummary.risks" :key="risk">{{ risk }}</span>
            </div>
          </section>

          <details class="advanced-diagnostics">
            <summary>高级诊断</summary>
            <div class="advanced-grid">
              <button @click="store.dryRunSkill(1)">Dry Run P1</button>
              <button @click="store.dryRunSkill(4)">Dry Run P4</button>
              <button @click="view = 'diagnostics'">查看 LangGraph 原始状态</button>
              <button @click="store.generateRevisionTasks">生成修订任务</button>
            </div>
            <pre>{{ prettyJson(store.langGraphRun ?? store.langGraphStatus ?? {}) }}</pre>
          </details>
        </div>

        <aside class="preview-column">
          <ArtifactPreview
            :artifact="store.selectedArtifact"
            :workspace-id="store.selectedWorkspaceId"
            @open-artifact="openArtifact"
          />
        </aside>
      </section>

      <section v-else-if="view === 'workspaces'" class="manager-view">
        <div class="section-head">
          <div>
            <p class="eyebrow">管理</p>
            <h2>工作区和历史运行</h2>
          </div>
          <button @click="store.initialize"><RefreshCw :size="16" />刷新</button>
        </div>
        <div class="manager-grid">
          <section class="manager-panel">
            <h3>Source 工作区</h3>
            <article v-for="workspace in activeWorkspaces" :key="workspace.id" :class="['workspace-row', { selected: workspace.id === store.selectedWorkspaceId }]">
              <button @click="store.selectWorkspace(workspace.id); view = 'home'">
                <strong>{{ workspace.name }}</strong>
                <small>{{ shortWorkspacePath(workspace.path) }}</small>
              </button>
              <button v-if="workspace.source !== 'examples'" class="danger" @click="archiveWorkspace(workspace.id)">归档</button>
              <span v-else class="badge info">示例只读</span>
            </article>
          </section>

          <section class="manager-panel">
            <h3>已归档</h3>
            <article v-for="workspace in archivedWorkspaces" :key="workspace.id" class="workspace-row">
              <button @click="store.selectWorkspace(workspace.id)">
                <strong>{{ workspace.name }}</strong>
                <small>{{ shortWorkspacePath(workspace.path) }}</small>
              </button>
              <button @click="store.restoreWorkspace(workspace.id)">恢复</button>
            </article>
            <p v-if="!archivedWorkspaces.length" class="muted">暂无归档工作区。</p>
          </section>

          <section class="manager-panel wide">
            <h3>历史运行副本</h3>
            <button @click="store.loadRunWorkspaces">刷新运行列表</button>
            <article v-for="run in store.runWorkspaces" :key="run.id" class="run-row">
              <button @click="openRun(run.id)">
                <strong>{{ run.name }}</strong>
                <small>{{ run.updated_at ?? '-' }}</small>
              </button>
              <button @click="store.deleteRunWorkspace(run.id, false)">归档 run</button>
              <button class="danger" @click="confirmDeleteRun(run.id, run.name)">永久删除</button>
            </article>
            <p v-if="!store.runWorkspaces.length" class="muted">暂无历史运行。</p>
          </section>
        </div>
      </section>

      <section v-else-if="view === 'settings'" class="settings-view">
        <section class="manager-panel">
          <h2>创建新工作区</h2>
          <form class="form-grid" @submit.prevent="createWorkspace">
            <label>名称<input v-model="createForm.name" placeholder="my-contest" /></label>
            <label>竞赛<input v-model="createForm.contest" /></label>
            <label>论文引擎<input v-model="createForm.engine" /></label>
            <label>语言<input v-model="createForm.language" /></label>
            <label>子问题<input v-model="createForm.subproblems" /></label>
            <label>绘图后端<input v-model="createForm.figure_backend" /></label>
            <button class="primary" type="submit">创建</button>
          </form>
        </section>

        <section class="manager-panel">
          <h2>上传题目和附件</h2>
          <p>上传 PDF、Excel、CSV、图片或数据文件，会保存到当前工作区的 `source/`。</p>
          <input type="file" multiple @change="uploadSource" />
          <div v-if="store.uploadResult" class="notice good">已保存 {{ store.uploadResult.saved.length }} 个文件。</div>
        </section>
      </section>

      <section v-else class="manager-panel">
        <h2>高级诊断</h2>
        <pre>{{ prettyJson({ status: store.langGraphStatus, latestRun: store.langGraphRun }) }}</pre>
      </section>
    </main>

    <div v-if="showHumanGateDialog" class="modal-backdrop" @click.self="showHumanGateDialog = false">
      <section class="gate-modal">
        <header>
          <div>
            <p class="eyebrow">Human Gate</p>
            <h2>先讨论，再写审核结论</h2>
          </div>
          <button @click="showHumanGateDialog = false">关闭</button>
        </header>
        <div class="gate-grid">
          <section>
            <h3>摘要</h3>
            <p>{{ store.humanGateSummary?.summary }}</p>
            <h4>风险</h4>
            <ul>
              <li v-for="risk in store.humanGateSummary?.risks ?? []" :key="risk">{{ risk }}</li>
            </ul>
            <h4>建议问题</h4>
            <button v-for="q in store.humanGateSummary?.suggested_questions ?? []" :key="q" @click="askGate(q)">{{ q }}</button>
          </section>
          <section>
            <h3>和 AI 讨论</h3>
            <textarea v-model="store.humanGateQuestion" rows="4" placeholder="例如：这个模型路线最大风险是什么？"></textarea>
            <button @click="askGate()">提问</button>
            <div v-if="store.humanGateChat" class="assistant-answer">
              <strong>AI 建议</strong>
              <p>{{ store.humanGateChat.answer }}</p>
            </div>
          </section>
          <section>
            <h3>写入人工审核</h3>
            <label>决策
              <select v-model="store.humanGateDecision">
                <option value="needs_revision">需要修改</option>
                <option value="approved">批准进入实验</option>
                <option value="rejected">拒绝当前路线</option>
              </select>
            </label>
            <textarea v-model="store.humanGateReviewNotes" rows="10"></textarea>
            <button class="primary" @click="submitGateReview">写入 HUMAN_MODEL_REVIEW.md</button>
            <p v-if="store.humanGateReviewResult" class="notice good">已写入：{{ store.humanGateReviewResult.written_path }}</p>
          </section>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from "vue";
import { FolderOpen, MessageCircle, PlayCircle, RefreshCw, Settings, ShieldCheck } from "lucide-vue-next";
import { api, type ArtifactReadResponse } from "./api";
import { isRunWorkspacePath, useControlStore } from "./store";

const store = useControlStore();
const view = ref<"home" | "workspaces" | "settings" | "diagnostics">("home");
const showHumanGateDialog = ref(false);
const createForm = ref({
  name: "",
  contest: "待确认",
  engine: "LaTeX",
  language: "中文",
  subproblems: "待确认",
  figure_backend: "matplotlib",
  nature: "not_requested" as "enabled" | "unavailable" | "not_requested",
});

const activeWorkspaces = computed(() => store.workspaces.filter((item) => !item.archived && !isRunWorkspacePath(item.path)));
const archivedWorkspaces = computed(() => store.workspaces.filter((item) => item.archived));
const canRun = computed(() => Boolean(store.selectedWorkspaceId) && !store.langGraphRunning && !store.selectedIsRunWorkspace);
const heroTitle = computed(() => store.selectedWorkspace?.name ?? "选择一个工作区");
const heroSubtitle = computed(() => {
  if (!store.selectedWorkspace) return "先创建或选择一个工作区，然后上传题目和附件。";
  if (store.selectedProvider === "none") return "当前为安全预演模式，不调用真实 API，适合先检查流程。";
  return `当前 Provider: ${store.selectedProvider}，请确认后端环境变量已配置。`;
});
const primaryBlocker = computed(() => {
  const item = store.activity?.primary_blocker;
  if (!item) return null;
  return {
    severity: String(item.severity ?? "INFO"),
    title: String(item.title ?? "下一步"),
    detail: String(item.detail ?? ""),
    artifact: item.artifact ? String(item.artifact) : "",
  };
});
const groupedIssues = computed(() => {
  const groups = new Map<string, { key: string; severity: string; title: string; detail: string; artifact: string; count: number }>();
  for (const item of store.summary?.issues ?? []) {
    const title = String(item.code ?? item.title ?? "issue");
    const detail = String(item.message ?? item.detail ?? item.evidence ?? "");
    const severity = String(item.severity ?? "INFO");
    const artifact = String(item.artifact ?? item.evidence ?? "");
    const key = `${severity}:${title}:${detail}:${artifact}`;
    const group = groups.get(key);
    if (group) group.count += 1;
    else groups.set(key, { key, severity, title, detail, artifact, count: 1 });
  }
  return Array.from(groups.values());
});

async function selectWorkspace() {
  await store.selectWorkspace(store.selectedWorkspaceId);
  await store.loadRunWorkspaces();
}

async function runRecommended() {
  const result = await store.runRecommendedGraph();
  if (result) {
    await store.loadRunWorkspaces();
    await store.refreshActivity();
  }
}

async function openWorkspaceManager() {
  view.value = "workspaces";
  await store.loadRunWorkspaces();
}

async function openArtifact(path: string) {
  await store.openArtifact(path);
}

async function openRun(runId: string) {
  await store.selectRunWorkspace(runId);
  view.value = "diagnostics";
}

async function archiveWorkspace(id: string) {
  if (id !== store.selectedWorkspaceId) {
    await store.selectWorkspace(id);
  }
  await store.archiveSelectedWorkspace();
}

async function confirmDeleteRun(runId: string, runName: string) {
  const typed = window.prompt(`永久删除运行副本请输入名称：${runName}`);
  if (typed === runName) {
    await store.deleteRunWorkspace(runId, true, runName);
  }
}

async function openHumanGate() {
  await store.loadHumanGateSummary();
  showHumanGateDialog.value = true;
}

async function askGate(question?: string) {
  await store.askHumanGate(question);
}

async function submitGateReview() {
  await store.submitHumanGateReview();
}

async function createWorkspace() {
  await store.createWorkspace({ ...createForm.value });
  view.value = "home";
}

async function uploadSource(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.files?.length) {
    await store.uploadSource(input.files);
    input.value = "";
  }
}

function statusTone(value: unknown) {
  const text = String(value ?? "").toLowerCase();
  if (text.includes("pass") || text.includes("ready") || text.includes("none") || text.includes("completed")) return "good";
  if (text.includes("fail") || text.includes("blocker") || text.includes("bad")) return "bad";
  if (text.includes("high") || text.includes("warn") || text.includes("pending") || text.includes("revision")) return "warn";
  return "info";
}

function humanStatus(value: unknown) {
  const raw = String(value ?? "UNKNOWN");
  const labels: Record<string, string> = {
    PASS: "通过",
    FAIL: "失败",
    READY: "就绪",
    REVISION_REQUIRED: "需要修订",
    HUMAN_GATE_REQUIRED: "需要人工确认",
    WAITING_FOR_HUMAN_MODEL_REVIEW: "等待人工审核",
    PHASE2_PLAN_ONLY: "仅生成 Phase 2 计划，未执行实验",
    CONTEST_GRAPH_REVIEW_READY: "流程已到审核态",
  };
  return labels[raw] ?? raw;
}

function shortWorkspacePath(path: string) {
  if (!path) return "未选择";
  const normalized = path.replace(/\\/g, "/");
  const examples = normalized.match(/examples\/(.+)$/i);
  if (examples) return `examples/${examples[1]}`;
  const runs = normalized.match(/runs\/([^/]+)$/i);
  if (runs) return `runs/${runs[1]}`;
  return normalized.split("/").filter(Boolean).slice(-3).join("/");
}

function pathLabel(path: string) {
  return path.split(/[\\/]/).slice(-2).join("/");
}

function prettyJson(value: unknown) {
  return JSON.stringify(value ?? {}, null, 2);
}

function escapeHtml(text: string) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderMarkdown(text: string) {
  return escapeHtml(text)
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br />");
}

const ArtifactPreview = defineComponent({
  props: {
    artifact: { type: Object as () => ArtifactReadResponse | null, default: null },
    workspaceId: { type: String, required: true },
  },
  emits: ["openArtifact"],
  setup(props) {
    return () => {
      const artifact = props.artifact;
      if (!artifact) {
        return h("section", { class: "preview-card" }, [h("h2", "产物预览"), h("p", "点击消息里的文件即可预览。")]);
      }
      const title = h("header", [h("h2", artifact.path), h("small", artifact.absolute_path ?? "")]);
      let body;
      if (!artifact.exists) body = h("p", { class: "muted" }, "文件不存在或尚未生成。");
      else if (artifact.type === "markdown") body = h("div", { class: "markdown-preview", innerHTML: renderMarkdown(artifact.content ?? "") });
      else if (artifact.type === "json" || artifact.type === "text") body = h("pre", { class: "code-preview" }, artifact.content ?? "");
      else if (artifact.type === "image") body = h("img", { class: "media-preview", src: api.rawUrl(props.workspaceId, artifact.path), alt: artifact.path });
      else if (artifact.type === "pdf") body = h("iframe", { class: "pdf-preview", src: api.rawUrl(props.workspaceId, artifact.path) });
      else body = h("p", { class: "muted" }, "此类型暂不支持内嵌预览。");
      return h("section", { class: "preview-card" }, [title, body]);
    };
  },
});

onMounted(async () => {
  await store.initialize();
  await store.loadRunWorkspaces();
});
</script>
