import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

/**
 * 全局会议状态 Store
 * 生命周期 = SPA 生命周期，不受路由切换影响
 * 通过 WebSocket 实时同步多终端
 */
export const useMeetingStore = defineStore('meeting', () => {
  // ============ 状态 ============

  // 当前议程
  const currentAgenda = ref(null)
  const agendaItems = ref([])

  // 当前动议
  const activeMotion = ref(null)

  // 发言名单
  const speakersList = ref([])
  const currentSpeaker = ref(null)

  // 计时器
  const timerRunning = ref(false)
  const unitRemaining = ref(0)
  const totalRemaining = ref(0)
  const elapsedSeconds = ref(0)
  let timerInterval = null

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

  let lastSyncTime = Date.now()

  function formatTime(seconds) {
    if (seconds < 0) seconds = 0
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }

  function initTimer() {
    if (activeMotion.value) {
      unitRemaining.value = activeMotion.value.unit_duration || 0
      totalRemaining.value = activeMotion.value.total_duration || 0
    }
    elapsedSeconds.value = 0
  }

  function startTimer() {
    if (timerRunning.value) return
    timerRunning.value = true
    lastSyncTime = Date.now()
    timerInterval = setInterval(() => {
      elapsedSeconds.value++

      if (totalRemaining.value > 0) {
        totalRemaining.value--
      }
      if (unitRemaining.value > 0) {
        unitRemaining.value--
        if (unitRemaining.value === 0) {
          // 有发言者时暂停（单位时间到），无发言者时继续倒计时总时长
          if (currentSpeaker.value) {
            pauseTimer()
            ElMessage.warning('单位发言时间到！')
          }
        }
      }
      if (totalRemaining.value === 0 && activeMotion.value?.total_duration) {
        pauseTimer()
        ElMessage.warning('总时长已耗尽！')
      }
    }, 1000)
  }

  function pauseTimer() {
    timerRunning.value = false
    if (timerInterval) {
      clearInterval(timerInterval)
      timerInterval = null
    }
  }

  function resetUnitTimer() {
    if (activeMotion.value?.unit_duration) {
      unitRemaining.value = activeMotion.value.unit_duration
    }
  }

  function setTimerState(state) {
    /** 从 WebSocket 同步远程计时器状态 */
    unitRemaining.value = state.unit_remaining
    totalRemaining.value = state.total_remaining
    elapsedSeconds.value = state.elapsed || 0
    if (state.running && !timerRunning.value) {
      startTimer()
    } else if (!state.running && timerRunning.value) {
      pauseTimer()
    }
  }

  // ============ 数据加载 ============

  async function loadFullState() {
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
        initTimer()
        await loadSpeakers()
      } else {
        activeMotion.value = null
        speakersList.value = []
        currentSpeaker.value = null
      }
      delegations.value = delRes.data
    } catch (e) {}
  }

  async function loadSpeakers() {
    if (!activeMotion.value) return
    try {
      const { data } = await api.get(`/api/staff/motions/${activeMotion.value.id}/speakers`)
      speakersList.value = data
      currentSpeaker.value = data.find(s => !s.has_spoken) || data.find(s => !s.has_spoken) || null
    } catch (e) {}
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
      pauseTimer()
      activeMotion.value = null
      currentSpeaker.value = null
      speakersList.value = []
      unitRemaining.value = 0
      totalRemaining.value = 0
      elapsedSeconds.value = 0
      timerRunning.value = false
      return true
    } catch (e) {
      ElMessage.error('操作失败')
      return false
    }
  }

  // ============ 发言操作 ============

  async function selectSpeaker(speaker) {
    if (currentSpeaker.value && speechContent.value) {
      await saveSpeechContent()
    }
    currentSpeaker.value = speaker
    speechContent.value = speaker.content || ''
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
    pauseTimer()
    if (currentSpeaker.value) {
      try {
        await api.put(`/api/staff/motions/${activeMotion.value.id}/speakers/${currentSpeaker.value.id}/end?duration=${elapsedSeconds.value}`)
        elapsedSeconds.value = 0
        currentSpeaker.value = null
        resetUnitTimer()
        await loadSpeakers()
      } catch (e) {
        ElMessage.error('操作失败')
      }
    }
  }

  async function addSpeaker(delegationId, delegateId) {
    if (!activeMotion.value) return
    try {
      await api.post(`/api/staff/motions/${activeMotion.value.id}/speakers`, {
        delegation_id: delegationId,
        delegate_id: delegateId
      })
      await loadSpeakers()
      return true
    } catch (e) {
      ElMessage.error('添加失败')
      return false
    }
  }

  async function removeSpeaker(speakerId) {
    if (!activeMotion.value) return
    try {
      await api.delete(`/api/staff/motions/${activeMotion.value.id}/speakers/${speakerId}`)
      await loadSpeakers()
    } catch (e) {
      ElMessage.error('操作失败')
    }
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
      case 'speaker_changed':
        currentSpeaker.value = data.speaker || null
        break
      case 'speakers_updated':
        speakersList.value = data.speakers || []
        break
      case 'timer_sync':
        setTimerState(data.timer)
        break
      case 'motion_changed':
        loadFullState()
        break
      case 'agenda_changed':
        currentAgenda.value = data.agenda || null
        break
    }
  }

  // ============ 清理 ============

  function cleanup() {
    pauseTimer()
  }

  return {
    // 状态
    currentAgenda, agendaItems,
    activeMotion, speakersList, currentSpeaker,
    timerRunning, unitRemaining, totalRemaining, elapsedSeconds,
    speechContent, delegations, allDelegates,
    // 计算属性
    hasActiveMeeting, isSpeaking, formattedUnitTime, formattedTotalTime,
    // 动作
    loadFullState, loadSpeakers, loadDelegates,
    initTimer, startTimer, pauseTimer, resetUnitTimer, setTimerState,
    createMotion, endMotion,
    selectSpeaker, saveSpeechContent, endSpeaker,
    addSpeaker, removeSpeaker,
    activateAgenda,
    applyMeetingUpdate,
    cleanup
  }
})
