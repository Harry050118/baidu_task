import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getOverview } from '../api/stats'
import { getDataStatus } from '../api/status'
import type { OverviewResponse } from '../types/api'

export const useOverviewStore = defineStore('overview', () => {
  const data = ref<OverviewResponse | null>(null)
  const isHistoricalSnapshot = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const latestObservedAt = computed(() => {
    if (!data.value?.latest_observed_at) return null
    const d = new Date(data.value.latest_observed_at)
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  })

  async function load() {
    loading.value = true
    error.value = null
    try {
      const [overview, status] = await Promise.all([getOverview(), getDataStatus()])
      data.value = overview
      isHistoricalSnapshot.value = status.data_freshness?.status === 'historical_snapshot'
    } catch (e: unknown) {
      error.value = (e as { userMessage?: string })?.userMessage ?? '加载统计失败'
    } finally {
      loading.value = false
    }
  }

  return { data, isHistoricalSnapshot, loading, error, latestObservedAt, load }
})
