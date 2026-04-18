<script setup>
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { onMounted, onUnmounted, ref } from 'vue'

const container = ref(null)
let scene, camera, renderer, model, animationId

const initThree = () => {
  // 创建场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf0f0f0)

  // 创建相机
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
  camera.position.z = 5

  // 创建渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(window.innerWidth, window.innerHeight)
  container.value.appendChild(renderer.domElement)

  // 添加灯光
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(1, 1, 1)
  scene.add(directionalLight)

  // 加载模型
  const loader = new GLTFLoader()
  loader.load('/models/demon_slayer_girl.glb', (gltf) => {
    model = gltf.scene
    model.scale.set(0.5, 0.5, 0.5)
    model.position.y = -1
    scene.add(model)
  }, undefined, (error) => {
    console.error('Error loading model:', error)
  })

  // 响应窗口大小变化
  window.addEventListener('resize', onWindowResize)
}

const onWindowResize = () => {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
}

const animate = () => {
  animationId = requestAnimationFrame(animate)
  
  if (model) {
    model.rotation.y += 0.01
  }
  
  renderer.render(scene, camera)
}

onMounted(() => {
  initThree()
  animate()
})

onUnmounted(() => {
  window.removeEventListener('resize', onWindowResize)
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (renderer) {
    renderer.dispose()
  }
})
</script>

<template>
  <div class="model-container" ref="container"></div>
</template>

<style scoped>
.model-container {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>
