<template>
  <div ref="mapContainerRef" id="map-container"></div>

  <div class="map-overlay">
    <div class="overlay-item">
      <span class="overlay-label">行驶车辆</span>
      <span class="overlay-value">{{ vehicles.length }}</span>
    </div>
    <div class="overlay-item">
      <span class="overlay-label">告警事件</span>
      <span class="overlay-value danger">{{ alertCount }}</span>
    </div>
  </div>

  <div v-if="selectedVehicle" class="info-panel">
    <button class="close-btn" @click="selectedVehicle = null">&times;</button>
    <h4>{{ selectedVehicle.name }}</h4>
    <div class="info-content">
      <p>
        <span>车牌</span> <span>{{ selectedVehicle.plate }}</span>
      </p>
      <p>
        <span>位置</span> <span>{{ selectedVehicle.position.join(", ") }}</span>
      </p>
      <p>
        <span>积分</span> <span>{{ selectedVehicle.score }}</span>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from "vue";

const props = defineProps({
  vehicles: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["vehicle-click"]);

const mapContainerRef = ref(null);
const alertCount = computed(() =>
  props.vehicles.filter((v) => v.compliance === "violation").length,
);
const selectedVehicle = ref(null);

const vehicleMarkers = new Map();
const markerContainer = ref(null);

function initMap() {
  const container = mapContainerRef.value;
  if (!container) return;

  container.innerHTML = "";
  container.style.background = "#1a1d27";

  const floorPlan = document.createElement("img");
  floorPlan.src = "/floot.svg";
  floorPlan.alt = "楼层平面图";
  floorPlan.style.cssText = `
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 96%; height: 96%;
    object-fit: contain; pointer-events: none;
  `;
  container.appendChild(floorPlan);

  const markerLayer = document.createElement("div");
  markerLayer.id = "marker-layer";
  markerLayer.style.cssText = `
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
  `;
  container.appendChild(markerLayer);
  markerContainer.value = markerLayer;

  floorPlan.onload = () => {
    updateVehicleMarkers();
  };

  floorPlan.onerror = () => {
    console.warn("楼层平面图加载失败");
  };
}

function getMarkerPosition(x, z) {
  if (!markerContainer.value) return { left: 0, top: 0 };

  const container = markerContainer.value.parentElement;
  if (!container || !container.offsetWidth) return { left: x, top: z };

  // SVG 像素空间（floot.svg: 502x636），在容器中居中缩放至 96%（object-fit: contain）
  const SVG_WIDTH = 502;
  const SVG_HEIGHT = 636;
  // contain 缩放：取两个方向缩放比的最小值，保证 SVG 完整显示
  const scale = Math.min(
    (container.offsetWidth * 0.96) / SVG_WIDTH,
    (container.offsetHeight * 0.96) / SVG_HEIGHT,
  );
  const scaledW = SVG_WIDTH * scale;
  const scaledH = SVG_HEIGHT * scale;
  const offsetX = (container.offsetWidth - scaledW) / 2;
  const offsetY = (container.offsetHeight - scaledH) / 2;

  return {
    left: offsetX + x * scale,
    top: offsetY + z * scale,
  };
}

function updateVehicleMarkers() {
  console.log(
    "[MapView] updateVehicleMarkers called, vehicles count:",
    props.vehicles.length,
  );
  if (!markerContainer.value) return;

  const currentIds = new Set(props.vehicles.map((v) => v.id));

  vehicleMarkers.forEach((el, id) => {
    if (!currentIds.has(id)) {
      el.remove();
      vehicleMarkers.delete(id);
    }
  });

  props.vehicles.forEach((vehicle) => {
    const pos2d = vehicle.position || [];
    const x = pos2d[0] ?? 0;
    const z = pos2d[2] ?? pos2d[1] ?? 0;
    const pos = getMarkerPosition(x, z);
    const isViolation = vehicle.compliance === "violation";
    const color = isViolation ? "#ef4444" : "#3b82f6";
    const plate = vehicle.plate || `T${vehicle.track_id}`;
    const markerId = vehicle.id || vehicle.plate || `track_${vehicle.track_id}`;

    if (vehicleMarkers.has(markerId)) {
      console.log(
        `[MapView] UPDATE marker ${markerId} → (${pos.left.toFixed(0)}, ${pos.top.toFixed(0)})`,
      );
      const el = vehicleMarkers.get(markerId);
      el.style.left = `${pos.left - 12}px`;
      el.style.top = `${pos.top - 12}px`;
    } else {
      console.log(
        `[MapView] CREATE marker ${markerId} at (${pos.left.toFixed(0)}, ${pos.top.toFixed(0)})`,
      );
      const el = document.createElement("div");
      el.className = "vehicle-marker";
      el.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <rect x="2" y="8" width="20" height="9" rx="3" fill="${color}" stroke="white" stroke-width="1.5"/>
        <circle cx="7" cy="18" r="2" fill="white"/>
        <circle cx="17" cy="18" r="2" fill="white"/>
        <rect x="5" y="10" width="6" height="4" rx="1" fill="rgba(255,255,255,0.3)"/>
        <rect x="13" y="10" width="6" height="4" rx="1" fill="rgba(255,255,255,0.3)"/>
      </svg>`;
      el.title = `${plate}  ${isViolation ? "⚠违规" : "✓合规"}`;
      el.style.cssText = `
        position: absolute; left: ${pos.left - 12}px; top: ${pos.top - 12}px;
        width: 24px; height: 24px; cursor: pointer; pointer-events: auto;
        filter: ${isViolation ? "drop-shadow(0 0 4px #ef4444)" : "drop-shadow(0 0 3px rgba(59,130,246,0.5))"};
        transition: filter 0.2s;
      `;
      el.onclick = () => {
        selectedVehicle.value = {
          name: `车辆 ${plate}`,
          plate: plate,
          position: vehicle.position,
          score: vehicle.score || "未知",
        };
        emit("vehicle-click", vehicle);
      };
      markerContainer.value.appendChild(el);
      vehicleMarkers.set(markerId, el);
    }
  });
}

watch(() => props.vehicles, updateVehicleMarkers, { deep: true });

onMounted(() => {
  initMap();
});

onUnmounted(() => {
  vehicleMarkers.forEach((el) => el.remove());
});
</script>
