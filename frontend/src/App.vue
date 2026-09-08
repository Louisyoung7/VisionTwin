<template>
  <div id="app">
    <!-- 左侧导航栏 -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-icon">V</div>
        <span class="logo-text">智瞳云枢</span>
      </div>
      <nav class="nav-menu">
        <!-- 首页 -->
        <div
          class="nav-item top-nav-item"
          :class="{ active: activeNav === 'home' }"
          @click="handleNavClick('home')"
        >
          <span class="nav-icon">🏠</span>
          首页
        </div>

        <!-- 监控列表 -->
        <div class="nav-group">
          <div
            class="nav-item nav-group-title-row"
            :class="{ active: activeNav.startsWith('monitor') }"
            @click="toggleNavGroup('monitor')"
          >
            <span class="nav-icon">📋</span>
            <span class="nav-label">监控列表</span>
            <span
              class="nav-arrow"
              :class="{ open: expandedGroups.includes('monitor') }"
              >▶</span
            >
          </div>
          <div v-if="expandedGroups.includes('monitor')" class="nav-children">
            <div
              class="nav-child-item"
              :class="{ active: activeNav === 'monitor-vehicle' }"
              @click="handleNavClick('monitor-vehicle')"
            >
              行驶车辆
            </div>
            <div
              class="nav-child-item"
              :class="{ active: activeNav === 'monitor-docked' }"
              @click="handleNavClick('monitor-docked')"
            >
              停靠车辆
            </div>
            <div
              class="nav-child-item"
              :class="{ active: activeNav === 'monitor-sensor' }"
              @click="handleNavClick('monitor-sensor')"
            >
              传感器监控
            </div>
          </div>
        </div>

        <!-- 告警管理 -->
        <div class="nav-group">
          <div
            class="nav-item nav-group-title-row"
            :class="{ active: activeNav.startsWith('alert') }"
            @click="toggleNavGroup('alert')"
          >
            <span class="nav-icon">⚠️</span>
            <span class="nav-label">告警管理</span>
            <span
              class="nav-arrow"
              :class="{ open: expandedGroups.includes('alert') }"
              >▶</span
            >
          </div>
          <div v-if="expandedGroups.includes('alert')" class="nav-children">
            <div
              class="nav-child-item"
              :class="{ active: activeNav === 'alert-vehicle' }"
              @click="handleNavClick('alert-vehicle')"
            >
              车辆告警
            </div>
            <div
              class="nav-child-item"
              :class="{ active: activeNav === 'alert-sensor' }"
              @click="handleNavClick('alert-sensor')"
            >
              传感器告警
            </div>
            <div
              class="nav-child-item"
              :class="{ active: activeNav === 'alert-pothole' }"
              @click="handleNavClick('alert-pothole')"
            >
              坑洼告警
            </div>
          </div>
        </div>

        <!-- 历史数据 -->
        <div class="nav-group">
          <div
            class="nav-item nav-group-title-row"
            :class="{ active: activeNav.startsWith('history') }"
            @click="toggleNavGroup('history')"
          >
            <span class="nav-icon">📊</span>
            <span class="nav-label">历史数据</span>
            <span
              class="nav-arrow"
              :class="{ open: expandedGroups.includes('history') }"
              >▶</span
            >
          </div>
          <div v-if="expandedGroups.includes('history')" class="nav-children">
            <div
              class="nav-child-item"
              :class="{ active: activeNav === 'history-alert' }"
              @click="handleNavClick('history-alert')"
            >
              告警记录
            </div>
            <div
              class="nav-child-item"
              :class="{ active: activeNav === 'history-methane' }"
              @click="handleNavClick('history-methane')"
            >
              甲烷趋势
            </div>
            <div
              class="nav-child-item"
              :class="{ active: activeNav === 'history-score' }"
              @click="handleNavClick('history-score')"
            >
              积分记录
            </div>
            <div
              class="nav-child-item"
              :class="{ active: activeNav === 'history-stats' }"
              @click="handleNavClick('history-stats')"
            >
              统计报表
            </div>
            <div
              class="nav-child-item"
              :class="{ active: activeNav === 'history-pothole' }"
              @click="handleNavClick('history-pothole')"
            >
              坑洼记录
            </div>
          </div>
        </div>

        <!-- 系统设置 -->
        <div
          class="nav-item top-nav-item"
          :class="{ active: activeNav === 'settings' }"
          @click="handleNavClick('settings')"
        >
          <span class="nav-icon">⚙️</span>
          系统设置
        </div>
      </nav>
    </aside>

    <!-- 主区域 -->
    <div class="main-wrapper">
      <!-- 顶部标题栏 -->
      <header class="top-header">
        <div class="header-title-area">
          <span class="page-title">{{ currentPageTitle }}</span>
        </div>
        <div class="header-actions">
          <div class="user-info">
            <span class="status-dot" :class="{ online: isOnline }"></span>
            <span>{{ isOnline ? "在线" : "离线" }}</span>
            <div class="user-avatar">管</div>
          </div>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content-area">
        <!-- ===== 首页仪表盘 ===== -->
        <div v-if="activeNav === 'home'" class="dashboard-grid">
          <!-- 地图面板 -->
          <div class="panel-card map-section">
            <MapView
              :vehicles="vehicles"
              @vehicle-click="handleVehicleClick"
            />
          </div>

          <!-- 右侧面板组 -->
          <div class="right-panels">
            <!-- 传感器实时数据 -->
            <div class="panel-card">
              <div class="panel-head">
                <span class="panel-title">传感器实时数据</span>
                <span class="status-dot online"></span>
              </div>
              <div class="panel-body sensor-list">
                <template v-if="methaneSensors.length > 0">
                  <div
                    v-for="(sensor, idx) in methaneSensors"
                    :key="idx"
                    class="sensor-item"
                    :class="getSensorLevel(sensor.methane_percentage)"
                  >
                    <div class="sensor-header">
                      <span class="sensor-id">{{
                        sensor.id || "传感器" + (idx + 1)
                      }}</span>
                      <span class="sensor-value"
                        >{{ sensor.methane_percentage }}%</span
                      >
                    </div>
                    <div class="sensor-bar">
                      <div
                        class="sensor-fill"
                        :class="getSensorLevel(sensor.methane_percentage)"
                        :style="{ width: sensor.methane_percentage + '%' }"
                      ></div>
                    </div>
                    <div class="sensor-footer">
                      <span class="sensor-location"
                        >位置: {{ sensor.location?.join(", ") || "-" }}</span
                      >
                      <span
                        class="sensor-status"
                        :class="getSensorLevel(sensor.methane_percentage)"
                      >
                        {{ getStatusText(sensor.methane_percentage) }}
                      </span>
                    </div>
                  </div>
                </template>
                <div v-else class="empty-tip">暂无传感器数据</div>
              </div>
            </div>

            <!-- 行驶车辆表格 -->
            <div class="panel-card">
              <div class="panel-head">
                <span class="panel-title">行驶车辆</span>
                <span style="font-size: 12px; color: var(--text-secondary)"
                  >{{ vehicles.length }} 辆</span
                >
              </div>
              <div class="panel-body vehicle-table-container">
                <table v-if="vehicles.length > 0" class="vehicle-table">
                  <thead>
                    <tr>
                      <th>车牌号</th>
                      <th>积分</th>
                      <th>路线ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="v in vehicles" :key="v.plate">
                      <td class="plate-cell">{{ v.plate }}</td>
                      <td>
                        <span
                          class="score-cell"
                          :class="
                            v.score >= 80
                              ? 'high'
                              : v.score !== undefined && v.score < 60
                                ? 'low'
                                : ''
                          "
                          >{{ v.score }}</span
                        >
                      </td>
                      <td class="route-cell">{{ v.route_id || "-" }}</td>
                    </tr>
                  </tbody>
                </table>
                <div v-else class="empty-tip">暂无行驶车辆</div>
              </div>
            </div>

            <!-- 停靠车辆表格 -->
            <div class="panel-card">
              <div class="panel-head">
                <span class="panel-title">停靠车辆</span>
                <span style="font-size: 12px; color: var(--text-secondary)"
                  >{{ dockedVehicles.length }} 辆</span
                >
              </div>
              <div class="panel-body vehicle-table-container">
                <table v-if="dockedVehicles.length > 0" class="vehicle-table">
                  <thead>
                    <tr>
                      <th>车牌号</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="v in dockedVehicles" :key="v.id">
                      <td class="plate-cell">{{ v.plate }}</td>
                    </tr>
                  </tbody>
                </table>
                <div v-else class="empty-tip">暂无停靠车辆</div>
              </div>
            </div>
          </div>

          <!-- 底部：告警记录（全宽） -->
          <div class="panel-card dashboard-full-row">
            <div class="alert-table-container">
              <table v-if="alerts.length > 0" class="alert-table">
                <thead>
                  <tr>
                    <th>名称</th>
                    <th>时间</th>
                    <th>告警级别</th>
                    <th>告警类型</th>
                    <th>位置</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="a in alerts" :key="a.id">
                    <td class="plate-cell">{{ a.message.substring(0, 16) }}</td>
                    <td>{{ a.time }}</td>
                    <td>
                      <span
                        class="level-badge"
                        :class="a.level === 'danger' ? 'important' : 'normal'"
                      >
                        {{ a.level === "danger" ? "重要" : "普通" }}
                      </span>
                    </td>
                    <td>{{ a.level === "danger" ? "危险" : "预警" }}</td>
                    <td>{{ a.location }}</td>
                    <td>待处理</td>
                    <td>
                      <button
                        class="confirm-btn"
                        @click="confirmAlertHome(a.id)"
                      >
                        确认
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-else class="empty-tip">暂无告警信息</div>
            </div>
          </div>
        </div>

        <!-- ===== 监控列表 - 行驶车辆 ===== -->
        <div v-else-if="activeNav === 'monitor-vehicle'" class="full-page">
          <VehiclePage :vehicles="allVehicles" @refresh="loadAllVehicles" />
        </div>

        <!-- ===== 监控列表 - 停靠车辆 ===== -->
        <div v-else-if="activeNav === 'monitor-docked'" class="full-page">
          <DockedVehiclePage
            :vehicles="dockedVehiclesWithScore"
            @refresh="loadDockedVehicles"
          />
        </div>

        <!-- ===== 监控列表 - 传感器监控 ===== -->
        <div v-else-if="activeNav === 'monitor-sensor'" class="full-page">
          <SensorPage :sensors="methaneSensors" @refresh="loadMethaneSensors" />
        </div>

        <!-- ===== 告警管理页 ===== -->
        <div v-else-if="activeNav === 'alert-vehicle'" class="full-page">
          <AlertPage
            :alerts="vehicleAlerts"
            @refresh="loadAllAlerts"
            @confirm="confirmAlert"
            @delete="deleteAlert"
          />
        </div>
        <div v-else-if="activeNav === 'alert-sensor'" class="full-page">
          <AlertPage
            :alerts="sensorAlerts"
            @refresh="loadAllAlerts"
            @confirm="confirmAlert"
            @delete="deleteAlert"
          />
        </div>
        <div v-else-if="activeNav === 'alert-pothole'" class="full-page">
          <AlertPage
            :alerts="potholeAlerts"
            @refresh="loadAllAlerts"
            @confirm="confirmAlert"
            @delete="deleteAlert"
          />
        </div>

        <!-- ===== 历史数据页面 ===== -->
        <div v-else-if="activeNav === 'history-alert'" class="full-page">
          <HistoryAlertPage @refresh="loadHistoryAlert" />
        </div>
        <div v-else-if="activeNav === 'history-methane'" class="full-page">
          <HistoryMethanePage @refresh="loadHistoryMethane" />
        </div>

        <div v-else-if="activeNav === 'history-score'" class="full-page">
          <HistoryScorePage @refresh="loadHistoryScore" />
        </div>
        <div v-else-if="activeNav === 'history-stats'" class="full-page">
          <HistoryStatsPage @refresh="loadHistoryStats" />
        </div>
        <div v-else-if="activeNav === 'history-pothole'" class="full-page">
          <HistoryPotholePage />
        </div>

        <!-- ===== 其他页面（占位） ===== -->
        <div v-else class="full-page placeholder-page">
          <div class="placeholder-icon">📋</div>
          <div class="placeholder-text">{{ getNavLabel(activeNav) }}</div>
          <div class="placeholder-desc">页面开发中...</div>
        </div>
      </main>

      <!-- 底部状态栏 -->
      <footer class="status-bar">
        <span>系统运行正常</span>
      </footer>
    </div>

    <!-- 传感器告警弹窗 -->
    <div v-if="sensorAlertPopup" class="sensor-alert-popup" :class="sensorAlertPopup.level">
      <div class="sensor-alert-header">
        <span class="sensor-alert-icon">{{ sensorAlertPopup.level === 'danger' ? '⚠️' : '⚡' }}</span>
        <span class="sensor-alert-title">{{ sensorAlertPopup.level === 'danger' ? '危险告警' : '预警' }}</span>
        <button class="sensor-alert-close" @click="sensorAlertPopup = null">×</button>
      </div>
      <div class="sensor-alert-body">
        <p class="sensor-alert-message">{{ sensorAlertPopup.message }}</p>
        <p class="sensor-alert-time">{{ sensorAlertPopup.time }}</p>
      </div>
    </div>

    <!-- 通知提示 -->
    <div class="notification-area">
      <div v-for="n in notifications" :key="n.id" class="notification">
        车辆 #{{ n.vehicleId }} 未按路线行驶，积分 {{ n.score }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import MapView from "./components/MapView.vue";
