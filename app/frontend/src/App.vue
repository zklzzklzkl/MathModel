<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <strong>MathModel Control</strong>
        <span>V2.7-alpha · LangGraph Runtime</span>
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
          <option v-for="item in store.harnesses" :key="item.id">{{ item.id }}</option>
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
                    <small>{{ phase.next_action }}</small>
                  </span>
                  <span :class="['badge', phase.status_class]">{{ phase.status }}</span>
                </button>
              </div>
            </Panel>

            <Panel title="下一步建议" subtitle="audit + required files">
              <div class="recommendation-list">
                <button
                  v-for="item in store.summary?.recommendations ?? []"
                  :key="`${item.title}-${item.artifact}`"
                  class="recommendation-item"
                  @click="selectRecommendation(item)"
                >
                  <span :class="['badge', statusClass(item.severity)]">{{ item.severity }}</span>
                  <span>
                    <strong>{{ item.title }}</strong>
                    <small>{{ item.detail }}</small>
                  </span>
                </button>
              </div>
              <div class="button-row">
                <button class="primary" @click="store.generateRevisionTasks">生成修订任务</button>
                <button @click="view = 'artifacts'">查看文件</button>
              </div>
            </Panel>
          </div>

          <div class="grid-dashboard second-row">
            <Panel title="审计问题" subtitle="BLOCKER/HIGH first">
              <IssueList :issues="store.summary?.issues ?? []" />
            </Panel>
            <Panel title="修订任务" subtitle="REVISION_ACTIONS_CONTROL.md">
              <div class="task-list">
                <div v-for="task in store.revisionTasks" :key="task.id" class="task-item">
                  <span :class="['badge', statusClass(task.severity)]">{{ task.severity }}</span>
                  <strong>{{ task.id }} · Phase {{ task.phase }}</strong>
                  <small>{{ task.action }}</small>
                </div>
                <div v-if="!store.revisionTasks.length" class="empty">点击“生成修订任务”后显示。</div>
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
              <span :class="['badge', currentPhase?.ready ? 'good' : 'warn']">{{ currentPhase?.ready ? "ready" : "check" }}</span>
            </div>
            <div class="field-grid">
              <div class="field"><label>Skill</label><strong>{{ currentPhase?.skill }}</strong></div>
              <div class="field"><label>Harness</label><strong>{{ harness }}</strong></div>
              <div class="field wide"><label>下一步</label><strong>{{ currentPhase?.next_action }}</strong></div>
            </div>
            <div class="check-grid">
              <div>
                <h3>输入</h3>
                <div v-for="path in currentPhase?.inputs ?? []" :key="path" class="check-row">
                  <span :class="['badge', currentPhase?.missing_inputs.includes(path) ? 'bad' : 'good']">
                    {{ currentPhase?.missing_inputs.includes(path) ? "missing" : "ok" }}
                  </span>
                  <button @click="openArtifact(path)">{{ path }}</button>
                </div>
              </div>
              <div>
                <h3>输出</h3>
                <div v-for="path in currentPhase?.outputs ?? []" :key="path" class="check-row">
                  <span :class="['badge', currentPhase?.missing_outputs.includes(path) ? 'warn' : 'good']">
                    {{ currentPhase?.missing_outputs.includes(path) ? "pending" : "ok" }}
                  </span>
                  <button @click="openArtifact(path)">{{ path }}</button>
                </div>
              </div>
            </div>
            <div class="prompt-box">{{ store.prompt?.phase === selectedPhase ? store.prompt.prompt : "点击生成 Prompt 获取当前阶段执行指令。" }}</div>
            <div class="button-row">
              <button class="primary" @click="store.generatePrompt(selectedPhase, harness)">生成 Prompt</button>
              <button @click="store.prepareHarness(selectedPhase, harness, true)">准备安全副本</button>
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
            <div class="quick-filter-row">
              <button
                v-for="group in ARTIFACT_GROUPS_ORDER"
                :key="group"
                :class="{ active: artifactFilterGroup === group }"
                @click="artifactFilterGroup = artifactFilterGroup === group ? '' : group"
              >
                {{ group }}
              </button>
              <button v-if="artifactFilterGroup" class="clear-filter" @click="artifactFilterGroup = ''">清除</button>
            </div>
            <div class="artifact-list">
              <button v-for="artifact in filteredArtifacts" :key="artifact.path" class="artifact-item" @click="openArtifact(artifact.path)">
                <span><strong>{{ artifact.path }}</strong><small>{{ artifact.type }} · {{ artifact.exists ? "exists" : "missing" }}</small></span>
                <span :class="['badge', artifact.exists ? 'info' : 'bad']">{{ artifact.required ? "required" : "file" }}</span>
              </button>
            </div>
          </Panel>

          <Panel :title="store.selectedArtifact?.path ?? 'Preview'" :subtitle="store.selectedArtifact?.absolute_path ?? ''">
            <div v-if="!store.selectedArtifact" class="empty">未选择文件。</div>
            <div v-else-if="!store.selectedArtifact.exists" class="missing-box">
              <strong>文件不存在</strong>
              <p>{{ missingSuggestion(store.selectedArtifact.path) }}</p>
              <button class="primary" @click="store.generatePrompt(selectedPhase, harness)">生成修复 Prompt</button>
            </div>
            <div v-else-if="store.selectedArtifact.type === 'markdown'" class="markdown-preview" v-html="markdownPreview"></div>
            <pre v-else-if="store.selectedArtifact.type === 'json' || store.selectedArtifact.type === 'text'" class="code-box">{{ artifactPreview }}</pre>
            <img v-else-if="store.selectedArtifact.type === 'image'" class="image-preview" :src="rawUrl(store.selectedArtifact.path)" />
            <div v-else-if="store.selectedArtifact.type === 'pdf'" class="pdf-box">
              <iframe :src="rawUrl(store.selectedArtifact.path)" title="PDF preview"></iframe>
              <a :href="rawUrl(store.selectedArtifact.path)" target="_blank" rel="noreferrer">打开 PDF</a>
            </div>
            <div v-else class="code-box">{{ artifactPreview }}</div>
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
                  <option v-for="item in store.harnesses" :key="item.id">{{ item.id }}</option>
                </select>
              </div>
            </div>
            <div class="button-row">
              <button class="primary" @click="store.generatePrompt(selectedPhase, harness)">生成</button>
              <button @click="store.prepareHarness(selectedPhase, harness, true)">准备安全副本</button>
              <button @click="copyPrompt">复制</button>
            </div>
            <div v-if="store.preparedRun" class="prepared-box">
              <strong>Run workspace</strong>
              <p>{{ store.preparedRun.run_workspace }}</p>
              <strong>Command preview</strong>
              <pre>{{ store.preparedRun.command_preview }}</pre>
            </div>
            <pre class="prompt-box">{{ store.prompt?.prompt ?? "等待生成 Prompt。" }}</pre>
          </Panel>

          <Panel title="运行历史" subtitle="runs/control-center-history.jsonl">
            <div class="history-list">
              <div v-for="entry in reversedHistory" :key="`${entry.timestamp}-${entry.event}`" class="message">
                <strong>{{ entry.timestamp }} · {{ entry.event }}</strong>
                <p>{{ entry.note }}</p>
                <small v-if="entry.run_workspace">{{ entry.run_workspace }}</small>
              </div>
              <div v-if="!store.history.length" class="empty">暂无运行记录。</div>
            </div>
          </Panel>
        </section>

        <section v-else-if="view === 'benchmark'" class="view benchmark-lab">
          <!-- Legacy 2022C -->
          <Panel title="Legacy 2022C Audit Benchmark" subtitle="examples/2022C · audit_benchmark.py">
            <div class="button-row"><button class="primary" @click="store.loadBenchmark">刷新 Benchmark</button></div>
            <div class="table-wrap" style="margin-top:10px">
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

          <!-- LangGraph Benchmark Arena -->
          <Panel title="LangGraph Benchmark Arena" subtitle="contest_graph_v3 provider=none fixture runs">
            <div class="report-card">
              <strong>Fixture Benchmark Report</strong>
              <small>docs/LANGGRAPH_BENCHMARK_REPORT.md · docs/LANGGRAPH_BENCHMARK_REPORT.json</small>
              <p>Pre-computed contest_graph_v3 runs against example workspaces with provider=none. Contains per-workspace contest status, completed phases, Human Gate state, phase-level status table, and final audit severity.</p>
              <div class="button-row">
                <button @click="openArtifact('docs/LANGGRAPH_BENCHMARK_REPORT.md')">查看报告</button>
              </div>
            </div>
          </Panel>

          <!-- Real Provider Benchmark -->
          <Panel title="Real Provider Benchmark" subtitle="DeepSeek Phase 1 llm_plan smoke">
            <div class="report-card" v-for="(label, path) in realBenchmarkReports" :key="path">
              <strong>{{ label }}</strong>
              <small>{{ path }}</small>
              <p>Real API call, validated PhasePlan JSON output. Single-provider Phase 1 planning smoke — no controlled_apply, no experiment, no paper drafting, no final PASS.</p>
            </div>
            <div v-if="!Object.keys(realBenchmarkReports).length" class="empty">docs/real_benchmarks/ 下暂无可展示报告。</div>
          </Panel>

          <!-- Multi-model comparison -->
          <Panel title="Multi-Model Comparison" subtitle="scripts/multi_model_benchmark.py">
            <div class="report-card">
              <strong>Provider comparison reports</strong>
              <small>docs/real_benchmarks/LANGGRAPH_PROVIDER_COMPARISON_*.md</small>
              <p>Run <code>python scripts/multi_model_benchmark.py</code> or <code>python scripts/real_provider_compare.py</code> to generate deterministic multi-provider Phase 1 planning comparisons.</p>
            </div>
          </Panel>
        </section>

        <section v-else-if="view === 'langgraph'" class="view langgraph-layout">
          <!-- Runtime Status -->
          <Panel title="Runtime 状态" subtitle="LangGraph optional dependency">
            <div class="service-row">
              <span><strong>Available</strong><small>{{ store.langGraphStatus?.note ?? "loading..." }}</small></span>
              <span :class="['badge', store.langGraphStatus?.available ? 'good' : 'bad']">
                {{ store.langGraphStatus?.available ? "ready" : "unavailable" }}
              </span>
            </div>
            <div v-if="store.langGraphStatus?.version" class="service-row">
              <span><strong>Version</strong></span>
              <span class="badge info">{{ store.langGraphStatus.version }}</span>
            </div>
            <div v-if="store.langGraphStatus?.import_error" class="warning-box">
              {{ store.langGraphStatus.import_error }}
            </div>
            <div class="button-row" style="margin-top:10px">
              <button @click="store.loadLangGraphStatus">刷新 LangGraph 状态</button>
            </div>
          </Panel>

          <!-- Run Config -->
          <Panel title="Run Config" subtitle="contest_graph_v3 · provider=none 默认安全">
            <div class="warning-box" style="margin-bottom:12px">
              contest_graph_v3 不会自动写 VERIFY_REPORT.md；进入 Phase 2 前必须通过 HUMAN_MODEL_REVIEW.md；建议保持 copy_workspace=true。
            </div>
            <div class="field-grid">
              <div class="field">
                <label>Mode</label>
                <select v-model="store.selectedLangGraphMode">
                  <option v-for="m in LANGGRAPH_MODES" :key="m" :value="m">{{ m }}</option>
                </select>
              </div>
              <div class="field">
                <label>Phase (P0-P6)</label>
                <select v-model.number="store.selectedLangGraphPhase">
                  <option v-for="p in 7" :key="p - 1" :value="p - 1">P{{ p - 1 }}</option>
                </select>
              </div>
              <div class="field">
                <label>Provider</label>
                <select v-model="store.selectedProvider">
                  <option value="none">none</option>
                  <option value="dry-run">dry-run</option>
                  <option value="openai-compatible">openai-compatible</option>
                  <option value="deepseek">deepseek</option>
                </select>
              </div>
              <div class="field">
                <label>Model (optional)</label>
                <input v-model="store.selectedModel" placeholder="deepseek-chat" />
              </div>
              <div class="field">
                <label>Run name (optional)</label>
                <input v-model="store.langGraphRunName" placeholder="ui-contest-graph-v3" />
              </div>
              <div class="field">
                <label>Temperature</label>
                <input v-model.number="store.langGraphTemperature" type="number" step="0.1" min="0" max="2" />
              </div>
              <div class="field">
                <label>Max Tokens</label>
                <input v-model.number="store.langGraphMaxTokens" type="number" step="512" min="512" max="32768" />
              </div>
              <div class="field checkbox-line">
                <label>Copy workspace</label>
                <input v-model="store.langGraphCopyWorkspace" type="checkbox" />
              </div>
            </div>
            <div class="button-row" style="margin-top:10px">
              <button class="primary" :disabled="store.langGraphRunning" @click="store.runLangGraph">
                {{ store.langGraphRunning ? "运行中..." : "Run LangGraph" }}
              </button>
            </div>
            <div v-if="store.langGraphRun?.provider_error" class="warning-box" style="margin-top:10px">
              {{ store.langGraphRun.provider_error }}
            </div>
          </Panel>

          <!-- Run Summary -->
          <Panel title="Run Summary" subtitle="最近一次运行结果">
            <div v-if="!store.langGraphRun" class="empty">尚未运行。请配置 Run Config 后点击 Run LangGraph。</div>
            <div v-else class="field-grid">
              <div class="field"><label>Status</label><span :class="['badge', statusClass(store.langGraphRun.status)]">{{ store.langGraphRun.status }}</span></div>
              <div class="field"><label>Contest Status</label><strong>{{ store.langGraphRun.contest_status ?? "-" }}</strong></div>
              <div class="field"><label>Mode</label><strong>{{ store.langGraphRun.mode }}</strong></div>
              <div class="field"><label>Provider</label><strong>{{ store.langGraphRun.provider }} / {{ store.langGraphRun.model ?? "none" }}</strong></div>
              <div class="field wide"><label>Run Workspace</label><strong style="font-size:12px;word-break:break-all">{{ store.langGraphRun.run_workspace }}</strong></div>
              <div class="field"><label>Completed Phases</label><strong>{{ store.langGraphRun.completed_phases.join(", ") || "-" }}</strong></div>
              <div class="field"><label>Paused At</label><strong>{{ store.langGraphRun.paused_at ?? "-" }}</strong></div>
            </div>
            <div v-if="store.langGraphRun" class="field-grid" style="margin-top:8px">
              <div class="field">
                <label>Human Gate</label>
                <span :class="['badge', store.langGraphRun.human_gate_required ? 'warn' : 'good']">
                  {{ store.langGraphRun.human_gate_required ? "required" : "ok" }}
                </span>
                <small>{{ store.langGraphRun.human_gate_file ?? "HUMAN_MODEL_REVIEW.md" }}</small>
              </div>
              <div class="field">
                <label>Needs Human</label>
                <span :class="['badge', store.langGraphRun.needs_human ? 'warn' : 'good']">
                  {{ store.langGraphRun.needs_human ? "yes" : "no" }}
                </span>
              </div>
            </div>
            <div v-if="store.langGraphRun && (store.langGraphRun.needs_human || store.langGraphRun.human_gate_required)" class="human-gate-alert">
              需要人工确认 HUMAN_MODEL_REVIEW.md
            </div>
          </Panel>

          <!-- Phase Results -->
          <Panel :title="`Phase Results (${store.langGraphRun?.phase_results?.length ?? 0})`" subtitle="graph strategy per phase">
            <div v-if="!store.langGraphRun?.phase_results?.length" class="empty">无 phase results。</div>
            <div v-else class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Phase</th>
                    <th>Strategy</th>
                    <th>Status</th>
                    <th>Sandbox</th>
                    <th>Paper</th>
                    <th>Revision</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in store.langGraphRun.phase_results" :key="idx">
                    <td><span class="badge info">P{{ field(row, ["phase", "phase_id", "id"], "?") }}</span></td>
                    <td>{{ field(row, ["strategy", "mode"], "-") }}</td>
                    <td><span :class="['badge', statusClass(field(row, 'status', 'UNKNOWN'))]">{{ field(row, "status", "-") }}</span></td>
                    <td>{{ field(row, "sandbox_status", "-") }}</td>
                    <td>{{ field(row, "paper_sandbox_status", "-") }}</td>
                    <td>{{ field(row, "revision_sandbox_status", "-") }}</td>
                    <td style="max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ phaseResultNote(row) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Panel>

          <!-- Sandbox / Paper / Revision -->
          <Panel title="Sandbox · Paper · Revision" subtitle="沙箱执行状态">
            <div v-if="!store.langGraphRun" class="empty">尚未运行。</div>
            <div v-else class="field-grid">
              <div class="field"><label>Sandbox</label><strong>{{ store.langGraphRun.sandbox_status ?? "-" }}</strong><small>manifest_created_empty: {{ store.langGraphRun.manifest_created_empty }}</small></div>
              <div class="field"><label>Paper Sandbox</label><strong>{{ store.langGraphRun.paper_sandbox_status ?? "-" }}</strong><small>files: {{ store.langGraphRun.paper_files_written.length }}</small></div>
              <div class="field"><label>Revision Sandbox</label><strong>{{ store.langGraphRun.revision_sandbox_status ?? "-" }}</strong><small>files: {{ store.langGraphRun.revision_files_written.length }}</small></div>
            </div>
            <div v-if="store.langGraphRun" class="path-list" style="margin-top:8px">
              <div v-if="store.langGraphRun.claim_trace_path" class="path-chip" :title="store.langGraphRun.claim_trace_path">Claim Trace: {{ pathChipLabel(store.langGraphRun.claim_trace_path) }}</div>
              <div v-if="store.langGraphRun.method_matrix_path" class="path-chip" :title="store.langGraphRun.method_matrix_path">Method Matrix: {{ pathChipLabel(store.langGraphRun.method_matrix_path) }}</div>
              <div v-if="store.langGraphRun.paper_build_report_path" class="path-chip" :title="store.langGraphRun.paper_build_report_path">Build Report: {{ pathChipLabel(store.langGraphRun.paper_build_report_path) }}</div>
              <div v-if="store.langGraphRun.revision_status_path" class="path-chip" :title="store.langGraphRun.revision_status_path">Revision Status: {{ pathChipLabel(store.langGraphRun.revision_status_path) }}</div>
            </div>
          </Panel>

          <!-- Files -->
          <Panel title="Files" subtitle="planned · written · rejected">
            <div v-if="!store.langGraphRun" class="empty">尚未运行。</div>
            <div v-else class="field-grid">
              <div class="field">
                <label>Files Planned ({{ store.langGraphRun.files_planned.length }})</label>
                <div class="path-list">
                  <div v-for="p in store.langGraphRun.files_planned" :key="p" class="path-chip">{{ p }}</div>
                  <div v-if="!store.langGraphRun.files_planned.length" class="empty" style="padding:6px">none</div>
                </div>
              </div>
              <div class="field">
                <label>Files Written ({{ store.langGraphRun.files_written.length }})</label>
                <div class="path-list">
                  <div v-for="p in store.langGraphRun.files_written" :key="p" class="path-chip">{{ p }}</div>
                  <div v-if="!store.langGraphRun.files_written.length" class="empty" style="padding:6px">none</div>
                </div>
              </div>
              <div class="field wide">
                <label>Files Rejected</label>
                <pre v-if="store.langGraphRun.files_rejected.length" class="code-box" style="max-height:120px">{{ prettyJson(store.langGraphRun.files_rejected) }}</pre>
                <div v-else class="empty" style="padding:6px">none</div>
              </div>
              <div class="field wide">
                <label>Report Paths</label>
                <div class="path-list">
                  <div v-if="store.langGraphRun.report_path" class="path-chip" :title="store.langGraphRun.report_path">Report: {{ pathChipLabel(store.langGraphRun.report_path) }}</div>
                  <div v-if="store.langGraphRun.graph_report_path" class="path-chip" :title="store.langGraphRun.graph_report_path">Graph: {{ pathChipLabel(store.langGraphRun.graph_report_path) }}</div>
                  <div v-if="store.langGraphRun.plan_path" class="path-chip" :title="store.langGraphRun.plan_path">Plan JSON: {{ pathChipLabel(store.langGraphRun.plan_path) }}</div>
                  <div v-if="store.langGraphRun.plan_markdown_path" class="path-chip" :title="store.langGraphRun.plan_markdown_path">Plan MD: {{ pathChipLabel(store.langGraphRun.plan_markdown_path) }}</div>
                  <div v-if="store.langGraphRun.apply_diff_path" class="path-chip" :title="store.langGraphRun.apply_diff_path">Apply Diff: {{ pathChipLabel(store.langGraphRun.apply_diff_path) }}</div>
                  <div v-if="store.langGraphRun.raw_output_path" class="path-chip" :title="store.langGraphRun.raw_output_path">Raw Output: {{ pathChipLabel(store.langGraphRun.raw_output_path) }}</div>
                </div>
              </div>
              <div v-if="store.langGraphRun.paper_files_written.length" class="field">
                <label>Paper Files Written</label>
                <div class="path-list">
                  <div v-for="p in store.langGraphRun.paper_files_written" :key="p" class="path-chip">{{ p }}</div>
                </div>
              </div>
              <div v-if="store.langGraphRun.revision_files_written.length" class="field">
                <label>Revision Files Written</label>
                <div class="path-list">
                  <div v-for="p in store.langGraphRun.revision_files_written" :key="p" class="path-chip">{{ p }}</div>
                </div>
              </div>
            </div>
          </Panel>

          <!-- Audit -->
          <Panel title="Audit" subtitle="pre / post / final">
            <div v-if="!store.langGraphRun" class="empty">尚未运行。</div>
            <div v-else class="field-grid">
              <div class="field">
                <label>Pre Audit</label>
                <pre class="code-box" style="max-height:140px">{{ prettyJson(store.langGraphRun.pre_audit) }}</pre>
              </div>
              <div class="field">
                <label>Post Audit</label>
                <pre class="code-box" style="max-height:140px">{{ prettyJson(store.langGraphRun.post_audit) }}</pre>
              </div>
              <div class="field wide">
                <label>Final Audit</label>
                <pre class="code-box" style="max-height:140px">{{ prettyJson(store.langGraphRun.final_audit) }}</pre>
              </div>
            </div>
            <div v-if="store.langGraphRun?.issues.length" style="margin-top:10px">
              <label>Issues ({{ store.langGraphRun.issues.length }})</label>
              <IssueList :issues="store.langGraphRun.issues" />
            </div>
          </Panel>
        </section>

        <section v-else class="view settings-grid">
          <Panel title="新建工作区" subtitle="scripts/new_v2_workspace.py">
            <form class="form-grid" @submit.prevent="createWorkspace">
              <label>名称<input v-model="createForm.name" placeholder="2026-demo" /></label>
              <label>竞赛<input v-model="createForm.contest" /></label>
              <label>排版引擎<input v-model="createForm.engine" /></label>
              <label>语言<input v-model="createForm.language" /></label>
              <label>子问题<input v-model="createForm.subproblems" /></label>
              <label>绘图后端<input v-model="createForm.figure_backend" /></label>
              <label>Nature
                <select v-model="createForm.nature">
                  <option value="not_requested">not_requested</option>
                  <option value="enabled">enabled</option>
                  <option value="unavailable">unavailable</option>
                </select>
              </label>
              <label class="checkbox-line"><input v-model="createForm.force" type="checkbox" /> force</label>
              <button class="primary" type="submit">创建</button>
            </form>
          </Panel>

          <Panel title="上传 source" subtitle="题面/附件/数据">
            <input type="file" multiple @change="uploadSource" />
            <div v-if="store.uploadResult" class="code-box">saved: {{ store.uploadResult.saved.join(", ") }}
