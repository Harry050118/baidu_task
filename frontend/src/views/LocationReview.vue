<template>
  <div class="location-review">
    <header class="page-header">
      <h1 class="page-title">坐标校核</h1>
      <template v-if="locStatus">
        <span class="stat mono">总数 {{ locStatus.total_stations }}</span>
        <span class="stat mono">候选 {{ locStatus.candidate_count }}</span>
        <span class="stat mono">已审核 {{ locStatus.approved_count }}</span>
        <span class="stat mono">已拒绝 {{ locStatus.rejected_count }}</span>
      </template>
    </header>

    <SkeletonBlock v-if="loading" width="100%" height="200px" />
    <ErrorState v-else-if="error" :message="error" />
    <div v-else class="layout">
      <aside class="station-list">
        <div
          v-for="p in missingPoints"
          :key="p.station_code"
          :class="['station-item', { active: selectedCode === p.station_code }]"
          tabindex="0"
          :aria-label="`选择 ${p.station_name}，坐标缺失`"
          @click="selectedCode = p.station_code"
          @keydown.enter="selectedCode = p.station_code"
        >
          <span class="sname">{{ p.station_name }}</span>
          <CoordStatusTag :status="p.coordinate_status" />
        </div>
        <EmptyState v-if="missingPoints.length === 0" message="暂无待校核点位" />
      </aside>
      <main class="review-main">
        <LocationReviewPanel
          :station-code="selectedCode"
          :station="selectedStation"
          @reviewed="onReviewed"
        />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import SkeletonBlock from '../components/SkeletonBlock.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'
import CoordStatusTag from '../components/CoordStatusTag.vue'
import LocationReviewPanel from '../components/LocationReviewPanel.vue'
import { getLocationsStatus } from '../api/locations'
import { getMapPoints } from '../api/map'
import { useLocationsStore } from '../stores/locations'
import type { MapPoint, LocationsStatusResponse } from '../types/api'

const locationsStore = useLocationsStore()
const loading = ref(false)
const error = ref<string | null>(null)
const locStatus = ref<LocationsStatusResponse | null>(null)
const allPoints = ref<MapPoint[]>([])
const selectedCode = ref<string | null>(null)

const missingPoints = computed(() =>
  allPoints.value.filter((p) => p.coordinate_status !== 'approved'),
)
const selectedStation = computed(() => {
  const p = allPoints.value.find((x) => x.station_code === selectedCode.value)
  return p ? { station_name: p.station_name } : null
})

async function loadAll() {
  loading.value = true
  error.value = null
  try {
    const [s, pts] = await Promise.all([getLocationsStatus(), getMapPoints()])
    locStatus.value = s
    locationsStore.status = s
    allPoints.value = pts.points
    const selectedStillPending = missingPoints.value.some((point) => point.station_code === selectedCode.value)
    if (!selectedStillPending && missingPoints.value.length > 0) {
      selectedCode.value = missingPoints.value[0].station_code
    } else if (!selectedStillPending) {
      selectedCode.value = null
    }
  } catch (e: unknown) {
    error.value = (e as { userMessage?: string })?.userMessage ?? '加载坐标状态失败'
  } finally {
    loading.value = false
  }
}

function onReviewed() {
  loadAll()
}

onMounted(loadAll)
</script>

<style scoped>
.location-review { padding: 24px; display: flex; flex-direction: column; gap: 16px; height: 100%; overflow: hidden; }
.page-header { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.page-title { font-size: 18px; font-weight: 600; }
.stat { font-size: 13px; color: var(--text-secondary); }
.layout { display: flex; gap: 0; flex: 1; overflow: hidden; border: 1px solid var(--border); border-radius: 6px; }
.station-list { width: 220px; flex-shrink: 0; border-right: 1px solid var(--border); overflow-y: auto; }
.station-item {
  padding: 10px 12px; cursor: pointer; display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid var(--border); font-size: 13px;
}
.station-item:hover { background: var(--bg-raised); }
.station-item.active { background: var(--bg-raised); border-left: 2px solid var(--chart-line); }
.sname { flex: 1; margin-right: 8px; }
.review-main { flex: 1; overflow-y: auto; }
</style>
