import { ref, onMounted, onUnmounted } from 'vue'
import api from '../api'

// 通知状态
const notifications = ref({
  directives: false,
  documents: false,
  updates: false,
  meetingFiles: false
})

// 上次检查的数量
const lastCounts = ref({
  directives: 0,
  documents: 0,
  updates: 0,
  meetingFiles: 0
})

let pollTimer = null
let initialized = false

export function useNotification(role) {
  // 从 localStorage 恢复上次的数量
  function restoreCounts() {
    const saved = localStorage.getItem(`notification_counts_${role}`)
    if (saved) {
      try {
        lastCounts.value = JSON.parse(saved)
      } catch (e) {}
    }
  }

  // 保存数量到 localStorage
  function saveCounts() {
    localStorage.setItem(`notification_counts_${role}`, JSON.stringify(lastCounts.value))
  }

  // 检查新内容
  async function checkNewItems() {
    try {
      if (role === 'staff') {
        const [dRes, docRes, uRes] = await Promise.all([
          api.get('/api/staff/directives'),
          api.get('/api/staff/documents'),
          api.get('/api/staff/updates')
        ])

        const newDirectives = dRes.data.length
        const newDocuments = docRes.data.length
        const newUpdates = uRes.data.filter(u => u.type === 'text').length

        // 只在初始化后才比较（避免首次加载就闪动）
        if (initialized) {
          notifications.value.directives = newDirectives > lastCounts.value.directives
          notifications.value.documents = newDocuments > lastCounts.value.documents
          notifications.value.updates = newUpdates > lastCounts.value.updates
        }

        lastCounts.value.directives = newDirectives
        lastCounts.value.documents = newDocuments
        lastCounts.value.updates = newUpdates
        saveCounts()
      } else if (role === 'delegate') {
        const [uRes, mRes] = await Promise.all([
          api.get('/api/delegate/updates'),
          api.get('/api/delegate/meeting-files')
        ])

        const newUpdates = uRes.data.filter(u => u.type === 'text').length
        const newMeetingFiles = mRes.data.length

        if (initialized) {
          notifications.value.updates = newUpdates > lastCounts.value.updates
          notifications.value.meetingFiles = newMeetingFiles > lastCounts.value.meetingFiles
        }

        lastCounts.value.updates = newUpdates
        lastCounts.value.meetingFiles = newMeetingFiles
        saveCounts()
      }

      if (!initialized) {
        initialized = true
      }
    } catch (e) {}
  }

  // 清除某个通知（用户点击后）
  function clearNotification(type) {
    notifications.value[type] = false
  }

  // 启动轮询
  function startPolling() {
    restoreCounts()
    checkNewItems()
    pollTimer = setInterval(checkNewItems, 10000) // 每10秒检查一次
  }

  // 停止轮询
  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    notifications,
    clearNotification,
    startPolling,
    stopPolling
  }
}
