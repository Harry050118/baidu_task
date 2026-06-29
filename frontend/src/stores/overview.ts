import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getOverview } from '../api/stats'
import { getDataStatus } from '../api/status'
import { normalizeObservationWindow } from '../utils/commandMap'
import type { OverviewResponse } from '../types/api'

export const useOverviewStore = defineStore('overview', () => {
  const data = ref<OverviewResponse | null>(null)
  const isHistoricalSnapshot = ref(false)
  const freshnessLabel = ref<string | null>(null)
  const observationWindow = ref<{ earliest: string | null; latest: string | null }>({
    earliest: null,
    latest: null,
  })
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
      freshnessLabel.value = status.data_freshness?.label ?? null
      const normalizedWindow = normalizeObservationWindow(
        status.flood_water_levels,
        null,
        overview.latest_observed_at ?? null,
      )
      observationWindow.value = {
        earliest: normalizedWindow.earliest,
        latest: normalizedWindow.latest,
      }
    } catch (e: unknown) {
      error.value = (e as { userMessage?: string })?.userMessage ?? '加载统计失败'
    } finally {
      loading.value = false
    }
  }

  return { data, isHistoricalSnapshot, freshnessLabel, observationWindow, loading, error, latestObservedAt, load }
})
