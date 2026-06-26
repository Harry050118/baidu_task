<template>
  <div class="error-state" role="alert">
    <span class="error-state__icon" aria-hidden="true">!</span>
    <p class="error-state__msg">{{ displayMessage }}</p>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ code?: number; message?: string }>()

const CODE_MESSAGES: Record<number, string> = {
  404: '点位不存在或暂不支持该点位',
  422: '请求参数不合法，请修正后重试',
  503: '后端依赖暂不可用',
}

const displayMessage =
  props.message ?? (props.code ? CODE_MESSAGES[props.code] : '发生错误，请稍后重试')
</script>

<style scoped>
.error-state {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(218, 54, 51, 0.1);
  border: 1px solid rgba(218, 54, 51, 0.3);
  border-radius: 6px;
  color: var(--text-primary);
}
.error-state__icon {
  font-weight: 700;
  color: #DA3633;
  font-size: 16px;
  line-height: 1.4;
}
.error-state__msg {
  font-size: 13px;
  line-height: 1.5;
}
</style>
