<template>
  <section class="map-section">
    <div ref="mapContainerRef" id="map-container"></div>

    <div class="map-overlay">
      <div class="overlay-item">
        <span class="overlay-label">在线车辆</span>
        <span class="overlay-value">{{ vehicles.length }}</span>
      </div>
      <div class="overlay-item">
        <span class="overlay-label">告警事件</span>
        <span class="overlay-value danger">{{ alertCount }}</span>
      </div>
    </div>

    <div v-if="selectedVehicle" class="info-panel">
      <button class="close-btn" @click="selectedVehicle = null">×</button>
      <h4>{{ selectedVehicle.name }}</h4>
      <div class="info-content">
        <p>位置: {{ selectedVehicle.position.join(', ') }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  vehicles: {
    type: Array,
    default: () => []
  },
  methaneSensors: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['vehicle-click', 'sensor-click'])

const mapContainerRef = ref(null)
const alertCount = ref(0)
const selectedVehicle = ref(null)

const vehicleMarkers = new Map()
const sensorMarkers = new Map()
const markerContainer = ref(null)

function initMap() {
  const container = mapContainerRef.value
  if (!container) return

  container.innerHTML = ''
  container.style.background = '#1a1d27'

  const floorPlan = document.createElement('img')
  floorPlan.src = '/floot.svg'
  floorPlan.alt = '楼层平面图'
  floorPlan.style.cssText = `
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 96%; height: 96%;
    object-fit: contain; pointer-events: none;
  `
  container.appendChild(floorPlan)

  const markerLayer = document.createElement('div')
  markerLayer.id = 'marker-layer'
  markerLayer.style.cssText = `
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
  `
  container.appendChild(markerLayer)
  markerContainer.value = markerLayer

  floorPlan.onload = () => {
    updateVehicleMarkers()
    updateSensorMarkers()
  }

  floorPlan.onerror = () => {
    console.warn('楼层平面图加载失败')
  }
}

function getMarkerPosition(x, z) {
  if (!markerContainer.value) return { left: 0, top: 0 }

  const container = markerContainer.value.parentElement
  const containerWidth = container.offsetWidth
  const containerHeight = container.offsetHeight
  const displayWidth = containerWidth * 0.96
  const displayHeight = containerHeight * 0.96

  // SVG viewBox="0 0 502 636"，世界坐标系 BOUNDS=12 → [-6, +6]
  // 世界 X 轴：-6=left, +6=right
  // 世界 Z 轴：-6=top(north), +6=bottom(south)，SVG Y轴朝下（Z小→Y小）无需翻转
  const SVG_WIDTH = 502
  const SVG_HEIGHT = 636
  const floorPlanRatio = SVG_WIDTH / SVG_HEIGHT
  const containerRatio = displayWidth / displayHeight

  let scaleX, scaleY, offsetX, offsetY

  const WORLD_SCALE = 12  // 世界坐标系范围 [-6, +6]

  if (containerRatio > floorPlanRatio) {
    // 容器更宽，Y方向填满，X方向letterbox
    scaleY = displayHeight / WORLD_SCALE
    scaleX = scaleY * floorPlanRatio
    offsetX = (displayWidth - scaleX * WORLD_SCALE) / 2
    offsetY = 0
  } else {
    // 容器更高，X方向填满，Y方向letterbox
    scaleX = displayWidth / WORLD_SCALE
    scaleY = scaleX / floorPlanRatio
    offsetX = 0
    offsetY = (displayHeight - scaleY * WORLD_SCALE) / 2
  }

  // 世界(-6,-6)→SVG(0,0)，世界(0,0)→SVG中心，世界(+6,+6)→SVG(SVG_WIDTH,SVG_HEIGHT)
  return {
    left: offsetX + (x + 6) * scaleX,
    top: offsetY + (z + 6) * scaleY
  }
}

function updateVehicleMarkers() {
  if (!markerContainer.value) return

  const currentIds = new Set(props.vehicles.map(v => v.id))

  vehicleMarkers.forEach((el, id) => {
    if (!currentIds.has(id)) {
      el.remove()
      vehicleMarkers.delete(id)
    }
  })

  props.vehicles.forEach(vehicle => {
    const [x, , z] = vehicle.position
    const pos = getMarkerPosition(x, z)

    if (vehicleMarkers.has(vehicle.id)) {
      const el = vehicleMarkers.get(vehicle.id)
      el.style.left = `${pos.left}px`
      el.style.top = `${pos.top}px`
    } else {
      const el = document.createElement('div')
      el.className = 'vehicle-marker'
      el.innerHTML = `<div class="vehicle-icon"></div>`
      el.title = `车辆 ${vehicle.id}`
      el.style.cssText = `
        position: absolute; left: ${pos.left}px; top: ${pos.top}px;
        width: 24px; height: 24px; cursor: pointer; pointer-events: auto;
      `
      el.onclick = () => {
        selectedVehicle.value = { name: `车辆 ${vehicle.id}`, position: vehicle.position }
        emit('vehicle-click', vehicle)
      }
      markerContainer.value.appendChild(el)
      vehicleMarkers.set(vehicle.id, el)
    }
  })
}

function updateSensorMarkers() {
  if (!markerContainer.value) return

  const currentIds = new Set(props.methaneSensors.map(s => s.id))

  sensorMarkers.forEach((el, id) => {
    if (!currentIds.has(id)) {
      el.remove()
      sensorMarkers.delete(id)
    }
  })

  props.methaneSensors.forEach(sensor => {
    const level = sensor.methane_percentage > 70 ? 'danger' : sensor.methane_percentage > 40 ? 'warning' : 'normal'
    const [x, , z] = sensor.location
    const pos = getMarkerPosition(x, z)

    if (sensorMarkers.has(sensor.id)) {
      const el = sensorMarkers.get(sensor.id)
      el.style.left = `${pos.left + 4}px`
      el.style.top = `${pos.top + 4}px`
      el.className = `sensor-marker ${level}`
    } else {
      const el = document.createElement('div')
      el.className = 'sensor-marker'
      el.innerHTML = `<div class="sensor-dot ${level}"></div>`
      el.title = `甲烷传感器 #${sensor.id} - ${sensor.methane_percentage}%`
      el.style.cssText = `
        position: absolute; left: ${pos.left + 4}px; top: ${pos.top + 4}px;
        width: 16px; height: 16px; cursor: pointer; pointer-events: auto;
      `
      el.onclick = () => emit('sensor-click', sensor)
      markerContainer.value.appendChild(el)
      sensorMarkers.set(sensor.id, el)
    }
  })
}

watch(() => props.vehicles, updateVehicleMarkers, { deep: true })
watch(() => props.methaneSensors, updateSensorMarkers, { deep: true })

onMounted(() => {
  initMap()
})

onUnmounted(() => {
  vehicleMarkers.forEach(el => el.remove())
  sensorMarkers.forEach(el => el.remove())
})
</script>
