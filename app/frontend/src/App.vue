<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <strong>MathModel Control</strong>
        <span>V2.3 workspace shell</span>
      </div>

      <nav class="nav">
        <button v-for="item in navItems" :key="item.id" :class="{ active: view === item.id }" @click="view = item.id">
          <component :is="item.icon" :size="17" />
          {{ item.label }}
        </button>
      </nav>

      <div class="workspace-mini">
        <label>工作区</label>
        <select v-model="store.selectedWorkspaceId" @change="store.selectWorkspace(store.selectedWorkspaceId)">
          <option v-for="workspace in store.workspaces" :key="workspace.id" :value="workspace.id">
            {{ workspace.name }}
          </option>
        </select>
        <label>Harness</label>
        <select v-model="harness">
          <option>Manual</option>
          <option>Codex</option>
          <option>Claude Code</option>
          <option>OpenCode</option>
        </select>
      </div>
    </aside>

    <section class="content">
      <header class="topbar">
        <div class="title-block">
          <h1>{{ title }}</h1>
          <p>{{ store.selectedWorkspace?.path ?? "未选择工作区" }}</p>
        </div>
        <div class="top-actions">
          <button @click="store.initialize"><RefreshCw :size="16" />刷新</button>
          <button @click="store.runAudit"><ShieldCheck :size="16" />运行审计</button>
          <button class="primary" @click="store.generatePrompt(selectedPhase, harness)"><Copy :size="16" />生成 Prompt</button>
        </div>
      </header>

      <main class="main">
        <div v-if="store.error" class="alert">{{ store.error }}</div>
        <div v-if="store.loading" class="loading">正在读取本地工作区...</div>

        <section v-if="view === 'dashboard'" class="view">
          <div class="status-strip">
            <div class="metric">
              <label>Audit</label>
              <strong :class="['badge', statusClass(store.summary?.status)]">{{ store.summary?.status ?? "UNKNOWN" }}</strong>
              <small>Worst: {{ store.summary?.worst_severity ?? "NONE" }}</small>
            </div>
            <div class="metric">
              <label>Manifest</label>
              <strong>{{ store.summary?.manifest.schema ?? "-" }}</strong>
              <small>figures: {{ store.summary?.manifest.figures ?? 0 }}</small>
            </div>
            <div class="metric">
              <label>Paper</label>
              <strong>{{ store.summary?.paper.pdf_count ?? 0 }}</strong>
              <small>PDF files</small>
            </div>
            <div class="metric">
              <label>Missing</label>
              <strong>{{ store.summary?.required_missing.length ?? 0 }}</strong>
              <small>required artifacts</small>
            </div>
          </div>

          <div class="grid-dashboard">
            <Panel title="阶段流" subtitle="Phase 0-6">
              <div class="phase-timeline">
                <button
                  v-for="phase in store.summary?.phases ?? []"
                  :key="phase.id"
                  :class="['phase-row', { selected: selectedPhase === phase.id }]"
                  @click="selectedPhase = phase.id; view = 'phase'"
                >
                  <span class="phase-id">P{{ phase.id }}</span>
                  <span>
                    <strong>{{ phase.name }}</strong>
                    <small>{{ phase.skill }} -> {{ phase.gate }}</small>
                  </span>
                  <span :class="['badge', phase.status_class]">{{ phase.status }}</span>
                </button>
              </div>
            </Panel>

            <Panel title="风险与下一步" subtitle="audit_v2_run.py">
              <IssueList :issues="store.summary?.issues ?? []" />
              <div class="button-row">
                <button class="primary" @click="store.generatePrompt(selectedPhase, harness)">生成修复 Prompt</button>
                <button @click="view = 'artifacts'">查看文件</button>
              </div>
            </Panel>
          </div>
        </section>

        <section v-else-if="view === 'phase'" class="view phase-layout">
          <Panel title="阶段" subtitle="选择工作焦点">
            <div class="phase-list">
              <button
                v-for="phase in store.summary?.phases ?? []"
                :key="phase.id"
                :class="['phase-button', { active: selectedPhase === phase.id }]"
                @click="selectedPhase = phase.id"
              >
                <span class="phase-id">P{{ phase.id }}</span>
                <span>{{ phase.name }}</span>
                <span :class="['badge', phase.status_class]">{{ phase.status }}</span>
              </button>
            </div>
          </Panel>

          <Panel title="阶段详情" :subtitle="currentPhase?.gate ?? 'Gate'">
            <div class="phase-head">
              <h2>{{ currentPhase?.name }}</h2>
              <span :class="['badge', currentPhase?.status_class]">{{ currentPhase?.status }}</span>
            </div>
            <div class="field-grid">
              <div class="field"><label>Skill</label><strong>{{ currentPhase?.skill }}</strong></div>
              <div class="field"><label>Harness</label><strong>{{ harness }}</strong></div>
              <div class="field wide"><label>Gate</label><strong>{{ currentPhase?.gate }}</strong></div>
            </div>
            <div class="prompt-box">{{ store.prompt?.phase === selectedPhase ? store.prompt.prompt : "点击生成 Prompt 获取当前阶段执行指令。" }}</div>
            <div class="button-row">
              <button class="primary" @click="store.generatePrompt(selectedPhase, harness)">生成 Prompt</button>
              <button @click="copyPrompt">复制</button>
            </div>
          </Panel>

          <Panel title="阶段文件" :subtitle="`${currentPhase?.artifacts.length ?? 0} files`">
            <div class="artifact-list">
              <button v-for="path in currentPhase?.artifacts ?? []" :key="path" class="artifact-item" @click="openArtifact(path)">
                <span><strong>{{ path }}</strong><small>phase artifact</small></span>
                <span class="badge info">open</span>
              </button>
            </div>
          </Panel>
        </section>

        <section v-else-if="view === 'artifacts'" class="view artifact-layout">
          <Panel title="Artifact Index" subtitle="workspace truth">
            <input v-model="artifactQuery" class="search" placeholder="搜索 artifact..." />
            <div class="artifact-list">
              <button v-for="artifact in filteredArtifacts" :key="artifact.path" class="artifact-item" @click="openArtifact(artifact.path)">
                <span><strong>{{ artifact.path }}</strong><small>{{ artifact.type }} · {{ artifact.exists ? "exists" : "missing" }}</small></span>
                <span :class="['badge', artifact.exists ? 'info' : 'bad']">{{ artifact.required ? "required" : "file" }}</span>
              </button>
            </div>
          </Panel>

          <Panel :title="store.selectedArtifact?.path ?? 'Preview'" :subtitle="store.selectedArtifact?.absolute_path ?? ''">
            <pre class="code-box">{{ artifactPreview }}</pre>
          </Panel>
        </section>

        <section v-else-if="view === 'console'" class="view console-layout">
          <Panel title="执行 Prompt" subtitle="Manual harness mode">
            <div class="field-grid">
              <div class="field">
                <label>Phase</label>
                <select v-model.number="selectedPhase">
                  <option v-for="phase in store.summary?.phases ?? []" :key="phase.id" :value="phase.id">P{{ phase.id }} {{ phase.name }}</option>
                </select>
              </div>
              <div class="field">
                <label>Harness</label>
                <select v-model="harness">
                  <option>Manual</option>
                  <option>Codex</option>
                  <option>Claude Code</option>
                  <option>OpenCode</option>
                </select>
              </div>
            </div>
            <div class="button-row">
              <button class="primary" @click="store.generatePrompt(selectedPhase, harness)">生成</button>
              <button @click="copyPrompt">复制</button>
            </div>
            <pre class="prompt-box">{{ store.prompt?.prompt ?? "等待生成 Prompt。" }}</pre>
          </Panel>

          <Panel title="运行记录" subtitle="local status">
            <div class="message"><strong>Workspace</strong><p>{{ store.selectedWorkspace?.path }}</p></div>
            <div class="message"><strong>Audit</strong><p>{{ store.summary?.status }} / {{ store.summary?.worst_severity }}</p></div>
            <div class="message"><strong>Manual</strong><p>首版只生成可复制 Prompt，不自动调用 harness。</p></div>
          </Panel>
        </section>

        <section v-else-if="view === 'benchmark'" class="view">
          <Panel title="2022C Benchmark" subtitle="examples/2022C">
            <div class="button-row"><button class="primary" @click="store.loadBenchmark">刷新 Benchmark</button></div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Workspace</th>
                    <th>Status</th>
                    <th>Worst</th>
                    <th>Figures</th>
                    <th>Pages</th>
                    <th>Issues</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in benchmarkRows" :key="row.workspace">
                    <td>{{ row.workspace }}</td>
                    <td><span :class="['badge', statusClass(row.status)]">{{ row.status }}</span></td>
                    <td><span :class="['badge', statusClass(row.worst)]">{{ row.worst }}</span></td>
                    <td>{{ row.figures }}</td>
                    <td>{{ row.pages }}</td>
                    <td>{{ row.issues }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Panel>
        </section>

        <section v-else class="view settings-grid">
          <Panel title="服务健康" subtitle="local backend">
            <div class="service-row">
              <span><strong>Backend</strong><small>Python {{ store.health?.python }}</small></span>
              <span :class="['badge', store.health?.ok ? 'good' : 'bad']">{{ store.health?.ok ? "ready" : "check" }}</span>
            </div>
            <div v-for="(script, name) in store.health?.scripts" :key="name" class="service-row">
              <span><strong>{{ name }}</strong><small>{{ script.path }}</small></span>
              <span :class="['badge', script.exists ? 'good' : 'bad']">{{ script.exists ? "exists" : "missing" }}</span>
            </div>
          </Panel>

          <Panel title="路径" subtitle="configuration">
            <div class="code-box">MATHMODEL_ROOT={{ store.health?.mathmodel_root }}
WORKSPACE_ROOT={{ store.health?.workspace_root }}
EXAMPLES_ROOT={{ store.health?.examples_root }}</div>
          </Panel>
        </section>
      </main>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from "vue";
import { BarChart3, Copy, FileText, Gauge, LayoutDashboard, RefreshCw, Settings, ShieldCheck, TerminalSquare } from "lucide-vue-next";
import { useControlStore } from "./store";

const store = useControlStore();
const view = ref("dashboard");
const selectedPhase = ref(2);
const harness = ref("Manual");
const artifactQuery = ref("");

const navItems = [
  { id: "dashboard", label: "总览", icon: LayoutDashboard },
  { id: "phase", label: "阶段", icon: Gauge },
  { id: "artifacts", label: "文件", icon: FileText },
  { id: "console", label: "执行", icon: TerminalSquare },
  { id: "benchmark", label: "对标", icon: BarChart3 },
  { id: "settings", label: "设置", icon: Settings },
];

const title = computed(() => navItems.find((item) => item.id === view.value)?.label ?? "MathModel Control");
const currentPhase = computed(() => store.summary?.phases.find((phase) => phase.id === selectedPhase.value));
const filteredArtifacts = computed(() => {
  const query = artifactQuery.value.trim().toLowerCase();
  return store.artifacts.filter((artifact) => artifact.path.toLowerCase().includes(query));
});
const artifactPreview = computed(() => {
  const artifact = store.selectedArtifact;
  if (!artifact) return "未选择文件。";
  if (!artifact.exists) return "文件不存在。";
  if (artifact.content) return artifact.content;
  return `${artifact.type}\n${artifact.absolute_path ?? ""}`;
});
const benchmarkRows = computed(() =>
  (store.benchmark?.results ?? []).map((item) => {
    const summary = (item.summary ?? {}) as Record<string, unknown>;
    return {
      workspace: String(item.workspace ?? "").split(/[\\/]/).pop() ?? "",
      status: String(item.status ?? "UNKNOWN"),
      worst: String(item.worst_severity ?? "NONE"),
      figures: Number(summary.figures ?? 0),
      pages: String(summary.paper_pages ?? ""),
      issues: Number(summary.issue_count ?? 0),
    };
  }),
);

function statusClass(status: unknown) {
  const value = String(status ?? "").toLowerCase();
  if (value.includes("pass") && !value.includes("fail")) return "good";
  if (value.includes("fail") || value.includes("blocker") || value.includes("missing")) return "bad";
  if (value.includes("high") || value.includes("warn") || value.includes("legacy") || value.includes("pending")) return "warn";
  return "info";
}

async function openArtifact(path: string) {
  await store.openArtifact(path);
  view.value = "artifacts";
}

async function copyPrompt() {
  if (store.prompt?.prompt) {
    await navigator.clipboard.writeText(store.prompt.prompt);
  }
}

const Panel = defineComponent({
  props: {
    title: { type: String, required: true },
    subtitle: { type: String, default: "" },
  },
  setup(props, { slots }) {
    return () =>
      h("section", { class: "panel" }, [
        h("div", { class: "panel-header" }, [h("h2", props.title), h("span", props.subtitle)]),
        h("div", { class: "panel-body" }, slots.default?.()),
      ]);
  },
});

const IssueList = defineComponent({
  props: {
    issues: { type: Array<Record<string, unknown>>, required: true },
  },
  setup(props) {
    return () =>
      h(
        "div",
        { class: "risk-list" },
        props.issues.length
          ? props.issues.slice(0, 8).map((issue) =>
              h("div", { class: ["risk-item", String(issue.severity ?? "").toLowerCase()] }, [
                h("strong", `${issue.severity ?? "INFO"} - ${issue.code ?? "issue"}`),
                h("p", String(issue.message ?? issue.evidence ?? "")),
              ]),
            )
          : [h("div", { class: "empty" }, "暂无审计问题。")],
      );
  },
});

onMounted(() => {
  store.initialize();
});
</script>
