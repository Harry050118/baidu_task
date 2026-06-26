<template>
  <div class="assessment-list">
    <h1 class="page-title">规则研判</h1>
    <AssessmentTable :items="items" :loading="loading" :error="error" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AssessmentTable from '../components/AssessmentTable.vue'
import { getAssessments } from '../api/assessments'
import type { AssessmentItem } from '../types/api'

const items = ref<AssessmentItem[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

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
</style>
