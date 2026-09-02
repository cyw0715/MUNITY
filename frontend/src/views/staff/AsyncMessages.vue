<template>
  <div class="async-messages-page animate-fade-in">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2>非对称消息</h2>
        <p>危机联动核心通信系统</p>
      </div>
      <el-button type="primary" size="large" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>发送消息
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card-item">
        <div class="stat-icon" style="background: #edf3fb; color: #5b92e5;">
          <el-icon :size="20"><Message /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-num">{{ messages.length }}</span>
          <span class="stat-desc">总消息</span>
        </div>
      </div>
      <div class="stat-card-item">
        <div class="stat-icon" style="background: #f0fdf4; color: #16a34a;">
          <el-icon :size="20"><Select /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-num">{{ messages.filter(m => m.visibility === 'public').length }}</span>
          <span class="stat-desc">公开</span>
        </div>
      </div>
      <div class="stat-card-item">
        <div class="stat-icon" style="background: #fffbeb; color: #d97706;">
          <el-icon :size="20"><Avatar /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-num">{{ messages.filter(m => m.visibility === 'delegation').length }}</span>
          <span class="stat-desc">代表团</span>
        </div>
      </div>
      <div class="stat-card-item">
        <div class="stat-icon" style="background: #fef2f2; color: #dc2626;">
          <el-icon :size="20"><Lock /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-num">{{ messages.filter(m => m.visibility === 'private').length }}</span>
          <span class="stat-desc">私密</span>
        </div>
      </div>
    </div>

    <!-- 消息列表卡片 -->
    <div class="msg-card">
      <!-- 标签页 -->
      <div class="msg-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['tab-btn', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
          <span v-if="tab.count !== undefined" class="tab-count">{{ tab.count }}</span>
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!filteredMessages.length" class="empty-state">
        <div class="empty-icon">
          <el-icon :size="48"><ChatDotSquare /></el-icon>
        </div>
        <h3>暂无非对称消息</h3>
        <p>点击右上角"发送消息"创建第一条</p>
      </div>

      <!-- 消息列表 -->
      <div v-else class="msg-list">
        <transition-group name="list">
          <div
            v-for="item in filteredMessages"
            :key="item.id"
            class="msg-item"
            :class="{ 'is-unread': !item.is_read && item.visibility !== 'public' }"
          >
            <div class="msg-left">
              <div class="msg-badge" :class="'badge-' + item.visibility">
                {{ visibilityLabel(item.visibility) }}
              </div>
            </div>
            <div class="msg-body" @click="showDetail(item)">
              <div class="msg-meta">
                <span class="msg-sender">
                  <el-icon><UserFilled /></el-icon>
                  {{ item.sender_name }}
                </span>
                <span class="msg-target">
                  <el-icon><ArrowRight /></el-icon>
                  {{ formatRecipients(item) }}
                </span>
                <span class="msg-time">{{ formatTime(item.created_at) }}</span>
              </div>
              <div class="msg-title">{{ item.title }}</div>
              <div class="msg-excerpt">{{ truncate(item.content, 120) }}</div>
            </div>
            <div class="msg-actions">
              <el-tooltip content="撤回" placement="top">
                <el-button
                  text
                  type="danger"
                  size="small"
                  class="action-btn"
                  @click="handleDelete(item)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </div>
        </transition-group>
      </div>
    </div>

    <!-- 发送对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="发送非对称消息"
      width="580px"
      destroy-on-close
      class="send-dialog"
    >
      <el-form :model="form" label-position="top" class="send-form">
        <div class="visibility-cards">
          <div
            v-for="v in visibilityOptions"
            :key="v.value"
            :class="['vis-card', { active: form.visibility === v.value }]"
            @click="form.visibility = v.value"
          >
            <el-icon :size="22">{{ v.icon }}</el-icon>
            <span class="vis-label">{{ v.label }}</span>
            <span class="vis-desc">{{ v.desc }}</span>
          </div>
        </div>

        <el-form-item v-if="form.visibility === 'private'" label="选择接收代表（可多选）">
          <el-select v-model="form.receiver_ids" multiple filterable collapse-tags placeholder="搜索代表姓名或席位..." style="width: 100%">
            <el-option-group v-for="d in delegations" :key="d.id" :label="d.name">
              <el-option
                v-for="m in getDelegationMembers(d.id)"
                :key="m.id"
                :label="m.seat + (m.is_leader ? ' (阁首)' : '')"
                :value="m.id"
              />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.visibility === 'delegation'" label="选择接收代表团（可多选）">
          <el-select v-model="form.receiver_delegation_ids" multiple filterable collapse-tags placeholder="选择代表团..." style="width: 100%">
            <el-option v-for="d in delegations" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="消息标题">
          <el-input v-model="form.title" placeholder="输入消息标题..." maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="消息正文">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="5"
            placeholder="输入消息正文..."
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">
          发送消息
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      :title="detailItem?.title || '消息详情'"
      width="560px"
      class="detail-dialog"
    >
      <div v-if="detailItem" class="detail-content">
        <div class="detail-header-bar">
        <el-tag :type="visibilityTagType(detailItem.visibility)" effect="dark" size="small">
          {{ visibilityLabel(detailItem.visibility) }}
        </el-tag>
        <span class="detail-sender">{{ detailItem.sender_name }}</span>
        <span class="detail-time">{{ formatTime(detailItem.created_at) }}</span>
      </div>
      <div v-if="detailItem && (detailItem.receiver_names?.length || detailItem.receiver_delegation_names?.length)" class="detail-recipient">
        <el-icon><ArrowRight /></el-icon>
        接收: {{ formatRecipients(detailItem) }}
      </div>
        <el-divider />
        <div class="detail-body">{{ detailItem.content || '（无内容）' }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Message, Loading, ChatDotSquare, Delete, UserFilled, ArrowRight, Lock, Select, Avatar, Edit } from '@element-plus/icons-vue'
