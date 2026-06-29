<template>
  <div class="card">
    <p class="card__label">积涝点数据范围</p>
    <SkeletonBlock v-if="loading" width="100%" height="60px" />
    <ErrorState v-else-if="error" :message="error" />
    <template v-else-if="data || recordCount != null">
      <p class="card__row">最早 <span class="mono">{{ normalized.earliest ?? '—' }}</span></p>
      <p class="card__row">最新 <span class="mono">{{ normalized.latest ?? '—' }}</span></p>
      <p class="card__row">总计 <span class="mono">{{ displayRecordCount }}</span> 条</p>
    </template>
    <EmptyState v-else message="暂无积涝点数据范围" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SkeletonBlock from './SkeletonBlock.vue'
import ErrorState from './ErrorState.vue'
import EmptyState from './EmptyState.vue'
import { normalizeObservationWindow } from '../utils/commandMap'
import type { TimeRangeResponse } from '../types/api'
const props = defineProps<{
  data: TimeRangeResponse | null
  loading: boolean
  error?: string | null
  recordCount?: number | null
}>()

const normalized = computed(() =>
  normalizeObservationWindow(null, props.data?.flood_water_levels, null),
)
const displayRecordCount = computed(() => {
  const value = normalized.value.recordCount ?? props.recordCount
  return value != null ? value.toLocaleString() : '—'
})
</script>

<style scoped>
.card { background: var(--bg-raised); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }
.card__label { font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; }
.card__row { font-size: 13px; margin-bottom: 4px; color: var(--text-secondary); }
.card__row .mono { color: var(--text-primary); }
</style>