import VehiclePage from "./components/VehiclePage.vue";
import DockedVehiclePage from "./components/DockedVehiclePage.vue";
import SensorPage from "./components/SensorPage.vue";
import AlertPage from "./components/AlertPage.vue";
import HistoryAlertPage from "./components/HistoryAlertPage.vue";
import HistoryMethanePage from "./components/HistoryMethanePage.vue";

import HistoryScorePage from "./components/HistoryScorePage.vue";
import HistoryStatsPage from "./components/HistoryStatsPage.vue";
import HistoryPotholePage from "./components/HistoryPotholePage.vue";
import {
  fetchMethaneSensors,
  fetchAlerts,
  fetchDockedVehicles,
  fetchVehicles,
  fetchHistoryAlerts,
  fetchHistoryMethane,
  fetchHistoryScore,
  fetchHistoryStats,
  fetchHistoryPothole,
} from "./api.js";

// 导航
const expandedGroups = ref(["monitor", "alert", "history"]);
const activeNav = ref("home");

const navLabels = {
  home: "首页",
  "monitor-vehicle": "行驶车辆",
  "monitor-docked": "停靠车辆",
  "monitor-sensor": "传感器监控",
  "alert-vehicle": "车辆告警",
  "alert-sensor": "传感器告警",
  "alert-pothole": "坑洼告警",
  "history-alert": "告警记录",
  "history-methane": "甲烷趋势",
  "history-score": "积分记录",
  "history-stats": "统计报表",
  "history-pothole": "坑洼记录",
  history: "历史数据",
  settings: "系统设置",
};

