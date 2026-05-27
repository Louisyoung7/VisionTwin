// REST API 请求（甲烷传感器、车辆）
const API_BASE = 'http://127.0.0.1:8000';

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
