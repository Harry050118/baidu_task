<template>
  <ul class="high-risk-list" aria-label="高风险点位列表">
    <li
      v-for="item in items"
      :key="item.station_code"
      class="risk-item"
      :tabindex="0"
      @click="$emit('select', item.station_code)"
      @keydown.enter="$emit('select', item.station_code)"
    >
      <RiskBadge :level="item.risk_level" />
      <span class="name">{{ item.station_name }}</span>
      <span class="level mono">{{ item.latest_water_level_m != null ? item.latest_water_level_m.toFixed(2) + 'm' : '—' }}</span>
      <TrendIndicator :trend="item.trend" />
    </li>
    <li v-if="items.length === 0" class="empty">暂无高风险点位</li>
  </ul>
</template>

<script setup lang="ts">
import RiskBadge from './RiskBadge.vue'
import TrendIndicator from './TrendIndicator.vue'
import type { AssessmentItem } from '../types/api'

defineProps<{ items: AssessmentItem[] }>()
defineEmits<{ (e: 'select', code: string): void }>()
</script>

<style scoped>
.high-risk-list { list-style: none; display: flex; flex-direction: column; gap: 4px; padding: 0; }
.risk-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}
.risk-item:hover { background: var(--bg-raised); }
.name { flex: 1; color: var(--text-primary); }
.level { color: var(--text-secondary); }
.empty { color: var(--text-muted); font-size: 13px; padding: 8px; }
</style>
