<template>
  <div class="app-wrapper">
    <router-view />
    <div class="icp-footer">
      <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">
        沪ICP备2026026317号-1
      </a>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { initGlobalWebSocket, destroyGlobalWebSocket, useWebSocket } from './composables/useWebSocket'
import { useMeetingStore } from './stores/meeting'

let wsCleanup = null
let wsListeners = []

onMounted(() => {
  const ws = initGlobalWebSocket()

  // 全局会议状态同步监听
  const meetingStore = useMeetingStore()

  const handleMeetingUpdate = (data) => {
    if (data.type === 'motion_changed' || data.type === 'speakers_updated') {
      meetingStore.loadFullState()
    }
  }

  ws.on('motion_changed', handleMeetingUpdate)
  ws.on('speakers_updated', handleMeetingUpdate)
  wsListeners = [
    () => ws.off('motion_changed', handleMeetingUpdate),
    () => ws.off('speakers_updated', handleMeetingUpdate)
  ]
})

onUnmounted(() => {
  destroyGlobalWebSocket()
  wsListeners.forEach(fn => fn())
})
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: var(--font-family);
  -webkit-font-smoothing: antialiased;
}
.app-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.icp-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  text-align: center;
  padding: 4px 0;
  font-size: 11px;
  color: #909399;
  background: rgba(245, 247, 250, 0.85);
  z-index: 9999;
  pointer-events: none;
}
.icp-footer a {
  color: #909399;
  text-decoration: none;
  pointer-events: auto;
  transition: color 0.15s;
}
.icp-footer a:hover {
  color: var(--brand-primary, #5b92e5);
}
</style>
