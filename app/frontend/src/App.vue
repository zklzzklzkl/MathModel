<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <strong>MathModel Control</strong>
        <span>V2.6 workspace shell</span>
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
