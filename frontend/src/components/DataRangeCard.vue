<template>
  <div class="card">
    <p class="card__label">积涝点数据范围</p>
    <SkeletonBlock v-if="loading" width="100%" height="60px" />
    <ErrorState v-else-if="error" :message="error" />
    <template v-else-if="data">
      <p class="card__row">最早 <span class="mono">{{ data.flood_water_levels.earliest_observed_at ?? '—' }}</span></p>
      <p class="card__row">最新 <span class="mono">{{ data.flood_water_levels.latest_observed_at ?? '—' }}</span></p>
      <p class="card__row">总计 <span class="mono">{{ data.flood_water_levels.record_count?.toLocaleString() }}</span> 条</p>
    </template>
  </div>
</template>

<script setup lang="ts">
import SkeletonBlock from './SkeletonBlock.vue'
import ErrorState from './ErrorState.vue'
import type { TimeRangeResponse } from '../types/api'
defineProps<{ data: TimeRangeResponse | null; loading: boolean; error?: string | null }>()
</script>

<style scoped>
.card { background: var(--bg-raised); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }
.card__label { font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; }
.card__row { font-size: 13px; margin-bottom: 4px; color: var(--text-secondary); }
.card__row .mono { color: var(--text-primary); }
</style>
