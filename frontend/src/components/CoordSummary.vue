<template>
  <div class="coord-summary">
    <template v-if="loading">正在加载坐标治理状态...</template>
    <template v-else-if="error">
      <span class="error-text">{{ error }}</span>
    </template>
    <template v-else>
      <span>地图可见 <strong class="mono">{{ coordinateCounts.withCoordinates }}</strong> 个</span>
      <span>缺坐标 <strong class="mono warn">{{ coordinateCounts.missingCoordinates }}</strong> 个</span>
      <span v-if="status">候选 <strong class="mono">{{ status.candidate_count }}</strong> 个</span>
      <router-link to="/locations">前往校核</router-link>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { LocationsStatusResponse } from '../types/api'
import type { CoordinateCounts } from '../utils/commandMap'

defineProps<{
  status: LocationsStatusResponse | null
  coordinateCounts: CoordinateCounts
  loading?: boolean
  error?: string | null
}>()
</script>

<style scoped>
.coord-summary {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 6px 16px;
  background: var(--bg-surface);
  border-top: 1px solid var(--border);
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}
.warn { color: var(--risk-warning); }
.error-text { color: var(--risk-danger); }
</style>
