<template>
  <div ref="container" class="map-workspace" :aria-label="`地图工作区，共 ${points.length} 个审核点位`">
    <svg
      class="scatter"
      :viewBox="`0 0 ${W} ${H}`"
      :aria-label="`散点工作区，展示 ${points.length} 个已审核坐标点位`"
    >
      <StationMarker
        v-for="p in points"
        :key="p.station_code"
        :point="p"
        :cx="toX(p.longitude!)"
        :cy="toY(p.latitude!)"
        @click="$emit('pointClick', p.station_code)"
      />
    </svg>
    <div v-if="points.length === 0" class="map-placeholder">
      <span>暂无已审核坐标点位，请前往坐标校核页补全坐标</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import StationMarker from './StationMarker.vue'
import type { MapPoint } from '../types/api'

const props = defineProps<{ points: MapPoint[] }>()
defineEmits<{ (e: 'pointClick', code: string): void }>()

const W = 800
const H = 500

// Shenzhen bounding box approx
const LON_MIN = 113.75, LON_MAX = 114.62
const LAT_MIN = 22.44,  LAT_MAX = 22.86

const toX = (lon: number) => ((lon - LON_MIN) / (LON_MAX - LON_MIN)) * W
const toY = (lat: number) => H - ((lat - LAT_MIN) / (LAT_MAX - LAT_MIN)) * H

const points = computed(() =>
  props.points.filter((p) => p.has_coordinates && p.coordinate_status === 'approved'),
)
</script>

<style scoped>
.map-workspace {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--bg-base);
  overflow: hidden;
}
.scatter {
  width: 100%;
  height: 100%;
}
.map-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 13px;
  pointer-events: none;
}
</style>
