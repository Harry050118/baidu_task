<template>
  <span class="risk-badge" :style="badgeStyle" :aria-label="label">
    <span class="risk-badge__bar" :style="{ background: color }"></span>
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import type { RiskLevel } from '../types/api'

const props = defineProps<{ level: RiskLevel }>()

const MAP: Record<RiskLevel, { label: string; color: string }> = {
  danger:    { label: '危险', color: '#DA3633' },
  warning:   { label: '警戒', color: '#D29922' },
  attention: { label: '关注', color: '#9E6A03' },
  normal:    { label: '正常', color: '#238636' },
  no_data:   { label: '无数据', color: '#484F58' },
}

const color = MAP[props.level]?.color ?? '#484F58'
const label = MAP[props.level]?.label ?? props.level

const badgeStyle = {
  background: `${color}1F`,
}
</script>

<style scoped>
.risk-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 8px 2px 4px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  border-left: 4px solid v-bind(color);
  color: v-bind(color);
}
.risk-badge__bar {
  display: none;
}
</style>
