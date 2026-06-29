<template>
  <div class="overview-panel">
    <template v-if="loading">
      <SkeletonBlock width="68%" height="14px" />
      <SkeletonBlock width="92%" height="14px" />
      <SkeletonBlock width="54%" height="14px" />
    </template>
    <ErrorState v-else-if="error" :message="error" />
    <div v-else class="overview-content">
      <div class="stat-grid">
        <span class="stat-item">积涝点 <strong class="mono">{{ overview?.flood_station_count ?? coordinateCounts.total }}</strong></span>
        <span class="stat-item">记录数 <strong class="mono">{{ overview?.flood_record_count ?? '—' }}</strong></span>
        <span class="stat-item">有坐标 <strong class="mono">{{ coordinateCounts.withCoordinates }}</strong></span>
        <span class="stat-item">缺坐标 <strong class="mono warn">{{ coordinateCounts.missingCoordinates }}</strong></span>
      </div>
      <div class="fact-row">
        <span>最新观测 <strong class="mono">{{ latestTime ?? overview?.latest_observed_at ?? '—' }}</strong></span>
      </div>
      <div class="fact-row fact-row--stacked">
        <span>覆盖范围</span>
        <strong class="mono">{{ observationWindowText }}</strong>
      </div>
      <div class="fact-row">
        <span>数据状态 <strong>{{ freshnessText }}</strong></span>
        <span v-if="isHistoricalSnapshot" class="snapshot-tag">历史快照</span>
      </div>
      <div class="risk-row" aria-label="风险统计，来自规则研判接口">
        <span v-for="item in riskSummary" :key="item.key" class="risk-chip" :style="{ color: item.color }">
          {{ item.label }} <strong class="mono">{{ item.count }}</strong>
        </span>
      </div>
      <p class="source-note">风险统计由规则研判列表聚合；统计接口仅用于点位、记录和时间事实。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SkeletonBlock from './SkeletonBlock.vue'
import ErrorState from './ErrorState.vue'
import type { OverviewResponse } from '../types/api'
import { formatObservationWindow, type CoordinateCounts, type RiskSummaryItem } from '../utils/commandMap'

const props = defineProps<{
  overview: OverviewResponse | null
  riskSummary: RiskSummaryItem[]
  coordinateCounts: CoordinateCounts
  latestTime?: string | null
  observationWindow?: { earliest: string | null; latest: string | null }
  freshnessLabel?: string | null
  isHistoricalSnapshot?: boolean
  loading?: boolean
  error?: string | null
}>()

const freshnessText = computed(() => props.freshnessLabel ?? (props.isHistoricalSnapshot ? '历史导入快照' : '可用'))
const observationWindowText = computed(() =>
  formatObservationWindow(
    props.observationWindow?.earliest ?? null,
    props.observationWindow?.latest ?? props.overview?.latest_observed_at ?? null,
  ),
)
</script>

<style scoped>
.overview-panel {
  padding: 12px 16px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.overview-content { display: flex; flex-direction: column; gap: 8px; }
.stat-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 14px;
  font-size: 13px;
  color: var(--text-secondary);
}
.stat-item strong { color: var(--text-primary); font-size: 15px; }
.stat-item .warn { color: var(--risk-warning); }
.fact-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 12px;
}
.fact-row strong { color: var(--text-primary); font-weight: 500; }
.fact-row--stacked {
  align-items: flex-start;
  flex-direction: column;
  gap: 2px;
}
.fact-row--stacked strong {
  font-size: 11px;
  overflow-wrap: anywhere;
}
.snapshot-tag {
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid rgba(210, 153, 34, 0.4);
  color: var(--risk-warning);
  background: rgba(210, 153, 34, 0.12);
}
.risk-row { display: flex; gap: 10px; flex-wrap: wrap; }
.risk-chip { font-size: 12px; }
.source-note {
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
}
</style>