function toggleNavGroup(key) {
  if (expandedGroups.value.includes(key)) {
    expandedGroups.value = expandedGroups.value.filter((k) => k !== key);
  } else {
    expandedGroups.value.push(key);
  }
}

function handleNavClick(key) {
  activeNav.value = key;
}

function getNavLabel(key) {
  return navLabels[key] || key;
}

const currentPageTitle = computed(() => {
  const label = navLabels[activeNav.value] || "智瞳云枢";
  return label + " - 智瞳云枢";
});

// 状态
const isOnline = ref(true);
const currentTime = ref("");

function updateTime() {
  const now = new Date();
  currentTime.value = now.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

// 首页数据
const vehicles = ref([]);
const dockedVehicles = ref([]);
const frozenVehicles = ref({}); // 违规冻结的车辆：{plate: frozenPosition}
const methaneSensors = ref([]);
const alerts = ref([]);
const notifications = ref([]);

// 传感器告警弹窗
const sensorAlertPopup = ref(null);

// 页面专用数据
const allVehicles = ref([]);
const allAlerts = ref([]);

// 计算属性：各子页数据
const vehicleAlerts = computed(() => {
  return allAlerts.value.filter((a) => a.source === "vehicle");
});

const sensorAlerts = computed(() => {
  return allAlerts.value.filter((a) => a.source === "sensor");
});

const potholeAlerts = computed(() => {
  return allAlerts.value.filter((a) => a.source === "pothole");
});

const dockedVehiclesWithScore = computed(() => {
  const scoreMap = {};
  for (const v of allVehicles.value) {
    scoreMap[v.plate] = v.score;
  }
  return dockedVehicles.value.map((v) => ({
    ...v,
    score: scoreMap[v.plate] ?? 100,
  }));
});

// WebSocket
let ws = null;
let timeInterval = null;
let pollInterval = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

function connectWebSocket() {
  ws = new WebSocket("ws://127.0.0.1:8000/ws");

  ws.onopen = () => {
    console.log("WebSocket 已连接");
    isOnline.value = true;
    reconnectAttempts = 0;
    // 重连时清空旧数据，避免残留标记与新车叠加
    vehicles.value = [];
    dockedVehicles.value = [];
    frozenVehicles.value = {}; // 重连后重新开始判断冻结
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "score_change") {
        showScoreNotification(data.plate, data.score);
        // 同步更新 vehicles 列表里的积分
        const idx = vehicles.value.findIndex((v) => v.plate === data.plate);
        if (idx >= 0) {
          const updated = [...vehicles.value];
          updated[idx] = { ...updated[idx], score: data.score };
          vehicles.value = updated;
        }
        // 同步更新 allVehicles 列表
        const idx2 = allVehicles.value.findIndex((v) => v.plate === data.plate);
        if (idx2 >= 0) {
          const updated2 = [...allVehicles.value];
          updated2[idx2] = { ...updated2[idx2], score: data.score };
          allVehicles.value = updated2;
        }
        return;
      }
      if (data.type === "moving_vehicle") {
        // 行驶车辆数据更新
        const existingIndex = vehicles.value.findIndex(
          (v) => v.plate === data.plate,
        );
        const isViolation = !data.followed;
        const isFirstViolation =
          existingIndex >= 0 &&
          vehicles.value[existingIndex].compliance !== "violation" &&
          isViolation;

        // 违规瞬间冻结位置（保留冻结时的坐标）
        if (isFirstViolation) {
          const existing = vehicles.value[existingIndex];
          frozenVehicles.value[data.plate] = existing
            ? existing.position
            : data.position || [];
          console.log(
            "[WS] 车辆违规冻结:",
            data.plate,
            "位置:",
            frozenVehicles.value[data.plate],
          );
        }

        // 已冻结的车辆：位置不再更新，只更新积分/状态
        // 首次出现就是违规的车辆（followed=False）也要立即冻结
        if (existingIndex >= 0) {
          const isFirstViolation =
            vehicles.value[existingIndex].compliance !== "violation" &&
            isViolation;
          if (isFirstViolation) {
            frozenVehicles.value[data.plate] =
              vehicles.value[existingIndex].position;
          }
        } else if (isViolation) {
          // 新车首次出现就是违规，直接冻结
          frozenVehicles.value[data.plate] = data.position || [];
        }
        // 车辆恢复合规时解除冻结，使用最新坐标
        if (data.followed) {
          delete frozenVehicles.value[data.plate];
        }
        const vehicleData = {
          id: data.plate,
          plate: data.plate,
          route_id: data.route_id,
          position: frozenVehicles.value[data.plate] || data.position || [],
          score: data.score,
          followed: data.followed,
          compliance: data.followed ? "compliant" : "violation",
          track_id: data.track_id,
        };
        if (existingIndex >= 0) {
          // 必须创建新数组引用，否则 Vue 检测不到 prop 变化，子组件不重新渲染
          const updated = [...vehicles.value];
          updated[existingIndex] = vehicleData;
          vehicles.value = updated;
        } else {
          vehicles.value.push(vehicleData);
        }
        return;
      }
      if (data.type === "vehicle_stopped") {
        // 车辆停止行驶，从行驶列表移除，加入停靠列表
        const plate = data.plate;
        vehicles.value = vehicles.value.filter((v) => v.plate !== plate);
        dockedVehicles.value.push({ id: plate, plate: plate });
        delete frozenVehicles.value[plate];
        return;
      }
      if (data.type === "alert") {
        // 新告警（来自 WebSocket 广播）
        const alert = data.alert;
        if (alert) {
          alerts.value.unshift(alert);
          allAlerts.value.unshift(alert);
          if (alerts.value.length > 50)
            alerts.value = alerts.value.slice(0, 50);
          if (allAlerts.value.length > 50)
            allAlerts.value = allAlerts.value.slice(0, 50);
          console.log("[WS] 收到告警:", alert);

          // 传感器告警弹窗
          if (alert.source === "sensor") {
            sensorAlertPopup.value = {
              id: alert.id,
              level: alert.level,
              message: alert.message,
              time: alert.time
            };
          }
        }
        return;
      }
      if (data.type === "methane_sensor") {
        // 气体传感器数据（来自 WebSocket 广播）
        console.log("[WS] 气体传感器:", data);
        const sensor = {
          id: data.sensor_id,
          methane_percentage: data.methane_percentage,
          location: data.location,
          last_update: Date.now() / 1000,
          alert_level: data.alert_level
        };
        const idx = methaneSensors.value.findIndex(s => s.id === sensor.id);
        if (idx >= 0) {
          const updated = [...methaneSensors.value];
          updated[idx] = sensor;
          methaneSensors.value = updated;
        } else {
          methaneSensors.value.push(sensor);
        }
        return;
      }
    } catch (error) {
      console.error("解析消息失败:", error);
    }
  };

  ws.onerror = () => {
    isOnline.value = false;
  };
  ws.onclose = () => {
    isOnline.value = false;
    reconnectAttempts++;
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      setTimeout(connectWebSocket, reconnectAttempts * 3000);
    }
  };
}

