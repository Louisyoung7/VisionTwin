<template>
  <div class="page-container">
    <!-- 工具栏 -->
    <div class="page-toolbar">
      <div class="toolbar-left">
        <select v-model="selectedPlate" class="filter-select">
          <option value="">全部车辆</option>
          <option v-for="p in plates" :key="p" :value="p">{{ p }}</option>
        </select>
        <select v-model="timeRange" class="filter-select">
          <option value="1">最近1小时</option>
          <option value="6">最近6小时</option>
          <option value="24">最近24小时</option>
          <option value="168">最近一周</option>
        </select>
      </div>
      <div class="toolbar-right">
        <span class="data-count">共 {{ filteredData.length }} 条记录</span>
        <button class="btn-refresh" @click="loadData">刷新</button>
      </div>
    </div>

    <!-- 积分趋势曲线图 -->
    <div class="chart-container">
      <div class="chart-header">
        <span class="chart-title">积分变化趋势</span>
      </div>
      <div ref="chartRef" class="chart-area"></div>
    </div>

    <!-- 统计数据 -->
    <div class="stats-row">
      <div class="stat-card">
        <span class="stat-label">扣分总数</span>
        <span class="stat-value danger">{{ totalDeduction }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">涉及车辆</span>
        <span class="stat-value">{{ plates.length }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">最低积分</span>
        <span class="stat-value danger">{{ minScore }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">记录条数</span>
        <span class="stat-value">{{ filteredData.length }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { fetchHistoryScore } from '../api.js'

const emit = defineEmits(['refresh'])

const scoreData = ref([])
const plates = ref([])
const selectedPlate = ref('')
const timeRange = ref('24')
const chartRef = ref(null)
let chartInstance = null

const filteredData = computed(() => {
  if (!selectedPlate.value) return scoreData.value
  return scoreData.value.filter(d => d.plate === selectedPlate.value)
})

const totalDeduction = computed(() => {
  return filteredData.value.reduce((acc, d) => acc + Math.max(0, d.old_score - d.new_score), 0)
})

const minScore = computed(() => {
  if (filteredData.value.length === 0) return 100
  return Math.min(...filteredData.value.map(d => d.new_score))
})

// 按车牌分组，构建 ECharts series
function buildChartOption() {
  // 按时间正序
  const sorted = [...filteredData.value].sort(
    (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
  )

  // 按车牌分组
  const plateGroups = {}
  for (const item of sorted) {
    if (!plateGroups[item.plate]) {
      plateGroups[item.plate] = []
    }
    plateGroups[item.plate].push(item)
  }

  // 收集所有时间点（去重排序）
  const allTimes = [...new Set(sorted.map(d => d.timestamp))].sort(
    (a, b) => new Date(a) - new Date(b)
  )

  // 颜色池
  const colors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316']

  const series = Object.entries(plateGroups).map(([plate, items], idx) => {
    // 构建该车牌在每个时间点的积分值
    const dataMap = new Map()
    for (const item of items) {
      dataMap.set(item.timestamp, item.new_score)
    }
    const data = allTimes.map(t => dataMap.has(t) ? dataMap.get(t) : null)

    return {
      name: plate,
      type: 'line',
      data,
      connectNulls: true,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { width: 2 },
      itemStyle: { color: colors[idx % colors.length] },
      emphasis: {
        focus: 'series',
        itemStyle: { borderWidth: 2, borderColor: '#fff' }
      }
    }
  })

  const timeLabels = allTimes.map(t => {
    const d = new Date(t)
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
  })

  // 60分及格线标记（放在第一条 series 上）
  if (series.length > 0) {
    series[0].markLine = {
      silent: true,
      symbol: 'none',
      lineStyle: { color: '#ef4444', type: 'dashed', width: 1 },
      data: [{ yAxis: 60, label: { formatter: '及格线 60', color: '#ef4444', fontSize: 10 } }]
    }
  }

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(20, 22, 30, 0.95)',
      borderColor: '#2a2e3d',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter(params) {
        let html = `<div style="font-weight:600;margin-bottom:4px;">${params[0].axisValue}</div>`
        for (const p of params) {
          if (p.value !== null && p.value !== undefined) {
            html += `<div style="display:flex;align-items:center;gap:6px;">
              <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
              <span>${p.seriesName}：</span>
              <span style="font-weight:600">${p.value}</span>
            </div>`
          }
        }
        return html
      }
    },
    legend: {
      data: Object.keys(plateGroups),
      top: 0,
      textStyle: { color: '#94a3b8', fontSize: 12 },
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
      itemGap: 16
    },
    grid: {
      top: 36,
      left: 50,
      right: 20,
      bottom: 30
    },
    xAxis: {
      type: 'category',
      data: timeLabels,
      axisLine: { lineStyle: { color: '#2a2e3d' } },
      axisLabel: { color: '#64748b', fontSize: 11, rotate: timeLabels.length > 10 ? 30 : 0 },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      name: '积分',
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#64748b', fontSize: 11 },
      splitLine: { lineStyle: { color: '#1e2235', type: 'dashed' } }
    },
    series
  }
}

function renderChart() {
  if (!chartInstance) return
  if (filteredData.value.length === 0) {
    chartInstance.clear()
    chartInstance.setOption({
      title: {
        text: '暂无积分变化记录',
        left: 'center',
        top: 'center',
        textStyle: { color: '#64748b', fontSize: 14, fontWeight: 'normal' }
      }
    })
    return
  }
  chartInstance.setOption(buildChartOption(), true)
}

function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value, null, { renderer: 'canvas' })
  renderChart()
}

function handleResize() {
  chartInstance?.resize()
}

async function loadData() {
  try {
    const params = { hours: parseInt(timeRange.value) }
    if (selectedPlate.value) {
      params.plate = selectedPlate.value
    }
    const data = await fetchHistoryScore(params)
    scoreData.value = data.score_history || []
    plates.value = [...new Set(scoreData.value.map(d => d.plate))]
    await nextTick()
    renderChart()
  } catch (e) { console.error('加载积分历史失败:', e) }
}

watch([selectedPlate, timeRange], () => loadData())

onMounted(() => {
  loadData()
  nextTick(initChart)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
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

.chart-header { margin-bottom: 8px; }
.chart-title { font-weight: 600; font-size: 14px; }

.chart-area {
  flex: 1;
  min-height: 280px;
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
