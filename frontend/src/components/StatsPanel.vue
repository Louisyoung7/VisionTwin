<template>
  <aside class="stats-panel">
    <div class="stats-summary">
      <div class="summary-title">系统概览</div>
      <div class="summary-item">
        <span class="summary-label">行驶车辆</span>
        <span class="summary-value">{{ vehicleCount }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">监控摄像</span>
        <span class="summary-value">{{ cameraCount }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">告警事件</span>
        <span class="summary-value" :class="alertCount > 0 ? 'danger' : ''">{{ alertCount }}</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  vehicleCount: {
    type: Number,
    default: 0
  },
  cameraCount: {
    type: Number,
    default: 0
  },
  alertCount: {
    type: Number,
    default: 0
  }
})
</script>