skipped: {{ store.uploadResult.skipped.join(", ") }}</div>
          </Panel>

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

          <Panel title="Harness Adapters" subtitle="prepare only">
            <div v-for="item in store.harnesses" :key="item.id" class="service-row">
              <span><strong>{{ item.label }}</strong><small>{{ item.note }}</small></span>
              <span :class="['badge', item.available ? 'good' : 'bad']">{{ item.managed ? "managed" : "prompt" }}</span>
            </div>
          </Panel>
        </section>
      </main>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { BarChart3, Copy, FileText, Gauge, LayoutDashboard, RefreshCw, Settings, ShieldCheck, TerminalSquare, Workflow } from "lucide-vue-next";
import { api } from "./api";
import { useControlStore } from "./store";
import Panel from "./components/Panel.vue";
import IssueList from "./components/IssueList.vue";

const store = useControlStore();
const view = ref("dashboard");
const selectedPhase = ref(2);
const harness = ref("Manual");
const artifactQuery = ref("");
const createForm = ref({
  name: "",
  contest: "待确认",
  engine: "LaTeX",
  language: "中文",
  subproblems: "待确认",
  figure_backend: "matplotlib",
  nature: "not_requested" as "enabled" | "unavailable" | "not_requested",
  force: false,
});

const navItems = [
  { id: "dashboard", label: "总览", icon: LayoutDashboard },
  { id: "phase", label: "阶段", icon: Gauge },
  { id: "artifacts", label: "文件", icon: FileText },
  { id: "console", label: "执行", icon: TerminalSquare },
  { id: "langgraph", label: "LangGraph", icon: Workflow },
  { id: "benchmark", label: "对标", icon: BarChart3 },
  { id: "settings", label: "设置", icon: Settings },
];

