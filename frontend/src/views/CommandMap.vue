<template>
  <div class="command-map">
    <div class="map-area">
      <MapWorkspace :points="pointsWithRisk" @point-click="onPointClick" />
      <PointDrawer
        :point="mapPointsStore.selectedPoint"
        :assessment="selectedAssessment"
        @close="mapPointsStore.select(null)"
      />
    </div>
    <aside class="side-panel">
      <ErrorState v-if="mapPointsStore.error" :message="mapPointsStore.error" />
      <OverviewPanel
        :overview="overviewStore.data"
        :assessments="assessments"
        :approved-count="approvedCount"
      />
      <div class="side-section">
        <p class="section-title">高风险点位</p>
        <HighRiskList :items="highRiskItems" @select="onPointClick" />
      </div>
      <CoordSummary :status="locationsStore.status" />
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
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
import type { AssessmentItem } from '../types/api'

const mapPointsStore = useMapPointsStore()
const overviewStore = useOverviewStore()
const locationsStore = useLocationsStore()

const assessments = ref<AssessmentItem[]>([])

const assessmentMap = computed(() => {
  const m = new Map<string, AssessmentItem>()
  for (const a of assessments.value) m.set(a.station_code, a)
  return m
})

const pointsWithRisk = computed(() =>
  mapPointsStore.points.map((p) => ({
    ...p,
    risk_level: assessmentMap.value.get(p.station_code)?.risk_level ?? 'no_data',
  })),
)
const selectedAssessment = computed(() =>
  assessments.value.find((a) => a.station_code === mapPointsStore.selectedCode) ?? null,
)
const highRiskItems = computed(() =>
  assessments.value.filter((a) => a.risk_level === 'danger' || a.risk_level === 'warning'),
)
const approvedCount = computed(() => mapPointsStore.approvedPoints.length)

function onPointClick(code: string) {
  mapPointsStore.select(code)
}

onMounted(async () => {
  await Promise.all([
    mapPointsStore.load(),
    overviewStore.load(),
    locationsStore.load(),
    getAssessments().then((r) => { assessments.value = r.items }).catch(() => {}),
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
  width: 300px;
  flex-shrink: 0;
  background: var(--bg-surface);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
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
