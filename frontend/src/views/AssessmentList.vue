<template>
  <div class="assessment-list">
    <h1 class="page-title">规则研判</h1>
    <p v-if="targetStationCode" class="target-hint">已定位站点 {{ targetStationCode }}</p>
    <AssessmentTable
      :items="items"
      :loading="loading"
      :error="error"
      :target-station-code="targetStationCode"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AssessmentTable from '../components/AssessmentTable.vue'
import { getAssessments } from '../api/assessments'
import type { AssessmentItem } from '../types/api'

const route = useRoute()
const items = ref<AssessmentItem[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const targetStationCode = computed(() => {
  const value = route.query.stationCode
  return typeof value === 'string' && value.length > 0 ? value : null
})

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    const data = await getAssessments()
    items.value = data.items
  } catch (e: unknown) {
    error.value = (e as { userMessage?: string })?.userMessage ?? '加载研判数据失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.assessment-list { padding: 24px; max-width: 1100px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }
.page-title { font-size: 18px; font-weight: 600; }
.target-hint { font-size: 12px; color: var(--chart-line); }
</style>
