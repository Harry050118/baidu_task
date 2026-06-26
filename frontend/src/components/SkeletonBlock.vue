<template>
  <div class="skeleton" :style="{ width, height }" aria-hidden="true"></div>
</template>

<script setup lang="ts">
defineProps<{ width?: string; height?: string }>()
</script>

<style scoped>
.skeleton {
  background: linear-gradient(90deg, var(--bg-raised) 25%, #2d3748 50%, var(--bg-raised) 75%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
  border-radius: 4px;
}
@keyframes shimmer {
  0%   { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}
</style>
