<template>
  <div id="layout">
    <header class="topbar">
      <span class="topbar-brand">深圳积水监测</span>
      <span v-if="latestTime" class="topbar-time mono">最新观测: {{ latestTime }}</span>
      <span v-if="isHistoricalSnapshot" class="tag-historical">历史快照</span>
      <span class="health-dot" :class="healthStatus" :title="healthTitle" aria-label="服务状态"></span>
      <nav class="topbar-nav">
        <router-link to="/data-status">数据状态</router-link>
        <router-link to="/locations">坐标校核</router-link>
        <router-link to="/assessments">研判结果</router-link>
      </nav>
    </header>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useOverviewStore } from './stores/overview'
import { getHealth } from './api/health'

const overviewStore = useOverviewStore()
const latestTime = computed(() => overviewStore.latestObservedAt)
const isHistoricalSnapshot = computed(() => overviewStore.isHistoricalSnapshot)

type HealthStatus = 'ok' | 'error' | 'checking'
const healthStatus = ref<HealthStatus>('checking')
const healthTitle = computed(() => ({
  ok: '服务正常',
  error: '服务不可用',
  checking: '检查中...',
}[healthStatus.value]))

onMounted(async () => {
  overviewStore.load()
  try {
    await getHealth()
    healthStatus.value = 'ok'
  } catch {
    healthStatus.value = 'error'
  }
})
</script>

<style scoped>
#layout {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 44px;
  padding: 0 16px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.topbar-brand {
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.topbar-time {
  font-size: 13px;
  color: var(--text-secondary);
}

.tag-historical {
  font-size: 12px;
  padding: 2px 8px;
  background: rgba(210, 153, 34, 0.15);
  border: 1px solid rgba(210, 153, 34, 0.4);
  color: var(--risk-warning);
  border-radius: 4px;
}

.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.health-dot.ok       { background: #3FB950; }
.health-dot.error    { background: #DA3633; }
.health-dot.checking { background: #8B949E; }

.topbar-nav {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.topbar-nav a {
  font-size: 13px;
  padding: 4px 10px;
  border-radius: 4px;
  color: var(--text-secondary);
  transition: color 0.15s, background 0.15s;
}

.topbar-nav a:hover,
.topbar-nav a.router-link-active {
  color: var(--text-primary);
  background: var(--bg-raised);
}

.main-content {
  flex: 1;
  overflow: hidden;
}
</style>