const LANGGRAPH_MODES = [
  "dry_run",
  "llm_plan",
  "controlled_apply",
  "phase_execute",
  "contest_graph_v0",
  "contest_graph_v1",
  "contest_graph_v2",
  "contest_graph_v3",
];

const title = computed(() => navItems.find((item) => item.id === view.value)?.label ?? "MathModel Control");
const currentPhase = computed(() => store.summary?.phases.find((phase) => phase.id === selectedPhase.value));
const filteredArtifacts = computed(() => {
  const query = artifactQuery.value.trim().toLowerCase();
  let pool = store.artifacts;
  if (artifactFilterGroup.value && ARTIFACT_GROUPS[artifactFilterGroup.value]) {
    const tokens = ARTIFACT_GROUPS[artifactFilterGroup.value];
    pool = pool.filter((artifact) => tokens.some((t) => artifact.path.includes(t)));
  }
  if (!query) return pool;
  return pool.filter((artifact) => artifact.path.toLowerCase().includes(query));
});
const artifactPreview = computed(() => {
  const artifact = store.selectedArtifact;
  if (!artifact) return "未选择文件。";
  if (!artifact.exists) return "文件不存在。";
  if (artifact.content) return artifact.content;
  return `${artifact.type}\n${artifact.absolute_path ?? ""}`;
});
const markdownPreview = computed(() => renderMarkdown(store.selectedArtifact?.content ?? ""));
const reversedHistory = computed(() => [...store.history].reverse());
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

