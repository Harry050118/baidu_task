<template>
  <Teleport to="body">
    <div v-if="visible" class="dialog-overlay" @click.self="$emit('cancel')">
      <div class="dialog" role="dialog" :aria-label="title">
        <p class="dialog__title">{{ title }}</p>
        <p class="dialog__body">{{ message }}</p>
        <div class="dialog__actions">
          <button @click="$emit('cancel')">取消</button>
          <button class="btn-confirm" @click="$emit('confirm')">确认</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{ visible: boolean; title: string; message: string }>()
defineEmits<{ (e: 'confirm'): void; (e: 'cancel'): void }>()
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.dialog {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 24px;
  min-width: 300px;
  max-width: 420px;
}
.dialog__title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 10px;
}
.dialog__body {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 20px;
  line-height: 1.6;
}
.dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.btn-confirm {
  background: var(--chart-line);
  color: #0D1117;
  border-color: var(--chart-line);
  font-weight: 600;
}
</style>
