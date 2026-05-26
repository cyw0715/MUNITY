<template>
  <div class="meeting-page">
    <!-- 当前议程 -->
    <el-card style="margin-bottom: 16px">
      <template #header>
        <div class="card-header">
          <span>当前议程</span>
          <el-button size="small" @click="showAgendaDialog">选择议程</el-button>
        </div>
      </template>
      <div v-if="currentAgenda">
        <el-tag type="success">当前</el-tag>
        <span style="margin-left: 8px; font-size: 16px; font-weight: bold">{{ currentAgenda.title }}</span>
      </div>
      <div v-else style="color: #999">暂无激活的议程，请点击"选择议程"按钮选择</div>
    </el-card>

    <!-- 动议管理 -->
    <el-card style="margin-bottom: 16px">
      <template #header>
        <div class="card-header">
          <span>动议管理</span>
          <el-button type="primary" size="small" @click="showMotionDialog">新建动议</el-button>
        </div>
      </template>

      <div v-if="activeMotion" class="active-motion">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="类型">
            <el-tag>{{ motionTypeLabels[activeMotion.type] }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="主题">{{ activeMotion.topic || '无' }}</el-descriptions-item>
          <el-descriptions-item label="提出者">
            {{ activeMotion.proposer_delegation_name || '未知' }}{{ activeMotion.proposer_delegate_name ? ' - ' + activeMotion.proposer_delegate_name : '' }}
          </el-descriptions-item>
          <el-descriptions-item label="单位时长" v-if="activeMotion.unit_duration">
            {{ activeMotion.unit_duration }}秒
          </el-descriptions-item>
          <el-descriptions-item label="总时长" v-if="activeMotion.total_duration">
            {{ activeMotion.total_duration }}秒
          </el-descriptions-item>
        </el-descriptions>
        <div style="margin-top: 12px">
          <el-button type="danger" size="small" @click="endMotion">结束</el-button>
        </div>
      </div>
      <el-empty v-else description="暂无进行中的动议" />
    </el-card>

    <!-- 发言计时器 + 发言名单 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>发言计时器</span>
          </template>
          <div v-if="currentSpeaker" class="timer-section">
            <!-- 总时长（小字，放在国家名上方） -->
            <div class="total-timer">
              <span class="total-time">{{ formatTime(totalRemaining) }}</span>
            </div>
            <div class="current-speaker">
              <span class="speaker-name">{{ currentSpeaker.delegation_name }}{{ currentSpeaker.delegate_name ? ' - ' + currentSpeaker.delegate_name : '' }}</span>
            </div>
            <!-- 单位时长倒计时（大字） -->
            <div class="timer-display">
              <span class="time" :class="{ 'time-warning': unitRemaining <= 10 && unitRemaining > 0 }">{{ formatTime(unitRemaining) }}</span>
            </div>
            <div class="timer-controls">
              <el-button v-if="!timerRunning" type="success" @click="startTimer">开始</el-button>
              <el-button v-else type="warning" @click="pauseTimer">暂停</el-button>
              <el-button type="danger" @click="endSpeaker">结束发言</el-button>
            </div>
            <!-- 发言内容记录 -->
            <div class="speech-content">
              <el-input
                v-model="speechContent"
                type="textarea"
                :rows="4"
                placeholder="记录发言内容..."
                @change="saveSpeechContent"
              />
              <el-button size="small" type="primary" @click="saveSpeechContent" style="margin-top: 8px">
                保存内容
              </el-button>
            </div>
          </div>
          <div v-else class="no-speaker-timer">
            <div v-if="activeMotion && activeMotion.total_duration" class="total-duration-display">
              <div class="timer-label">剩余总时长</div>
              <div class="timer-value">{{ formatTime(totalRemaining) }}</div>
            </div>
            <el-empty v-else description="请选择发言者" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>发言名单</span>
              <el-button v-if="activeMotion" type="primary" size="small" @click="showAddSpeakerDialog">添加发言者</el-button>
            </div>
          </template>
          <div v-if="speakersList.length">
            <div v-for="(speaker, index) in speakersList" :key="speaker.id" class="speaker-item"
              :class="{ active: index === 0 && !speaker.has_spoken, spoken: speaker.has_spoken }"
              @click="selectSpeaker(speaker)">
              <span class="order">{{ index + 1 }}</span>
              <span class="name">{{ speaker.delegation_name }}{{ speaker.delegate_name ? ' - ' + speaker.delegate_name : '' }}</span>
              <span v-if="speaker.has_spoken" class="status">
                <el-tag size="small" type="info">已发言 {{ speaker.duration }}秒</el-tag>
              </span>
              <span v-else-if="index === 0" class="status">
                <el-tag size="small" type="success">当前</el-tag>
              </span>
              <el-button size="small" type="danger" text @click.stop="removeSpeaker(speaker.id)">移除</el-button>
            </div>
          </div>
          <el-empty v-else description="发言名单为空" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 新建动议对话框 -->
    <el-dialog v-model="motionDialogVisible" title="新建动议" width="500px">
      <el-form :model="motionForm">
        <el-form-item label="动议类型">
          <el-select v-model="motionForm.type" style="width: 100%">
            <el-option label="有主持核心磋商" value="moderated_caucus" />
            <el-option label="自由辩论" value="unmoderated_caucus" />
            <el-option label="自由磋商" value="free_caucus" />
            <el-option label="轮席发言" value="speakers_list" />
          </el-select>
        </el-form-item>
        <el-form-item label="主题">
          <el-input v-model="motionForm.topic" />
        </el-form-item>
        <el-form-item label="提出动议">
          <div style="width: 100%">
            <el-select v-model="motionProposerDelegation" placeholder="选择代表团" clearable style="width: 100%; margin-bottom: 8px" @change="onMotionProposerDelegationChange">
              <el-option v-for="d in delegations" :key="d.id" :label="d.name" :value="d.id" />
            </el-select>
            <el-select v-model="motionProposerDelegate" placeholder="选择代表" clearable style="width: 100%" :disabled="!motionProposerDelegation">
              <el-option v-for="m in filteredMotionProposers" :key="m.id" :label="m.username + (m.is_leader ? ' (阁首)' : '')" :value="m.id" />
            </el-select>
          </div>
        </el-form-item>
        <el-form-item label="单位时长（秒）" v-if="motionForm.type === 'moderated_caucus'">
          <el-input-number v-model="motionForm.unit_duration" :min="10" :step="10" />
        </el-form-item>
        <el-form-item label="总时长（秒）">
          <el-input-number v-model="motionForm.total_duration" :min="30" :step="30" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="motionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createMotion">创建</el-button>
      </template>
    </el-dialog>

    <!-- 添加发言者对话框 -->
    <el-dialog v-model="addSpeakerDialogVisible" title="添加发言者" width="400px">
      <el-form>
        <el-form-item label="代表团">
          <el-select v-model="selectedDelegationId" placeholder="选择代表团" style="width: 100%" @change="onDelegationChange">
            <el-option v-for="d in delegations" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="代表" v-if="selectedDelegationId">
          <el-select v-model="selectedDelegateId" placeholder="选择代表" style="width: 100%">
            <el-option v-for="m in filteredDelegates" :key="m.id" :label="m.username + (m.is_leader ? ' (阁首)' : '')" :value="m.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addSpeakerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addSpeaker">添加</el-button>
      </template>
    </el-dialog>

    <!-- 议程选择对话框 -->
    <el-dialog v-model="agendaDialogVisible" title="选择议程" width="600px">
      <div class="agenda-list">
        <div v-for="item in agendaItems" :key="item.id" 
          class="agenda-item" 
          :class="{ active: item.is_active, selected: selectedAgendaId === item.id }"
          :style="{ paddingLeft: (item.level - 1) * 24 + 'px' }"
          @click="selectedAgendaId = item.id">
          <el-tag size="small" :type="getLevelType(item.level)">L{{ item.level }}</el-tag>
          <span class="agenda-title">{{ item.title }}</span>
          <el-tag v-if="item.is_active" size="small" type="success" style="margin-left: auto">当前</el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="agendaDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!selectedAgendaId" @click="activateSelectedAgenda">激活选中议程</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api'

const currentAgenda = ref(null)
const agendaItems = ref([])
const agendaDialogVisible = ref(false)
const selectedAgendaId = ref(null)
const activeMotion = ref(null)
const speakersList = ref([])
const currentSpeaker = ref(null)
const delegations = ref([])
const speechContent = ref('')

const motionDialogVisible = ref(false)
const addSpeakerDialogVisible = ref(false)
const selectedDelegationId = ref(null)
const selectedDelegateId = ref(null)
const allDelegates = ref([])

// 筛选当前代表团的代表
const filteredDelegates = computed(() => {
  if (!selectedDelegationId.value) return []
  return allDelegates.value.filter(d => d.delegation_id === selectedDelegationId.value)
})

function onDelegationChange() {
  selectedDelegateId.value = null
}

const motionForm = ref({
  type: 'moderated_caucus',
  topic: '',
  unit_duration: 60,
  total_duration: 300
})

const motionProposerDelegation = ref(null)
const motionProposerDelegate = ref(null)

// 筛选提出动议的代表
const filteredMotionProposers = computed(() => {
  if (!motionProposerDelegation.value) return []
  return allDelegates.value.filter(d => d.delegation_id === motionProposerDelegation.value)
})

function onMotionProposerDelegationChange() {
  motionProposerDelegate.value = null
}

const motionTypeLabels = {
  moderated_caucus: '有主持核心磋商',
  unmoderated_caucus: '自由辩论',
  free_caucus: '自由磋商',
  speakers_list: '轮席发言'
}

// 计时器相关
const unitRemaining = ref(0)  // 单位时长剩余
const totalRemaining = ref(0)  // 总时长剩余
const timerRunning = ref(false)
let timerInterval = null
const elapsedSeconds = ref(0)  // 已用时间（用于记录发言时长）

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
  timerInterval = setInterval(() => {
    elapsedSeconds.value++
    // 总时长倒计时
    if (totalRemaining.value > 0) {
      totalRemaining.value--
    }
    // 单位时长倒计时
    if (unitRemaining.value > 0) {
      unitRemaining.value--
      if (unitRemaining.value === 0) {
        pauseTimer()
        ElMessage.warning('单位发言时间到！')
      }
    }
    // 总时长耗尽
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

async function selectSpeaker(speaker) {
  // 先保存当前发言者的内容
  if (currentSpeaker.value && speechContent.value) {
    await saveSpeechContent()
  }
  // 切换到新发言者
  currentSpeaker.value = speaker
  speechContent.value = speaker.content || ''
  // 加载发言者详情
  try {
    const { data } = await api.get(`/api/staff/motions/${activeMotion.value.id}/speakers/${speaker.id}`)
    speechContent.value = data.content || ''
  } catch (e) {}
  // 通知后端开始发言
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
      ElMessage.success('发言结束')
      elapsedSeconds.value = 0
      currentSpeaker.value = null
      resetUnitTimer()
      loadSpeakers()
    } catch (e) {
      ElMessage.error('操作失败')
    }
  }
}

async function loadAgenda() {
  try {
    const { data } = await api.get('/api/staff/agenda')
    agendaItems.value = data
    currentAgenda.value = data.find(a => a.is_active) || null
  } catch (e) {}
}

function getLevelType(level) {
  const types = ['', 'success', 'warning', 'danger', 'info']
  return types[(level - 1) % types.length] || ''
}

function showAgendaDialog() {
  selectedAgendaId.value = currentAgenda.value?.id || null
  agendaDialogVisible.value = true
}

async function activateSelectedAgenda() {
  if (!selectedAgendaId.value) return
  try {
    await api.put(`/api/staff/agenda/${selectedAgendaId.value}/activate`)
    ElMessage.success('议程已激活')
    agendaDialogVisible.value = false
    loadAgenda()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function loadMotions() {
  try {
    const { data } = await api.get('/api/staff/motions')
    activeMotion.value = data.find(m => m.status === 'active') || null
    if (activeMotion.value) {
      initTimer()
      loadSpeakers()
    }
  } catch (e) {}
}

async function loadSpeakers() {
  if (!activeMotion.value) return
  try {
    const { data } = await api.get(`/api/staff/motions/${activeMotion.value.id}/speakers`)
    speakersList.value = data
    // 设置当前发言者（第一个未发言的）
    currentSpeaker.value = data.find(s => !s.has_spoken) || null
  } catch (e) {}
}

async function loadDelegations() {
  try {
    const { data } = await api.get('/api/staff/delegations')
    delegations.value = data
  } catch (e) {}
}

async function showMotionDialog() {
  motionForm.value = { type: 'moderated_caucus', topic: '', unit_duration: 60, total_duration: 300 }
  motionProposerDelegation.value = null
  motionProposerDelegate.value = null
  // 加载所有代表（如果尚未加载）
  if (!allDelegates.value.length) {
    try {
      const { data } = await api.get('/api/staff/delegates')
      allDelegates.value = data
    } catch (e) {}
  }
  motionDialogVisible.value = true
}

async function createMotion() {
  try {
    const payload = {
      ...motionForm.value,
      proposer_delegation_id: motionProposerDelegation.value,
      proposer_delegate_id: motionProposerDelegate.value
    }
    await api.post('/api/staff/motions', payload)
    ElMessage.success('动议创建成功')
    motionDialogVisible.value = false
    loadMotions()
  } catch (e) {
    ElMessage.error('创建失败')
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
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function showAddSpeakerDialog() {
  selectedDelegationId.value = null
  selectedDelegateId.value = null
  // 加载所有代表
  try {
    const { data } = await api.get('/api/staff/delegates')
    allDelegates.value = data
  } catch (e) {}
  addSpeakerDialogVisible.value = true
}

async function addSpeaker() {
  if (!selectedDelegateId.value) {
    ElMessage.warning('请选择代表')
    return
  }
  try {
    await api.post(`/api/staff/motions/${activeMotion.value.id}/speakers`, {
      delegation_id: selectedDelegationId.value,
      delegate_id: selectedDelegateId.value
    })
    ElMessage.success('添加成功')
    addSpeakerDialogVisible.value = false
    loadSpeakers()
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function removeSpeaker(speakerId) {
  try {
    await api.delete(`/api/staff/motions/${activeMotion.value.id}/speakers/${speakerId}`)
    ElMessage.success('移除成功')
    loadSpeakers()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  loadAgenda()
  loadMotions()
  loadDelegations()
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.active-motion { padding: 8px 0; }
.timer-section { text-align: center; padding: 20px 0; }
.current-speaker { margin-bottom: 16px; }
.speaker-name { font-size: 24px; font-weight: bold; color: #303133; }
.total-timer { margin-bottom: 4px; }
.total-time { font-size: 14px; color: #909399; font-family: monospace; }
.timer-display { margin-bottom: 20px; }
.time { font-size: 48px; font-weight: bold; color: #409eff; font-family: monospace; }
.time-warning { color: #e6a23c !important; }
.timer-controls { display: flex; justify-content: center; gap: 12px; margin-bottom: 20px; }
.no-speaker-timer { text-align: center; padding: 40px 0; }
.total-duration-display { margin-bottom: 16px; }
.timer-label { font-size: 14px; color: #909399; margin-bottom: 8px; }
.timer-value { font-size: 48px; font-weight: bold; color: #409eff; font-family: monospace; }
.speech-content { text-align: left; margin-top: 16px; padding-top: 16px; border-top: 1px solid #eee; }
.speech-content .el-textarea { margin-bottom: 8px; }
.speaker-item { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #eee; cursor: pointer; }
.speaker-item:last-child { border-bottom: none; }
.speaker-item:hover { background: #f5f7fa; }
.speaker-item.active { background: #f0f9eb; border-radius: 4px; padding: 10px; }
.speaker-item.spoken { opacity: 0.6; }
.order { width: 30px; font-weight: bold; color: #909399; }
.agenda-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
.agenda-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
}
.agenda-item:last-child {
  border-bottom: none;
}
.agenda-item:hover {
  background: #f5f7fa;
}
.agenda-item.active {
  background: #f0f9eb;
}
.agenda-item.selected {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
}
.agenda-title {
  flex: 1;
}
.name { flex: 1; font-size: 14px; }
.status { margin-right: 8px; }
</style>
