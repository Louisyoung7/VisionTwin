<template>
  <div class="page-container">
    <!-- 工具栏 -->
    <div class="page-toolbar">
      <div class="toolbar-left">
        <input
          v-model="searchKey"
          type="text"
          class="search-input"
          placeholder="搜索车牌号..."
        />
      </div>
      <div class="toolbar-right">
        <span class="data-count">共 {{ filteredVehicles.length }} 辆车</span>
        <button class="btn-refresh" @click="$emit('refresh')">刷新</button>
      </div>
    </div>

    <!-- 车辆表格 -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>车牌号</th>
            <th>积分</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in filteredVehicles" :key="v.plate">
            <td class="plate-cell">{{ v.plate }}</td>
            <td>
              <span
                class="score-cell"
                :class="v.score >= 80 ? 'high' : v.score < 60 ? 'low' : ''"
              >{{ v.score }}</span>
            </td>
          </tr>
          <tr v-if="filteredVehicles.length === 0">
            <td colspan="2" class="empty-cell">暂无停靠车辆</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  vehicles: {
    type: Array,
    default: () => []
  }
})

defineEmits(['refresh'])

const searchKey = ref('')

const filteredVehicles = computed(() => {
  let list = props.vehicles
  if (searchKey.value) {
    const kw = searchKey.value.toLowerCase()
    list = list.filter(v => v.plate.toLowerCase().includes(kw))
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
  color: var(--text-primary);
}

.score-cell {
  font-weight: 600;
}
.score-cell.high { color: var(--accent); }
.score-cell.low { color: var(--danger); }

.empty-cell {
  text-align: center;
  color: var(--text-secondary);
  padding: 40px !important;
}
</style>