import api from '../../api'
import { useWebSocket } from '../../composables/useWebSocket'

const activeTab = ref('all')
const messages = ref([])
const delegations = ref([])
const allDelegates = ref([])
const loading = ref(false)

const createDialogVisible = ref(false)
const createLoading = ref(false)
const detailVisible = ref(false)
const detailItem = ref(null)

const form = ref({
  visibility: 'public',
  receiver_ids: [],
  receiver_delegation_ids: [],
  title: '',
  content: ''
})

const tabs = computed(() => [
  { key: 'all', label: '全部', count: messages.value.length },
  { key: 'public', label: '公开', count: messages.value.filter(m => m.visibility === 'public').length },
  { key: 'delegation', label: '代表团', count: messages.value.filter(m => m.visibility === 'delegation').length },
  { key: 'private', label: '私密', count: messages.value.filter(m => m.visibility === 'private').length },
])

const visibilityOptions = [
  { value: 'public', label: '公开', icon: 'Select', desc: '委员会内所有代表可见', color: '#16a34a' },
  { value: 'delegation', label: '代表团', icon: 'Avatar', desc: '仅指定代表团成员可见', color: '#d97706' },
  { value: 'private', label: '私密', icon: 'Lock', desc: '仅指定代表本人可见', color: '#dc2626' },
]

const filteredMessages = computed(() => {
  if (activeTab.value === 'all') return messages.value
  return messages.value.filter(m => m.visibility === activeTab.value)
})

function visibilityLabel(v) {
  return { public: '公开', delegation: '代表团', private: '私密' }[v] || v
}
function visibilityTagType(v) {
  return { public: 'success', delegation: 'warning', private: 'danger' }[v] || 'info'
}

function formatTime(t) {
  if (!t) return ''
  const d = new Date(t)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function formatRecipients(item) {
  const parts = []
  if (item.receiver_delegation_names?.length) {
    parts.push(...item.receiver_delegation_names)
  }
  if (item.receiver_names?.length) {
    parts.push(...item.receiver_names)
  }
  if (item.visibility === 'public') {
    return '所有人'
  }
  return parts.join(', ') || '所有人'
}

function truncate(text, len) {
  if (!text) return ''
  return text.length > len ? text.substring(0, len) + '...' : text
}

function getDelegationMembers(delegationId) {
  return allDelegates.value.filter(d => d.delegation_id === delegationId)
}

async function loadData() {
  loading.value = true
  try {
    const params = activeTab.value !== 'all' ? { visibility: activeTab.value } : {}
    const [mRes, availRes] = await Promise.all([
      api.get('/api/staff/async-messages', { params }),
      api.get('/api/staff/available-delegates').catch(() => null)
    ])
    messages.value = mRes.data
    if (availRes?.data) {
      delegations.value = availRes.data.delegations || []
      allDelegates.value = availRes.data.delegates || []
    } else {
      // fallback
      const [dRes, delRes] = await Promise.all([
        api.get('/api/staff/delegations'),
        api.get('/api/staff/delegates')
      ])
      delegations.value = dRes.data
      allDelegates.value = delRes.data
    }
  } catch (e) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  form.value = { visibility: 'public', receiver_ids: [], receiver_delegation_ids: [], title: '', content: '' }
  createDialogVisible.value = true
}

function showDetail(item) {
  detailItem.value = item
  detailVisible.value = true
}

async function handleCreate() {
  if (!form.value.title?.trim()) { ElMessage.warning('请输入消息标题'); return }
  if (!form.value.content?.trim()) { ElMessage.warning('请输入消息内容'); return }
  if (form.value.visibility === 'private' && (!form.value.receiver_ids || form.value.receiver_ids.length === 0)) { ElMessage.warning('请至少选择一个接收代表'); return }
  if (form.value.visibility === 'delegation' && (!form.value.receiver_delegation_ids || form.value.receiver_delegation_ids.length === 0)) { ElMessage.warning('请至少选择一个接收代表团'); return }

  createLoading.value = true
  try {
    await api.post('/api/staff/async-messages', {
      visibility: form.value.visibility,
      receiver_ids: form.value.receiver_ids || [],
      receiver_delegation_ids: form.value.receiver_delegation_ids || [],
      title: form.value.title.trim(),
      content: form.value.content.trim()
    })
    ElMessage.success({ message: '消息已发送', duration: 2000 })
    createDialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '发送失败')
  } finally {
    createLoading.value = false
  }
}

