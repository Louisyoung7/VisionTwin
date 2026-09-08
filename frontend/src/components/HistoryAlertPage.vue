<template>
  <div class="page-container">
    <!-- 工具栏 -->
    <div class="page-toolbar">
      <div class="toolbar-left">
        <select v-model="filterSource" class="filter-select">
          <option value="">全部来源</option>
          <option value="sensor">传感器</option>
          <option value="vehicle">车辆</option>
        </select>
        <select v-model="filterLevel" class="filter-select">
          <option value="">全部级别</option>
          <option value="danger">重要</option>
          <option value="warning">普通</option>
        </select>
        <select v-model="timeRange" class="filter-select">
          <option value="1">最近1小时</option>
          <option value="6">最近6小时</option>
          <option value="24">最近24小时</option>
          <option value="168">最近一周</option>
        </select>
      </div>
      <div class="toolbar-right">
        <span class="data-count">共 {{ filteredAlerts.length }} 条记录</span>
        <button class="btn-refresh" @click="loadData">刷新</button>
      </div>
    </div>

    <!-- 告警表格 -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>告警ID</th>
            <th>消息内容</th>
            <th>来源</th>
            <th>级别</th>
            <th>浓度</th>
            <th>位置</th>
            <th>时间</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in filteredAlerts" :key="a.id">
            <td class="id-cell">{{ a.id }}</td>
            <td class="msg-cell">{{ a.message }}</td>
            <td>
              <span class="source-tag" :class="a.source">{{ a.source === 'sensor' ? '传感器' : '车辆' }}</span>
            </td>
            <td>
              <span class="level-badge" :class="a.level">
                {{ a.level === 'danger' ? '重要' : '普通' }}
              </span>
            </td>
            <td>
              <span class="methane-val" :class="a.level">{{ a.methane_percentage || '-' }}</span>
            </td>
            <td class="coord-cell">{{ formatLocation(a.location) }}</td>
            <td class="time-cell">{{ a.timestamp || a.time }}</td>
            <td>
              <span class="state-tag" :class="a.confirmed ? 'confirmed' : 'pending'">
                {{ a.confirmed ? '已确认' : '待处理' }}
              </span>
            </td>
          </tr>
          <tr v-if="filteredAlerts.length === 0">
            <td colspan="8" class="empty-cell">暂无告警记录</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { fetchHistoryAlerts } from '../api.js'

const emit = defineEmits(['refresh'])

const alerts = ref([])
const filterSource = ref('')
const filterLevel = ref('')
const timeRange = ref('24')

const filteredAlerts = computed(() => {
  let list = alerts.value
  if (filterSource.value) {
    list = list.filter(a => a.source === filterSource.value)
  }
  if (filterLevel.value) {
    list = list.filter(a => a.level === filterLevel.value)
  }
  return list
})

function formatLocation(loc) {
  if (!loc || !Array.isArray(loc)) return '-'
  return `${loc[0]}, ${loc[2]}`
}

async function loadData() {
  try {
    const data = await fetchHistoryAlerts({
      source: filterSource.value,
      level: filterLevel.value,
      hours: parseInt(timeRange.value)
    })
    alerts.value = data.alerts || []
  } catch (e) { console.error('加载告警历史失败:', e) }
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

.filter-select {
  padding: 7px 10px;
  background: var(--bg-dark);
  border: 1px solid var(--border);
  border-radius: 5px;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.filter-select:focus {
  border-color: var(--info);
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
}

.btn-refresh:hover {
  opacity: 0.9;
}

.table-wrapper {
  flex: 1;
  overflow: auto;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.data-table th {
  background: var(--bg-card-hover);
  font-weight: 600;
  font-size: 13px;
  color: var(--text-secondary);
  position: sticky;
  top: 0;
}

.data-table td {
  font-size: 13px;
}

.id-cell { color: var(--text-secondary); font-size: 12px; }
.msg-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.coord-cell { font-size: 12px; color: var(--text-secondary); }
.time-cell { font-size: 12px; color: var(--text-secondary); }

.source-tag {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
}
.source-tag.sensor { background: rgba(59, 130, 246, 0.2); color: var(--info); }
.source-tag.vehicle { background: rgba(34, 197, 94, 0.2); color: var(--accent); }

.level-badge {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
}
.level-badge.danger { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
.level-badge.warning { background: rgba(245, 158, 11, 0.2); color: var(--warning); }

.methane-val { font-weight: 600; }
.methane-val.danger { color: var(--danger); }
.methane-val.warning { color: var(--warning); }

.state-tag {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
}
.state-tag.confirmed { background: rgba(34, 197, 94, 0.2); color: var(--accent); }
.state-tag.pending { background: rgba(245, 158, 11, 0.2); color: var(--warning); }

.empty-cell {
  text-align: center;
  color: var(--text-secondary);
  padding: 40px;
}
</style>
