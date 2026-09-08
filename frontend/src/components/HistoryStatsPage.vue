<template>
  <div class="page-container">
    <!-- 工具栏 -->
    <div class="page-toolbar">
      <div class="toolbar-left">
        <select v-model="timeRange" class="filter-select">
          <option value="1">最近1小时</option>
          <option value="6">最近6小时</option>
          <option value="24">最近24小时</option>
          <option value="168">最近一周</option>
        </select>
      </div>
      <div class="toolbar-right">
        <button class="btn-refresh" @click="loadData">刷新</button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card large">
        <div class="stat-icon danger">⚠️</div>
        <div class="stat-content">
          <span class="stat-value danger">{{ stats.total_alerts || 0 }}</span>
          <span class="stat-label">总告警数</span>
        </div>
      </div>
      <div class="stat-card large">
        <div class="stat-icon warning">📍</div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.by_source?.sensor || 0 }}</span>
          <span class="stat-label">传感器告警</span>
        </div>
      </div>
      <div class="stat-card large">
        <div class="stat-icon info">🚗</div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.by_source?.vehicle || 0 }}</span>
          <span class="stat-label">车辆告警</span>
        </div>
      </div>
      <div class="stat-card large">
        <div class="stat-icon accent">🔬</div>
        <div class="stat-content">
          <span class="stat-value" :class="stats.max_methane_value >= 70 ? 'danger' : stats.max_methane_value >= 40 ? 'warning' : ''">
            {{ stats.max_methane_value || 0 }}%
          </span>
          <span class="stat-label">最高甲烷浓度</span>
          <span class="stat-sub">传感器 #{{ stats.max_methane_sensor }}</span>
        </div>
      </div>
    </div>

    <!-- 告警分布 -->
    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">告警级别分布</div>
        <div class="pie-container">
          <div class="pie-chart" :style="levelPieStyle">
            <div class="pie-center">
              <span>{{ stats.total_alerts || 0 }}</span>
              <span class="pie-label">总计</span>
            </div>
          </div>
          <div class="pie-legend">
            <div class="legend-item">
              <span class="dot danger"></span>
              <span>危险 ({{ stats.by_level?.danger || 0 }})</span>
            </div>
            <div class="legend-item">
              <span class="dot warning"></span>
              <span>预警 ({{ stats.by_level?.warning || 0 }})</span>
            </div>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-title">告警来源分布</div>
        <div class="pie-container">
          <div class="pie-chart sensor" :style="sourcePieStyle">
            <div class="pie-center">
              <span>{{ stats.total_alerts || 0 }}</span>
              <span class="pie-label">总计</span>
            </div>
          </div>
          <div class="pie-legend">
            <div class="legend-item">
              <span class="dot info"></span>
              <span>传感器 ({{ stats.by_source?.sensor || 0 }})</span>
            </div>
            <div class="legend-item">
              <span class="dot accent"></span>
              <span>车辆 ({{ stats.by_source?.vehicle || 0 }})</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详细数据表格 -->
    <div class="table-section">
      <div class="section-title">详细数据</div>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>统计项</th>
              <th>数值</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>总告警数</td>
              <td class="value-cell danger">{{ stats.total_alerts || 0 }}</td>
              <td class="desc-cell">时间范围内的告警总计</td>
            </tr>
            <tr>
              <td>传感器告警</td>
              <td class="value-cell">{{ stats.by_source?.sensor || 0 }}</td>
              <td class="desc-cell">甲烷浓度超限触发</td>
            </tr>
            <tr>
              <td>车辆告警</td>
              <td class="value-cell">{{ stats.by_source?.vehicle || 0 }}</td>
              <td class="desc-cell">车辆偏离路线触发</td>
            </tr>
            <tr>
              <td>危险告警</td>
              <td class="value-cell danger">{{ stats.by_level?.danger || 0 }}</td>
              <td class="desc-cell">甲烷≥70%或严重偏离</td>
            </tr>
            <tr>
              <td>预警告警</td>
              <td class="value-cell warning">{{ stats.by_level?.warning || 0 }}</td>
              <td class="desc-cell">甲烷40-70%或轻微偏离</td>
            </tr>
            <tr>
              <td>最高甲烷浓度</td>
              <td class="value-cell" :class="stats.max_methane_value >= 70 ? 'danger' : stats.max_methane_value >= 40 ? 'warning' : ''">
                {{ stats.max_methane_value || 0 }}%
              </td>
              <td class="desc-cell">来自传感器 #{{ stats.max_methane_sensor }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { fetchHistoryStats } from '../api.js'

