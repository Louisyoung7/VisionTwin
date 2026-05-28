<template>
  <aside class="stats-panel">
    <div class="panel-card">
      <h3>车辆统计</h3>
      <div ref="vehicleChartRef" class="chart-container"></div>
    </div>
    <div class="panel-card">
      <h3>甲烷浓度趋势</h3>
      <div ref="methaneChartRef" class="chart-container"></div>
    </div>
    <div class="panel-card">
      <h3>实时人流密度</h3>
      <div ref="densityChartRef" class="chart-container"></div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
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

const vehicleChartRef = ref(null)
const methaneChartRef = ref(null)
const densityChartRef = ref(null)

let vehicleChart = null
let methaneChart = null
let densityChart = null
let methaneUpdateInterval = null

function initVehicleChart() {
  if (!vehicleChartRef.value) return
  vehicleChart = echarts.init(vehicleChartRef.value)
  updateVehicleChart()
}

function updateVehicleChart() {
  if (!vehicleChart) return
  vehicleChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 8,
        borderColor: '#1a1d27',
        borderWidth: 2
      },
      label: { show: true, color: '#e4e4e7' },
      data: [
        { value: 12, name: '正常行驶', itemStyle: { color: '#22c55e' } },
        { value: 3, name: '临时停车', itemStyle: { color: '#f59e0b' } },
        { value: props.alertCount || 1, name: '违停告警', itemStyle: { color: '#ef4444' } }
      ]
    }]
  })
}

function initMethaneChart() {
  if (!methaneChartRef.value) return
  methaneChart = echarts.init(methaneChartRef.value)
  updateMethaneChart()
}

function updateMethaneChart() {
  if (!methaneChart) return

  const timestamps = []
  const data1 = []
  const data2 = []
  const now = Date.now()

  for (let i = 10; i >= 0; i--) {
    timestamps.push(new Date(now - i * 3000).toLocaleTimeString())
    data1.push(Math.random() * 30 + 20)
    data2.push(Math.random() * 20 + 10)
  }

  methaneChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLine: { lineStyle: { color: '#2a2e3d' } },
      axisLabel: { color: '#8b8d98', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#2a2e3d' } },
      axisLabel: { color: '#8b8d98' },
      splitLine: { lineStyle: { color: '#2a2e3d' } }
    },
    series: [
      {
        name: '传感器1',
        type: 'line',
        smooth: true,
        data: data1,
        lineStyle: { color: '#22c55e' },
        areaStyle: { color: 'rgba(34, 197, 94, 0.2)' }
      },
      {
        name: '传感器2',
        type: 'line',
        smooth: true,
        data: data2,
        lineStyle: { color: '#3b82f6' },
        areaStyle: { color: 'rgba(59, 130, 246, 0.2)' }
      }
    ],
    grid: { left: 40, right: 10, top: 30, bottom: 30 }
  })
}

function initDensityChart() {
  if (!densityChartRef.value) return
  densityChart = echarts.init(densityChartRef.value)
  updateDensityChart()
}

function updateDensityChart() {
  if (!densityChart) return

  const hours = ['6:00', '8:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00']
  const pedestrian = [120, 350, 280, 520, 300, 380, 680, 240]
  const vehicle = [80, 150, 120, 180, 140, 160, 200, 100]

  densityChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['行人', '车辆'],
      textStyle: { color: '#8b8d98' }
    },
    xAxis: {
      type: 'category',
      data: hours,
      axisLine: { lineStyle: { color: '#2a2e3d' } },
      axisLabel: { color: '#8b8d98', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#2a2e3d' } },
      axisLabel: { color: '#8b8d98' },
      splitLine: { lineStyle: { color: '#2a2e3d' } }
    },
    series: [
      {
        name: '行人',
        type: 'bar',
        data: pedestrian,
        itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] }
      },
      {
        name: '车辆',
        type: 'bar',
        data: vehicle,
        itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] }
      }
    ],
    grid: { left: 40, right: 10, top: 40, bottom: 30 }
  })
}

function resizeCharts() {
  vehicleChart?.resize()
  methaneChart?.resize()
  densityChart?.resize()
}

watch(() => props.alertCount, updateVehicleChart)

onMounted(() => {
  initVehicleChart()
  initMethaneChart()
  initDensityChart()

  window.addEventListener('resize', resizeCharts)

  methaneUpdateInterval = setInterval(updateMethaneChart, 3000)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  if (methaneUpdateInterval) clearInterval(methaneUpdateInterval)
  vehicleChart?.dispose()
  methaneChart?.dispose()
  densityChart?.dispose()
})
</script>
