<template>
  <div>
    <div class="filter-bar" role="group" aria-label="风险等级筛选">
      <button
        v-for="f in FILTERS"
        :key="f.value"
        :class="['filter-btn', { active: activeRisk === f.value }]"
        @click="activeRisk = f.value"
      >{{ f.label }}</button>
    </div>
    <div class="filter-bar" role="group" aria-label="趋势筛选">
      <button
        v-for="f in TREND_FILTERS"
        :key="f.value"
        :class="['filter-btn', { active: activeTrend === f.value }]"
        @click="activeTrend = f.value"
      >{{ f.label }}</button>
    </div>
    <p class="rule-version">规则版本：flood_rule_v1</p>
    <SkeletonBlock v-if="loading" width="100%" height="200px" />
    <ErrorState v-else-if="error" :message="error" />
    <div v-else-if="filtered.length === 0">
      <EmptyState message="暂无研判数据" />
    </div>
    <div v-else class="table-wrap">
      <table class="assessment-table">
        <thead>
          <tr>
            <th>测站</th><th>水位</th><th>风险</th><th>趋势</th><th>规则说明</th><th>生成时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filtered" :key="item.station_code">
            <td>{{ item.station_name }}</td>
            <td class="mono">{{ item.latest_water_level_m != null ? item.latest_water_level_m.toFixed(2) + ' m' : '—' }}</td>
            <td><RiskBadge :level="item.risk_level" /></td>
            <td><TrendIndicator :trend="item.trend" /></td>
            <td class="rule-desc">{{ item.rule_description }}</td>
            <td class="mono time-col">{{ item.generated_at }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import RiskBadge from './RiskBadge.vue'
import TrendIndicator from './TrendIndicator.vue'
import SkeletonBlock from './SkeletonBlock.vue'
import ErrorState from './ErrorState.vue'
import EmptyState from './EmptyState.vue'
import type { AssessmentItem, RiskLevel, Trend } from '../types/api'

const props = defineProps<{
  items: AssessmentItem[]
  loading: boolean
  error?: string | null
}>()

type FilterValue = RiskLevel | 'all'
type TrendFilterValue = Trend | 'all'

const FILTERS: Array<{ value: FilterValue; label: string }> = [
  { value: 'all', label: '全部' },
  { value: 'danger', label: '危险' },
  { value: 'warning', label: '警戒' },
  { value: 'attention', label: '关注' },
  { value: 'normal', label: '正常' },
  { value: 'no_data', label: '无数据' },
]

const TREND_FILTERS: Array<{ value: TrendFilterValue; label: string }> = [
  { value: 'all', label: '全趋势' },
  { value: 'rising', label: '↑ 上升' },
  { value: 'falling', label: '↓ 下降' },
  { value: 'stable', label: '→ 稳定' },
  { value: 'fluctuating', label: '↕ 波动' },
  { value: 'no_data', label: '— 无数据' },
]

const activeRisk = ref<FilterValue>('all')
const activeTrend = ref<TrendFilterValue>('all')

const filtered = computed(() =>
  props.items.filter((i) => {
    const riskOk = activeRisk.value === 'all' || i.risk_level === activeRisk.value
    const trendOk = activeTrend.value === 'all' || i.trend === activeTrend.value
    return riskOk && trendOk
  }),
)
</script>

<style scoped>
.filter-bar { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
.filter-btn { padding: 4px 10px; font-size: 12px; }
.filter-btn.active { background: var(--chart-line); color: #0D1117; border-color: var(--chart-line); }
.rule-version { font-size: 12px; color: var(--text-muted); margin-bottom: 12px; }
.table-wrap { overflow-x: auto; }
.assessment-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.assessment-table th {
  text-align: left; padding: 8px 10px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary); font-weight: 500;
}
.assessment-table td { padding: 8px 10px; border-bottom: 1px solid #1F2937; }
.rule-desc { white-space: normal; line-height: 1.5; }
.time-col { font-size: 11px; color: var(--text-muted); white-space: nowrap; }
</style>
