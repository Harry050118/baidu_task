<template>
  <div class="data-status">
    <h1 class="page-title">数据状态</h1>

    <SkeletonBlock v-if="loading" width="100%" height="120px" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="!dataStatus && !timeRange && !importData" message="暂无数据状态信息" />
    <template v-else>
      <div class="cards">
        <DataRangeCard
          :data="timeRange"
          :record-count="dataStatus?.flood_water_levels.record_count ?? null"
          :loading="false"
        />
        <ImportBatchCard :data="importData" :loading="false" />
        <div class="card">
          <p class="card__label">数据新鲜度</p>
          <FreshnessTag v-if="dataStatus" :status="dataStatus.data_freshness.status" />
          <EmptyState v-else message="暂无数据新鲜度信息" />
          <p v-if="dataStatus?.data_freshness.status === 'historical_snapshot'" class="freshness-note">
            当前数据为历史导入快照，非实时推送
          </p>
          <p v-else-if="dataStatus?.data_freshness.message" class="freshness-note">
            {{ dataStatus.data_freshness.message }}
          </p>
        </div>
      </div>

      <div class="extra-info">
        <p class="info-row">水库数据：仅状态摘要，不参与地图和积水风险主线</p>
        <p v-if="dataStatus" class="info-row">
          测站坐标：缺失 <span class="mono">{{ coordCounts.missing ?? '—' }}</span> 个 &nbsp;
          候选 <span class="mono">{{ coordCounts.candidates ?? '—' }}</span> 个 &nbsp;
          已审核 <span class="mono">{{ coordCounts.approved ?? '—' }}</span> 个
        </p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import SkeletonBlock from '../components/SkeletonBlock.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'
import DataRangeCard from '../components/DataRangeCard.vue'
import ImportBatchCard from '../components/ImportBatchCard.vue'
import FreshnessTag from '../components/FreshnessTag.vue'
import { getDataStatus, getTimeRange, getLatestImport } from '../api/status'
import { getLocationsStatus } from '../api/locations'
import { getStatusCoordinateCounts } from '../utils/commandMap'
import type {
  DataStatusResponse,
  TimeRangeResponse,
  LatestImportResponse,
  LocationsStatusResponse,
} from '../types/api'

const loading = ref(false)
const error = ref<string | null>(null)
const dataStatus = ref<DataStatusResponse | null>(null)
const timeRange = ref<TimeRangeResponse | null>(null)
const importData = ref<LatestImportResponse | null>(null)
const locStatus = ref<LocationsStatusResponse | null>(null)

const coordCounts = computed(() =>
  getStatusCoordinateCounts(dataStatus.value?.stations, locStatus.value),
)

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    const [ds, tr, imp, loc] = await Promise.all([
      getDataStatus(),
      getTimeRange(),
      getLatestImport(),
      getLocationsStatus(),
    ])
    dataStatus.value = ds
    timeRange.value = tr
    importData.value = imp
    locStatus.value = loc
  } catch (e: unknown) {
    error.value = (e as { userMessage?: string })?.userMessage ?? '加载数据状态失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.data-status { padding: 24px; max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }
.page-title { font-size: 18px; font-weight: 600; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
.card { background: var(--bg-raised); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }
.card__label { font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; }
.freshness-note { font-size: 12px; color: var(--text-secondary); margin-top: 8px; line-height: 1.5; }
.extra-info { display: flex; flex-direction: column; gap: 8px; }
.info-row { font-size: 13px; color: var(--text-secondary); }
</style>
