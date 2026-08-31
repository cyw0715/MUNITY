<template>
  <router-view />
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
</style>