const realBenchmarkReports = {
  "docs/real_benchmarks/LANGGRAPH_REAL_BENCHMARK_DeepSeekV4Pro_V2.3.md": "DeepSeek llm_plan Phase 1 · DeepSeekV4Pro_V2.3",
  "docs/real_benchmarks/LANGGRAPH_DEEPSEEK_LLM_PLAN_PHASE1_DeepSeekV4Pro_V2.3.md": "DeepSeek LLM Plan Phase 1 Report",
  "docs/real_benchmarks/LANGGRAPH_REAL_BENCHMARK_DeepSeekV4Pro_V2.3.json": "DeepSeek llm_plan Phase 1 JSON",
  "docs/real_benchmarks/LANGGRAPH_DEEPSEEK_LLM_PLAN_PHASE1_DeepSeekV4Pro_V2.3.json": "DeepSeek LLM Plan Phase 1 JSON",
};

const artifactFilterGroup = ref("");

const ARTIFACT_GROUPS: Record<string, string[]> = {
  "Core Gates": ["HUMAN_MODEL_REVIEW.md", "MODELING_DECISION.md", "VERIFY_REPORT.md"],
  "LangGraph Reports": ["LANGGRAPH_RUN_REPORT.md", "LANGGRAPH_PHASE_PLAN.json", "LANGGRAPH_CONTEST_GRAPH_REPORT.md", "LANGGRAPH_BENCHMARK_REPORT.md", "CONTROL_LANGGRAPH_PHASE_", "AGENT_RUNS.md", "LANGGRAPH_APPLY_DIFF.md", "LANGGRAPH_RAW_MODEL_OUTPUT.md"],
  Evidence: ["RESULTS_MANIFEST.json", "CLAIM_TRACE.md", "METHOD_IMPLEMENTATION_MATRIX.md", "FIGURE_AUDIT.md"],
  Review: ["PAPER_SCORECARD.md", "REVISION_ACTIONS.md", "REVISION_STATUS.md", "REVISION_ACTIONS_CONTROL.md"],
};

