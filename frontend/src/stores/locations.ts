import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getLocationsStatus } from '../api/locations'
import type { LocationsStatusResponse } from '../types/api'

export const useLocationsStore = defineStore('locations', () => {
  const status = ref<LocationsStatusResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function load() {
    loading.value = true
    error.value = null
    try {
      status.value = await getLocationsStatus()
    } catch (e: unknown) {
      error.value = (e as { userMessage?: string })?.userMessage ?? '加载坐标状态失败'
    } finally {
      loading.value = false
    }
  }

  return { status, loading, error, load }
})
