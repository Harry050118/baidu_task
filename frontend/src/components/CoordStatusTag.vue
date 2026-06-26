<template>
  <span class="coord-tag" :class="cls" :aria-label="label">{{ label }}</span>
</template>

<script setup lang="ts">
import type { CoordinateStatus } from '../types/api'

const props = defineProps<{ status: CoordinateStatus; source?: string }>()

const MAP: Record<CoordinateStatus, { label: string; cls: string }> = {
  approved:             { label: '已审核', cls: 'approved' },
  missing_coordinates:  { label: '坐标缺失', cls: 'missing' },
  pending:              { label: '待审核', cls: 'pending' },
  rejected:             { label: '已拒绝', cls: 'rejected' },
}

const meta = MAP[props.status] ?? { label: props.status, cls: 'missing' }
const label = props.source ? `${props.source} · ${meta.label}` : meta.label
const cls = meta.cls
</script>

<style scoped>
.coord-tag {
  display: inline-block;
  font-size: 12px;
  padding: 1px 6px;
  border-radius: 3px;
  border: 1px solid;
}
.coord-tag.approved  { color: #3FB950; border-color: rgba(63,185,80,0.4); background: rgba(63,185,80,0.1); }
.coord-tag.missing   { color: #DA3633; border-color: rgba(218,54,51,0.4); background: rgba(218,54,51,0.1); }
.coord-tag.pending   { color: #D29922; border-color: rgba(210,153,34,0.4); background: rgba(210,153,34,0.1); }
.coord-tag.rejected  { color: #8B949E; border-color: rgba(139,148,158,0.4); background: rgba(139,148,158,0.1); }
</style>
