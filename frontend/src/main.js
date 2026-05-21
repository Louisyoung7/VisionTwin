// 从 node_modules 导入 Three.js（享受类型提示和 Tree-shaking）
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// ========== 1. 场景初始化 ==========
const scene = new THREE.Scene();  // 创建 Three.js 场景对象
scene.background = new THREE.Color(0x0a0a0a); // 设置场景背景为深灰色

const camera = new THREE.PerspectiveCamera(
  75,                                    // 视野角度 (FOV)
  window.innerWidth / window.innerHeight, // 宽高比
  0.1,                                   // 近裁切面
  1000                                   // 远裁切面
);
camera.position.set(0, 20, 20);  // 相机位置 (x, y, z)
camera.lookAt(0, 0, 0);           // 相机朝向原点

const renderer = new THREE.WebGLRenderer({ antialias: true }); // 创建 WebGL 渲染器，启用抗锯齿
renderer.setSize(window.innerWidth, window.innerHeight); // 全屏尺寸渲染
document.body.appendChild(renderer.domElement); // 将 Canvas 元素添加到 HTML body

// 添加轨道控制器，实现鼠标交互控制视角
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;      // 启用阻尼（惯性效果）
controls.dampingFactor = 0.05;      // 阻尼系数
controls.enableZoom = true;         // 启用缩放
controls.enablePan = true;           // 启用平移
controls.maxPolarAngle = Math.PI / 2 - 0.05; // 限制视角不能低于地面

// 添加地面（使用平面图纹理）
const textureLoader = new THREE.TextureLoader();
const floorTexture = textureLoader.load('/floor-plan.png');

floorTexture.wrapS = THREE.RepeatWrapping;
floorTexture.wrapT = THREE.RepeatWrapping;

const floorGeometry = new THREE.PlaneGeometry(30, 30); // 创建 30×30 单位的平面几何体
const floorMaterial = new THREE.MeshBasicMaterial({ 
  map: floorTexture,
  side: THREE.DoubleSide
}); // 使用 MeshBasicMaterial 应用纹理

const floor = new THREE.Mesh(floorGeometry, floorMaterial);
floor.rotation.x = -Math.PI / 2; // 绕 X 轴旋转 -90° 使平面水平放置
floor.position.y = 0;
scene.add(floor);

// 添加边缘线框，增强视觉效果
const edgesGeometry = new THREE.EdgesGeometry(floorGeometry);
const edgesMaterial = new THREE.LineBasicMaterial({ color: 0xffffff, opacity: 0.3, transparent: true });
const edges = new THREE.LineSegments(edgesGeometry, edgesMaterial);
edges.rotation.x = -Math.PI / 2;
edges.position.y = 0.01; // 略高于地面避免 z-fighting
scene.add(edges);

// ========== 2. 获取车辆元数据 ==========
let vehicleMetadata = {};

async function fetchVehicleMetadata() {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/vehicles');
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

// ========== 3. WebSocket 连接 ==========
let wsData = { objects: [] };

function connectWebSocket() {
  const ws = new WebSocket('ws://127.0.0.1:8000/ws');

  ws.onopen = () => {
    console.log('WebSocket connected');
    ws.send('start');  // 发送启动信号
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

// ========== 4. 创建标签 Sprite ==========
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

// ========== 5. 3D 渲染逻辑 ==========
let markers = [];
let labels = [];

function updateScene(objects) {
  // 清除旧标记和标签
  markers.forEach(m => scene.remove(m));
  labels.forEach(l => scene.remove(l));
  markers = [];
  labels = [];

  // 创建新标记
  objects.forEach(obj => {
    const geometry = new THREE.BoxGeometry(1, 0.5, 2);
    const material = new THREE.MeshBasicMaterial({ color: 0x0088ff });

    const marker = new THREE.Mesh(geometry, material);
    marker.position.set(
      obj.position[0],
      obj.position[1] + 0.25,
      obj.position[2]
    );

    scene.add(marker);
    markers.push(marker);

    // 创建车牌标签
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

// ========== 6. 动画循环 ==========
function animate() {
  requestAnimationFrame(animate);  // 循环调用
  
  controls.update();  // 更新控制器状态
  
  if (Date.now() % 200 < 16) {
    updateScene(wsData.objects);
    document.getElementById('info').textContent =
      `Objects: ${wsData.objects.length}`;
  }
  
  renderer.render(scene, camera);  // 渲染场景
}
animate();

// 窗口自适应调整
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
