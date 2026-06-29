<template>
  <div class="point-detail">
    <header class="detail-header">
      <router-link to="/" class="back-link" aria-label="返回地图">← 返回地图</router-link>
      <h1 class="station-name">{{ stationName }}</h1>
      <RiskBadge v-if="assessment" :level="assessment.risk_level" />
      <TrendIndicator v-if="assessment" :trend="assessment.trend" />
    </header>

    <SkeletonBlock v-if="loadingDetail" width="100%" height="80px" />
    <ErrorState v-else-if="detailError" :message="detailError" />
    <template v-else-if="detail">
      <div class="meta-row">
        <span class="water-level mono">当前水位 {{ wlDisplay }}</span>
        <span class="obs-time mono">观测时间 {{ observedAtDisplay }}</span>
      </div>
      <div v-if="assessment" class="rule-info">
        <p>规则版本: {{ assessment.rule_version }}</p>
        <p>规则说明: {{ assessment.rule_description }}</p>
      </div>
      <div class="coord-info">
        <CoordStatusTag :status="detail.coordinates.coordinate_status" :source="detail.coordinates.coord_source" />
        <span v-if="detail.coordinates.has_coordinates" class="coord-text mono">
          {{ detail.coordinates.longitude }}, {{ detail.coordinates.latitude }}
          <template v-if="detail.coordinates.coord_quality"> · {{ detail.coordinates.coord_quality }}</template>
        </span>
      </div>
    </template>
    <EmptyState v-else message="暂无点位详情" />

    <div class="chart-section">
      <div class="chart-controls">
        <span class="chart-label">历史水位曲线 · 选择最近记录条数</span>
        <div class="limit-btns" role="group" aria-label="数据量选择">
          <button
            v-for="l in LIMITS"
            :key="l"
            :class="['limit-btn', { active: limit === l }]"
            @click="setLimit(l)"
          >最近 {{ l }} 条</button>
        </div>
      </div>
      <WaterLevelChart :records="historyRecords" :loading="loadingHistory" :error="historyError" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import RiskBadge from '../components/RiskBadge.vue'
import TrendIndicator from '../components/TrendIndicator.vue'
import SkeletonBlock from '../components/SkeletonBlock.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'
import CoordStatusTag from '../components/CoordStatusTag.vue'
import WaterLevelChart from '../components/WaterLevelChart.vue'
import { getPoint, getHistory, getPointAssessment } from '../api/points'
import type { PointDetailResponse, AssessmentItem, WaterLevelRecord } from '../types/api'

const route = useRoute()
const stationCode = computed(() => route.params.stationCode as string)

const detail = ref<PointDetailResponse | null>(null)
const assessment = ref<AssessmentItem | null>(null)
const loadingDetail = ref(false)
const detailError = ref<string | null>(null)

const historyRecords = ref<WaterLevelRecord[]>([])
const loadingHistory = ref(false)
const historyError = ref<string | null>(null)
const LIMITS = [100, 500, 1000, 5000] as const
const limit = ref<number>(500)

const stationName = computed(() => detail.value?.station.station_name ?? stationCode.value)
const wlDisplay = computed(() => {
  const latest = detail.value?.latest_water_level
  const v = latest?.latest_water_level_m ?? latest?.water_level_m
  return v != null ? `${v.toFixed(3)} m` : '— m'
})
const observedAtDisplay = computed(() => {
  const latest = detail.value?.latest_water_level
  return latest?.latest_observed_at ?? latest?.observed_at ?? '—'
})

async function loadDetail() {
  loadingDetail.value = true
  detailError.value = null
  try {
    const [d, a] = await Promise.all([
      getPoint(stationCode.value),
      getPointAssessment(stationCode.value).catch(() => null),
    ])
    detail.value = d
    assessment.value = a
  } catch (e: unknown) {
    detailError.value = (e as { userMessage?: string })?.userMessage ?? '加载点位失败'
  } finally {
    loadingDetail.value = false
  }
}

async function loadHistory() {
  loadingHistory.value = true
  historyError.value = null
  try {
    const data = await getHistory(stationCode.value, limit.value)
    historyRecords.value = data.items
  } catch (e: unknown) {
    const err = e as { userMessage?: string; response?: { status: number } }
    if (err.response?.status === 422) {
      historyError.value = '参数超出范围，请选择较小的数据量'
    } else {
      historyError.value = err.userMessage ?? '加载历史数据失败'
    }
  } finally {
    loadingHistory.value = false
  }
}

function setLimit(l: number) {
  limit.value = l
  loadHistory()
}

onMounted(() => {
  loadDetail()
  loadHistory()
})

watch(stationCode, () => {
  loadDetail()
  loadHistory()
})
</script>

<style scoped>
.point-detail { padding: 24px; max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }
.detail-header { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.back-link { font-size: 13px; color: var(--text-secondary); }
.station-name { font-size: 18px; font-weight: 600; }
.meta-row { display: flex; gap: 24px; align-items: baseline; flex-wrap: wrap; }
.water-level { font-size: 28px; font-weight: 700; }
.obs-time { font-size: 13px; color: var(--text-secondary); }
.rule-info { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }
.coord-info { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.coord-text { color: var(--text-secondary); font-size: 12px; }
.chart-section { display: flex; flex-direction: column; gap: 8px; }
.chart-controls { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.chart-label { font-size: 13px; color: var(--text-secondary); }
.limit-btns { display: flex; gap: 4px; flex-wrap: wrap; }
.limit-btn { padding: 3px 8px; font-size: 12px; white-space: nowrap; }
.limit-btn.active { background: var(--chart-line); color: #0D1117; border-color: var(--chart-line); }
</style>
