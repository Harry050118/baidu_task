<template>
  <span v-if="isHistorical" class="freshness-tag historical" aria-label="历史快照">
    历史快照
  </span>
  <span v-else class="freshness-tag realtime" aria-label="实时数据">
    实时
  </span>
</template>

<script setup lang="ts">
const props = defineProps<{ status: string }>()
const isHistorical = props.status === 'historical_snapshot'
</script>

<style scoped>
.freshness-tag {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 3px;
  border: 1px solid;
}
.freshness-tag.historical {
  color: #D29922;
  border-color: rgba(210,153,34,0.4);
  background: rgba(210,153,34,0.12);
}
.freshness-tag.realtime {
  color: #3FB950;
  border-color: rgba(63,185,80,0.4);
  background: rgba(63,185,80,0.1);
}
</style>
