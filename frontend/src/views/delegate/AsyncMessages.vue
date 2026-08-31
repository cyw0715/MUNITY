<template>
  <div class="async-messages-page animate-fade-in">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2>非对称消息</h2>
        <p>查看你的非对称消息 — 公开消息、代表团消息和私密消息</p>
      </div>
      <div v-if="unreadCount > 0" class="unread-bar">
        <span>{{ unreadCount }} 条未读</span>
        <el-button text type="primary" size="small" @click="markAllRead">全部标记已读</el-button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="msg-card">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <div v-else-if="!messages.length" class="empty-state">
        <div class="empty-icon"><el-icon :size="48"><ChatDotSquare /></el-icon></div>
        <h3>暂无非对称消息</h3>
        <p>学团发送的消息将显示在这里</p>
      </div>

      <div v-else class="msg-list">
        <div
          v-for="item in messages"
          :key="item.id"
          class="msg-item"
          :class="{ 'is-unread': !item.is_read }"
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
              <span v-if="!item.is_read" class="unread-tag">新</span>
              <span class="msg-time">{{ formatTime(item.created_at) }}</span>
            </div>
            <div class="msg-title">{{ item.title }}</div>
            <div class="msg-excerpt">{{ truncate(item.content, 100) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      :title="detailItem?.title || '消息详情'"
      width="560px"
      class="detail-dialog"
      @opened="markRead"
    >
      <div v-if="detailItem" class="detail-content">
        <div class="detail-header-bar">
          <el-tag :type="visibilityTagType(detailItem.visibility)" effect="dark" size="small">
            {{ visibilityLabel(detailItem.visibility) }}
          </el-tag>
          <span class="detail-sender">{{ detailItem.sender_name }}</span>
          <span class="detail-time">{{ formatTime(detailItem.created_at) }}</span>
        </div>
        <el-divider />
        <div class="detail-body">{{ detailItem.content || '（无内容）' }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, ChatDotSquare, UserFilled } from '@element-plus/icons-vue'
import api from '../../api'
import { useWebSocket } from '../../composables/useWebSocket'

const messages = ref([])
const loading = ref(false)
const detailVisible = ref(false)
const detailItem = ref(null)
const unreadCount = ref(0)

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

function truncate(text, len) {
  if (!text) return ''
  return text.length > len ? text.substring(0, len) + '...' : text
}

async function loadData() {
  loading.value = true
  try {
    const [mRes, cRes] = await Promise.all([
      api.get('/api/delegate/async-messages'),
      api.get('/api/delegate/async-messages/unread-count')
    ])
    messages.value = mRes.data
    unreadCount.value = cRes.data.count
  } catch (e) {
    ElMessage.error('加载消息失败')
  } finally {
    loading.value = false
  }
}

function showDetail(item) {
  detailItem.value = item
  detailVisible.value = true
}

async function markRead() {
  if (!detailItem.value || detailItem.value.is_read) return
  try {
    await api.put(`/api/delegate/async-messages/${detailItem.value.id}/read`)
    detailItem.value.is_read = true
    loadData()
  } catch (e) {}
}

async function markAllRead() {
  try {
    const unread = messages.value.filter(m => !m.is_read)
    await Promise.all(unread.map(m => api.put(`/api/delegate/async-messages/${m.id}/read`)))
    ElMessage.success('已全部标记为已读')
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

let wsCleanup = null
onMounted(() => {
  loadData()
  const ws = useWebSocket()
  const handler = () => loadData()
  ws.on('*', handler)
  wsCleanup = () => ws.off('*', handler)
})
onUnmounted(() => { if (wsCleanup) wsCleanup() })
</script>

<style scoped>
.async-messages-page { max-width: 800px; margin: 0 auto; }

/* 未读提示栏 */
.unread-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #eef2ff;
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  color: #1a73e8;
}

/* 消息卡片 */
.msg-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  overflow: hidden;
}

/* 加载 / 空状态 */
.loading-state, .empty-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 60px 20px; gap: 12px;
  color: #94a3b8;
}
.empty-icon { color: #cbd5e1; }
.empty-state h3 { font-size: 16px; color: #64748b; margin: 0; }
.empty-state p { font-size: 13px; color: #94a3b8; margin: 0; }

/* 消息列表 */
.msg-list { padding: 4px 0; }
.msg-item {
  display: flex;
  gap: 14px;
  padding: 16px 20px;
  border-bottom: 1px solid #f8fafc;
  transition: all 0.2s;
}
.msg-item:last-child { border-bottom: none; }
.msg-item:hover { background: #f8fafc; }

.msg-left { display: flex; align-items: flex-start; padding-top: 2px; min-width: 56px; }
.msg-badge {
  font-size: 11px; font-weight: 700; padding: 3px 10px;
  border-radius: 20px; letter-spacing: 0.5px; white-space: nowrap;
}
.badge-public { background: #f0fdf4; color: #16a34a; }
.badge-delegation { background: #fffbeb; color: #d97706; }
.badge-private { background: #fef2f2; color: #dc2626; }

.msg-body { flex: 1; min-width: 0; cursor: pointer; }
.msg-meta {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; color: #94a3b8; margin-bottom: 4px;
}
.msg-sender { display: flex; align-items: center; gap: 3px; }
.unread-tag {
  font-size: 10px; font-weight: 700; color: #fff;
  background: #ef4444; padding: 0 6px; border-radius: 4px;
  line-height: 18px;
}
.msg-time { margin-left: auto; white-space: nowrap; }
.msg-title {
  font-size: 15px; font-weight: 600; color: #0f172a;
  margin-bottom: 3px; line-height: 1.4;
}
.msg-excerpt {
  font-size: 13px; color: #94a3b8; line-height: 1.4;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* 未读高亮 */
.msg-item.is-unread {
  background: #f0f7ff;
  border-left: 3px solid #1a73e8;
  margin-left: 0;
}
.msg-item.is-unread .msg-title { color: #1a73e8; }

/* 详情 */
.detail-content { padding: 4px 0; }
.detail-header-bar {
  display: flex; align-items: center; gap: 10px; margin-bottom: 8px;
}
.detail-sender { font-weight: 600; font-size: 14px; color: #0f172a; }
.detail-time { font-size: 12px; color: #94a3b8; margin-left: auto; }
.detail-body {
  white-space: pre-wrap; font-size: 14px; line-height: 1.7;
  color: #334155; background: #f8fafc; padding: 16px;
  border-radius: 8px; min-height: 80px;
}
</style>
