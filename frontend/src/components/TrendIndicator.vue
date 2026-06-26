<template>
  <span class="trend-indicator" :aria-label="meta.label">
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <path :d="meta.path" :stroke="meta.color" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <span :style="{ color: meta.color }">{{ meta.label }}</span>
  </span>
</template>

<script setup lang="ts">
import type { Trend } from '../types/api'

const props = defineProps<{ trend: Trend }>()

const MAP: Record<Trend, { label: string; color: string; path: string }> = {
  rising:      { label: '↑ 上升',  color: '#F85149', path: 'M2 11 L7 3 L12 11' },
  falling:     { label: '↓ 下降',  color: '#3FB950', path: 'M2 3 L7 11 L12 3' },
  stable:      { label: '→ 稳定',  color: '#8B949E', path: 'M2 7 L12 7' },
  fluctuating: { label: '↕ 波动',  color: '#E3B341', path: 'M2 10 L5 4 L8 10 L11 4' },
  no_data:     { label: '— 无数据', color: '#484F58', path: 'M3 7 L11 7' },
}

const meta = MAP[props.trend] ?? MAP.no_data
</script>

<style scoped>
.trend-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}
</style>
