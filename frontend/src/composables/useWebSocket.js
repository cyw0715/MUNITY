import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { ElNotification } from 'element-plus'

let ws = null
let reconnectTimer = null
let heartbeatTimer = null
const listeners = new Map()
const isConnected = ref(false)

/**
 * WebSocket 连接管理 composable
 * 提供全局 WebSocket 连接和消息监听能力
 */
export function useWebSocket() {
  const authStore = useAuthStore()
  let baseUrl = ''

  function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) return
    if (!authStore.user?.id) return

    // 动态获取 WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    baseUrl = `${protocol}//${window.location.host}/api/ws/${authStore.user.id}`

    try {
      ws = new WebSocket(baseUrl)

      ws.onopen = () => {
        isConnected.value = true
        console.log('[WebSocket] 已连接')
        startHeartbeat()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'pong') return

          // 触发所有已注册的监听器
          if (data.type && listeners.has(data.type)) {
            listeners.get(data.type).forEach(cb => cb(data))
          }

          // 全局监听器（不区分类型）
          if (listeners.has('*')) {
            listeners.get('*').forEach(cb => cb(data))
          }

          // 新消息通知 — 常驻直到用户点击关闭
          if (data.type === 'new_async_message') {
            ElNotification({
              title: '新的非对称消息',
              message: data.message?.title || '你收到了一条非对称消息',
              type: 'info',
              duration: 0
            })
          }

          // 联署完成通知 — 全屏模式时不弹出
          if (data.type === 'endorsement_completed' && !document.fullscreenElement) {
            const isApproved = data.result === 'approved'
            ElNotification({
              title: isApproved ? '联署已全部通过' : '联署未通过',
              message: `《${data.title}》${data.label || (isApproved ? '已获得所有联署代表团通过' : '已有代表团拒绝联署')}`,
              type: isApproved ? 'success' : 'warning',
              duration: 0
            })
          }
        } catch (e) {
          // 忽略非 JSON 消息
        }
      }

      ws.onclose = () => {
        isConnected.value = false
        stopHeartbeat()
        // 自动重连
        if (!reconnectTimer) {
          reconnectTimer = setTimeout(() => {
            reconnectTimer = null
            connect()
          }, 5000)
        }
      }

      ws.onerror = () => {
        ws?.close()
      }
    } catch (e) {
      console.error('[WebSocket] 连接失败:', e)
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    stopHeartbeat()
    if (ws) {
      ws.close()
      ws = null
    }
    isConnected.value = false
  }

  function startHeartbeat() {
    stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send('ping')
      }
    }, 30000) // 每30秒心跳
  }

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  /**
   * 注册消息监听器
   * @param {string} type - 消息类型，'*' 表示所有类型
   * @param {Function} callback - 回调函数
   */
  function on(type, callback) {
    if (!listeners.has(type)) {
      listeners.set(type, new Set())
    }
    listeners.get(type).add(callback)
  }

  /**
   * 移除消息监听器
   */
  function off(type, callback) {
    if (listeners.has(type)) {
      listeners.get(type).delete(callback)
    }
  }

  return {
    isConnected,
    connect,
    disconnect,
    on,
    off
  }
}

// 全局单例状态
let globalWs = null
let globalCleanup = null

/**
 * 初始化全局 WebSocket 连接（在 App.vue 中调用）
 */
export function initGlobalWebSocket() {
  if (globalWs) return
  const ws = useWebSocket()
  // 延迟2秒连接，确保 auth store 已初始化
  setTimeout(() => ws.connect(), 2000)
  globalWs = ws
  globalCleanup = () => ws.disconnect()
  return ws
}

/**
 * 关闭全局 WebSocket 连接
 */
export function destroyGlobalWebSocket() {
  if (globalCleanup) {
    globalCleanup()
    globalWs = null
    globalCleanup = null
  }
}
