<template>
  <div id="app">
    <header>
      <div class="header-left">
        <h1>智瞳云枢</h1>
        <span class="subtitle">校园安全全息感知与智能管理系统</span>
      </div>
      <div class="header-right">
        <div class="status-item">
          <span class="status-dot" :class="{ online: isOnline }"></span>
          <span>{{ isOnline ? '系统在线' : '系统离线' }}</span>
        </div>
        <div class="status-item">
          <span id="time-display">{{ currentTime }}</span>
        </div>
      </div>
    </header>

    <main class="dashboard">
      <StatsPanel
        :vehicleCount="vehicleCount"
        :cameraCount="cameraCount"
        :alertCount="alertCount"
      />

      <MapView
        :vehicles="vehicles"
        :methaneSensors="methaneSensors"
        @vehicle-click="handleVehicleClick"
        @sensor-click="handleSensorClick"
      />

      <AlertPanel
        :alerts="alerts"
        :sensors="methaneSensors"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import StatsPanel from './components/StatsPanel.vue'
import MapView from './components/MapView.vue'
import AlertPanel from './components/AlertPanel.vue'
import { fetchMethaneSensors, fetchAlerts } from './api.js'

const isOnline = ref(true)
const currentTime = ref('')
const vehicleCount = ref(0)
const cameraCount = ref(5)
const alertCount = ref(0)
const vehicles = ref([])
const methaneSensors = ref([])
const alerts = ref([])

let ws = null
let timeInterval = null
let pollInterval = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function connectWebSocket() {
  ws = new WebSocket('ws://127.0.0.1:8000/ws')

  ws.onopen = () => {
    console.log('WebSocket 已连接（车辆实时推送）')
    isOnline.value = true
    reconnectAttempts = 0
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.vehicles) {
        vehicles.value = data.vehicles
        vehicleCount.value = vehicles.value.length
      }
    } catch (error) {
      console.error('解析消息失败:', error)
    }
  }

  ws.onerror = () => {
    isOnline.value = false
  }

  ws.onclose = () => {
    isOnline.value = false
    reconnectAttempts++
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      setTimeout(connectWebSocket, reconnectAttempts * 3000)
    }
  }
}

async function loadMethaneSensors() {
  try {
    const data = await fetchMethaneSensors()
    methaneSensors.value = data.methane || []
  } catch (error) {
    console.error('加载甲烷传感器失败:', error)
  }
}

async function loadAlerts() {
  try {
    const data = await fetchAlerts()
    alerts.value = (data.alerts || []).map(a => ({
      id: a.id,
      type: a.level,
      message: a.message,
      location: `${a.location[0]}, ${a.location[2]}`,
      time: a.time
    }))
    alertCount.value = alerts.value.filter(a => a.type === 'danger').length
  } catch (error) {
    console.error('加载告警失败:', error)
  }
}

async function pollData() {
  await Promise.all([loadMethaneSensors(), loadAlerts()])
}

function handleVehicleClick(vehicle) {
  console.log('点击车辆:', vehicle)
}

function handleSensorClick(sensor) {
  console.log('点击传感器:', sensor)
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
  connectWebSocket()
  pollData()
  pollInterval = setInterval(pollData, 1000)
})

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval)
  if (pollInterval) clearInterval(pollInterval)
  if (ws) ws.close()
})
</script>
