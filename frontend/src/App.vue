<template>
  <router-view />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { initGlobalWebSocket, destroyGlobalWebSocket } from './composables/useWebSocket'

let wsCleanup = null

onMounted(() => {
  const ws = initGlobalWebSocket()
  // 可以添加全局消息监听
})

onUnmounted(() => {
  destroyGlobalWebSocket()
})
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}
</style>