function showScoreNotification(vehicleId, score) {
  const id = Date.now();
  notifications.value.push({ id, vehicleId, score });
  setTimeout(() => {
    notifications.value = notifications.value.filter((n) => n.id !== id);
  }, 4000);
}

// 首页数据加载
async function loadMethaneSensors() {
  try {
    const data = await fetchMethaneSensors();
    methaneSensors.value = data.methane || [];
  } catch (e) {
    console.error("加载传感器失败:", e);
  }
}

async function loadAlerts() {
  try {
    const data = await fetchAlerts();
    alerts.value = (data.alerts || []).map((a) => ({
      id: a.id,
      type: a.level,
      message: a.message,
      location: `${a.location[0]}, ${a.location[2]}`,
      time: a.time,
    }));
  } catch (e) {
    console.error("加载告警失败:", e);
  }
}

async function loadDockedVehicles() {
  try {
    const data = await fetchDockedVehicles();
    dockedVehicles.value = data.docked_vehicles || [];
  } catch (e) {
    console.error("加载停靠车辆失败:", e);
  }
}

async function pollHomeData() {
  await Promise.all([loadMethaneSensors(), loadAlerts(), loadDockedVehicles()]);
}

// 车辆监控页数据
async function loadAllVehicles() {
  try {
    const data = await fetchVehicles();
    allVehicles.value = data.vehicles || [];
  } catch (e) {
    console.error("加载车辆列表失败:", e);
  }
}

