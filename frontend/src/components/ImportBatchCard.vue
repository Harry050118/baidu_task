<template>
  <div class="card">
    <p class="card__label">最近导入批次</p>
    <SkeletonBlock v-if="loading" width="100%" height="60px" />
    <ErrorState v-else-if="error" :message="error" />
    <template v-else-if="data">
      <p class="card__value mono">{{ data.latest_imported_at ?? '—' }}</p>
      <p class="card__sub">记录 <span class="mono">{{ data.import_count?.toLocaleString() }}</span> &nbsp; 批次数 <span class="mono">{{ data.items.length }}</span></p>
    </template>
  </div>
</template>

<script setup lang="ts">
import SkeletonBlock from './SkeletonBlock.vue'
import ErrorState from './ErrorState.vue'
import type { LatestImportResponse } from '../types/api'
defineProps<{ data: LatestImportResponse | null; loading: boolean; error?: string | null }>()
</script>

<style scoped>
.card { background: var(--bg-raised); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }
.card__label { font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; }
.card__value { font-size: 15px; margin-bottom: 4px; }
.card__sub { font-size: 12px; color: var(--text-secondary); }
</style>
