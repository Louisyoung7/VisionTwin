<template>
  <aside class="alert-panel">
    <div class="panel-header">
      <h2>实时告警</h2>
      <span class="status-indicator" :class="{ online: alerts.length > 0 }"></span>
    </div>
    <div class="alert-list">
      <div v-if="alerts.length === 0" class="empty-tip">暂无告警信息</div>
      <div
        v-for="alert in alerts"
        :key="alert.id"
        class="alert-item"
        :class="alert.type"
      >
        <div class="alert-header">
          <span class="alert-type">{{ alert.type === 'danger' ? '危险告警' : '预警提示' }}</span>
          <span class="alert-time">{{ alert.time }}</span>
        </div>
        <div class="alert-message">{{ alert.message }}</div>
        <div class="alert-location">位置: {{ alert.location }}</div>
      </div>
    </div>

    <div class="panel-header">
      <h2>甲烷气体监测</h2>
    </div>
    <div class="sensor-list">
      <div v-if="sensors.length === 0" class="loading">加载中...</div>
      <div
        v-for="sensor in sensors"
        :key="sensor.id"
        class="sensor-item"
        :class="getSensorLevel(sensor.methane_percentage)"
      >
        <div class="sensor-header">
          <span class="sensor-id">传感器 #{{ sensor.id }}</span>
          <span class="sensor-value">{{ sensor.methane_percentage }}%</span>
        </div>
        <div class="sensor-bar">
          <div
            class="sensor-fill"
            :class="getSensorLevel(sensor.methane_percentage)"
            :style="{ width: sensor.methane_percentage + '%' }"
          ></div>
        </div>
        <div class="sensor-location">
          位置: {{ sensor.location[0].toFixed(1) }}, {{ sensor.location[2].toFixed(1) }}
        </div>
        <div class="sensor-status" :class="getSensorLevel(sensor.methane_percentage)">
          {{ getStatusText(sensor.methane_percentage) }}
        </div>
      </div>
    </div>

    <div class="panel-footer">
      <button class="refresh-btn" @click="$emit('refresh')">
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path fill="currentColor" d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
        </svg>
        刷新数据
      </button>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  alerts: {
    type: Array,
    default: () => []
  },
  sensors: {
    type: Array,
    default: () => []
  }
})

defineEmits(['refresh'])

function getSensorLevel(percentage) {
  if (percentage > 70) return 'danger'
  if (percentage > 40) return 'warning'
  return 'normal'
}

function getStatusText(percentage) {
  const level = getSensorLevel(percentage)
  if (level === 'danger') return '告警'
  if (level === 'warning') return '预警'
  return '正常'
}
</script>