const ARTIFACT_GROUPS_ORDER = ["Core Gates", "LangGraph Reports", "Evidence", "Review"];

function statusClass(status: unknown) {
  const value = String(status ?? "").toLowerCase();
  if (value.includes("pass") && !value.includes("fail")) return "good";
  if (value.includes("fail") || value.includes("blocker") || value.includes("missing")) return "bad";
  if (value.includes("high") || value.includes("warn") || value.includes("legacy") || value.includes("pending")) return "warn";
  return "info";
}

function rawUrl(path: string) {
  return store.selectedWorkspaceId ? api.rawUrl(store.selectedWorkspaceId, path) : "";
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

async function createWorkspace() {
  await store.createWorkspace({ ...createForm.value });
}

async function uploadSource(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.files?.length) {
    await store.uploadSource(input.files);
    input.value = "";
  }
}

function selectRecommendation(item: Record<string, unknown>) {
  if (typeof item.phase === "number") {
    selectedPhase.value = item.phase;
    view.value = "phase";
    return;
  }
  if (typeof item.artifact === "string") {
    openArtifact(item.artifact);
  }
}

function missingSuggestion(path: string) {
  if (path.includes("RESULTS_MANIFEST")) return "运行 Phase 2 并生成 metrics/tables/figures/scripts 对象结构。";
  if (path.includes("FIGURE_AUDIT")) return "运行 Phase 2/3，补齐图表审计列和论文插入位置。";
  if (path.includes("PAPER_SCORECARD")) return "运行 Phase 4 竞赛评分审查。";
  return "回到阶段页查看该 artifact 的输入输出要求，并生成对应 Phase Prompt。";
}