async function handleDelete(item) {
  try {
    await ElMessageBox.confirm(
      `确定撤回「${item.title}」？`,
      '撤回确认',
      { confirmButtonText: '撤回', cancelButtonText: '取消', type: 'warning' }
    )
    await api.delete(`/api/staff/async-messages/${item.id}`)
    ElMessage.success('已撤回')
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '撤回失败')
  }
}

let wsCleanup = null
let ws2Cleanup = null
onMounted(() => {
  loadData()
  const ws = useWebSocket()
  const handler = () => loadData()
  ws.on('new_async_message', handler)
  wsCleanup = () => ws.off('new_async_message', handler)
  // 也监听通配符
  ws2Cleanup = () => {}
})
onUnmounted(() => {
  if (wsCleanup) wsCleanup()
  if (ws2Cleanup) ws2Cleanup()
})
</script>

<style scoped>
.async-messages-page {
  max-width: 1000px;
  margin: 0 auto;
}

/* 统计卡片 */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}
.stat-card-item {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #fff;
  padding: 18px 20px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  transition: all 0.2s;
}
.stat-card-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transform: translateY(-1px);
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-info {
  display: flex;
  flex-direction: column;
}
.stat-num {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}
.stat-desc {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 1px;
}

/* 消息卡片容器 */
.msg-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  overflow: hidden;
}

/* 自定义标签页 */
.msg-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid #f1f5f9;
  padding: 0 20px;
}
.tab-btn {
  position: relative;
  padding: 14px 18px;
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}
.tab-btn:hover { color: #1e293b; }
.tab-btn.active { color: #5b92e5; }
.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 18px;
  right: 18px;
  height: 3px;
  background: #5b92e5;
  border-radius: 3px 3px 0 0;
}
.tab-count {
  font-size: 11px;
  background: #f1f5f9;
  color: #94a3b8;
  padding: 1px 7px;
  border-radius: 10px;
  font-weight: 600;
}
.tab-btn.active .tab-count {
  background: #edf3fb;
  color: #5b92e5;
}

/* 加载 / 空状态 */
.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 12px;
  color: #94a3b8;
}
.empty-icon { color: #cbd5e1; }
.empty-state h3 { font-size: 16px; color: #64748b; margin: 0; }
.empty-state p { font-size: 13px; color: #94a3b8; margin: 0; }

/* 消息列表 */
.msg-list { padding: 4px 0; }

.msg-item {
  display: flex;
  align-items: stretch;
  gap: 0;
  padding: 16px 20px;
  border-bottom: 1px solid #f8fafc;
  transition: all 0.2s;
  cursor: default;
}
.msg-item:last-child { border-bottom: none; }
.msg-item:hover { background: #f8fafc; }

/* 左侧badge */
.msg-left {
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
  min-width: 56px;
}
.msg-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.badge-public { background: #f0fdf4; color: #16a34a; }
.badge-delegation { background: #fffbeb; color: #d97706; }
.badge-private { background: #fef2f2; color: #dc2626; }

/* 消息正文 */
.msg-body {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}
.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 4px;
}
.msg-sender, .msg-target { display: flex; align-items: center; gap: 3px; }
.msg-target .el-icon { font-size: 12px; }
.msg-time { margin-left: auto; white-space: nowrap; }
.msg-title {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 3px;
  line-height: 1.4;
}
.msg-excerpt {
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.msg-item.is-unread {
  background: #f0f7ff;
  border-left: 3px solid #5b92e5;
  margin-left: 0;
}
.msg-item.is-unread .msg-title { color: #5b92e5; }

/* 右侧操作 */
.msg-actions {
  display: flex;
  align-items: center;
  padding-left: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}
.msg-item:hover .msg-actions { opacity: 1; }
.action-btn { font-size: 16px; }

/* 列表动画 */
.list-enter-active, .list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from { opacity: 0; transform: translateX(-20px); }
.list-leave-to { opacity: 0; transform: translateX(20px); }

/* 发送对话框 */
.send-dialog :deep(.el-dialog__body) { max-height: 60vh; overflow-y: auto; }
.send-form { margin-top: 4px; }

.visibility-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}
.vis-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 12px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}
.vis-card:hover {
  border-color: #5b92e5;
  background: #f8faff;
}
.vis-card.active {
  border-color: #5b92e5;
  background: #edf3fb;
}
.vis-card .vis-label { font-size: 13px; font-weight: 600; color: #0f172a; }
.vis-card .vis-desc { font-size: 11px; color: #94a3b8; line-height: 1.3; }

/* 详情对话框 */
.detail-content { padding: 4px 0; }
.detail-header-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.detail-sender { font-weight: 600; font-size: 14px; color: #0f172a; }
.detail-time { font-size: 12px; color: #94a3b8; margin-left: auto; }
.detail-recipient {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}
.detail-body {
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.7;
  color: #334155;
  background: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  min-height: 80px;
}
</style>
