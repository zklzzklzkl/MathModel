<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
}>();
</script>

<template>
  <section class="panel">
    <div class="panel-header">
      <h2>{{ title }}</h2>
      <span>{{ subtitle ?? "" }}</span>
    </div>
    <div class="panel-body">
      <slot />
    </div>
  </section>
</template>
