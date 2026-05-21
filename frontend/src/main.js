import './style.css';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

const API_BASE = 'http://127.0.0.1:8000';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0a0a);

const camera = new THREE.PerspectiveCamera(
  75,
  800 / 500,
  0.1,
  1000
);
camera.position.set(0, 20, 20);
camera.lookAt(0, 0, 0);

const container = document.getElementById('viewer-container');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.enableZoom = true;
controls.enablePan = true;
controls.maxPolarAngle = Math.PI / 2 - 0.05;

const textureLoader = new THREE.TextureLoader();
const floorTexture = textureLoader.load('/floor-plan.png');
floorTexture.wrapS = THREE.RepeatWrapping;
floorTexture.wrapT = THREE.RepeatWrapping;

const floorGeometry = new THREE.PlaneGeometry(30, 30);
const floorMaterial = new THREE.MeshBasicMaterial({
  map: floorTexture,
  side: THREE.DoubleSide
});

const floor = new THREE.Mesh(floorGeometry, floorMaterial);
floor.rotation.x = -Math.PI / 2;
floor.position.y = 0;
scene.add(floor);

const edgesGeometry = new THREE.EdgesGeometry(floorGeometry);
const edgesMaterial = new THREE.LineBasicMaterial({ color: 0xffffff, opacity: 0.3, transparent: true });
const edges = new THREE.LineSegments(edgesGeometry, edgesMaterial);
edges.rotation.x = -Math.PI / 2;
edges.position.y = 0.01;
scene.add(edges);

let vehicleMetadata = {};

async function fetchVehicleMetadata() {
  try {
    const res = await fetch(`${API_BASE}/api/vehicles`);
    const data = await res.json();
    vehicleMetadata = {};
    data.vehicles.forEach(v => {
      vehicleMetadata[v.id] = v.plate;
    });
  } catch (err) {
    console.error('Failed to fetch vehicle metadata:', err);
  }
}
fetchVehicleMetadata();

let wsData = { objects: [] };

function connectWebSocket() {
  const ws = new WebSocket(`${API_BASE.replace('http', 'ws')}/ws`);

  ws.onopen = () => {
    console.log('WebSocket connected');
    ws.send('start');
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    wsData = data;
  };

  ws.onerror = (err) => {
    console.error('WebSocket error:', err);
  };

  ws.onclose = () => {
    console.log('WebSocket closed, reconnecting...');
    setTimeout(connectWebSocket, 2000);
  };
}
connectWebSocket();

function createLabel(text) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = 256;
  canvas.height = 64;

  ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = 'white';
  ctx.font = 'bold 32px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, canvas.width / 2, canvas.height / 2);

  const texture = new THREE.CanvasTexture(canvas);
  const spriteMaterial = new THREE.SpriteMaterial({ map: texture });
  const sprite = new THREE.Sprite(spriteMaterial);
  sprite.scale.set(2, 0.5, 1);

  return sprite;
}

let markers = [];
let labels = [];

function updateScene(objects) {
  markers.forEach(m => scene.remove(m));
  labels.forEach(l => scene.remove(l));
  markers = [];
  labels = [];

  objects.forEach(obj => {
    const geometry = new THREE.BoxGeometry(1, 0.5, 2);
    const material = new THREE.MeshBasicMaterial({ color: 0x22c55e });

    const marker = new THREE.Mesh(geometry, material);
    marker.position.set(
      obj.position[0],
      obj.position[1] + 0.25,
      obj.position[2]
    );

    scene.add(marker);
    markers.push(marker);

    const plate = vehicleMetadata[obj.id] || `ID:${obj.id}`;
    const label = createLabel(plate);
    label.position.set(
      obj.position[0],
      obj.position[1] + 1.2,
      obj.position[2]
    );

    scene.add(label);
    labels.push(label);
  });
}

function animate() {
  requestAnimationFrame(animate);

  controls.update();

  if (Date.now() % 200 < 16) {
    updateScene(wsData.objects);
    document.getElementById('info').textContent =
      `Objects: ${wsData.objects.length}`;
  }

  renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
  const width = container.clientWidth;
  const height = container.clientHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
});

function getMethaneLevel(value) {
  if (value < 50) return 'normal';
  if (value < 80) return 'warning';
  return 'danger';
}

function formatTime(timestamp) {
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString('zh-CN', { hour12: false });
}

async function fetchMethaneData() {
  const btn = document.getElementById('refresh-btn');
  btn.classList.add('loading');

  try {
    const res = await fetch(`${API_BASE}/api/methane`);
    const data = await res.json();

    const container = document.getElementById('methane-data');

    if (!data.sensors || data.sensors.length === 0) {
      container.innerHTML = '<div class="error">暂无传感器数据</div>';
      return;
    }

    container.innerHTML = data.sensors.map(sensor => {
      const level = getMethaneLevel(sensor.methane_percentage);
      const [x, , z] = sensor.location;

      return `
        <div class="sensor-card">
          <div class="sensor-header">
            <span class="sensor-id">传感器 #${sensor.id}</span>
            <span class="sensor-location">位置 (${x.toFixed(1)}, ${z.toFixed(1)})</span>
          </div>
          <div class="methane-value ${level}">
            ${sensor.methane_percentage.toFixed(1)}
            <span class="unit">%</span>
          </div>
          <div class="methane-bar">
            <div class="methane-bar-fill ${level}" style="width: ${sensor.methane_percentage}%"></div>
          </div>
          <div class="last-update">更新: ${formatTime(sensor.last_update)}</div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed to fetch methane data:', err);
    document.getElementById('methane-data').innerHTML =
      '<div class="error">数据加载失败</div>';
  } finally {
    btn.classList.remove('loading');
  }
}

async function updateAllSensors() {
  await Promise.all([
    fetch(`${API_BASE}/api/methane/0/update`, { method: 'POST' }),
    fetch(`${API_BASE}/api/methane/1/update`, { method: 'POST' }),
    fetch(`${API_BASE}/api/methane/2/update`, { method: 'POST' }),
    fetch(`${API_BASE}/api/methane/3/update`, { method: 'POST' }),
    fetch(`${API_BASE}/api/methane/4/update`, { method: 'POST' }),
  ]);
}

document.getElementById('refresh-btn').addEventListener('click', () => {
  const btn = document.getElementById('refresh-btn');
  btn.classList.add('loading');
  updateAllSensors().then(fetchMethaneData).finally(() => btn.classList.remove('loading'));
});

fetchMethaneData();
setInterval(async () => {
  await updateAllSensors();
  fetchMethaneData();
}, 5000);
