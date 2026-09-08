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
        <span class="data-count">共 {{ potholeData.length }} 条记录</span>
        <button class="btn-refresh" @click="loadData">刷新</button>
      </div>
    </div>

    <!-- 坑洼卡片网格 -->
    <div class="pothole-grid" v-if="potholeData.length > 0">
      <div v-for="item in potholeData" :key="item.id" class="pothole-card">
        <div class="card-image">
          <img
            v-if="item.image_filename"
            :src="imageUrl(item.image_filename)"
            :alt="`坑洼 #${item.detection_id}`"
            @error="(e) => e.target.style.display='none'"
          />
          <div v-else class="image-placeholder">
            <span>无图片</span>
          </div>
          <div class="confidence-badge" :class="getConfClass(item.confidence)">
            {{ (item.confidence * 100).toFixed(0) }}%
          </div>
        </div>
        <div class="card-body">
          <div class="card-title">坑洼 #{{ item.detection_id }}</div>
          <div class="card-meta">
            <span>帧 #{{ item.frame_id }}</span>
            <span>{{ item.detection_time }}</span>
          </div>
          <div class="card-bbox" v-if="item.bbox">
            位置: ({{ item.bbox.x }}, {{ item.bbox.y }})
            尺寸: {{ item.bbox.w }}×{{ item.bbox.h }}
          </div>
          <div class="card-time">{{ item.timestamp }}</div>
        </div>
      </div>
    </div>

    <div v-else class="empty-tip">暂无坑洼检测记录</div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { fetchHistoryPothole } from '../api.js'

const potholeData = ref([])
const timeRange = ref('24')

function imageUrl(filename) {
  return `http://127.0.0.1:8000/alerts/pothole_images/${filename}`
}

function getConfClass(conf) {
  if (conf >= 0.8) return 'high'
  if (conf >= 0.5) return 'mid'
  return 'low'
}

async function loadData() {
  try {
    const data = await fetchHistoryPothole({ hours: parseInt(timeRange.value) })
    potholeData.value = data.pothole_history || []
  } catch (e) {
    console.error('加载坑洼历史失败:', e)
  }
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

.data-count { font-size: 13px; color: var(--text-secondary); }

.btn-refresh {
  padding: 7px 16px;
  background: var(--info);
  border: none;
  border-radius: 5px;
  color: white;
  font-size: 13px;
  cursor: pointer;
}

.pothole-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  overflow-y: auto;
  align-content: start;
}

.pothole-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.15s;
}

.pothole-card:hover {
  border-color: var(--info);
}

.card-image {
  position: relative;
  height: 160px;
  background: var(--bg-dark);
  overflow: hidden;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 13px;
}

.confidence-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.confidence-badge.high { background: rgba(239, 68, 68, 0.85); color: #fff; }
.confidence-badge.mid { background: rgba(245, 158, 11, 0.85); color: #fff; }
.confidence-badge.low { background: rgba(100, 116, 139, 0.85); color: #fff; }

.card-body {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-title { font-weight: 600; font-size: 13px; }

.card-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-secondary);
}

.card-bbox {
  font-size: 11px;
  color: var(--text-secondary);
}

.card-time {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.empty-tip {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 14px;
}
</style>
