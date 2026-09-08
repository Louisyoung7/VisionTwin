<template>
  <div class="page-container">
    <!-- 工具栏 -->
    <div class="page-toolbar">
      <div class="toolbar-left">
        <input
          v-model="searchKey"
          type="text"
          class="search-input"
          placeholder="搜索传感器ID..."
        />
        <select v-model="filterLevel" class="filter-select">
          <option value="">全部状态</option>
          <option value="danger">告警</option>
          <option value="warning">预警</option>
          <option value="normal">正常</option>
        </select>
      </div>
      <div class="toolbar-right">
        <span class="data-count">共 {{ filteredSensors.length }} 个传感器</span>
        <button class="btn-refresh" @click="$emit('refresh')">刷新</button>
      </div>
    </div>

    <!-- 传感器表格 -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>传感器ID</th>
            <th>位置坐标</th>
            <th>甲烷浓度</th>
            <th>状态</th>
            <th>更新时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in filteredSensors" :key="s.id">
            <td class="plate-cell">{{ s.id }}</td>
            <td class="coord-cell">{{ s.location ? s.location.join(', ') : '-' }}</td>
            <td>
              <div class="value-bar">
                <span
                  class="value-text"
                  :class="getLevel(s.methane_percentage)"
                >{{ s.methane_percentage }}%</span>
                <div class="bar-track">
                  <div
                    class="bar-fill"
                    :class="getLevel(s.methane_percentage)"
                    :style="{ width: s.methane_percentage + '%' }"
                  ></div>
                </div>
              </div>
            </td>
            <td>
              <span class="status-tag" :class="getLevel(s.methane_percentage)">
                {{ getStatusText(s.methane_percentage) }}
              </span>
            </td>
            <td class="time-cell">{{ formatTime(s.last_update) }}</td>
          </tr>
          <tr v-if="filteredSensors.length === 0">
            <td colspan="5" class="empty-cell">暂无传感器数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  sensors: {
    type: Array,
    default: () => []
  }
})

defineEmits(['refresh'])

const searchKey = ref('')
const filterLevel = ref('')

function getLevel(pct) {
  if (pct > 70) return 'danger'
  if (pct > 40) return 'warning'
  return 'normal'
}

function getStatusText(pct) {
  if (pct > 70) return '告警'
  if (pct > 40) return '预警'
  return '正常'
}

function formatTime(ts) {
  if (!ts) return '-'
  return new Date(ts * 1000).toLocaleTimeString('zh-CN')
}

const filteredSensors = computed(() => {
  let list = props.sensors
  if (searchKey.value) {
    const kw = searchKey.value.toLowerCase()
    list = list.filter(s => String(s.id).toLowerCase().includes(kw))
  }
  if (filterLevel.value) {
    list = list.filter(s => getLevel(s.methane_percentage) === filterLevel.value)
  }
  return list
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

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  padding: 7px 12px;
  background: var(--bg-dark);
  border: 1px solid var(--border);
  border-radius: 5px;
  color: var(--text-primary);
  font-size: 13px;
  width: 200px;
  outline: none;
  transition: border-color 0.15s;
}

.search-input:focus {
  border-color: var(--info);
}

.search-input::placeholder {
  color: var(--text-secondary);
}

.filter-select {
  padding: 7px 10px;
  background: var(--bg-dark);
  border: 1px solid var(--border);
  border-radius: 5px;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  cursor: pointer;
}

.data-count {
  font-size: 13px;
  color: var(--text-secondary);
}

.btn-refresh {
  padding: 7px 16px;
  background: var(--info);
  border: none;
  border-radius: 5px;
  color: white;
  font-size: 13px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.btn-refresh:hover {
  opacity: 0.85;
}

.table-wrapper {
  flex: 1;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  background: var(--bg-sidebar);
  color: var(--text-secondary);
  padding: 10px 14px;
  text-align: left;
  font-weight: 500;
  font-size: 12px;
  position: sticky;
  top: 0;
  z-index: 1;
  border-bottom: 1px solid var(--border);
}

.data-table td {
  padding: 9px 14px;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr {
  transition: background 0.12s;
}

.data-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.03);
}

.plate-cell {
  font-weight: 600;
}

.value-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.value-text {
  font-weight: 600;
  min-width: 44px;
}

.value-text.danger { color: var(--danger); }
.value-text.warning { color: var(--warning); }
.value-text.normal { color: var(--accent); }

.bar-track {
  flex: 1;
  height: 5px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
  max-width: 120px;
}

.bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.bar-fill.danger { background: var(--danger); }
.bar-fill.warning { background: var(--warning); }
.bar-fill.normal { background: var(--accent); }

.status-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
}

.status-tag.danger {
  background: rgba(239, 68, 68, 0.15);
  color: var(--danger);
}

.status-tag.warning {
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning);
}

.status-tag.normal {
  background: rgba(34, 197, 94, 0.15);
  color: var(--accent);
}

.coord-cell {
  font-size: 12px;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.time-cell {
  font-size: 12px;
  color: var(--text-secondary);
}

.empty-cell {
  text-align: center;
  color: var(--text-secondary);
  padding: 40px !important;
}
</style>
