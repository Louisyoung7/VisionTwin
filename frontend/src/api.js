// REST API 请求（甲烷传感器、车辆）
// 开发环境通过 vite 代理到后端
const API_BASE = '';

const DEFAULT_TIMEOUT = 10000;

async function requestWithTimeout(url, options = {}, timeout = DEFAULT_TIMEOUT) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('请求超时');
    }
    throw error;
  }
}

export async function fetchMethaneSensors() {
  return requestWithTimeout(`${API_BASE}/api/methane`);
}

export async function fetchVehicles() {
  return requestWithTimeout(`${API_BASE}/api/vehicles`);
}

export async function fetchVehicle(vehicleId) {
  return requestWithTimeout(`${API_BASE}/api/vehicles/${vehicleId}`);
}

export async function updateMethaneSensor(sensorId) {
  return requestWithTimeout(`${API_BASE}/api/methane/${sensorId}/update`, {
    method: 'POST'
  });
}

export async function fetchAlerts() {
  return requestWithTimeout(`${API_BASE}/api/alerts`);
}

export async function fetchDockedVehicles() {
  return requestWithTimeout(`${API_BASE}/api/vehicles/docked`);
}

export async function fetchVehicleScore(plate) {
  return requestWithTimeout(`${API_BASE}/api/vehicles/${plate}/score`);
}

// ===== 历史数据 =====

export async function fetchHistoryAlerts(params = {}) {
  const queryParts = [`hours=${params.hours || 24}`];
  if (params.source) queryParts.push(`source=${params.source}`);
  if (params.level) queryParts.push(`level=${params.level}`);
  return requestWithTimeout(`${API_BASE}/api/history/alerts?${queryParts.join('&')}`);
}

export async function fetchHistoryMethane(params = {}) {
  const queryParts = [`hours=${params.hours || 24}`];
  if (params.sensor_id) queryParts.push(`sensor_id=${params.sensor_id}`);
  return requestWithTimeout(`${API_BASE}/api/history/methane?${queryParts.join('&')}`);
}

export async function fetchHistoryScore(params = {}) {
  const queryParts = [`hours=${params.hours || 24}`];
  if (params.plate) queryParts.push(`plate=${params.plate}`);
  return requestWithTimeout(`${API_BASE}/api/history/score?${queryParts.join('&')}`);
}

export async function fetchHistoryStats(params = {}) {
  const query = new URLSearchParams({
    hours: params.hours || 24
  }).toString();
  return requestWithTimeout(`${API_BASE}/api/history/stats?${query}`);
}

export async function fetchHistoryPothole(params = {}) {
  const query = new URLSearchParams({
    hours: params.hours || 24
  }).toString();
  return requestWithTimeout(`${API_BASE}/api/history/pothole?${query}`);
}
