<template>
  <div class="map-workspace" :aria-label="`地图工作区，共 ${renderablePoints.length} 个可渲染坐标点位`">
    <svg
      class="scatter"
      :viewBox="`0 0 ${W} ${H}`"
      :aria-label="`散点工作区，展示 ${renderablePoints.length} 个已审核坐标点位`"
    >
      <defs>
        <pattern id="grid" width="80" height="50" patternUnits="userSpaceOnUse">
          <path d="M80 0H0V50" fill="none" stroke="rgba(139, 148, 158, 0.14)" stroke-width="1" />
        </pattern>
      </defs>
      <rect width="800" height="500" fill="url(#grid)" />
      <path
        class="reference-shape"
        d="M72,174 C137,111 217,87 318,98 C394,106 438,83 512,98 C614,119 701,184 740,262 C702,343 605,407 491,411 C403,414 328,384 252,401 C166,420 98,371 68,294 C45,236 45,201 72,174 Z"
      />
      <path class="coast-line" d="M435,390 C504,360 580,358 666,325 C707,309 735,282 754,250" />
      <text x="34" y="42" class="map-label">西</text>
      <text x="744" y="42" class="map-label">东</text>
      <text x="382" y="34" class="map-label">北</text>
      <text x="382" y="474" class="map-label">南</text>
      <text x="96" y="136" class="district-label">宝安 / 光明</text>
      <text x="290" y="128" class="district-label">龙华</text>
      <text x="450" y="146" class="district-label">龙岗</text>
      <text x="604" y="206" class="district-label">坪山</text>
      <text x="270" y="300" class="district-label">南山 / 福田</text>
      <text x="444" y="330" class="district-label">罗湖 / 盐田</text>
      <StationMarker
        v-for="p in renderablePoints"
        :key="p.station_code"
        :point="p"
        :cx="toX(p.longitude!)"
        :cy="toY(p.latitude!)"
        @click="$emit('pointClick', p.station_code)"
      />
    </svg>
    <div v-if="loading" class="map-state">
      <SkeletonBlock width="52%" height="14px" />
      <SkeletonBlock width="36%" height="14px" />
      <span>正在加载地图点位，接口较慢时仍保留工作区。</span>
    </div>
    <div v-else-if="error" class="map-state map-state--error">
      <ErrorState :message="error" />
    </div>
    <div v-else-if="renderablePoints.length === 0" class="map-state">
      <EmptyState message="暂无可渲染坐标点位。缺坐标点不进入地图，请查看右侧坐标统计。" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import StationMarker from './StationMarker.vue'
import SkeletonBlock from './SkeletonBlock.vue'
import ErrorState from './ErrorState.vue'
import EmptyState from './EmptyState.vue'
import { getRenderablePoints, type MapPointWithRisk } from '../utils/commandMap'

const props = defineProps<{
  points: MapPointWithRisk[]
  loading?: boolean
  error?: string | null
}>()
defineEmits<{ (e: 'pointClick', code: string): void }>()

const W = 800
const H = 500

// Shenzhen bounding box approx
const LON_MIN = 113.75, LON_MAX = 114.62
const LAT_MIN = 22.44,  LAT_MAX = 22.86

const toX = (lon: number) => ((lon - LON_MIN) / (LON_MAX - LON_MIN)) * W
const toY = (lat: number) => H - ((lat - LAT_MIN) / (LAT_MAX - LAT_MIN)) * H

const renderablePoints = computed(() => getRenderablePoints(props.points) as MapPointWithRisk[])
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
.map-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-muted);
  font-size: 13px;
  padding: 24px;
  text-align: center;
}
.map-state--error {
  align-items: stretch;
  margin: auto;
  max-width: 420px;
  inset: 0;
}
</style>
