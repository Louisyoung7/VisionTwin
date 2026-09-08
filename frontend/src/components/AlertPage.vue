<template>
  <div class="page-container">
    <!-- 工具栏 -->
    <div class="page-toolbar">
      <div class="toolbar-left">
        <input
          v-model="searchKey"
          type="text"
          class="search-input"
          placeholder="搜索告警信息..."
        />
        <select v-model="filterLevel" class="filter-select">
          <option value="">全部级别</option>
          <option value="danger">重要</option>
          <option value="warning">普通</option>
        </select>
        <select v-model="filterStatus" class="filter-select">
          <option value="">全部状态</option>
          <option value="pending">待处理</option>
          <option value="confirmed">已确认</option>
        </select>
      </div>
      <div class="toolbar-right">
        <span class="data-count">共 {{ filteredAlerts.length }} 条告警</span>
        <button class="btn-refresh" @click="$emit('refresh')">刷新</button>
      </div>
    </div>

    <!-- 告警表格 -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>告警ID</th>
            <th>消息内容</th>
            <th>级别</th>
            <th>{{ hasPothole ? '置信度' : '甲烷浓度' }}</th>
            <th>{{ hasPothole ? '帧号' : '位置' }}</th>
            <th>时间</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in filteredAlerts" :key="a.id">
            <td class="id-cell">{{ a.id }}</td>
            <td class="msg-cell">{{ a.message }}</td>
            <td>
              <span class="level-badge" :class="a.level">
                {{ a.level === 'danger' ? '重要' : '普通' }}
              </span>
            </td>
            <td>
              <span
                class="methane-val"
                :class="a.level"
              >{{ a.source === 'pothole' ? ((a.confidence || 0) * 100).toFixed(0) + '%' : (a.methane_percentage || '-') + '%' }}</span>
            </td>
            <td class="coord-cell">
              {{ a.source === 'pothole' ? '#' + a.frame_id : (a.location ? a.location.join(', ') : '-') }}
            </td>
            <td class="time-cell">{{ a.time }}</td>
            <td>
              <span class="state-tag" :class="a.confirmed ? 'confirmed' : 'pending'">
                {{ a.confirmed ? '已确认' : '待处理' }}
              </span>
            </td>
            <td>
              <div class="action-btns">
                <button
                  v-if="!a.confirmed"
                  class="btn-confirm"
                  @click="$emit('confirm', a.id)"
                >确认</button>
                <button
                  class="btn-delete"
                  @click="$emit('delete', a.id)"
                >删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredAlerts.length === 0">
            <td colspan="7" class="empty-cell">暂无告警记录</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  alerts: {
    type: Array,
    default: () => []
  }
})

defineEmits(['refresh', 'confirm', 'delete'])

const searchKey = ref('')
const filterLevel = ref('')
const filterStatus = ref('')

const hasPothole = computed(() => props.alerts.some(a => a.source === 'pothole'))

const filteredAlerts = computed(() => {
  let list = props.alerts
  if (searchKey.value) {
    const kw = searchKey.value.toLowerCase()
    list = list.filter(a => a.message.toLowerCase().includes(kw) || String(a.id).includes(kw))
  }
  if (filterLevel.value) {
    list = list.filter(a => a.level === filterLevel.value)
  }
  if (filterStatus.value) {
    const isConfirmed = filterStatus.value === 'confirmed'
    list = list.filter(a => !!a.confirmed === isConfirmed)
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
  width: 220px;
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
  padding: 10px 12px;
  text-align: left;
  font-weight: 500;
  font-size: 12px;
  position: sticky;
  top: 0;
  z-index: 1;
  border-bottom: 1px solid var(--border);
}

.data-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
  font-size: 12px;
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

.id-cell {
  font-variant-numeric: tabular-nums;
  color: var(--text-secondary);
}

.msg-cell {
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.coord-cell {
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.time-cell {
  color: var(--text-secondary);
}

.level-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
}

.level-badge.danger {
  background: rgba(239, 68, 68, 0.15);
  color: var(--danger);
}

.level-badge.warning {
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning);
}

.methane-val {
  font-weight: 600;
}

.methane-val.danger { color: var(--danger); }
.methane-val.warning { color: var(--warning); }

.state-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
}

.state-tag.pending {
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning);
}

.state-tag.confirmed {
  background: rgba(34, 197, 94, 0.15);
  color: var(--accent);
}

.action-btns {
  display: flex;
  gap: 6px;
}

.btn-confirm {
  padding: 3px 12px;
  background: var(--info);
  border: none;
  border-radius: 4px;
  color: white;
  font-size: 11px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.btn-confirm:hover {
  opacity: 0.85;
}

.btn-delete {
  padding: 3px 12px;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 4px;
  color: var(--danger);
  font-size: 11px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.btn-delete:hover {
  opacity: 0.85;
}

.empty-cell {
  text-align: center;
  color: var(--text-secondary);
  padding: 40px !important;
}
</style>
