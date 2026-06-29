<template>
  <Transition name="drawer">
    <aside v-if="point" class="drawer" role="complementary" :aria-label="`点位详情：${point.station_name}`">
      <header class="drawer__header">
        <div>
          <p class="drawer__name">{{ point.station_name }}</p>
          <p class="drawer__code mono">站码 {{ point.station_code }}</p>
        </div>
        <button class="drawer__close" aria-label="关闭抽屉" @click="$emit('close')">✕</button>
      </header>
      <div class="drawer__body">
        <p class="drawer__level mono">{{ levelDisplay }}</p>
        <div class="drawer__status">
          <RiskBadge :level="assessment?.risk_level ?? 'no_data'" />
          <TrendIndicator :trend="assessment?.trend ?? 'no_data'" />
        </div>
        <p class="drawer__time mono">观测时间 {{ point.latest_observed_at ?? '—' }}</p>
        <hr class="divider" />
        <div class="field-list">
          <div class="field-row">
            <span>坐标状态</span>
            <CoordStatusTag :status="point.coordinate_status" :source="point.coord_source" />
          </div>
          <div class="field-row">
            <span>坐标来源</span>
            <strong>{{ point.coord_source ?? '未提供' }}</strong>
          </div>
          <div class="field-row">
            <span>坐标质量</span>
            <strong>{{ point.coord_quality ?? '未提供' }}</strong>
          </div>
        </div>
        <hr class="divider" />
        <div class="drawer__actions">
          <router-link :to="`/points/${point.station_code}`">
            <button>查看历史曲线</button>
          </router-link>
          <router-link :to="{ path: '/assessments', query: { stationCode: point.station_code } }">
            <button>查看研判</button>
          </router-link>
        </div>
      </div>
    </aside>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import RiskBadge from './RiskBadge.vue'
import TrendIndicator from './TrendIndicator.vue'
import CoordStatusTag from './CoordStatusTag.vue'
import type { MapPoint, AssessmentItem } from '../types/api'

const props = defineProps<{
  point: MapPoint | null
  assessment?: AssessmentItem | null
}>()
defineEmits<{ (e: 'close'): void }>()

const levelDisplay = computed(() => {
  const v = props.point?.latest_water_level_m
  return v != null ? `${v.toFixed(2)} m` : '— m'
})
</script>

<style scoped>
.drawer {
  position: absolute;
  top: 0;
  right: 0;
  width: 280px;
  height: 100%;
  background: var(--bg-surface);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 10;
  overflow-y: auto;
}
.drawer__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  border-bottom: 1px solid var(--border);
}
.drawer__name { font-size: 15px; font-weight: 600; }
.drawer__code { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.drawer__close { background: none; border: none; color: var(--text-secondary); padding: 0; font-size: 16px; }
.drawer__body { padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.drawer__level { font-size: 28px; font-weight: 700; }
.drawer__status { display: flex; gap: 12px; align-items: center; }
.drawer__time { font-size: 12px; color: var(--text-secondary); }
.divider { border: none; border-top: 1px solid var(--border); }
.field-list { display: flex; flex-direction: column; gap: 8px; }
.field-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 12px;
}
.field-row strong { color: var(--text-primary); font-weight: 500; }
.drawer__actions { display: flex; gap: 8px; flex-wrap: wrap; }

.drawer-enter-active, .drawer-leave-active { transition: transform 0.2s ease; }
.drawer-enter-from, .drawer-leave-to { transform: translateX(100%); }
</style>
