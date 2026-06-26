<template>
  <div class="empty-state">
    <p class="empty-state__msg">{{ message }}</p>
    <button v-if="action" @click="$emit('action')">{{ action }}</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ message: string; action?: string }>()
defineEmits<{ (e: 'action'): void }>()
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 16px;
  color: var(--text-muted);
  font-size: 13px;
}
</style>
