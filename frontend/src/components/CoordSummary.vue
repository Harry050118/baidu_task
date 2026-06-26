<template>
  <div class="coord-summary" v-if="status">
    坐标：缺失 <strong class="mono">{{ status.candidate_count === 0 ? status.total_stations - status.approved_count : status.total_stations - status.approved_count }}</strong> 个 &nbsp;
    候选 <strong class="mono">{{ status.candidate_count }}</strong> 个 &nbsp;
    <router-link to="/locations">前往校核</router-link>
  </div>
</template>

<script setup lang="ts">
import type { LocationsStatusResponse } from '../types/api'
defineProps<{ status: LocationsStatusResponse | null }>()
</script>

<style scoped>
.coord-summary {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 6px 16px;
  background: var(--bg-surface);
  border-top: 1px solid var(--border);
}
</style>
