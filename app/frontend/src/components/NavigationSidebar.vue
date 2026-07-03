<template>
  <aside class="sidebar">
    <div class="brand">
      <strong>MathModel Control</strong>
      <span>任务向导 · V2.7</span>
    </div>

    <nav class="nav">
      <button v-for="item in items" :key="item.id" :class="{ active: active === item.id }" @click="$emit('update:active', item.id)">
        <component :is="item.icon" :size="17" />
        {{ item.label }}
      </button>
    </nav>

    <div class="workspace-mini">
      <label>工作区</label>
      <select :value="store.selectedWorkspaceId" @change="store.selectWorkspace(($event.target as HTMLSelectElement).value)">
        <option v-for="workspace in store.workspaces" :key="workspace.id" :value="workspace.id">
          {{ workspaceLabel(workspace) }}
        </option>
      </select>
      <small>{{ store.selectedWorkspace?.path ?? '未选择工作区' }}</small>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { BarChart3, FileText, FolderOpen, LayoutDashboard, Settings } from "lucide-vue-next";
import { isRunWorkspacePath, useControlStore } from "../store";

const store = useControlStore();

def workspaceLabel(workspace: { name: string; path: string }) {
  return `${isRunWorkspacePath(workspace.path) ? "[RUN]" : "[SOURCE]"} ${workspace.name}`;
}

defineProps<{
  active: string;
}>();

defineEmits<{
  "update:active": [value: string];
}>();

const items = [
  { id: "overview", label: "总览", icon: LayoutDashboard },
  { id: "runs", label: "运行结果", icon: FolderOpen },
  { id: "artifacts", label: "文件", icon: FileText },
  { id: "benchmark", label: "评测", icon: BarChart3 },
  { id: "settings", label: "设置", icon: Settings },
];
</script>
