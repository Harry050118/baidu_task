<template>
  <ul class="high-risk-list" aria-label="高风险点位列表">
    <li v-if="loading" class="state-row">
      <SkeletonBlock width="100%" height="16px" />
      <SkeletonBlock width="74%" height="16px" />
    </li>
    <li v-else-if="error" class="state-row">
      <ErrorState :message="error" />
    </li>
    <template v-else-if="items.length > 0">
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
        <span class="time mono">{{ item.latest_observed_at ?? '—' }}</span>
      </li>
    </template>
    <li v-else class="empty">
      当前无危险、警戒或关注点位；请继续关注最新观测时间和数据新鲜度。
    </li>
  </ul>
</template>

<script setup lang="ts">
import RiskBadge from './RiskBadge.vue'
import TrendIndicator from './TrendIndicator.vue'
import SkeletonBlock from './SkeletonBlock.vue'
import ErrorState from './ErrorState.vue'
import type { AssessmentItem } from '../types/api'

defineProps<{ items: AssessmentItem[]; loading?: boolean; error?: string | null }>()
defineEmits<{ (e: 'select', code: string): void }>()
</script>

<style scoped>
.high-risk-list { list-style: none; display: flex; flex-direction: column; gap: 6px; padding: 0; }
.risk-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 6px 8px;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  border: 1px solid transparent;
}
.risk-item:hover,
.risk-item:focus { background: var(--bg-raised); border-color: var(--border); outline: none; }
.name { flex: 1; color: var(--text-primary); }
.level { color: var(--text-secondary); }
.time {
  grid-column: 2 / 4;
  color: var(--text-muted);
  font-size: 11px;
}
.state-row {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.empty {
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.5;
  padding: 10px;
  border: 1px dashed var(--border);
  border-radius: 4px;
  background: rgba(31, 41, 55, 0.35);
}
</style>