async function loadMovingVehicles() {
  try {
    const data = await fetchVehicles();
    vehicles.value = data.vehicles || [];
  } catch (e) {
    console.error("加载行驶车辆失败:", e);
  }
}

// 告警管理页数据
async function loadAllAlerts() {
  try {
    const data = await fetchAlerts();
    allAlerts.value = (data.alerts || []).map((a) => ({
      ...a,
      location: a.location,
    }));
  } catch (e) {
    console.error("加载告警列表失败:", e);
  }
}

// 告警操作
async function confirmAlert(alertId) {
  try {
    await fetch(`/api/alerts/${alertId}/confirm`, { method: "POST" });
    const alert = allAlerts.value.find((a) => a.id === alertId);
    if (alert) alert.confirmed = true;
  } catch (e) {
    console.error("确认告警失败:", e);
  }
}

async function deleteAlert(alertId) {
  try {
    await fetch(`/api/alerts/${alertId}`, { method: "DELETE" });
    allAlerts.value = allAlerts.value.filter((a) => a.id !== alertId);
  } catch (e) {
    console.error("删除告警失败:", e);
  }
}

// 历史数据加载函数
async function loadHistoryAlert() {
  // 由子组件自行加载
}

async function loadHistoryMethane() {
  // 由子组件自行加载
}

