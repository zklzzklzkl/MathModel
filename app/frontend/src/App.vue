<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <strong>MathModel Control</strong>
        <span>V2.7-alpha · LangGraph Runtime</span>
      </div>

      <nav class="nav">
        <button v-for="item in orderedNavItems" :key="item.id" :class="{ active: view === item.id }" @click="view = item.id">
          <component :is="item.icon" :size="17" />
          {{ navLabel(item.id) }}
        </button>
      </nav>

      <div class="workspace-mini">
        <label>工作区</label>
        <select v-model="store.selectedWorkspaceId" @change="store.selectWorkspace(store.selectedWorkspaceId)">
          <option v-for="workspace in store.workspaces" :key="workspace.id" :value="workspace.id">
            {{ workspaceOptionLabel(workspace) }}
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
          <div class="workspace-context-bar">
            <span :class="['workspace-type-badge', workspaceTypeClass]">{{ workspaceTypeLabel }}</span>
            <span class="workspace-path" :title="store.selectedWorkspace?.path ?? ''">{{ workspaceKindTag }} {{ workspaceDisplayPath }}</span>
            <button v-if="store.selectedWorkspace?.path" class="copy-path-button" :title="store.selectedWorkspace.path" @click="copyWorkspacePath">复制路径</button>
            <span v-if="selectedIsRunWorkspace" class="badge warn">Result context only</span>
          </div>
          <p>{{ store.selectedWorkspace?.path ?? "未选择工作区" }}</p>
        </div>
        <div class="top-actions">
          <button @click="store.initialize"><RefreshCw :size="16" />刷新</button>
          <button @click="store.runAudit"><ShieldCheck :size="16" />运行审计</button>
          <button v-if="view !== 'dashboard'" class="primary top-run-button" :disabled="store.langGraphRunning || selectedIsRunWorkspace" :title="selectedIsRunWorkspace ? runDisabledHelp : ''" @click="runRecommendedFromUi">
            <PlayCircle :size="16" />{{ store.langGraphRunning ? "运行中..." : "Run Recommended" }}
          </button>
        </div>
      </header>

      <main class="main">
        <div v-if="store.error" class="alert">{{ store.error }}</div>
        <div v-if="selectedIsRunWorkspace" class="warning-box workspace-warning">
          当前选择的是 Run Workspace，只适合查看运行结果。再次运行请先选择对应的 Source Workspace。
        </div>
        <div v-if="store.loading" class="loading">正在读取本地工作区...</div>

        <section v-if="view === 'dashboard'" class="view">
          <div v-if="showBeginnerGuide" class="beginner-guide-card">
            <div class="beginner-guide-head">
              <div>
                <span class="badge info">新手模式</span>
                <h2>第一次使用？按这 3 步开始</h2>
              </div>
              <button @click="dismissBeginnerGuide">我知道了，隐藏此提示</button>
            </div>
            <div class="onboarding-steps">
              <div>
                <strong>Step 1：选择或新建工作区</strong>
                <p>一个工作区就是一道数学建模题目的文件夹。</p>
              </div>
              <div>
                <strong>Step 2：上传题目和附件</strong>
                <p>在“设置”页上传 PDF、Excel、CSV、图片等 source 文件。</p>
              </div>
              <div>
                <strong>Step 3：点击 Run Recommended Graph</strong>
                <p>默认 provider=none，不需要 API key，不会花钱，用来验证流程是否跑通。</p>
              </div>
            </div>
            <div v-if="looksLikeFreshWorkspace" class="warning-box">
              看起来还没有完整结果。建议先上传题目和附件，然后点击 Run Recommended Graph 跑一次安全基线。
            </div>
            <div class="button-row">
              <button @click="goUploadSource">去设置页上传题目</button>
              <button class="primary" :disabled="store.langGraphRunning || selectedIsRunWorkspace" :title="selectedIsRunWorkspace ? runDisabledHelp : ''" @click="runRecommendedFromUi">
                Run Recommended Graph
              </button>
              <button @click="openLatestRun">查看运行结果</button>
              <button @click="view = 'help'">查看帮助</button>
            </div>
          </div>

          <div v-if="looksLikeFreshWorkspace" class="empty-state-guide">
            <strong>这个工作区还没有完整结果。</strong>
            <p>建议先上传题目和附件，然后点击 Run Recommended Graph 跑一次安全基线。</p>
            <div class="button-row">
              <button @click="goUploadSource">上传 source</button>
              <button class="primary" :disabled="store.langGraphRunning || selectedIsRunWorkspace" @click="runRecommendedFromUi">Run Recommended Graph</button>
              <button @click="view = 'help'">查看帮助</button>
            </div>
          </div>

          <div class="status-strip">
            <div class="metric">
              <label title="审计检查：发现缺失文件、图表路径、证据链等问题">Audit</label>
              <strong :class="['badge', statusClass(store.summary?.status)]">{{ humanStatus(store.summary?.status ?? "UNKNOWN") }}</strong>
              <small>Raw: {{ store.summary?.status ?? "UNKNOWN" }} · Worst: {{ store.summary?.worst_severity ?? "NONE" }}</small>
            </div>
            <div class="metric">
              <label title="结果清单：记录生成了哪些指标、表格、图像和脚本">Manifest</label>
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

          <div class="primary-action-card">
            <div>
              <span class="badge info">Recommended Action</span>
              <h2>运行 contest_graph_v3 安全基线</h2>
              <p>
                当前推荐：provider=none，不调用真实 API，用于验证流程、安全边界和产物链路。
                provider=none 是安全基线，不代表真实 LLM 建模质量；Human Gate 不会被前端绕过。
              </p>
            </div>
            <div class="action-grid">
              <button class="primary" :disabled="store.langGraphRunning || selectedIsRunWorkspace" :title="selectedIsRunWorkspace ? runDisabledHelp : ''" @click="runRecommendedFromUi">
                <PlayCircle :size="16" />{{ store.langGraphRunning ? "运行中..." : "Run Recommended Graph" }}
              </button>
              <button :disabled="store.langGraphRunning || selectedIsRunWorkspace || !selectedPhaseCanExecute" :title="selectedPhaseRunTitle" @click="runCurrentSkillFromUi">
                <Gauge :size="16" />{{ selectedPhaseCanExecute ? "Run Current Skill" : "Skill Run Unsupported" }}
              </button>
              <button @click="openLatestRun">
                <FolderOpen :size="16" />Open Latest Run
              </button>
            </div>
            <p v-if="!selectedPhaseCanExecute" class="disabled-help">
              当前阶段暂不支持单阶段执行，请使用 Run Recommended Graph 或进入阶段页点击 Dry Run。
            </p>
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
                <div
                  v-for="group in groupedRecommendationItems"
                  :key="group.key"
                  class="recommendation-item recommendation-group"
                >
                  <button class="recommendation-main" @click="selectRecommendation(group.first)">
                    <span :class="['badge', statusClass(group.first.severity)]">{{ group.first.severity }}</span>
                    <span>
                      <strong>{{ group.first.title }}<em v-if="group.count > 1"> × {{ group.count }}</em></strong>
                      <small>{{ group.first.detail }}</small>
                    </span>
                  </button>
                  <details v-if="group.count > 1" class="recommendation-details">
                    <summary>查看 {{ group.count }} 条原始建议</summary>
                    <button
                      v-for="(item, index) in group.items"
                      :key="`${group.key}-${index}`"
                      class="path-pill recommendation-raw"
                      @click="selectRecommendation(item)"
                    >
                      {{ item.artifact ?? item.title ?? item.detail }}
                    </button>
                  </details>
                </div>
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
                  <button class="path-pill" :title="path" @click="openArtifact(path)">{{ path }}</button>
                </div>
              </div>
              <div>
                <h3>输出</h3>
                <div v-for="path in currentPhase?.outputs ?? []" :key="path" class="check-row">
                  <span :class="['badge', currentPhase?.missing_outputs.includes(path) ? 'warn' : 'good']">
                    {{ currentPhase?.missing_outputs.includes(path) ? "pending" : "ok" }}
                  </span>
                  <button class="path-pill" :title="path" @click="openArtifact(path)">{{ path }}</button>
                </div>
              </div>
            </div>
            <div class="button-row">
              <button class="primary" :disabled="store.langGraphRunning || selectedIsRunWorkspace || !selectedPhaseCanExecute" :title="selectedPhaseRunTitle" @click="runCurrentSkillFromUi">
                <PlayCircle :size="16" />{{ store.langGraphRunning ? "运行中..." : recommendedPhaseActionLabel(selectedPhase) }}
              </button>
              <button :disabled="store.langGraphRunning || selectedIsRunWorkspace" :title="selectedIsRunWorkspace ? runDisabledHelp : 'Dry Run 是安全预检，不会正式产出完整结果。'" @click="dryRunSkillFromUi">
                <ShieldCheck :size="16" />Dry Run
              </button>
            </div>
            <p class="muted-help">{{ phaseRunHint(selectedPhase) }}</p>
            <p v-if="!selectedPhaseCanExecute" class="human-status-note">
              单阶段执行暂不可用；可 Dry Run 预检，或运行完整 contest_graph_v3。
            </p>
            <details class="advanced-tools">
              <summary>Advanced Tools</summary>
              <div class="prompt-box">{{ store.prompt?.phase === selectedPhase ? store.prompt.prompt : "使用 Generate Prompt 生成当前阶段手动执行指令。" }}</div>
              <div class="button-row">
                <button @click="store.generatePrompt(selectedPhase, harness)">Generate Prompt</button>
                <button @click="store.prepareHarness(selectedPhase, harness, true)">Prepare Harness Copy</button>
                <button @click="copyPrompt">Copy Prompt</button>
              </div>
            </details>
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
          <Panel title="Artifact Index" :subtitle="artifactContextSubtitle">
            <p v-if="selectedIsRunWorkspace" class="human-status-note">当前查看的是运行产物，不是原始题目工作区。</p>
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
              <button @click="view = 'console'">打开高级 Prompt 工具</button>
            </div>
            <div v-else-if="store.selectedArtifact.type === 'directory'" class="directory-box">
              <strong>目录</strong>
              <p>这是一个目录。请从左侧文件索引选择具体文件查看内容。</p>
              <div v-if="directoryChildArtifacts.length" class="artifact-list">
                <button v-for="artifact in directoryChildArtifacts" :key="artifact.path" class="artifact-item" @click="openArtifact(artifact.path)">
                  <span><strong>{{ artifact.path }}</strong><small>{{ artifact.type }} · {{ artifact.exists ? "exists" : "missing" }}</small></span>
                  <span class="badge info">open</span>
                </button>
              </div>
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
          <Panel title="高级手动工具" subtitle="Prompt / Harness 调试流程">
            <p class="muted-help">
              这里保留 Prompt/Harness 工作流，用于调试或外部 Agent 手动执行。普通使用请优先使用 Run Recommended 或 Run This Skill。
            </p>
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
              <button @click="store.generatePrompt(selectedPhase, harness)">Generate Prompt</button>
              <button @click="store.prepareHarness(selectedPhase, harness, true)">Prepare Harness Copy</button>
              <button @click="copyPrompt">Copy Prompt</button>
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

        <!-- Runs page -->
        <section v-else-if="view === 'runs'" class="view runs-layout">
          <Panel title="Run Workspaces" :subtitle="`${store.runWorkspaces.length} runs`">
            <div class="button-row" style="margin-bottom:10px">
              <button class="primary" @click="store.loadRunWorkspaces">刷新 Runs</button>
            </div>
            <div v-if="!store.runWorkspaces.length" class="empty">暂无 run workspace。运行 LangGraph 后将在此显示。</div>
            <div v-else class="run-workspace-list">
              <button
                v-for="run in store.runWorkspaces"
                :key="run.id"
                :class="['artifact-item', { selected: store.selectedRunWorkspaceId === run.id }]"
                @click="store.selectRunWorkspace(run.id)"
              >
                <span>
                  <strong>{{ run.name }}</strong>
                  <small>{{ run.updated_at ?? '-' }}</small>
                </span>
                <span class="badge-group">
                  <span v-if="run.has_langgraph_report" class="badge good">LG</span>
                  <span v-if="run.has_agent_runs" class="badge info">AR</span>
                  <span v-if="run.has_phase_plan" class="badge warn">PP</span>
                </span>
              </button>
            </div>
          </Panel>

          <Panel :title="`Run Artifacts (${filteredRunArtifacts.length})`" subtitle="只读 · run workspace">
            <div v-if="!store.selectedRunWorkspaceId" class="empty">请先选择一个 run workspace。</div>
            <div v-else>
              <input v-model="artifactQuery" class="search" placeholder="搜索..." />
              <div class="quick-filter-row">
                <button
                  v-for="group in RUN_ARTIFACT_GROUPS_ORDER"
                  :key="group"
                  :class="{ active: runArtifactFilterGroup === group }"
                  @click="runArtifactFilterGroup = runArtifactFilterGroup === group ? '' : group"
                >{{ group }}</button>
                <button v-if="runArtifactFilterGroup" class="clear-filter" @click="runArtifactFilterGroup = ''">清除</button>
              </div>
              <div class="artifact-list" style="max-height:400px;overflow:auto">
                <button
                  v-for="artifact in filteredRunArtifacts"
                  :key="artifact.path"
                  class="artifact-item"
                  @click="store.openRunArtifact(artifact.path)"
                >
                  <span><strong>{{ artifact.path }}</strong><small>{{ artifact.type }} · {{ artifact.size }} bytes</small></span>
                  <span :class="['badge', artifact.exists ? 'info' : 'bad']">{{ artifact.exists ? "file" : "missing" }}</span>
                </button>
              </div>
            </div>
          </Panel>

          <Panel :title="store.selectedRunArtifact?.path ?? 'Preview'" :subtitle="store.selectedRunArtifact?.absolute_path ?? ''">
            <div v-if="!store.selectedRunArtifact" class="empty">未选择文件。</div>
            <div v-else-if="!store.selectedRunArtifact.exists" class="missing-box">
              <strong>文件不存在</strong>
            </div>
            <div v-else-if="store.selectedRunArtifact.type === 'markdown'" class="markdown-preview" v-html="renderMarkdown(store.selectedRunArtifact.content ?? '')"></div>
            <pre v-else-if="store.selectedRunArtifact.type === 'json' || store.selectedRunArtifact.type === 'text'" class="code-box">{{ store.selectedRunArtifact.content }}</pre>
            <img v-else-if="store.selectedRunArtifact.type === 'image' && store.selectedWorkspaceId && store.selectedRunWorkspaceId" class="image-preview" :src="api.runRawUrl(store.selectedWorkspaceId, store.selectedRunWorkspaceId, store.selectedRunArtifact.path)" />
            <div v-else-if="store.selectedRunArtifact.type === 'pdf' && store.selectedWorkspaceId && store.selectedRunWorkspaceId" class="pdf-box">
              <iframe :src="api.runRawUrl(store.selectedWorkspaceId, store.selectedRunWorkspaceId, store.selectedRunArtifact.path)" title="PDF preview"></iframe>
            </div>
            <div v-else class="code-box">{{ store.selectedRunArtifact.content ?? 'binary file' }}</div>
          </Panel>
        </section>

        <section v-else-if="view === 'benchmark'" class="view benchmark-lab">
          <!-- Overview -->
          <Panel title="评测实验室（Benchmark Lab）" subtitle="报告浏览器 · 只读">
            <!-- Safe Benchmark Launcher -->
            <div class="safe-benchmark-card">
              <strong>安全评测基线（provider=none）</strong>
              <p style="margin:4px 0 8px;color:var(--muted);font-size:12px">此按钮只运行 provider=none 安全基线，不调用真实 API，不代表真实 LLM 自动效果。mode 固定为 contest_graph_v3，provider 固定为 none，copy_workspace 固定为 true。</p>
              <div class="button-row">
                <button class="primary" :disabled="store.safeBenchmarkRunning || selectedIsRunWorkspace" :title="selectedIsRunWorkspace ? runDisabledHelp : ''" @click="store.runSafeLangGraphBenchmark">
                  {{ store.safeBenchmarkRunning ? "运行中..." : "运行 provider=none 安全评测" }}
                </button>
              </div>
              <p v-if="selectedIsRunWorkspace" class="disabled-help">{{ runDisabledHelp }}</p>
              <div v-if="store.safeBenchmarkResult" style="margin-top:10px" class="field-grid">
                <div class="field"><label>Status</label><span :class="['badge', statusClass(store.safeBenchmarkResult.status)]">{{ humanStatus(store.safeBenchmarkResult.status) }}</span><small>Raw: {{ store.safeBenchmarkResult.status }}</small></div>
                <div class="field"><label>Contest Status</label><strong>{{ humanStatus(store.safeBenchmarkResult.contest_status ?? '-') }}</strong><small>Raw: {{ store.safeBenchmarkResult.contest_status ?? '-' }}</small></div>
                <div class="field"><label>Run Workspace</label><strong style="font-size:11px;word-break:break-all">{{ store.safeBenchmarkResult.run_workspace }}</strong></div>
                <div class="field"><label>Completed Phases</label><strong>{{ store.safeBenchmarkResult.completed_phases.join(", ") || '-' }}</strong></div>
                <div class="field"><label>Sandbox</label><strong>{{ store.safeBenchmarkResult.sandbox_status ?? '-' }}</strong></div>
                <div class="field"><label>Paper Sandbox</label><strong>{{ store.safeBenchmarkResult.paper_sandbox_status ?? '-' }}</strong></div>
                <div class="field"><label>Revision Sandbox</label><strong>{{ store.safeBenchmarkResult.revision_sandbox_status ?? '-' }}</strong></div>
                <div class="field"><label>Final Audit</label><span :class="['badge', statusClass(store.safeBenchmarkResult.final_audit?.worst_severity)]">{{ store.safeBenchmarkResult.final_audit?.worst_severity ?? 'NONE' }}</span></div>
              </div>
            </div>
            <!-- /Safe Benchmark Launcher -->
            <div class="status-strip">
              <div class="metric">
                <label>Total</label>
                <strong>{{ store.benchmarkReports.length }}</strong>
                <small>benchmark reports</small>
              </div>
              <div class="metric">
                <label>Provider</label>
                <strong>{{ store.benchmarkReports.filter(r => r.category === 'provider').length }}</strong>
                <small>DeepSeek / OpenAI</small>
              </div>
              <div class="metric">
                <label>Multi-Model</label>
                <strong>{{ store.benchmarkReports.filter(r => r.category === 'multi_model').length }}</strong>
                <small>comparison reports</small>
              </div>
              <div class="metric">
                <label>Real WS</label>
                <strong>{{ store.benchmarkReports.filter(r => r.category === 'real_workspace').length }}</strong>
                <small>workspace benchmarks</small>
              </div>
            </div>
            <div class="button-row">
              <button class="primary" @click="store.loadBenchmarkReports">刷新报告</button>
              <button @click="store.loadBenchmark">刷新 Legacy 2022C</button>
            </div>
          </Panel>

          <!-- Report List -->
          <Panel :title="`报告列表 (${filteredBenchmarkReports.length})`" subtitle="点击选中查看详情">
            <div class="filter-row">
              <label>Category
                <select v-model="store.benchmarkCategoryFilter">
                  <option value="all">all</option>
                  <option value="legacy">legacy</option>
                  <option value="fixture">fixture</option>
                  <option value="real_workspace">real_workspace</option>
                  <option value="provider">provider</option>
                  <option value="multi_model">multi_model</option>
                </select>
              </label>
              <label>Provider
                <select v-model="store.benchmarkProviderFilter">
                  <option value="all">all</option>
                  <option value="deepseek">deepseek</option>
                  <option value="openai-compatible">openai-compatible</option>
                  <option value="none">none</option>
                </select>
              </label>
            </div>
            <div class="artifact-list" style="max-height:420px;overflow:auto">
              <button
                v-for="report in filteredBenchmarkReports"
                :key="report.id"
                :class="['artifact-item', { selected: store.selectedBenchmarkReportId === report.id }]"
                @click="store.openBenchmarkReport(report.id)"
              >
                <span><strong>{{ report.title }}</strong><small>{{ report.category }} · {{ report.provider ?? '-' }} · {{ report.mode ?? '-' }}</small></span>
                <span :class="['badge', report.type === 'json' ? 'info' : 'warn']">{{ report.type }}</span>
              </button>
              <div v-if="!filteredBenchmarkReports.length" class="empty">暂无报告。点击"刷新报告"加载。</div>
            </div>
          </Panel>

          <!-- Report Preview -->
          <Panel :title="store.selectedBenchmarkReport?.title ?? '报告预览'" :subtitle="store.selectedBenchmarkReport?.path ?? ''">
            <div v-if="!store.selectedBenchmarkReport" class="empty">请从报告列表中选择一份报告。</div>
            <div v-else class="report-meta">
              <span :class="['badge', store.selectedBenchmarkReport.type === 'json' ? 'info' : 'warn']">{{ store.selectedBenchmarkReport.type }}</span>
              <span class="badge info">{{ store.selectedBenchmarkReport.category }}</span>
              <span v-if="store.selectedBenchmarkReport.provider" class="badge">{{ store.selectedBenchmarkReport.provider }}</span>
              <span v-if="store.selectedBenchmarkReport.mode" class="badge">{{ store.selectedBenchmarkReport.mode }}</span>
            </div>
            <div v-if="store.selectedBenchmarkReport" style="margin-top:12px">
              <div v-if="store.selectedBenchmarkReport.type === 'json' && store.selectedBenchmarkReport.summary" class="field-grid" style="margin-bottom:10px">
                <div class="field" v-for="(val, key) in store.selectedBenchmarkReport.summary" :key="key">
                  <label>{{ key }}</label>
                  <strong>{{ typeof val === 'object' ? prettyJson(val) : String(val) }}</strong>
                </div>
              </div>
              <div v-if="store.selectedBenchmarkReport.type === 'markdown'" class="markdown-preview" v-html="renderMarkdown(store.selectedBenchmarkReport.content)"></div>
              <pre v-else class="code-box" style="max-height:55vh">{{ prettyJson(store.selectedBenchmarkReport.data ?? store.selectedBenchmarkReport.content) }}</pre>
            </div>
          </Panel>

          <!-- Multi-Model Compare -->
          <Panel title="多模型对比" subtitle="metadata-level comparison">
            <div v-if="!store.benchmarkReports.length" class="empty">加载报告列表后自动生成。</div>
            <div v-else class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Report</th>
                    <th>Provider</th>
                    <th>Mode</th>
                    <th>Workspace</th>
                    <th>Category</th>
                    <th>Size</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="report in filteredBenchmarkReports" :key="report.id" @click="store.openBenchmarkReport(report.id)" style="cursor:pointer">
                    <td :class="{ 'phase-row selected': store.selectedBenchmarkReportId === report.id }"><strong>{{ report.title }}</strong></td>
                    <td>{{ report.provider ?? '-' }}</td>
                    <td><span class="badge info">{{ report.mode ?? '-' }}</span></td>
                    <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ report.workspace ?? '-' }}</td>
                    <td><span :class="['badge', report.category === 'provider' ? 'good' : report.category === 'multi_model' ? 'warn' : 'info']">{{ report.category }}</span></td>
                    <td>{{ report.size ? (report.size / 1024).toFixed(1) + 'k' : '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="store.selectedBenchmarkReport?.type === 'json' && Object.keys(store.selectedBenchmarkReport.summary).length" style="margin-top:12px">
              <label>选中的报告对比摘要</label>
              <div class="field-grid">
                <div class="field" v-for="(val, key) in store.selectedBenchmarkReport.summary" :key="key">
                  <label>{{ key }}</label>
                  <strong>{{ typeof val === 'object' ? prettyJson(val) : String(val) }}</strong>
                </div>
              </div>
            </div>
          </Panel>

          <!-- Legacy 2022C -->
          <Panel title="旧版 2022C 审计评测" subtitle="examples/2022C · audit_benchmark.py">
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
                    <td><span :class="['badge', statusClass(row.status)]">{{ humanStatus(row.status) }}</span><small>{{ row.status }}</small></td>
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
          <Panel title="LangGraph 评测竞技场" subtitle="contest_graph_v3 provider=none fixture runs">
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
          <Panel title="真实 Provider 评测" subtitle="DeepSeek Phase 1 llm_plan smoke">
            <div class="report-card" v-for="(label, path) in realBenchmarkReports" :key="path">
              <strong>{{ label }}</strong>
              <small>{{ path }}</small>
              <p>Real API call, validated PhasePlan JSON output. Single-provider Phase 1 planning smoke — no controlled_apply, no experiment, no paper drafting, no final PASS.</p>
            </div>
            <div v-if="!Object.keys(realBenchmarkReports).length" class="empty">docs/real_benchmarks/ 下暂无可展示报告。</div>
          </Panel>

          <!-- Multi-model comparison -->
          <Panel title="多模型对比" subtitle="scripts/multi_model_benchmark.py">
            <div class="report-card">
              <strong>Provider comparison reports</strong>
              <small>docs/real_benchmarks/LANGGRAPH_PROVIDER_COMPARISON_*.md</small>
              <p>Run <code>python scripts/multi_model_benchmark.py</code> or <code>python scripts/real_provider_compare.py</code> to generate deterministic multi-provider Phase 1 planning comparisons.</p>
            </div>
          </Panel>
        </section>

        <section v-else-if="view === 'langgraph'" class="view langgraph-layout">
          <div class="compact-runtime-bar">
            <span><strong>LangGraph:</strong> {{ store.langGraphStatus?.available ? "ready" : "unavailable" }}</span>
            <span v-if="store.langGraphStatus?.version">version {{ store.langGraphStatus.version }}</span>
            <span>modes: contest_graph_v3 available</span>
            <button @click="store.loadLangGraphStatus">刷新</button>
            <details>
              <summary>Runtime details</summary>
              <div class="runtime-details">
                <span>{{ store.langGraphStatus?.note ?? "loading..." }}</span>
                <span v-if="store.langGraphStatus?.import_error">{{ store.langGraphStatus.import_error }}</span>
              </div>
            </details>
          </div>
          <!-- Runtime Status -->
          <Panel v-if="false" title="Runtime 状态" subtitle="LangGraph optional dependency">
            <div class="service-row">
              <span><strong>Available</strong><small>{{ store.langGraphStatus?.note ?? "loading..." }}</small></span>
              <span :class="['badge', store.langGraphStatus?.available ? 'good' : 'bad']">
                {{ store.langGraphStatus?.available ? "ready" : "unavailable" }}
              </span>
            </div>
            <div v-if="store.langGraphStatus?.version" class="service-row">
              <span><strong>Version</strong></span>
              <span class="badge info">{{ store.langGraphStatus?.version }}</span>
            </div>
            <div v-if="store.langGraphStatus?.import_error" class="warning-box">
              {{ store.langGraphStatus?.import_error }}
            </div>
            <div class="button-row" style="margin-top:10px">
              <button @click="store.loadLangGraphStatus">刷新 LangGraph 状态</button>
            </div>
          </Panel>

          <!-- Recommended Run -->
          <Panel title="Run Recommended" subtitle="contest_graph_v3 · provider=none · copy_workspace=true">
            <div class="primary-action-card compact">
              <div>
                <span class="badge info">Safe baseline</span>
                <h2>contest_graph_v3</h2>
                <p>
                  mode=contest_graph_v3, provider=none, copy_workspace=true。它验证流程、安全边界和产物链路；
                  不调用真实 API，不代表真实 LLM 建模质量，不会绕过 Human Gate，也不会自动写 VERIFY_REPORT.md。
                </p>
              </div>
              <div class="action-grid">
                <button class="primary" :disabled="store.langGraphRunning || selectedIsRunWorkspace" :title="selectedIsRunWorkspace ? runDisabledHelp : ''" @click="runRecommendedFromUi">
                  <PlayCircle :size="16" />{{ store.langGraphRunning ? "运行中..." : "Run Recommended" }}
                </button>
                <button @click="openLatestRun"><FolderOpen :size="16" />Open Latest Run</button>
              </div>
            </div>

            <details class="advanced-tools">
              <summary>Advanced Run Config</summary>
              <div class="warning-box" style="margin-bottom:12px">
                Advanced config is for debugging provider/model behavior. Keep copy_workspace=true unless you are intentionally inspecting a copied run.
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
                <button :disabled="store.langGraphRunning || selectedIsRunWorkspace" :title="selectedIsRunWorkspace ? runDisabledHelp : ''" @click="store.runLangGraph">
                  {{ store.langGraphRunning ? "运行中..." : "Run Custom Config" }}
                </button>
              </div>
            </details>
            <div v-if="store.langGraphRun?.provider_error" class="warning-box" style="margin-top:10px">
              {{ store.langGraphRun.provider_error }}
            </div>
          </Panel>

          <Panel title="Human Gate" subtitle="HUMAN_MODEL_REVIEW.md remains manual">
            <div class="field-grid">
              <div class="field">
                <label>Gate State</label>
                <span :class="['badge', humanGateStatus.className]">{{ humanGateStatus.label }}</span>
                <small>{{ store.langGraphRun?.human_gate_file ?? "reports/HUMAN_MODEL_REVIEW.md" }}</small>
              </div>
              <div class="field">
                <label>Safety</label>
                <strong>Manual approval only</strong>
                <small>前端不会写 HUMAN_MODEL_REVIEW.md / MODELING_DECISION.md / VERIFY_REPORT.md。</small>
              </div>
            </div>
            <p class="human-status-note">{{ humanGateStatus.note }}</p>
            <div v-if="store.langGraphRun && (store.langGraphRun.needs_human || store.langGraphRun.human_gate_required)" class="human-gate-alert">
              需要人工确认 HUMAN_MODEL_REVIEW.md 后才能继续危险阶段。
            </div>
          </Panel>

          <!-- Run Summary -->
          <Panel title="Latest Run Summary" subtitle="最近一次运行结果">
            <div v-if="!store.langGraphRun" class="empty">尚未运行。点击 Run Recommended 后将在这里显示最新摘要。</div>
            <div v-else class="field-grid">
              <div class="field"><label>Status</label><span :class="['badge', statusClass(store.langGraphRun.status)]">{{ humanStatus(store.langGraphRun.status) }}</span><small>Raw: {{ store.langGraphRun.status }}</small></div>
              <div class="field"><label>Contest Status</label><strong>{{ humanStatus(store.langGraphRun.contest_status ?? "-") }}</strong><small>Raw: {{ store.langGraphRun.contest_status ?? "-" }}</small></div>
              <div class="field"><label>Mode</label><strong>{{ store.langGraphRun.mode }}</strong></div>
              <div class="field"><label>Provider</label><strong>{{ store.langGraphRun.provider }} / {{ store.langGraphRun.model ?? "none" }}</strong></div>
              <div class="field wide"><label>Run Workspace</label><strong style="font-size:12px;word-break:break-all">{{ store.langGraphRun.run_workspace }}</strong></div>
              <div class="field"><label>Completed Phases</label><strong>{{ store.langGraphRun.completed_phases.join(", ") || "-" }}</strong></div>
              <div class="field"><label>Paused At</label><strong>{{ store.langGraphRun.paused_at ?? "-" }}</strong></div>
            </div>
            <div v-if="store.langGraphRun" class="field-grid" style="margin-top:8px">
              <div class="field">
                <label>Needs Human</label>
                <span :class="['badge', store.langGraphRun.needs_human ? 'warn' : 'good']">
                  {{ store.langGraphRun.needs_human ? "yes" : "no" }}
                </span>
              </div>
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
                  <tr v-for="(row, idx) in (store.langGraphRun?.phase_results ?? [])" :key="idx">
                    <td><span class="badge info">P{{ field(row, ["phase", "phase_id", "id"], "?") }}</span></td>
                    <td>{{ field(row, ["strategy", "mode"], "-") }}</td>
                    <td><span :class="['badge', statusClass(field(row, 'status', 'UNKNOWN'))]">{{ humanStatus(field(row, "status", "-")) }}</span><small>{{ field(row, "status", "-") }}</small></td>
                    <td>{{ humanStatus(field(row, "sandbox_status", "-")) }}</td>
                    <td>{{ humanStatus(field(row, "paper_sandbox_status", "-")) }}</td>
                    <td>{{ humanStatus(field(row, "revision_sandbox_status", "-")) }}</td>
                    <td style="max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" :title="phaseResultNote(row)">{{ phaseResultNote(row) }}</td>
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
              <div class="field"><label>Paper Sandbox</label><strong>{{ store.langGraphRun.paper_sandbox_status ?? "-" }}</strong><small>files: {{ store.langGraphRun.paper_files_written?.length ?? 0 }}</small></div>
              <div class="field"><label>Revision Sandbox</label><strong>{{ store.langGraphRun.revision_sandbox_status ?? "-" }}</strong><small>files: {{ store.langGraphRun.revision_files_written?.length ?? 0 }}</small></div>
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
              <div v-if="(store.langGraphRun.paper_files_written?.length ?? 0)" class="field">
                <label>Paper Files Written</label>
                <div class="path-list">
                  <div v-for="p in (store.langGraphRun.paper_files_written ?? [])" :key="p" class="path-chip">{{ p }}</div>
                </div>
              </div>
              <div v-if="(store.langGraphRun.revision_files_written?.length ?? 0)" class="field">
                <label>Revision Files Written</label>
                <div class="path-list">
                  <div v-for="p in (store.langGraphRun.revision_files_written ?? [])" :key="p" class="path-chip">{{ p }}</div>
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

        <section v-else-if="view === 'help'" class="view help-page">
          <Panel title="帮助" subtitle="第一次使用 Control Center">
            <div class="help-section">
              <h3>快速开始</h3>
              <ol>
                <li>在“设置”页新建工作区。</li>
                <li>上传题目 PDF 和附件数据。</li>
                <li>回到“总览”。</li>
                <li>点击 Run Recommended Graph。</li>
                <li>去“运行结果”查看每次运行生成的报告。</li>
                <li>去“文件”查看当前工作区的论文、结果清单和审计报告。</li>
              </ol>
            </div>
            <div class="help-section">
              <h3>按钮说明</h3>
              <div class="glossary-grid">
                <div><strong>Run Recommended Graph</strong><p>运行推荐完整流程。默认 provider=none，不调用真实 API，不会花钱，用于安全验证流程。</p></div>
                <div><strong>Run Current Skill</strong><p>只运行当前阶段。当前 Runtime 只支持 P1/P4 单阶段执行，其它阶段请使用 Dry Run 或完整流程。</p></div>
                <div><strong>Dry Run</strong><p>只做预检，检查流程和文件路径，不代表正式建模结果。</p></div>
                <div><strong>Open Latest Run</strong><p>打开最近一次运行的产物文件夹。</p></div>
                <div><strong>运行审计</strong><p>检查当前工作区文件是否完整，是否存在缺失结果、图表路径、论文证据链问题。</p></div>
              </div>
            </div>
            <div class="help-section">
              <h3>术语解释</h3>
              <div class="glossary-grid">
                <div><strong>Workspace / 工作区</strong><p>一道题目的项目文件夹，包含 source、code、paper、results、reports 等目录。</p></div>
                <div><strong>Source Workspace</strong><p>原始题目工作区。推荐在这里启动运行。</p></div>
                <div><strong>Run Workspace</strong><p>每次运行复制出来的安全副本。主要用于查看结果，不建议在里面再次运行。</p></div>
                <div><strong>LangGraph</strong><p>负责把数学建模流程按阶段串起来的执行器。</p></div>
                <div><strong>contest_graph_v3</strong><p>当前推荐的完整安全流程。</p></div>
                <div><strong>Skill</strong><p>某个阶段的能力模块，例如建模策略、实验可视化、论文构建、评分审查。</p></div>
                <div><strong>Human Gate</strong><p>人工确认闸门。进入高风险阶段前必须人工确认模型选择和建模方案。</p></div>
                <div><strong>provider=none</strong><p>不调用真实大模型 API 的安全基线。不会花钱，用于验证流程和产物链路。</p></div>
                <div><strong>API key</strong><p>真实调用 DeepSeek / OpenAI-compatible 模型时需要的密钥。provider=none 不需要。</p></div>
                <div><strong>Audit</strong><p>审计检查，用于发现文件缺失、图表路径错误、证据链缺失等问题。</p></div>
                <div><strong>Manifest</strong><p>结果清单，记录生成了哪些指标、表格、图像和脚本。</p></div>
                <div><strong>Benchmark</strong><p>评测，用已有工作区或报告检查系统稳定性和不同模型表现。</p></div>
              </div>
            </div>
            <div class="help-section">
              <h3>API 配置说明</h3>
              <p>默认情况下可以不配置 API。provider=none 可以跑安全基线，不会产生真实模型质量结果。</p>
              <p>当你想让 DeepSeek / OpenAI-compatible 真正生成建模计划、代码、论文内容，或比较不同模型效果时，才需要 API key。</p>
              <p><strong>API key 应配置在后端运行环境中，不要粘贴到浏览器页面。</strong>配置后需要重启后端服务。</p>
              <pre class="code-box">DeepSeek 示例：
DEEPSEEK_API_KEY=你的密钥

OpenAI-compatible 示例：
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=兼容接口地址</pre>
            </div>
            <div class="help-section">
              <h3>常见问题</h3>
              <div class="faq-item"><strong>Q：不配置 API 能用吗？</strong><p>A：能。默认 provider=none 可以验证流程和安全边界，但不代表真实 LLM 建模效果。</p></div>
              <div class="faq-item"><strong>Q：Run Recommended 会花钱吗？</strong><p>A：默认 provider=none 不会调用真实 API，因此不会产生模型调用费用。</p></div>
              <div class="faq-item"><strong>Q：为什么 Run This Skill 按钮不可用？</strong><p>A：当前单阶段执行只支持 P1/P4，其它阶段请用 Dry Run 或完整 contest_graph_v3。</p></div>
              <div class="faq-item"><strong>Q：为什么有很多 Audit 问题？</strong><p>A：Audit 是检查器，发现缺图表、缺结果、缺证据链是正常的，它帮助你知道下一步该修哪里。</p></div>
              <div class="faq-item"><strong>Q：Human Gate 是错误吗？</strong><p>A：不是。它是人工确认机制，用来防止模型自动选择错误建模路线。</p></div>
              <div class="faq-item"><strong>Q：Run Workspace 是什么？</strong><p>A：每次运行的安全副本。查看结果可以用它，但不要在 run workspace 里继续嵌套运行。</p></div>
            </div>
          </Panel>
        </section>

        <section v-else class="view settings-grid">
          <Panel title="新建工作区" subtitle="scripts/new_v2_workspace.py">
            <p class="help-text">工作区是一道题目的项目文件夹。建议每道数学建模题单独创建一个工作区。</p>
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
            <p class="help-text">请上传题目 PDF、附件 Excel/CSV、图片或其它数据文件。上传后系统会保存到 source/ 目录。</p>
            <input type="file" multiple @change="uploadSource" />
            <div v-if="store.uploadResult" class="upload-success">
              <strong>{{ uploadSuccessMessage }}</strong>
              <small v-if="store.uploadResult.skipped.length">跳过：{{ store.uploadResult.skipped.join(", ") }}</small>
              <div class="button-row">
                <button @click="view = 'dashboard'">回到总览</button>
                <button class="primary" :disabled="store.langGraphRunning || selectedIsRunWorkspace" @click="runRecommendedFromUi">Run Recommended Graph</button>
              </div>
            </div>
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
import { BarChart3, FileText, FolderOpen, Gauge, HelpCircle, LayoutDashboard, PlayCircle, RefreshCw, Settings, ShieldCheck, TerminalSquare, Workflow } from "lucide-vue-next";
import { api } from "./api";
import { isRunWorkspacePath, useControlStore } from "./store";
import Panel from "./components/Panel.vue";
import IssueList from "./components/IssueList.vue";

const store = useControlStore();
const view = ref("dashboard");
const selectedPhase = ref(2);
const harness = ref("Manual");
const artifactQuery = ref("");
const showBeginnerGuide = ref(localStorage.getItem("mathmodel_beginner_guide_dismissed") !== "true");
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
  { id: "help", label: "帮助", icon: HelpCircle },
  { id: "dashboard", label: "总览", icon: LayoutDashboard },
  { id: "phase", label: "阶段", icon: Gauge },
  { id: "artifacts", label: "文件", icon: FileText },
  { id: "console", label: "Advanced", icon: TerminalSquare },
  { id: "langgraph", label: "LangGraph", icon: Workflow },
  { id: "runs", label: "Runs", icon: FolderOpen },
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

const PHASE_EXECUTE_SUPPORTED = new Set([1, 4]);

function canPhaseExecute(phase: number) {
  return PHASE_EXECUTE_SUPPORTED.has(phase);
}

function phaseRunHint(phase: number) {
  if (canPhaseExecute(phase)) {
    return "Run This Skill 会通过 LangGraph 安全执行，copy_workspace=true，provider=none。";
  }
  return "当前 Runtime 只支持 P1/P4 单阶段执行。P0/P2/P3/P5/P6 请使用 Dry Run 预检，或使用 Run Recommended Graph 运行完整 contest_graph_v3。";
}

function recommendedPhaseActionLabel(phase: number) {
  if (canPhaseExecute(phase)) return "Run This Skill";
  return "Run This Skill unavailable";
}

const NAV_ORDER = ["dashboard", "phase", "langgraph", "runs", "artifacts", "benchmark", "console", "help", "settings"];
const NAV_LABELS: Record<string, string> = {
  help: "帮助",
  dashboard: "总览",
  phase: "阶段运行",
  langgraph: "运行图",
  runs: "运行结果",
  artifacts: "文件",
  benchmark: "评测",
  console: "高级",
  settings: "设置",
};

const orderedNavItems = computed(() =>
  NAV_ORDER.map((id) => navItems.find((item) => item.id === id)).filter((item): item is (typeof navItems)[number] => Boolean(item)),
);

function navLabel(id: string) {
  return NAV_LABELS[id] ?? id;
}

const title = computed(() => navLabel(view.value) ?? "MathModel Control");
const selectedIsRunWorkspace = computed(() => store.selectedIsRunWorkspace);
const workspaceTypeLabel = computed(() => selectedIsRunWorkspace.value ? "Workspace Type: Run" : "Workspace Type: Source");
const workspaceTypeClass = computed(() => selectedIsRunWorkspace.value ? "run-badge" : "source-badge");
const workspaceKindTag = computed(() => selectedIsRunWorkspace.value ? "[RUN]" : "[SOURCE]");
const workspaceDisplayPath = computed(() => shortWorkspacePath(store.selectedWorkspace?.path ?? ""));
const artifactContextSubtitle = computed(() => selectedIsRunWorkspace.value ? "run workspace artifacts" : "source workspace artifacts");
const runDisabledHelp = "Run workspace is read-only result context. Select a source workspace to run again.";
const humanGateStatus = computed(() => {
  if (!store.langGraphRun) {
    return {
      className: "info",
      label: "Unknown",
      note: "No LangGraph run yet.",
    };
  }
  if (store.langGraphRun.human_gate_required || store.langGraphRun.needs_human) {
    return {
      className: "warn",
      label: "Required",
      note: "Current run is paused and needs reports/HUMAN_MODEL_REVIEW.md before dangerous phases.",
    };
  }
  return {
    className: "info",
    label: "Not blocking latest run",
    note: "Latest run is not blocked; manual confirmation is still required before dangerous phases.",
  };
});
const currentPhase = computed(() => store.summary?.phases.find((phase) => phase.id === selectedPhase.value));
const looksLikeFreshWorkspace = computed(() => {
  const summary = store.summary;
  if (!summary) return false;
  return (
    (summary.paper?.pdf_count ?? 0) === 0 ||
    (summary.manifest?.figures ?? 0) === 0 ||
    (summary.required_missing?.length ?? 0) > 0 ||
    store.history.length === 0
  );
});
const selectedPhaseCanExecute = computed(() => canPhaseExecute(selectedPhase.value));
const selectedPhaseRunTitle = computed(() => {
  if (selectedIsRunWorkspace.value) return runDisabledHelp;
  return phaseRunHint(selectedPhase.value);
});
const groupedRecommendationItems = computed(() => groupedRecommendations(store.summary?.recommendations ?? []));
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
const directoryChildArtifacts = computed(() => {
  const selected = store.selectedArtifact;
  if (!selected || selected.type !== "directory") return [];
  const prefix = selected.path.endsWith("/") ? selected.path : `${selected.path}/`;
  return store.artifacts.filter((artifact) => artifact.path.startsWith(prefix) && artifact.path !== selected.path).slice(0, 20);
});
const uploadSuccessMessage = computed(() => {
  const saved = store.uploadResult?.saved.length ?? 0;
  return `上传成功：${saved} 个文件已保存到 source/。下一步：回到总览，点击 Run Recommended Graph。`;
});
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

const runArtifactFilterGroup = ref("");

const filteredRunArtifacts = computed(() => {
  const query = artifactQuery.value.trim().toLowerCase();
  let pool = store.runArtifacts;
  if (runArtifactFilterGroup.value && RUN_ARTIFACT_GROUPS[runArtifactFilterGroup.value]) {
    const tokens = RUN_ARTIFACT_GROUPS[runArtifactFilterGroup.value];
    pool = pool.filter((a) => tokens.some((t) => a.path.includes(t)));
  }
  if (!query) return pool;
  return pool.filter((a) => a.path.toLowerCase().includes(query));
});

const RUN_ARTIFACT_GROUPS: Record<string, string[]> = {
  "LangGraph": ["LANGGRAPH_", "CONTROL_LANGGRAPH_", "AGENT_RUNS.md"],
  "Evidence": ["RESULTS_MANIFEST", "CLAIM_TRACE", "METHOD_IMPLEMENTATION", "FIGURE_AUDIT", "RESULTS_REPORT"],
  "Review": ["PAPER_SCORECARD", "REVISION_ACTIONS", "REVISION_STATUS"],
  "Paper": ["paper/", "main.tex", "main.typ"],
};

const RUN_ARTIFACT_GROUPS_ORDER = ["LangGraph", "Evidence", "Review", "Paper"];

const filteredBenchmarkReports = computed(() => {
  let pool = store.benchmarkReports;
  if (store.benchmarkCategoryFilter !== "all") {
    pool = pool.filter(r => r.category === store.benchmarkCategoryFilter);
  }
  if (store.benchmarkProviderFilter !== "all") {
    pool = pool.filter(r => r.provider === store.benchmarkProviderFilter);
  }
  return pool;
});

function statusClass(status: unknown) {
  const value = String(status ?? "").toLowerCase();
  if (value.includes("ready") || value.includes("completed")) return "good";
  if (value.includes("pass") && !value.includes("fail")) return "good";
  if (value.includes("fail") || value.includes("blocker") || value.includes("missing")) return "bad";
  if (value.includes("high") || value.includes("warn") || value.includes("legacy") || value.includes("pending")) return "warn";
  return "info";
}

function humanStatus(status: unknown) {
  const value = String(status ?? "UNKNOWN");
  const readableLabels: Record<string, string> = {
    PHASE2_PLAN_ONLY: "仅生成 Phase 2 计划，未执行实验",
    REVISION_REQUIRED: "需要修订",
    APPLY_READY_FOR_HUMAN_REVIEW: "等待人工审查",
    HUMAN_GATE_REQUIRED: "需要人工确认",
    COMPLETED: "已完成",
    PASS: "通过",
    FAIL: "失败",
    READY: "就绪",
  };
  if (readableLabels[value]) return readableLabels[value];
  const labels: Record<string, string> = {
    PHASE2_PLAN_ONLY: "仅生成 Phase 2 计划，未执行实验",
    REVISION_REQUIRED: "需要修订",
    APPLY_READY_FOR_HUMAN_REVIEW: "等待人工审查",
    HUMAN_GATE_REQUIRED: "需要人工确认",
    COMPLETED: "已完成",
    PASS: "通过",
    FAIL: "失败",
  };
  return labels[value] ?? value;
}

function workspaceOptionLabel(workspace: { name: string; path: string }) {
  return `${isRunWorkspacePath(workspace.path) ? "[RUN]" : "[SOURCE]"} ${workspace.name}`;
}

type RecommendationLike = Record<string, unknown>;

function groupedRecommendations(items: RecommendationLike[]) {
  const groups = new Map<string, { key: string; first: RecommendationLike; items: RecommendationLike[]; count: number }>();
  for (const item of items) {
    const key = ["code", "title", "detail", "severity", "artifact"]
      .map((fieldName) => String(item[fieldName] ?? ""))
      .join("::");
    const existing = groups.get(key);
    if (existing) {
      existing.items.push(item);
      existing.count += 1;
    } else {
      groups.set(key, { key, first: item, items: [item], count: 1 });
    }
  }
  return Array.from(groups.values());
}

function shortWorkspacePath(path: string) {
  if (!path) return "未选择工作区";
  const normalized = path.replace(/\\/g, "/");
  const runMatch = normalized.match(/\/runs\/([^/]+)(?:\/)?$/i) ?? normalized.match(/\/runs\/([^/]+)/i);
  if (runMatch?.[1]) return `runs/${runMatch[1]}`;
  const examplesIndex = normalized.toLowerCase().indexOf("/examples/");
  if (examplesIndex >= 0) return normalized.slice(examplesIndex + 1);
  const parts = normalized.split("/").filter(Boolean);
  return parts.slice(-3).join("/") || normalized;
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

async function copyWorkspacePath() {
  if (store.selectedWorkspace?.path) {
    await navigator.clipboard.writeText(store.selectedWorkspace.path);
  }
}

function dismissBeginnerGuide() {
  showBeginnerGuide.value = false;
  localStorage.setItem("mathmodel_beginner_guide_dismissed", "true");
}

function goUploadSource() {
  view.value = "settings";
}

async function runRecommendedFromUi() {
  const result = await store.runRecommendedGraph();
  if (result) {
    view.value = "langgraph";
  }
}

async function runCurrentSkillFromUi() {
  const result = await store.runCurrentSkill(selectedPhase.value);
  if (result) {
    view.value = "langgraph";
  }
}

async function dryRunSkillFromUi() {
  const result = await store.dryRunSkill(selectedPhase.value);
  if (result) {
    view.value = "langgraph";
  }
}

async function openLatestRun() {
  await store.loadRunWorkspaces();
  if (store.runWorkspaces.length > 0) {
    await store.selectRunWorkspace(store.runWorkspaces[0].id);
  }
  view.value = "runs";
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
