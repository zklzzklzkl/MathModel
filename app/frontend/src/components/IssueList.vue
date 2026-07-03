<script setup lang="ts">
defineProps<{
  issues: Array<Record<string, unknown>>;
}>();
</script>

<template>
  <div class="risk-list">
    <div
      v-for="issue in issues.slice(0, 8)"
      :key="String(issue.code ?? '') + String(issue.message ?? '')"
      :class="['risk-item', String(issue.severity ?? '').toLowerCase()]"
    >
      <strong>{{ issue.severity ?? "INFO" }} - {{ issue.code ?? "issue" }}</strong>
      <p>{{ issue.message ?? issue.evidence ?? "" }}</p>
    </div>
    <div v-if="!issues.length" class="empty">暂无审计问题。</div>
  </div>
</template>
