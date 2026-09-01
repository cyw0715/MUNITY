<template>
  <div class="meeting-page animate-fade-in">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2>会议进行</h2>
        <p>动议管理 · 发言计时 · 议程控制</p>
      </div>
      <div class="header-actions">
        <el-button size="small" @click="showAgendaDialog">选择议程</el-button>
        <el-button type="primary" size="default" @click="showMotionDialog">新建动议</el-button>
      </div>
    </div>

    <!-- 顶部：当前议程 + 动议信息 -->
    <div class="status-bar">
      <div class="status-item agenda-status">
        <span class="status-label">当前议程</span>
        <span v-if="store.currentAgenda" class="status-value">{{ store.currentAgenda.title }}</span>
        <span v-else class="status-value placeholder">未设置</span>
        <el-button v-if="store.currentAgenda" text type="primary" size="small" @click="showAgendaDialog">切换</el-button>
      </div>
      <div v-if="store.activeMotion" class="status-item motion-status">
        <span class="status-label">当前动议</span>
        <span class="status-value">{{ getMotionTypeLabel(store.activeMotion.type) }}</span>
        <span v-if="store.activeMotion.topic" class="status-topic">{{ store.activeMotion.topic }}</span>
        <el-button type="danger" size="small" plain @click="handleEndMotion">结束动议</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 左列：计时器 -->
      <el-col :span="14">
        <div class="timer-card">
          <div class="timer-header">
            <h3>发言计时器</h3>
            <span v-if="store.isSpeaking" class="live-badge">● LIVE</span>
          </div>

          <div class="timer-content">
            <!-- 当前发言者 -->
            <div v-if="store.currentSpeaker" class="speaker-display animate-slide-up">
              <div class="total-slot">
                <span class="total-label">总剩余</span>
                <span class="total-time">{{ store.formattedTotalTime }}</span>
              </div>
              <div class="speaker-name">
                <span class="flag-dot" :style="{ background: getSpeakerColor(store.currentSpeaker.delegation_name) }"></span>
                {{ store.currentSpeaker.delegation_name }}
                <span v-if="store.currentSpeaker.delegate_name" class="delegate-sub">— {{ store.currentSpeaker.delegate_name }}</span>
              </div>
              <div class="countdown" :class="{ warning: store.unitRemaining <= 10 && store.unitRemaining > 0, critical: store.unitRemaining <= 5 && store.unitRemaining > 0 }">
                {{ store.formattedUnitTime }}
              </div>
              <div class="timer-controls">
                <button v-if="!store.timerRunning" class="ctrl-btn btn-start" @click="store.startLocalTick()">
                  <el-icon><VideoPlay /></el-icon> 开始
                </button>
                <button v-else class="ctrl-btn btn-pause" @click="store.stopLocalTick()">
                  <el-icon><VideoPause /></el-icon> 暂停
                </button>
                <button class="ctrl-btn btn-end" @click="handleEndSpeaker">
                  <el-icon><CircleClose /></el-icon> 结束发言
                </button>
              </div>

              <!-- 发言内容记录 -->
              <div class="speech-area">
                <el-input
                  v-model="store.speechContent"
                  type="textarea"
                  :rows="3"
                  placeholder="记录发言内容..."
                  @blur="store.saveSpeechContent()"
                />
                <div class="speech-actions">
                  <span class="speech-hint">Ctrl+Enter 保存</span>
                  <el-button size="small" type="primary" @click="store.saveSpeechContent()">
                    <el-icon><Edit /></el-icon> 保存
                  </el-button>
                </div>
              </div>
            </div>

            <!-- 无发言者 — 显示总时长 -->
            <div v-else-if="store.activeMotion" class="no-speaker">
              <div class="total-only">
                <span class="total-label">剩余总时长</span>
                <div class="big-timer">{{ store.formattedTotalTime }}</div>
              </div>
              <div class="timer-controls" style="margin-top: 16px;">
                <button v-if="!store.timerRunning" class="ctrl-btn btn-start" @click="store.startLocalTick()">
                  <el-icon><VideoPlay /></el-icon> 开始计时
                </button>
                <button v-else class="ctrl-btn btn-pause" @click="store.stopLocalTick()">
                  <el-icon><VideoPause /></el-icon> 暂停
                </button>
              </div>
              <p class="no-speaker-hint">发言名单为空，计时器将在无发言者状态下倒数总时长</p>
            </div>

            <!-- 无动议 -->
            <div v-else class="no-motion">
              <div class="no-motion-icon">
                <el-icon :size="48"><Microphone /></el-icon>
              </div>
              <h3>暂无会议进行</h3>
              <p>创建一个新动议开始会议</p>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右列：发言名单 -->
      <el-col :span="10">
        <div class="speakers-card">
          <div class="speakers-header">
            <h3>发言名单</h3>
            <el-button v-if="store.activeMotion" type="primary" size="small" @click="showAddSpeakerDialog">
              <el-icon><Plus /></el-icon> 添加
            </el-button>
          </div>

          <div v-if="store.speakersList.length" class="speakers-list">
            <div
              v-for="(speaker, index) in store.speakersList"
              :key="speaker.id"
              class="speaker-row"
              :class="{
                active: index === 0 && !speaker.has_spoken,
                spoken: speaker.has_spoken,
                current: store.currentSpeaker?.id === speaker.id && store.timerRunning
              }"
              @click="handleSelectSpeaker(speaker)"
            >
              <span class="spk-order">{{ index + 1 }}</span>
              <span class="spk-flag" :style="{ background: getSpeakerColor(speaker.delegation_name) }"></span>
              <span class="spk-name">{{ speaker.delegation_name }}</span>
              <span v-if="speaker.delegate_name" class="spk-delegate">{{ speaker.delegate_name }}</span>
              <span v-if="speaker.has_spoken" class="spk-status">
                <el-tag size="small" type="info" round>{{ speaker.duration }}s</el-tag>
              </span>
              <span v-else-if="index === 0" class="spk-status">
                <span class="active-badge">当前</span>
              </span>
              <button class="spk-remove" @click.stop="store.removeSpeaker(speaker.id)" title="移除">
                <el-icon><Close /></el-icon>
              </button>
            </div>
          </div>
          <div v-else class="speakers-empty">
            <el-empty description="发言名单为空" :image-size="80" />
          </div>
        </div>

        <!-- 动议详情 -->
        <div v-if="store.activeMotion" class="motion-detail-card animate-slide-up">
          <div class="motion-detail-header">
            <h4>动议详情</h4>
          </div>
          <div class="motion-detail-body">
            <div class="detail-row">
              <span class="detail-key">类型</span>
              <el-tag size="small" effect="plain">{{ getMotionTypeLabel(store.activeMotion.type) }}</el-tag>
            </div>
            <div v-if="store.activeMotion.topic" class="detail-row">
              <span class="detail-key">主题</span>
              <span class="detail-val">{{ store.activeMotion.topic }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-key">提出者</span>
              <span class="detail-val">{{ store.activeMotion.proposer_delegation_name || '未知' }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ===== 新建动议对话框 ===== -->
    <el-dialog v-model="motionDialogVisible" title="新建动议" width="520px" class="motion-dialog">
      <el-form :model="motionForm" label-position="top">
        <el-form-item label="动议类型">
          <el-select v-model="motionForm.type" style="width: 100%" @change="onMotionTypeChange">
            <el-option-group label="内置类型">
              <el-option label="有主持核心磋商" value="moderated_caucus" />
              <el-option label="自由辩论" value="unmoderated_caucus" />
              <el-option label="自由磋商" value="free_caucus" />
              <el-option label="轮席发言" value="speakers_list" />
            </el-option-group>
            <el-option-group label="自定义类型">
              <el-option v-for="mt in motionTypesConfig.filter(m => !m.is_builtin)" :key="mt.name" :label="mt.name" :value="mt.name" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="主题">
          <el-input v-model="motionForm.topic" placeholder="动议讨论的主题…" />
        </el-form-item>
        <el-form-item label="提出者代表团">
          <el-select v-model="motionProposerDelegation" placeholder="选择代表团" clearable style="width: 100%; margin-bottom: 8px" @change="onMotionProposerDelegationChange">
            <el-option v-for="d in store.delegations" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
          <el-select v-model="motionProposerDelegate" placeholder="选择代表（可选）" clearable style="width: 100%" :disabled="!motionProposerDelegation">
            <el-option v-for="m in filteredProposers" :key="m.id" :label="m.seat + (m.is_leader ? ' (阁首)' : '')" :value="m.id" />
          </el-select>
        </el-form-item>
        <template v-if="motionTypeNeedsUnitDuration">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="单位时长（秒）">
                <el-input-number v-model="motionForm.unit_duration" :min="10" :step="10" :max="600" controls-position="right" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="总时长（秒）">
                <el-input-number v-model="motionForm.total_duration" :min="30" :step="30" :max="7200" controls-position="right" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
        <el-alert v-else type="info" :closable="false" show-icon style="margin-top: 8px">
          <template #default>此动议类型不包含时长设置</template>
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="motionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="motionLoading" @click="handleCreateMotion">创建动议</el-button>
      </template>
    </el-dialog>

    <!-- ===== 添加发言者对话框 ===== -->
    <el-dialog v-model="addSpeakerDialogVisible" title="添加发言者" width="400px">
      <el-form label-position="top">
        <el-form-item label="代表团">
          <el-select v-model="selectedDelegationId" placeholder="选择代表团" style="width: 100%" @change="onDelegationChange">
            <el-option v-for="d in store.delegations" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="代表" v-if="selectedDelegationId">
          <el-select v-model="selectedDelegateId" placeholder="选择代表" style="width: 100%">
            <el-option v-for="m in filteredDelegates" :key="m.id" :label="m.seat + (m.is_leader ? ' (阁首)' : '')" :value="m.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addSpeakerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addLoading" @click="handleAddSpeaker">添加</el-button>
      </template>
    </el-dialog>

    <!-- ===== 议程选择对话框 ===== -->
    <el-dialog v-model="agendaDialogVisible" title="选择议程" width="600px">
      <div class="agenda-select-list">
        <div
          v-for="item in store.agendaItems"
          :key="item.id"
          class="agenda-select-item"
          :class="{ active: item.id === selectedAgendaId }"
          :style="{ paddingLeft: (item.level - 1) * 24 + 16 + 'px' }"
          @click="selectedAgendaId = item.id"
        >
          <el-tag size="small" :type="levelTags[item.level - 1] || 'info'" effect="plain">L{{ item.level }}</el-tag>
          <span class="agenda-select-title">{{ item.title }}</span>
          <el-tag v-if="item.is_active" size="small" type="success" class="active-tag">当前</el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="agendaDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!selectedAgendaId" @click="handleActivateAgenda">激活选中议程</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay, VideoPause, CircleClose, Plus, Close, Edit, Microphone } from '@element-plus/icons-vue'
import { useMeetingStore } from '../../stores/meeting'
import api from '../../api'

const store = useMeetingStore()
const motionTypesConfig = ref([])  // 所有类型（内置+自定义）
const BUILTIN_KEYS = ['moderated_caucus', 'unmoderated_caucus', 'free_caucus', 'speakers_list']
const BUILTIN_LABELS = { moderated_caucus: '有主持核心磋商', unmoderated_caucus: '自由辩论', free_caucus: '自由磋商', speakers_list: '轮席发言' }

// 从 committee 接口加载所有动议类型
async function loadMotionTypesConfig() {
  try {
    const { data } = await api.get('/api/staff/committee')
    motionTypesConfig.value = data.motion_types || []
  } catch (e) {}
}

// 查找类型配置（内置类型用硬编码，自定义类型查列表）
function findTypeConfig(type) {
  if (BUILTIN_KEYS.includes(type)) {
    // 先查数据库有没有覆盖的内置类型
    const label = BUILTIN_LABELS[type]
    const fromDb = motionTypesConfig.value.find(m => m.name === label)
    if (fromDb) {
      return { ...fromDb, need_speakers_list: fromDb.need_speakers_list ?? true, need_unit_duration: fromDb.need_unit_duration ?? true, need_total_duration: fromDb.need_total_duration ?? true }
    }
    return { need_speakers_list: true, need_unit_duration: true, need_total_duration: true }
  }
  return motionTypesConfig.value.find(m => m.name === type)
}

// 查找当前选中类型的配置
const currentMotionTypeConfig = computed(() => {
  return findTypeConfig(motionForm.value.type)
})

// 根据类型配置动态显示/隐藏时长字段
const motionTypeNeedsUnitDuration = computed(() => {
  return currentMotionTypeConfig.value?.need_unit_duration ?? true
})

function onMotionTypeChange(newType) {
  const config = findTypeConfig(newType)
  if (config && !BUILTIN_KEYS.includes(newType)) {
    if (config.default_unit_duration) motionForm.value.unit_duration = config.default_unit_duration
    if (config.default_total_duration) motionForm.value.total_duration = config.default_total_duration
  }
}

// 对话框状态
const motionDialogVisible = ref(false)
const motionLoading = ref(false)
const addSpeakerDialogVisible = ref(false)
const addLoading = ref(false)
const agendaDialogVisible = ref(false)
const selectedAgendaId = ref(null)

const motionForm = ref({ type: 'moderated_caucus', topic: '', unit_duration: 60, total_duration: 300 })
const motionProposerDelegation = ref(null)
const motionProposerDelegate = ref(null)
const selectedDelegationId = ref(null)
const selectedDelegateId = ref(null)

const motionTypeLabels = { moderated_caucus: '有主持核心磋商', unmoderated_caucus: '自由辩论', free_caucus: '自由磋商', speakers_list: '轮席发言' }

// 获取动议类型显示名称（所有类型从 motionTypesConfig 中查）
function getMotionTypeLabel(type) {
  if (motionTypeLabels[type]) return motionTypeLabels[type]
  const found = motionTypesConfig.value.find(m => m.name === type)
  return found ? found.name : type
}

const levelTags = ['success', 'warning', 'danger', 'info', '']

// 计算属性
const filteredDelegates = computed(() => {
  if (!selectedDelegationId.value) return []
  return store.allDelegates.filter(d => d.delegation_id === selectedDelegationId.value)
})
const filteredProposers = computed(() => {
  if (!motionProposerDelegation.value) return []
  return store.allDelegates.filter(d => d.delegation_id === motionProposerDelegation.value)
})

// 发言者颜色
const delegationColors = {}
const colorPalette = ['#5b92e5','#e84393','#6c5ce7','#00b894','#fdcb6e','#e17055','#0984e3','#00cec9','#fd79a8','#636e72','#2ecc71','#e74c3c']
function getSpeakerColor(name) {
  if (!name) return '#94a3b8'
  if (!delegationColors[name]) {
    delegationColors[name] = colorPalette[Object.keys(delegationColors).length % colorPalette.length]
  }
  return delegationColors[name]
}

function onDelegationChange() { selectedDelegateId.value = null }
function onMotionProposerDelegationChange() { motionProposerDelegate.value = null }

function showAgendaDialog() {
  selectedAgendaId.value = store.currentAgenda?.id || null
  agendaDialogVisible.value = true
}

async function handleActivateAgenda() {
  if (!selectedAgendaId.value) return
  const ok = await store.activateAgenda(selectedAgendaId.value)
  if (ok) agendaDialogVisible.value = false
}

// 动议操作
async function showMotionDialog() {
  motionForm.value = { type: 'moderated_caucus', topic: '', unit_duration: 60, total_duration: 300 }
  motionProposerDelegation.value = null
  motionProposerDelegate.value = null
  await Promise.all([store.loadDelegates(), loadMotionTypesConfig()])
  motionDialogVisible.value = true
}

async function handleCreateMotion() {
  motionLoading.value = true
  const ok = await store.createMotion({
    ...motionForm.value,
    proposer_delegation_id: motionProposerDelegation.value,
    proposer_delegate_id: motionProposerDelegate.value
  })
  motionLoading.value = false
  if (ok) motionDialogVisible.value = false
}

async function handleEndMotion() {
  await store.endMotion()
}

// 发言操作
function handleSelectSpeaker(speaker) {
  if (store.currentSpeaker?.id === speaker.id) return
  store.selectSpeaker(speaker)
}

async function handleEndSpeaker() {
  await store.endSpeaker()
}

// 添加发言者
async function showAddSpeakerDialog() {
  selectedDelegationId.value = null
  selectedDelegateId.value = null
  await store.loadDelegates()
  addSpeakerDialogVisible.value = true
}

async function handleAddSpeaker() {
  if (!selectedDelegateId.value) { ElMessage.warning('请选择代表'); return }
  addLoading.value = true
  const ok = await store.addSpeaker(selectedDelegationId.value, selectedDelegateId.value)
  addLoading.value = false
  if (ok) addSpeakerDialogVisible.value = false
}

onMounted(() => {
  store.loadFullState()
  loadMotionTypesConfig()
  store.registerWebSocketListener()
})

onUnmounted(() => {
  // 保留 timer 和 WS 监听 — Pinia store 跨页面持有
})
</script>

<style scoped>
.meeting-page { max-width: 1200px; margin: 0 auto; }

.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}
.page-header h2 { font-size: 20px; font-weight: 700; color: #0f172a; margin: 0; }
.page-header p { font-size: 13px; color: #64748b; margin: 2px 0 0; }
.header-actions { display: flex; gap: 8px; }

/* 状态栏 */
.status-bar {
  display: flex; gap: 12px; margin-bottom: 16px;
}
.status-item {
  display: flex; align-items: center; gap: 10px;
  background: #fff; border-radius: 10px; padding: 12px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06); flex: 1;
}
.status-label {
  font-size: 12px; color: #94a3b8; font-weight: 600;
  white-space: nowrap;
}
.status-value {
  font-size: 14px; font-weight: 600; color: #0f172a;
}
.status-value.placeholder { color: #cbd5e1; font-weight: 400; }
.status-topic {
  font-size: 12px; color: #64748b;
  background: #f1f5f9; padding: 2px 8px; border-radius: 4px;
}

/* 计时器卡片 */
.timer-card {
  background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  overflow: hidden; height: 100%;
}
.timer-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 24px; border-bottom: 1px solid #f1f5f9;
}
.timer-header h3 { font-size: 16px; font-weight: 600; color: #0f172a; margin: 0; }
.live-badge { font-size: 11px; color: #ef4444; font-weight: 700; animation: pulse 1.5s infinite; }

.timer-content { padding: 32px 24px; text-align: center; }

/* 有发言者时 */
.speaker-display {}
.total-slot { margin-bottom: 4px; }
.total-label { font-size: 12px; color: #94a3b8; font-weight: 600; display: block; margin-bottom: 2px; }
.total-time { font-size: 16px; font-weight: 600; color: #64748b; font-family: monospace; }

.speaker-name {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  font-size: 22px; font-weight: 700; color: #0f172a; margin: 8px 0 4px;
}
.flag-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.delegate-sub { font-size: 14px; font-weight: 400; color: #64748b; }

.countdown {
  font-size: 64px; font-weight: 800; font-family: 'Fira Mono', 'JetBrains Mono', monospace;
  color: #5b92e5; line-height: 1.1; margin: 12px 0 20px;
  transition: color 0.3s;
}
.countdown.warning { color: #e6a23c; animation: pulse 1s infinite; }
.countdown.critical { color: #ef4444; animation: pulse 0.5s infinite; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.timer-controls { display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }
.ctrl-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 22px; border: none; border-radius: 10px;
  font-size: 14px; font-weight: 600; cursor: pointer;
  transition: all 0.2s;
}
.ctrl-btn:hover { transform: translateY(-1px); }
.btn-start { background: linear-gradient(135deg,#16a34a,#22c55e); color: #fff; }
.btn-start:hover { box-shadow: 0 4px 12px rgba(22,163,74,0.3); }
.btn-pause { background: linear-gradient(135deg,#d97706,#f59e0b); color: #fff; }
.btn-pause:hover { box-shadow: 0 4px 12px rgba(217,119,6,0.3); }
.btn-end { background: #f1f5f9; color: #64748b; }
.btn-end:hover { background: #fee2e2; color: #ef4444; }

.speech-area { text-align: left; padding-top: 16px; border-top: 1px solid #f1f5f9; }
.speech-actions {
  display: flex; justify-content: space-between; align-items: center; margin-top: 8px;
}
.speech-hint { font-size: 11px; color: #94a3b8; }

/* 无发言者 */
.no-speaker { padding: 20px 0; }
.total-only { margin-bottom: 16px; }
.big-timer {
  font-size: 72px; font-weight: 800; font-family: 'Fira Mono', monospace;
  color: #94a3b8; line-height: 1;
}
.no-speaker-hint { font-size: 14px; color: #94a3b8; }

/* 无动议 */
.no-motion { padding: 40px 0; }
.no-motion-icon { color: #cbd5e1; margin-bottom: 12px; }
.no-motion h3 { font-size: 18px; color: #64748b; margin: 0 0 8px; }
.no-motion p { font-size: 13px; color: #94a3b8; margin: 0; }

/* 发言名单卡片 */
.speakers-card {
  background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  overflow: hidden; margin-bottom: 12px;
}
.speakers-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid #f1f5f9;
}
.speakers-header h3 { font-size: 16px; font-weight: 600; color: #0f172a; margin: 0; }

.speakers-list { max-height: 340px; overflow-y: auto; padding: 4px 0; }

.speaker-row {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; cursor: pointer; transition: all 0.15s;
  border-left: 3px solid transparent;
}
.speaker-row:hover { background: #f8fafc; }
.speaker-row.active { background: #f0fdf4; border-left-color: #22c55e; }
.speaker-row.current { background: #edf3fb; border-left-color: #5b92e5; }
.speaker-row.spoken { opacity: 0.55; }

.spk-order {
  width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;
  background: #f1f5f9; border-radius: 50%; font-size: 11px; font-weight: 700; color: #64748b;
  flex-shrink: 0;
}
.spk-flag { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.spk-name { font-size: 14px; font-weight: 600; color: #1e293b; flex-shrink: 0; }
.spk-delegate { font-size: 12px; color: #94a3b8; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.spk-status { margin-left: auto; }
.active-badge {
  font-size: 11px; font-weight: 700; color: #fff;
  background: #22c55e; padding: 1px 8px; border-radius: 12px;
}
.spk-remove {
  display: none; background: none; border: none; cursor: pointer;
  color: #94a3b8; padding: 0 0 0 4px; font-size: 14px;
}
.speaker-row:hover .spk-remove { display: flex; align-items: center; }
.spk-remove:hover { color: #ef4444; }

.speakers-empty { padding: 20px 0; }

/* 动议详情卡片 */
.motion-detail-card {
  background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  overflow: hidden;
}
.motion-detail-header {
  padding: 14px 20px; border-bottom: 1px solid #f1f5f9;
}
.motion-detail-header h4 { font-size: 14px; font-weight: 600; color: #64748b; margin: 0; }
.motion-detail-body { padding: 12px 20px; }
.detail-row {
  display: flex; align-items: center; gap: 10px; padding: 6px 0;
}
.detail-key { font-size: 12px; color: #94a3b8; font-weight: 600; min-width: 50px; }
.detail-val { font-size: 13px; color: #1e293b; font-weight: 500; }

/* 议程选择列表 */
.agenda-select-list { max-height: 400px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 8px; }
.agenda-select-item {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; cursor: pointer; border-bottom: 1px solid #f1f5f9;
  transition: background 0.15s;
}
.agenda-select-item:last-child { border-bottom: none; }
.agenda-select-item:hover { background: #f8fafc; }
.agenda-select-item.active { background: #edf3fb; border-left: 3px solid #5b92e5; }
.agenda-select-title { flex: 1; font-size: 14px; color: #1e293b; }
</style>
