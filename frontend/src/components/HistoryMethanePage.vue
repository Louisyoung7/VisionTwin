<template>
  <div class="page-container">
    <!-- 工具栏 -->
    <div class="page-toolbar">
      <div class="toolbar-left">
        <select v-model="selectedSensor" class="filter-select">
          <option value="">全部传感器</option>
          <option v-for="s in sensors" :key="s" :value="s">传感器 {{ s }}</option>
        </select>
        <select v-model="timeRange" class="filter-select">
          <option value="1">最近1小时</option>
          <option value="6">最近6小时</option>
          <option value="24">最近24小时</option>
          <option value="168">最近一周</option>
        </select>
      </div>
      <div class="toolbar-right">
        <span class="data-count">共 {{ chartData.length }} 条数据</span>
        <button class="btn-refresh" @click="loadData">刷新</button>
      </div>
    </div>

    <!-- 趋势图 -->
    <div class="chart-container">
      <div class="chart-header">
        <span class="chart-title">甲烷浓度趋势</span>
        <div class="chart-legend">
          <span class="legend-item"><span class="dot warning"></span>预警线 40%</span>
          <span class="legend-item"><span class="dot danger"></span>危险线 70%</span>
        </div>
      </div>
      <div class="chart-area" ref="chartRef">
        <svg class="chart-svg" :viewBox="`0 0 ${chartWidth} ${chartHeight}`">
          <!-- 网格线 -->
          <line v-for="i in 5" :key="'grid-'+i"
            :x1="padding" :y1="padding + (i-1) * (chartHeight - padding * 2) / 4"
            :x2="chartWidth - padding" :y2="padding + (i-1) * (chartHeight - padding * 2) / 4"
            stroke="#2a2e3d" stroke-width="1" />
          <!-- 预警线 -->
          <line :x1="padding" :y1="getY(40)" :x2="chartWidth - padding" :y2="getY(40)"
            stroke="#f59e0b" stroke-width="1" stroke-dasharray="5,3" />
          <!-- 危险线 -->
          <line :x1="padding" :y1="getY(70)" :x2="chartWidth - padding" :y2="getY(70)"
            stroke="#ef4444" stroke-width="1" stroke-dasharray="5,3" />
          <!-- 数据线 -->
          <polyline v-if="polylinePoints"
            :points="polylinePoints"
            fill="none"
            stroke="#3b82f6"
            stroke-width="2" />
          <!-- 数据点 -->
          <circle v-for="(d, i) in chartData" :key="'point-'+i"
            :cx="getX(i)" :cy="getY(d.methane_percentage)"
            r="3" :fill="getPointColor(d.methane_percentage)" />
        </svg>
        <!-- Y轴标签 -->
        <div class="y-axis">
          <span>100%</span>
          <span>75%</span>
          <span>50%</span>
          <span>25%</span>
          <span>0%</span>
        </div>
        <!-- X轴标签 -->
        <div class="x-axis">
          <span v-for="(d, i) in xLabels" :key="i">{{ d }}</span>
        </div>
      </div>
    </div>

    <!-- 数据统计 -->
    <div class="stats-row">
      <div class="stat-card">
        <span class="stat-label">平均浓度</span>
        <span class="stat-value">{{ avgValue }}%</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">最大浓度</span>
        <span class="stat-value danger">{{ maxValue }}%</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">最小浓度</span>
        <span class="stat-value">{{ minValue }}%</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">数据条数</span>
        <span class="stat-value">{{ chartData.length }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { fetchHistoryMethane } from '../api.js'

const emit = defineEmits(['refresh'])

const chartData = ref([])
const sensors = ref([1, 2, 3, 4])
const selectedSensor = ref('')
const timeRange = ref('24')
const chartRef = ref(null)
const chartWidth = 800
const chartHeight = 300
const padding = 30

const polylinePoints = computed(() => {
  if (chartData.value.length < 2) return ''
  return chartData.value.map((d, i) => `${getX(i)},${getY(d.methane_percentage)}`).join(' ')
})

const xLabels = computed(() => {
  if (chartData.value.length === 0) return []
  const step = Math.max(1, Math.floor(chartData.value.length / 6))
  return chartData.value.filter((_, i) => i % step === 0)
    .map(d => formatTime(d.timestamp))
})

const avgValue = computed(() => {
  if (chartData.value.length === 0) return 0
  const sum = chartData.value.reduce((acc, d) => acc + d.methane_percentage, 0)
  return (sum / chartData.value.length).toFixed(1)
})

const maxValue = computed(() => {
  if (chartData.value.length === 0) return 0
  return Math.max(...chartData.value.map(d => d.methane_percentage)).toFixed(1)
})

const minValue = computed(() => {
  if (chartData.value.length === 0) return 0
  return Math.min(...chartData.value.map(d => d.methane_percentage)).toFixed(1)
})

function getX(index) {
  if (chartData.value.length <= 1) return padding
  return padding + (index / (chartData.value.length - 1)) * (chartWidth - padding * 2)
}

function getY(value) {
  return padding + (1 - value / 100) * (chartHeight - padding * 2)
}

function getPointColor(value) {
  if (value >= 70) return '#ef4444'
  if (value >= 40) return '#f59e0b'
  return '#3b82f6'
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function loadData() {
  try {
    const params = { hours: parseInt(timeRange.value) }
    if (selectedSensor.value) {
      params.sensor_id = parseInt(selectedSensor.value)
    }
    const data = await fetchHistoryMethane(params)
    // 按时间正序排列
    chartData.value = (data.methane_history || []).reverse()
  } catch (e) { console.error('加载甲烷历史失败:', e) }
}

watch([selectedSensor, timeRange], () => loadData())

onMounted(() => loadData())
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
}

.page-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
}

.toolbar-left { display: flex; align-items: center; gap: 10px; }
.toolbar-right { display: flex; align-items: center; gap: 12px; }

.filter-select {
  padding: 7px 10px;
  background: var(--bg-dark);
  border: 1px solid var(--border);
  border-radius: 5px;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.btn-refresh {
  padding: 7px 16px;
  background: var(--info);
  border: none;
  border-radius: 5px;
  color: white;
  font-size: 13px;
  cursor: pointer;
}

.data-count { font-size: 13px; color: var(--text-secondary); }

.chart-container {
  flex: 1;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border);
  padding: 16px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-title { font-weight: 600; font-size: 14px; }

.chart-legend { display: flex; gap: 16px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-secondary); }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.warning { background: var(--warning); }
.dot.danger { background: var(--danger); }

.chart-area {
  flex: 1;
  position: relative;
  min-height: 250px;
}

.chart-svg {
  width: 100%;
  height: 100%;
}

.y-axis {
  position: absolute;
  left: 0;
  top: 30px;
  bottom: 30px;
  width: 30px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-secondary);
  text-align: right;
  padding-right: 4px;
}

.x-axis {
  position: absolute;
  bottom: 0;
  left: 30px;
  right: 0;
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-secondary);
}

.stats-row {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

.stat-card {
  flex: 1;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-label { font-size: 12px; color: var(--text-secondary); }
.stat-value { font-size: 20px; font-weight: 600; }
.stat-value.danger { color: var(--danger); }
</style>
