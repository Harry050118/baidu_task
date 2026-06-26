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
    <!-- danger/warning: filled circle -->
    <circle
      v-if="point.risk_level === 'danger' || point.risk_level === 'warning'"
      r="7" :fill="riskMeta.color" :stroke="riskMeta.color" stroke-width="1.5"
    />
    <!-- attention: half-filled circle -->
    <g v-else-if="point.risk_level === 'attention'">
      <circle r="7" fill="none" :stroke="riskMeta.color" stroke-width="1.5" />
      <path :d="`M0,-7 A7,7 0 0 1 0,7 Z`" :fill="riskMeta.color" />
    </g>
    <!-- normal: hollow circle -->
    <circle
      v-else-if="point.risk_level === 'normal'"
      r="7" fill="none" :stroke="riskMeta.color" stroke-width="1.5"
    />
    <!-- no_data: question mark -->
    <g v-else>
      <circle r="7" fill="none" :stroke="riskMeta.color" stroke-width="1.5" />
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
</script>

<style scoped>
.station-marker {
  cursor: pointer;
}
.station-marker:focus {
  outline: none;
}
.station-marker:focus > circle,
.station-marker:hover > circle {
  filter: brightness(1.3);
}
</style>