async function loadHistoryScore() {
  // 由子组件自行加载
}

async function loadHistoryStats() {
  // 由子组件自行加载
}

async function confirmAlertHome(alertId) {
  try {
    await fetch(`/api/alerts/${alertId}/confirm`, { method: "POST" });
    alerts.value = alerts.value.filter((a) => a.id !== alertId);
  } catch (e) {
    console.error("确认告警失败:", e);
  }
}

function getSensorLevel(pct) {
  if (pct > 5) return "danger";
  if (pct > 0) return "warning";
  return "";
}

function getStatusText(pct) {
  if (pct > 5) return "告警";
  if (pct > 0) return "预警";
  return "正常";
}

function handleVehicleClick() {}

onMounted(() => {
  updateTime();
  timeInterval = setInterval(updateTime, 1000);
  connectWebSocket();
  pollHomeData();
  loadAllVehicles();
  loadAllAlerts();
  pollInterval = setInterval(pollHomeData, 1000);
});

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval);
  if (pollInterval) clearInterval(pollInterval);
  if (ws) ws.close();
});
</script>

<style scoped>
/* 全屏页面容器 */
.full-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 占位页面 */
.placeholder-page {
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.placeholder-icon {
  font-size: 48px;
  opacity: 0.5;
}

.placeholder-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.placeholder-desc {
  font-size: 14px;
}

/* 侧边栏层级导航 */
.nav-group {
  margin-bottom: 2px;
}

.nav-group-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  position: relative;
}

.nav-group-title-row .nav-icon {
  font-size: 14px;
}

.nav-group-title-row .nav-label {
  flex: 1;
}

.nav-arrow {
  font-size: 9px;
  color: var(--text-secondary);
  transition: transform 0.15s;
  transform: rotate(0deg);
}

.nav-arrow.open {
  transform: rotate(90deg);
}

.nav-children {
  padding-left: 16px;
  margin: 2px 0;
  border-left: 1px solid var(--border);
  margin-left: 20px;
}

.nav-child-item {
  padding: 7px 12px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition:
    background 0.12s,
    color 0.12s;
  margin: 1px 0;
}

.nav-child-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.nav-child-item.active {
  background: rgba(59, 130, 246, 0.15);
  color: var(--info);
  font-weight: 500;
}

.top-nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.top-nav-item .nav-icon {
  font-size: 14px;
}
</style>
