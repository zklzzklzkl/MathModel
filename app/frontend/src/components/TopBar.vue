<template>
  <header class="topbar">
    <div class="title-block">
      <h1>{{ title }}</h1>
      <div class="workspace-context-bar">
        <span :class="['workspace-type-badge', store.selectedIsRunWorkspace ? 'run-badge' : 'source-badge']">
          {{ store.selectedIsRunWorkspace ? 'Run Workspace' : 'Source Workspace' }}
        </span>
        <span class="workspace-path">{{ store.selectedWorkspace?.path ?? '未选择工作区' }}</span>
      </div>
    </div>
    <div class="top-actions">
      <button @click="store.initialize"><RefreshCw :size="16" />刷新</button>
      <button @click="store.runAudit"><ShieldCheck :size="16" />运行审计</button>
      <button class="primary" :disabled="store.langGraphRunning || store.selectedIsRunWorkspace" @click="store.runRecommendedGraph">
        <PlayCircle :size="16" />{{ store.langGraphRunning ? '运行中...' : '开始运行' }}
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { PlayCircle, RefreshCw, ShieldCheck } from "lucide-vue-next";
import { useControlStore } from "../store";

const store = useControlStore();

defineProps<{
  title: string;
}>();
</script>
