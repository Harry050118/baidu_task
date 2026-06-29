import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMapPoints } from '../api/map'
import { getCoordinateCounts, getRenderablePoints } from '../utils/commandMap'
import type { MapPoint } from '../types/api'

export const useMapPointsStore = defineStore('mapPoints', () => {
  const points = ref<MapPoint[]>([])
  const selectedCode = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const approvedPoints = computed(() => getRenderablePoints(points.value))
  const coordinateCounts = computed(() => getCoordinateCounts(points.value))

  const selectedPoint = computed(() =>
    points.value.find((p) => p.station_code === selectedCode.value) ?? null,
  )

  async function load() {
    loading.value = true
    error.value = null
    try {
      const data = await getMapPoints()
      points.value = data.points
    } catch (e: unknown) {
      error.value = (e as { userMessage?: string })?.userMessage ?? '加载点位失败'
    } finally {
      loading.value = false
    }
  }

  function select(code: string | null) {
    selectedCode.value = code
  }

  return { points, approvedPoints, coordinateCounts, selectedPoint, selectedCode, loading, error, load, select }
})
