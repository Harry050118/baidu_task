<template>
  <div class="overview-panel">
    <div class="stat-row">
      <span class="stat-item">积涝点 <strong class="mono">{{ overview?.flood_station_count ?? '—' }}</strong></span>
      <span class="stat-item">有坐标 <strong class="mono">{{ approvedCount }}</strong></span>
    </div>
    <div class="risk-row">
      <span v-for="(item, i) in riskSummary" :key="i" class="risk-chip" :style="{ color: item.color }">
        {{ item.label }} {{ item.count }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { OverviewResponse, AssessmentItem } from '../types/api'

const props = defineProps<{
  overview: OverviewResponse | null
  assessments: AssessmentItem[]
  approvedCount: number
}>()

const RISK_COLORS: Record<string, string> = {
  danger: '#DA3633', warning: '#D29922', attention: '#9E6A03', normal: '#238636', no_data: '#484F58',
}
const RISK_LABELS: Record<string, string> = {
  danger: '危险', warning: '警戒', attention: '关注', normal: '正常', no_data: '无数据',
}
const RISK_ORDER = ['danger', 'warning', 'attention', 'normal', 'no_data']

const riskSummary = computed(() => {
  const counts: Record<string, number> = {}
  for (const a of props.assessments) {
    counts[a.risk_level] = (counts[a.risk_level] ?? 0) + 1
  }
  return RISK_ORDER.map((k) => ({
    label: RISK_LABELS[k],
    color: RISK_COLORS[k],
    count: counts[k] ?? 0,
  }))
})
</script>

<style scoped>
.overview-panel {
  padding: 12px 16px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.stat-row { display: flex; gap: 20px; font-size: 13px; color: var(--text-secondary); }
.stat-item strong { color: var(--text-primary); font-size: 15px; }
.risk-row { display: flex; gap: 12px; flex-wrap: wrap; }
.risk-chip { font-size: 12px; }
</style>
