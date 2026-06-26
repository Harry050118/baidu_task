<template>
  <div class="review-panel">
    <template v-if="!station">
      <EmptyState message="请从左侧选择测站" />
    </template>
    <template v-else>
      <p class="station-name">{{ station.station_name }}</p>
      <p class="station-code mono">站码: {{ stationCode }}</p>

      <SkeletonBlock v-if="loadingCandidates" width="100%" height="80px" />
      <ErrorState v-else-if="candidateError" :message="candidateError" />
      <template v-else>
        <template v-if="candidates.length === 0">
          <EmptyState message="候选坐标：无" action="生成高德候选坐标" @action="onGeocode" />
        </template>
        <template v-else>
          <div v-for="c in candidates" :key="c.id" class="candidate">
            <p class="coord mono">{{ c.longitude.toFixed(6) }}, {{ c.latitude.toFixed(6) }}</p>
            <CoordStatusTag :status="c.review_status" :source="c.coord_source" />
            <div class="cand-actions" v-if="c.review_status === 'pending'">
              <button @click="onReview(c.id, 'approved')">通过</button>
              <button @click="onReview(c.id, 'rejected')">拒绝</button>
            </div>
          </div>
        </template>
        <ErrorState v-if="reviewError" :message="reviewError" />
      </template>
    </template>

    <ConfirmDialog
      :visible="confirmVisible"
      :title="confirmAction === 'approved' ? '确认通过坐标' : '确认拒绝坐标'"
      :message="confirmAction === 'approved' ? '审核通过后该坐标将进入地图点位。' : '拒绝后该坐标不会进入地图。'"
      @confirm="submitReview"
      @cancel="confirmVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import SkeletonBlock from './SkeletonBlock.vue'
import ErrorState from './ErrorState.vue'
import EmptyState from './EmptyState.vue'
import CoordStatusTag from './CoordStatusTag.vue'
import ConfirmDialog from './ConfirmDialog.vue'
import { getCandidates, geocode, review } from '../api/locations'
import type { LocationCandidate } from '../types/api'

const props = defineProps<{
  stationCode: string | null
  station: { station_name: string } | null
}>()

const emit = defineEmits<{ (e: 'reviewed'): void }>()

const candidates = ref<LocationCandidate[]>([])
const loadingCandidates = ref(false)
const candidateError = ref<string | null>(null)
const reviewError = ref<string | null>(null)

const confirmVisible = ref(false)
const confirmAction = ref<'approved' | 'rejected'>('approved')
const pendingCandidateId = ref<number | null>(null)

async function loadCandidates() {
  if (!props.stationCode) return
  loadingCandidates.value = true
  candidateError.value = null
  try {
    const data = await getCandidates(props.stationCode)
    candidates.value = data.items
  } catch (e: unknown) {
    candidateError.value = (e as { userMessage?: string })?.userMessage ?? '加载候选坐标失败'
  } finally {
    loadingCandidates.value = false
  }
}

async function onGeocode() {
  if (!props.stationCode) return
  candidateError.value = null
  try {
    await geocode({ station_code: props.stationCode })
    await loadCandidates()
  } catch (e: unknown) {
    candidateError.value = (e as { userMessage?: string })?.userMessage ?? '生成候选坐标失败'
  }
}

function onReview(id: number, action: 'approved' | 'rejected') {
  pendingCandidateId.value = id
  confirmAction.value = action
  confirmVisible.value = true
}

async function submitReview() {
  confirmVisible.value = false
  if (!props.stationCode || pendingCandidateId.value == null) return
  reviewError.value = null
  try {
    await review(props.stationCode, {
      candidate_id: pendingCandidateId.value,
      review_status: confirmAction.value,
    })
    await loadCandidates()
    emit('reviewed')
  } catch (e: unknown) {
    reviewError.value = (e as { userMessage?: string })?.userMessage ?? '审核操作失败'
  }
}

watch(() => props.stationCode, (code) => {
  if (code) loadCandidates()
  else candidates.value = []
}, { immediate: true })
</script>

<style scoped>
.review-panel { padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.station-name { font-size: 15px; font-weight: 600; }
.station-code { font-size: 12px; color: var(--text-secondary); }
.candidate { background: var(--bg-raised); border: 1px solid var(--border); border-radius: 6px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.coord { font-size: 13px; }
.cand-actions { display: flex; gap: 8px; }
</style>
