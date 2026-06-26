<template>
  <div class="chart-wrap" aria-label="历史水位折线图">
    <SkeletonBlock v-if="loading" width="100%" height="300px" />
    <ErrorState v-else-if="error" :message="error" />
    <v-chart v-else :option="option" autoresize style="width:100%;height:300px;" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import SkeletonBlock from './SkeletonBlock.vue'
import ErrorState from './ErrorState.vue'
import type { WaterLevelRecord } from '../types/api'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const props = defineProps<{
  records: WaterLevelRecord[]
  loading: boolean
  error?: string | null
}>()

const option = computed(() => ({
  backgroundColor: 'transparent',
  textStyle: { color: '#8B949E', fontFamily: 'JetBrains Mono, Consolas, monospace' },
  grid: { left: 60, right: 20, top: 20, bottom: 40 },
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#161B22',
    borderColor: '#30363D',
    textStyle: { color: '#E6EDF3', fontSize: 12 },
    formatter: (params: unknown[]) => {
      const p = (params as Array<{ axisValue: string; value: [string, number | null] }>)[0]
      const v = p.value[1]
      return `${p.axisValue}<br/>${v != null ? v.toFixed(3) + ' m' : '无数据'}`
    },
  },
  xAxis: {
    type: 'time',
    axisLabel: { fontSize: 11, color: '#484F58' },
    axisLine: { lineStyle: { color: '#30363D' } },
    splitLine: { show: false },
  },
  yAxis: {
    type: 'value',
    name: '水位 (m)',
    nameTextStyle: { color: '#484F58', fontSize: 11 },
    axisLabel: { fontSize: 11, color: '#484F58', formatter: (v: number) => v.toFixed(1) },
    splitLine: { lineStyle: { color: '#1F2937' } },
  },
  series: [{
    type: 'line',
    data: props.records.map((r) => [r.observed_at, r.water_level_m]),
    connectNulls: false,   // null values break the line — don't fill with 0
    symbol: 'none',
    lineStyle: { color: '#58A6FF', width: 1.5 },
    itemStyle: { color: '#58A6FF' },
  }],
}))
</script>
