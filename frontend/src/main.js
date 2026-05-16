// 从 node_modules 导入 Three.js（享受类型提示和 Tree-shaking）
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// ========== 1. 场景初始化 ==========
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0a0a);

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 20, 20);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// 添加轨道控制器
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.enableZoom = true;
controls.enablePan = true;
controls.maxPolarAngle = Math.PI / 2 - 0.05; // 限制视角不能低于地面

// 添加地面（使用平面图纹理）
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
floor.rotation.x = -Math.PI / 2; // 旋转使其水平
floor.position.y = 0;
scene.add(floor);

// 添加边缘线框（可选，增强视觉效果）
const edgesGeometry = new THREE.EdgesGeometry(floorGeometry);
const edgesMaterial = new THREE.LineBasicMaterial({ color: 0xffffff, opacity: 0.3, transparent: true });
const edges = new THREE.LineSegments(edgesGeometry, edgesMaterial);
edges.rotation.x = -Math.PI / 2;
edges.position.y = 0.01; // 略高于地面避免 z-fighting
scene.add(edges);

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
  markers.forEach(m => scene.remove(m));
  markers = [];
  
  objects.forEach(obj => {
    const geometry = obj.class_name === 'person'
      ? new THREE.CylinderGeometry(0.3, 0.3, 1.8)
      : new THREE.BoxGeometry(1, 0.5, 2);
      
    const material = new THREE.MeshBasicMaterial({ 
      color: obj.class_name === 'person' ? 0x00ff00 : 0x0088ff 
    });
    
    const marker = new THREE.Mesh(geometry, material);
    marker.position.set(
      (Math.random() - 0.5) * 25, 
      obj.class_name === 'person' ? 0.9 : 0.25,
      (Math.random() - 0.5) * 25  
    );
    
    scene.add(marker);
    markers.push(marker);
  });
}

// ========== 4. 动画循环 ==========
function animate() {
  requestAnimationFrame(animate);
  
  controls.update();
  
  if (Date.now() % 200 < 16) {
    const mockData = generateMockFrame();
    updateScene(mockData.objects);
    document.getElementById('info').textContent = 
      `Objects: ${mockData.objects.length}`;
  }
  
  renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});