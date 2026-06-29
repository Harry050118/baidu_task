<template>
  <g
    class="station-marker"
    :transform="`translate(${cx},${cy})`"
    role="button"
    :aria-label="`${point.station_name}，${riskMeta.label}`"
    tabindex="0"
    @click="$emit('click')"
    @keydown.enter="$emit('click')"
  >
    <circle class="hit-target" r="15" fill="transparent" />
    <circle class="marker-ring" r="8.5" fill="rgba(13, 17, 23, 0.86)" :stroke="riskMeta.color" stroke-width="1.8" />
    <circle class="marker-core" :r="coreRadius" :fill="riskMeta.color" />
    <circle
      v-if="point.risk_level === 'danger' || point.risk_level === 'warning'"
      class="marker-pulse"
      r="12"
      fill="none"
      :stroke="riskMeta.color"
      stroke-width="1"
      opacity="0.45"
    />
    <g v-if="point.risk_level === 'no_data'">
      <text y="4" text-anchor="middle" font-size="10" :fill="riskMeta.color">?</text>
    </g>
  </g>
</template>

<script setup lang="ts">
import type { MapPoint, RiskLevel } from '../types/api'

const props = defineProps<{
  point: MapPoint & { risk_level?: RiskLevel }
  cx: number
  cy: number
}>()
defineEmits<{ (e: 'click'): void }>()

const RISK_META: Record<RiskLevel, { label: string; color: string }> = {
  danger:    { label: '危险',   color: '#DA3633' },
  warning:   { label: '警戒',   color: '#D29922' },
  attention: { label: '关注',   color: '#9E6A03' },
  normal:    { label: '正常',   color: '#238636' },
  no_data:   { label: '无数据', color: '#484F58' },
}

const riskMeta = RISK_META[props.point.risk_level ?? 'no_data']
const coreRadius = props.point.risk_level === 'normal' ? 4.2 : 5.4
</script>

<style scoped>
.station-marker {
  cursor: pointer;
}
.station-marker:focus {
  outline: none;
}
.station-marker:focus .marker-ring,
.station-marker:hover .marker-ring,
.station-marker:focus .marker-core,
.station-marker:hover .marker-core {
  filter: brightness(1.3);
}
</style>