function escapeHtml(text: string) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function prettyJson(value: unknown) {
  return JSON.stringify(value ?? {}, null, 2);
}

function field(obj: Record<string, unknown> | null | undefined, keys: string | string[], fallback = "-"): string {
  if (!obj) return fallback;
  const keyList = Array.isArray(keys) ? keys : [keys];
  for (const key of keyList) {
    const value = obj[key];
    if (value !== undefined && value !== null) {
      return typeof value === "string" ? value : String(value);
    }
  }
  return fallback;
}

function phaseResultNote(row: Record<string, unknown>): string {
  const note = field(row, ["note", "notes", "stop_reason", "status"], "");
  const sandbox = field(row, "sandbox_status", "");
  const paper = field(row, "paper_sandbox_status", "");
  const revision = field(row, "revision_sandbox_status", "");
  const parts = [note, sandbox ? `SB:${sandbox}` : "", paper ? `PP:${paper}` : "", revision ? `RV:${revision}` : ""].filter(Boolean);
  return parts.join(" · ") || "-";
}

function pathChipLabel(p: string): string {
  const parts = p.split(/[\\/]/);
  return parts.slice(-2).join("/") || p;
}

function renderMarkdown(text: string) {
  const escaped = escapeHtml(text);
  return escaped
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>")
    .replace(/^\- (.*)$/gm, "<li>$1</li>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br />");
}

onMounted(() => {
  store.initialize();
});
</script>
