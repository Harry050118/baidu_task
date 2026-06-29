<template>
  <div class="command-map">
    <div class="map-area">
      <MapWorkspace
        :points="pointsWithRisk"
        :loading="mapPointsStore.loading"
        :error="mapPointsStore.error"
        @point-click="onPointClick"
      />
      <PointDrawer
        :point="mapPointsStore.selectedPoint"
        :assessment="selectedAssessment"
        @close="mapPointsStore.select(null)"
      />
    </div>
    <aside class="side-panel">
      <div v-if="loadErrors.length" class="side-alerts">
        <ErrorState v-for="message in loadErrors" :key="message" :message="message" />
      </div>
      <OverviewPanel
        :overview="overviewStore.data"
        :risk-summary="riskSummary"
        :coordinate-counts="coordinateCounts"
        :latest-time="overviewStore.data?.latest_observed_at ?? null"
        :observation-window="overviewStore.observationWindow"
        :freshness-label="overviewStore.freshnessLabel"
        :is-historical-snapshot="overviewStore.isHistoricalSnapshot"
        :loading="overviewStore.loading || assessmentsLoading"
        :error="overviewStore.error || assessmentsError"
      />
      <div class="side-section">
        <p class="section-title">高风险点位</p>
        <HighRiskList
          :items="highRiskItems"
          :loading="assessmentsLoading"
          :error="assessmentsError"
          @select="onPrioritySelect"
        />
      </div>
      <CoordSummary
        :status="locationsStore.status"
        :coordinate-counts="coordinateCounts"
        :loading="locationsStore.loading"
        :error="locationsStore.error"
      />
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import MapWorkspace from '../components/MapWorkspace.vue'
import PointDrawer from '../components/PointDrawer.vue'
import OverviewPanel from '../components/OverviewPanel.vue'
import HighRiskList from '../components/HighRiskList.vue'
import CoordSummary from '../components/CoordSummary.vue'
import ErrorState from '../components/ErrorState.vue'
import { useMapPointsStore } from '../stores/mapPoints'
import { useOverviewStore } from '../stores/overview'
import { useLocationsStore } from '../stores/locations'
import { getAssessments } from '../api/assessments'
import {
  getCoordinateCounts,
  getPriorityAssessments,
  mergePointsWithAssessments,
  summarizeRisks,
} from '../utils/commandMap'
import type { AssessmentItem } from '../types/api'

const router = useRouter()
const mapPointsStore = useMapPointsStore()
const overviewStore = useOverviewStore()
const locationsStore = useLocationsStore()

const assessments = ref<AssessmentItem[]>([])
const assessmentsLoading = ref(false)
const assessmentsError = ref<string | null>(null)

const assessmentMap = computed(() => {
  const m = new Map<string, AssessmentItem>()
  for (const a of assessments.value) m.set(a.station_code, a)
  return m
})

const pointsWithRisk = computed(() => mergePointsWithAssessments(mapPointsStore.points, assessments.value))
const selectedAssessment = computed(() =>
  assessments.value.find((a) => a.station_code === mapPointsStore.selectedCode) ?? null,
)
const highRiskItems = computed(() => getPriorityAssessments(assessments.value))
const riskSummary = computed(() => summarizeRisks(assessments.value))
const coordinateCounts = computed(() => getCoordinateCounts(mapPointsStore.points))
const loadErrors = computed(() =>
  [mapPointsStore.error, overviewStore.error, assessmentsError.value, locationsStore.error].filter(Boolean) as string[],
)

function onPointClick(code: string) {
  mapPointsStore.select(code)
}

function onPrioritySelect(code: string) {
  const point = mapPointsStore.points.find((item) => item.station_code === code)
  if (point?.has_coordinates && point.coordinate_status === 'approved') {
    mapPointsStore.select(code)
    return
  }
  router.push(`/points/${code}`)
}

async function loadAssessments() {
  assessmentsLoading.value = true
  assessmentsError.value = null
  try {
    const data = await getAssessments()
    assessments.value = data.items
  } catch (error: unknown) {
    assessmentsError.value = (error as { userMessage?: string })?.userMessage ?? '加载研判结果失败'
  } finally {
    assessmentsLoading.value = false
  }
}

onMounted(async () => {
  await Promise.allSettled([
    mapPointsStore.load(),
    overviewStore.load(),
    locationsStore.load(),
    loadAssessments(),
  ])
})
</script>

<style scoped>
.command-map {
  display: flex;
  height: 100%;
  overflow: hidden;
}
.map-area {
  flex: 1;
  position: relative;
  overflow: hidden;
}
.side-panel {
  width: 340px;
  flex-shrink: 0;
  background: var(--bg-surface);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.side-alerts {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 12px 0;
}
.side-section {
  padding: 12px 16px;
  flex: 1;
}
.section-title {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  font-weight: 500;
}
</style>
