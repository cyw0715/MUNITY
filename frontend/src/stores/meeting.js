import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'
import { useWebSocket } from '../composables/useWebSocket'

/**
 * 全局会议状态 Store
 * 生命周期 = SPA 生命周期，不受路由切换影响
 * 
 * 计时器架构：服务端持久化作为基准时钟
 * - 控制端（点击开始的那个）每 200ms 推送状态到服务端
 * - 服务端持久化到 DB 并 WS 广播给所有学团端
 * - 所有端（含控制端自己）收到 WS timer_sync 后更新显示
 * - 远程端收到 running=true 时启动本地显示倒数（不推送）
 * - 页面切换后 loadFullState() 从服务端 GET timer-state 恢复
 */
export const useMeetingStore = defineStore('meeting', () => {
  // ============ 状态 ============

  const currentAgenda = ref(null)
  const agendaItems = ref([])
  const activeMotion = ref(null)
  const speakersList = ref([])
  const currentSpeaker = ref(null)

  // 主发言名单：本会场启用该功能、且当前没有活跃动议时，
  // speakersList 装载的是主发言名单。它只跑单位时长计时（没有总时长），
  // 时长按会场保存，可在计时器抬头栏直接调整。
  const mainSpeakersEnabled = ref(false)
  const mainUnitDuration = ref(60)
  const isMainSpeakerMode = computed(() => mainSpeakersEnabled.value && !activeMotion.value)

  // 计时器（由服务端状态驱动）
  const timerRunning = ref(false)
  const unitRemaining = ref(0)
  const totalRemaining = ref(0)
  const elapsedSeconds = ref(0)

  // 本地时钟
  let controllerTick = null     // 控制端每秒倒数
  let controllerPush = null     // 控制端每 200ms 推送
  let isControlling = false     // 本端是否在控制计时器
  let displayTick = null        // 远程端本地显示倒数（不推送）

  // 发言记录
  const speechContent = ref('')

  // 基础数据
  const delegations = ref([])
  const allDelegates = ref([])

  // ============ 计算属性 ============

  const hasActiveMeeting = computed(() => !!activeMotion.value)
  const isSpeaking = computed(() => !!currentSpeaker.value)
  
  const formattedUnitTime = computed(() => formatTime(unitRemaining.value))
  const formattedTotalTime = computed(() => formatTime(totalRemaining.value))

  // ============ 计时器核心 ============

  function formatTime(seconds) {
    if (seconds < 0) seconds = 0
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }

  /** 本地一秒一跳（共用的倒数逻辑） */
  function tickDown() {
    elapsedSeconds.value++
    if (totalRemaining.value > 0) {
      totalRemaining.value--
    }
    if (unitRemaining.value > 0) {
      unitRemaining.value--
      if (unitRemaining.value === 0 && currentSpeaker.value) {
        stopAllTicks()
        ElMessage.warning('单位发言时间到！')
        return
      }
    }
    if (totalRemaining.value === 0 && activeMotion.value?.total_duration) {
      stopAllTicks()
      ElMessage.warning('总时长已耗尽！')
    }
  }

  function stopAllTicks() {
    timerRunning.value = false
    if (controllerTick) { clearInterval(controllerTick); controllerTick = null }
    if (controllerPush) { clearInterval(controllerPush); controllerPush = null }
    if (displayTick) { clearInterval(displayTick); displayTick = null }
    isControlling = false
  }

  /** 从服务端同步计时器状态（用于 loadFullState 后恢复） */
  async function loadTimerState() {
    if (!activeMotion.value) return
    try {
      const { data } = await api.get(`/api/staff/motions/${activeMotion.value.id}/timer-state`)
      timerRunning.value = data.running
      unitRemaining.value = data.unit_remaining
      totalRemaining.value = data.total_remaining
      elapsedSeconds.value = data.elapsed
      // 如果服务端返回全零但 motion 有配置，用配置值初始化（新建动议/旧数据）
      if (!data.running && data.unit_remaining === 0 && data.total_remaining === 0 && activeMotion.value.unit_duration) {
        unitRemaining.value = activeMotion.value.unit_duration
        totalRemaining.value = activeMotion.value.total_duration
        elapsedSeconds.value = 0
      }
      // 恢复后若服务端正在运行，启动远程显示倒数
      if (data.running && !isControlling) {
        startDisplayTick()
      }
    } catch (e) {
      // 网络错误时从 motion 配置初始化
      unitRemaining.value = activeMotion.value.unit_duration || 0
      totalRemaining.value = activeMotion.value.total_duration || 0
      elapsedSeconds.value = 0
      timerRunning.value = false
    }
  }

  /** 向服务端推送计时器状态并广播到所有端 */
  async function pushTimerState() {
    if (!activeMotion.value) return
    try {
      await api.put(`/api/staff/motions/${activeMotion.value.id}/timer-sync`, {
        running: timerRunning.value,
        unit_remaining: unitRemaining.value,
        total_remaining: totalRemaining.value,
        elapsed: elapsedSeconds.value,
        sync_at: Date.now()
      })
    } catch (e) {}
  }

  // ============ 控制端 ============

  /** 控制端：开始计时 */
  function startLocalTick() {
    stopAllTicks()
    isControlling = true
    timerRunning.value = true
    pushTimerState()  // 立即推送：其它端收到后启动 displayTick

    controllerTick = setInterval(tickDown, 1000)

    // 每 200ms 推送到服务端（服务端状态误差 ≤200ms）
    controllerPush = setInterval(() => {
      pushTimerState()
    }, 200)
  }

  /** 控制端：暂停 */
  function stopLocalTick() {
    stopAllTicks()
    pushTimerState()  // 推送停止状态：其它端收到后停止 displayTick
  }

  // ============ 远程端 ============

  /** 远程端：启动本地显示倒数（只倒数不推送） */
  function startDisplayTick() {
    if (displayTick) return
    timerRunning.value = true
    displayTick = setInterval(() => {
      tickDown()
    }, 1000)
  }

  function stopDisplayTick() {
    timerRunning.value = false
    if (displayTick) {
      clearInterval(displayTick)
      displayTick = null
    }
  }

  /** WS 收到远程 timer_sync 时调用 */
  function applyTimerSync(timer) {
    // 不论是不是控制端，都用服务端数值校准（控制端自身也校准，消除累积误差）
    unitRemaining.value = timer.unit_remaining
    totalRemaining.value = timer.total_remaining
    elapsedSeconds.value = timer.elapsed || 0

    if (isControlling) {
      // 控制端：只接受服务端的数值校准，运行状态由自己控制
      return
    }

    // 远程端：接受运行状态
    if (timer.running) {
      startDisplayTick()
    } else {
      stopDisplayTick()
    }
  }

  // ============ WebSocket 监听 ============

  let wsCleanup = null

  function registerWebSocketListener() {
    if (wsCleanup) return
    const ws = useWebSocket()
    const handler = (data) => {
      applyMeetingUpdate(data)
    }
    ws.on('*', handler)
    wsCleanup = () => ws.off('*', handler)
  }

  function unregisterWebSocketListener() {
    if (wsCleanup) {
      wsCleanup()
      wsCleanup = null
    }
  }

  // ============ 数据加载 ============

  // 同一时刻只允许一次全量拉取：motion_changed / speakers_updated 会被
  // App.vue 的全局监听与本 store 的 '*' 监听同时收到，不去重会翻倍打请求。
  let fullStateInFlight = null

  async function loadFullState() {
    if (fullStateInFlight) return fullStateInFlight
    fullStateInFlight = (async () => {
      try {
        const [agendaRes, motionRes, delRes] = await Promise.all([
          api.get('/api/staff/agenda'),
          api.get('/api/staff/motions'),
          api.get('/api/staff/delegations'),
        ])
        agendaItems.value = agendaRes.data
        currentAgenda.value = agendaRes.data.find(a => a.is_active) || null

        const active = motionRes.data.find(m => m.status === 'active')
        if (active) {
          activeMotion.value = active
          // 不从 motion 配置重置计时器 — 从服务端恢复
          await loadTimerState()
          await loadSpeakers()
        } else {
          activeMotion.value = null
          currentSpeaker.value = null
          // 没有活跃动议时显示主发言名单（未启用该功能时这里会置空）
          await loadMainSpeakers()
        }
        delegations.value = delRes.data
      } catch (e) {} 
    })()
    try {
      await fullStateInFlight
    } finally {
      fullStateInFlight = null
    }
  }

  async function loadSpeakers() {
    if (!activeMotion.value) return
    try {
      const { data } = await api.get(`/api/staff/motions/${activeMotion.value.id}/speakers`)
      speakersList.value = data
      currentSpeaker.value = data.find(s => s.has_spoken === 0) || null
    } catch (e) {}
  }

  /** 加载主发言名单；接口 403 表示本会场未启用该功能 */
  async function loadMainSpeakers() {
    try {
      const { data } = await api.get('/api/staff/main-speakers')
      mainSpeakersEnabled.value = true
      speakersList.value = data
      currentSpeaker.value = null
      await loadMainUnitDuration()
    } catch (e) {
      mainSpeakersEnabled.value = false
      speakersList.value = []
      currentSpeaker.value = null
    }
  }

  async function loadMainUnitDuration() {
    try {
      const { data } = await api.get('/api/staff/main-speakers/unit-duration')
      mainUnitDuration.value = data.unit_duration || 60
      // 待机状态下表盘要反映设定时长，否则停在残留的 00:00
      if (isMainSpeakerMode.value && !timerRunning.value && !currentSpeaker.value) {
        unitRemaining.value = mainUnitDuration.value
        elapsedSeconds.value = 0
      }
    } catch (e) {}
  }

  /** 调整主发言名单的单位时长（秒）；未在计时时同步表盘 */
  async function setMainUnitDuration(seconds) {
    const value = Math.max(5, Math.min(3600, Math.round(Number(seconds) || 60)))
    mainUnitDuration.value = value
    try {
      await api.put('/api/staff/main-speakers/unit-duration', { unit_duration: value })
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '设置时长失败')
      return
    }
    if (isMainSpeakerMode.value && !timerRunning.value) {
      unitRemaining.value = value
      elapsedSeconds.value = 0
    }
  }

  /** 按当前模式重新拉取名单位：主发言名单 / 动议发言名单 */
  async function refreshSpeakers() {
    if (isMainSpeakerMode.value) await loadMainSpeakers()
    else await loadSpeakers()
  }

  async function loadDelegates() {
    if (!allDelegates.value.length) {
      try {
        const { data } = await api.get('/api/staff/delegates')
        allDelegates.value = data
      } catch (e) {}
    }
  }

  // ============ 动议操作 ============

  async function createMotion(motionData) {
    try {
      await api.post('/api/staff/motions', motionData)
      ElMessage.success('动议创建成功')
      await loadFullState()
      return true
    } catch (e) {
      ElMessage.error('创建失败')
      return false
    }
  }

  async function endMotion() {
    if (!activeMotion.value) return
    try {
      await api.put(`/api/staff/motions/${activeMotion.value.id}/status?status=ended`)
      ElMessage.success('动议已结束')
      stopAllTicks()
      activeMotion.value = null
      currentSpeaker.value = null
      unitRemaining.value = 0
      totalRemaining.value = 0
      elapsedSeconds.value = 0
      timerRunning.value = false
      // 动议结束后自动从（动议的）发言名单切换为主发言名单
      await loadMainSpeakers()
      return true
    } catch (e) {
      ElMessage.error('操作失败')
      return false
    }
  }

  // ============ 发言操作 ============

  async function selectSpeaker(speaker) {
    // 主发言名单：没有动议上下文，计时纯本地，也不写服务端。
    // 切人时把单位计时刷满一个完整时长。
    if (isMainSpeakerMode.value) {
      stopAllTicks()
      currentSpeaker.value = speaker
      speechContent.value = ''
      unitRemaining.value = mainUnitDuration.value
      elapsedSeconds.value = 0
      totalRemaining.value = 0
      return
    }

    if (currentSpeaker.value && speechContent.value) {
      await saveSpeechContent()
    }
    currentSpeaker.value = speaker
    speechContent.value = speaker.content || ''

    // 切到新发言者时刷新单位计时：
    // 否则上一位的剩余时间（甚至已归零的 00:00）会被带到下一位，
    // 表现为「换了人但单位计时器没重置」。
    if (activeMotion.value?.unit_duration) {
      unitRemaining.value = activeMotion.value.unit_duration
      elapsedSeconds.value = 0
      await pushTimerState()
    }
    try {
      const { data } = await api.get(`/api/staff/motions/${activeMotion.value.id}/speakers/${speaker.id}`)
      speechContent.value = data.content || ''
    } catch (e) {}
    try {
      await api.put(`/api/staff/motions/${activeMotion.value.id}/speakers/${speaker.id}/start`)
    } catch (e) {}
  }

  async function saveSpeechContent() {
    if (!currentSpeaker.value || !activeMotion.value) return
    try {
      await api.put(`/api/staff/motions/${activeMotion.value.id}/speakers/${currentSpeaker.value.id}/content`, {
        content: speechContent.value
      })
    } catch (e) {}
  }

  async function endSpeaker() {
    stopAllTicks()
    // 主发言名单：本地结束即可，没有动议发言记录要落库
    if (isMainSpeakerMode.value) {
      currentSpeaker.value = null
      speechContent.value = ''
      unitRemaining.value = mainUnitDuration.value
      elapsedSeconds.value = 0
      return
    }
    if (currentSpeaker.value) {
      try {
        await api.put(`/api/staff/motions/${activeMotion.value.id}/speakers/${currentSpeaker.value.id}/end?duration=${elapsedSeconds.value}`)
        elapsedSeconds.value = 0
        currentSpeaker.value = null
        // 重置单位计时，并同步到服务端（否则其它端与刷新后仍是旧的 00:00）
        if (activeMotion.value?.unit_duration) {
          unitRemaining.value = activeMotion.value.unit_duration
        }
        await pushTimerState()
        await loadSpeakers()
      } catch (e) {
        ElMessage.error('操作失败')
      }
    }
  }

  async function addSpeaker(delegationId, delegateId) {
    const mainMode = isMainSpeakerMode.value
    if (!mainMode && !activeMotion.value) return
    const url = mainMode
      ? '/api/staff/main-speakers'
      : `/api/staff/motions/${activeMotion.value.id}/speakers`
    try {
      await api.post(url, { delegation_id: delegationId, delegate_id: delegateId })
      await refreshSpeakers()
      return true
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '添加失败')
      return false
    }
  }

  async function removeSpeaker(speakerId) {
    const mainMode = isMainSpeakerMode.value
    if (!mainMode && !activeMotion.value) return
    const url = mainMode
      ? `/api/staff/main-speakers/${speakerId}`
      : `/api/staff/motions/${activeMotion.value.id}/speakers/${speakerId}`
    try {
      await api.delete(url)
      await refreshSpeakers()
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }

  /** 拖拽排序：按当前模式提交到对应接口 */
  async function reorderSpeakers() {
    const ids = speakersList.value.map(s => s.id)
    const mainMode = isMainSpeakerMode.value
    if (!ids.length || (!mainMode && !activeMotion.value)) return
    const url = mainMode
      ? '/api/staff/main-speakers/reorder'
      : `/api/staff/motions/${activeMotion.value.id}/speakers/reorder`
    try {
      await api.put(url, { speaker_ids: ids })
    } catch (e) {}
  }

  // ============ 议程操作 ============

  async function activateAgenda(itemId) {
    try {
      await api.put(`/api/staff/agenda/${itemId}/activate`)
      await loadFullState()
      return true
    } catch (e) {
      ElMessage.error('操作失败')
      return false
    }
  }

  // ============ WebSocket 同步 ============

  function applyMeetingUpdate(data) {
    switch (data.type) {
      case 'timer_sync':
        if (data.motion_id === activeMotion.value?.id) {
          applyTimerSync(data.timer)
        }
        break
      case 'motion_changed':
        loadFullState()
        break
      case 'speaker_changed':
        currentSpeaker.value = data.speaker || null
        break
      case 'speakers_updated':
        loadSpeakers()
        break
      case 'main_speakers_updated':
        if (isMainSpeakerMode.value) loadMainSpeakers()
        break
      case 'agenda_changed':
        currentAgenda.value = data.agenda || null
        break
    }
  }

  // ============ 清理 ============

  function cleanup() {
    stopAllTicks()
    unregisterWebSocketListener()
  }

  return {
    currentAgenda, agendaItems,
    activeMotion, speakersList, currentSpeaker,
    timerRunning, unitRemaining, totalRemaining, elapsedSeconds,
    isControlling,
    speechContent, delegations, allDelegates,
    hasActiveMeeting, isSpeaking, formattedUnitTime, formattedTotalTime,
    loadFullState, loadSpeakers, loadDelegates,
    loadTimerState,
    startLocalTick, stopLocalTick, pushTimerState,
    createMotion, endMotion,
    selectSpeaker, saveSpeechContent, endSpeaker,
    addSpeaker, removeSpeaker, reorderSpeakers,
    mainSpeakersEnabled, isMainSpeakerMode, loadMainSpeakers, refreshSpeakers,
    mainUnitDuration, loadMainUnitDuration, setMainUnitDuration,
    activateAgenda,
    registerWebSocketListener, unregisterWebSocketListener,
    applyMeetingUpdate,
    cleanup
  }
})
