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

    <div class="panel-header">
      <h2>行驶车辆</h2>
    </div>
    <div class="vehicle-table-container">
      <table v-if="vehicles.length > 0" class="vehicle-table">
        <thead>
          <tr>
            <th>车牌号</th>
            <th>积分</th>
            <th>路线ID</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in vehicles" :key="v.plate">
            <td class="plate-cell">{{ v.plate }}</td>
            <td>
              <span
                class="score-cell"
                :class="v.score >= 80 ? 'high' : v.score < 60 ? 'low' : ''"
              >{{ v.score !== undefined ? v.score : '-' }}</span>
            </td>
            <td class="route-cell">{{ v.route_id || '-' }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-tip">暂无行驶车辆</div>
    </div>

    <div class="panel-header">
      <h2>停靠车辆</h2>
    </div>
    <div class="vehicle-table-container">
      <table v-if="dockedVehicles.length > 0" class="vehicle-table">
        <thead>
          <tr>
            <th>车牌号</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in dockedVehicles" :key="v.id">
            <td class="plate-cell">{{ v.plate }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-tip">暂无停靠车辆</div>
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
  },
  vehicles: {
    type: Array,
    default: () => []
  },
  dockedVehicles: {
    type: Array,
    default: () => []
  }
})

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
