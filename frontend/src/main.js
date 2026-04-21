// 从 node_modules 导入 Three.js（享受类型提示和 Tree-shaking）
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// ========== 1. 场景初始化 ==========
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0a0a);

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 15, 15);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// 添加轨道控制器
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; // 启用阻尼效果
controls.dampingFactor = 0.05; // 阻尼系数
controls.enableZoom = true; // 启用缩放
controls.enablePan = true; // 启用平移

// 添加地面网格
const gridHelper = new THREE.GridHelper(40, 40, 0xffffff, 0x444444);
gridHelper.position.y = -0.1;
scene.add(gridHelper);

// ========== 2. Mock 数据生成器 ==========
function generateMockFrame() {
  const objects = [];
  const count = Math.floor(Math.random() * 5);
  
  for (let i = 0; i < count; i++) {
    objects.push({
      class_name: ['person', 'car'][Math.floor(Math.random() * 2)],
      bbox: [
        Math.random() * 0.8,
        Math.random() * 0.8,
        Math.random() * 0.2 + 0.8,
        Math.random() * 0.2 + 0.8
      ]
    });
  }
  return { frame_id: Date.now(), objects };
}

// ========== 3. 3D 渲染逻辑 ==========
let markers = [];

function updateScene(objects) {
  // 清除旧标记
  markers.forEach(m => scene.remove(m));
  markers = [];
  
  // 创建新标记
  objects.forEach(obj => {
    const geometry = obj.class_name === 'person'
      ? new THREE.CylinderGeometry(0.3, 0.3, 1.8)
      : new THREE.BoxGeometry(1, 0.5, 2);
      
    const material = new THREE.MeshBasicMaterial({ 
      color: obj.class_name === 'person' ? 0x00ff00 : 0x0088ff 
    });
    
    const marker = new THREE.Mesh(geometry, material);
    marker.position.set(
      (Math.random() - 0.5) * 30, // x: -15 ~ 15
      obj.class_name === 'person' ? 0.9 : 0.25,
      (Math.random() - 0.5) * 30  // z: -15 ~ 15
    );
    
    scene.add(marker);
    markers.push(marker);
  });
}

// ========== 4. 动画循环 ==========
function animate() {
  requestAnimationFrame(animate);
  
  // 更新控制器
  controls.update();
  
  // 每 200ms 更新数据
  if (Date.now() % 200 < 16) {
    const mockData = generateMockFrame();
    updateScene(mockData.objects);
    document.getElementById('info').textContent = 
      `Objects: ${mockData.objects.length}`;
  }
  
  renderer.render(scene, camera);
}
animate();

// 自适应窗口
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});