const emit = defineEmits(['refresh'])

const stats = ref({})
const timeRange = ref('24')

const levelPieStyle = computed(() => {
  const danger = stats.value.by_level?.danger || 0
  const warning = stats.value.by_level?.warning || 0
  const total = danger + warning
  if (total === 0) return { background: 'conic-gradient(var(--border) 0deg 360deg)' }
  const dangerDeg = (danger / total) * 360
  return {
    background: `conic-gradient(var(--danger) 0deg ${dangerDeg}deg, var(--warning) ${dangerDeg}deg 360deg)`
  }
})

const sourcePieStyle = computed(() => {
  const sensor = stats.value.by_source?.sensor || 0
  const vehicle = stats.value.by_source?.vehicle || 0
  const total = sensor + vehicle
  if (total === 0) return { background: 'conic-gradient(var(--border) 0deg 360deg)' }
  const sensorDeg = (sensor / total) * 360
  return {
    background: `conic-gradient(var(--info) 0deg ${sensorDeg}deg, var(--accent) ${sensorDeg}deg 360deg)`
  }
})

async function loadData() {
  try {
    const data = await fetchHistoryStats({ hours: parseInt(timeRange.value) })
    stats.value = data || {}
  } catch (e) { console.error('加载统计失败:', e) }
}

watch(timeRange, () => loadData())

onMounted(() => loadData())
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
  overflow: auto;
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  flex-shrink: 0;
}

.stat-card {
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}
.stat-icon.danger { background: rgba(239, 68, 68, 0.15); }
.stat-icon.warning { background: rgba(245, 158, 11, 0.15); }
.stat-icon.info { background: rgba(59, 130, 246, 0.15); }
.stat-icon.accent { background: rgba(34, 197, 94, 0.15); }

.stat-content { display: flex; flex-direction: column; gap: 2px; }
.stat-value { font-size: 24px; font-weight: 700; }
.stat-value.danger { color: var(--danger); }
.stat-value.warning { color: var(--warning); }
.stat-label { font-size: 12px; color: var(--text-secondary); }
.stat-sub { font-size: 10px; color: var(--text-secondary); }

.charts-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  flex-shrink: 0;
}

.chart-card {
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border);
  padding: 16px;
}

.chart-title { font-weight: 600; font-size: 14px; margin-bottom: 16px; }

.pie-container { display: flex; align-items: center; gap: 24px; }

.pie-chart {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pie-center {
  width: 70px;
  height: 70px;
  background: var(--bg-card);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
}

.pie-label { font-size: 10px; color: var(--text-secondary); font-weight: normal; }

.pie-legend { display: flex; flex-direction: column; gap: 8px; }

.legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.dot { width: 10px; height: 10px; border-radius: 50%; }
.dot.danger { background: var(--danger); }
.dot.warning { background: var(--warning); }
.dot.info { background: var(--info); }
.dot.accent { background: var(--accent); }

.table-section {
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border);
  padding: 16px;
  flex-shrink: 0;
}

.section-title { font-weight: 600; font-size: 14px; margin-bottom: 12px; }

.table-wrapper { overflow: auto; }

.data-table { width: 100%; border-collapse: collapse; }

.data-table th,
.data-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.data-table th {
  background: var(--bg-card-hover);
  font-weight: 600;
  font-size: 12px;
  color: var(--text-secondary);
}

.data-table td { font-size: 13px; }

.value-cell { font-weight: 600; }
.value-cell.danger { color: var(--danger); }
.value-cell.warning { color: var(--warning); }
.desc-cell { color: var(--text-secondary); font-size: 12px; }
</style>
