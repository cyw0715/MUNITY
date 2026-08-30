<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>非对称消息</span>
        <el-button v-if="unreadCount > 0" type="primary" @click="markAllRead">
          全部标记已读 ({{ unreadCount }})
        </el-button>
      </div>
    </template>

    <div v-if="loading" style="text-align: center; padding: 40px">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      <p style="color: #909399; margin-top: 8px">加载中...</p>
    </div>

    <div v-else-if="messages.length">
      <div
        v-for="item in messages"
        :key="item.id"
        class="message-item"
        :class="{ 'unread': !item.is_read }"
        @click="showDetail(item)"
      >
        <div class="message-header">
          <div class="message-tags">
            <el-tag
              :type="visibilityType(item.visibility)"
              size="small"
              effect="dark"
            >
              {{ visibilityLabel(item.visibility) }}
            </el-tag>
            <el-tag type="info" size="small" effect="plain">
              {{ item.sender_name }}
            </el-tag>
          </div>
          <div class="message-time">{{ formatTime(item.created_at) }}</div>
        </div>
        <div class="message-title">{{ item.title }}</div>
        <div class="message-preview">{{ (item.content || '').substring(0, 100) }}{{ item.content?.length > 100 ? '...' : '' }}</div>
      </div>
    </div>
    <el-empty v-else description="暂无非对称消息" />
  </el-card>

  <!-- 详情对话框 -->
  <el-dialog v-model="detailVisible" :title="detailItem?.title || '消息详情'" width="600px" @opened="markRead">
    <div v-if="detailItem">
      <p>
        <el-tag :type="visibilityType(detailItem.visibility)" size="small" effect="dark">{{ visibilityLabel(detailItem.visibility) }}</el-tag>
        <span style="margin-left: 8px; color: #909399; font-size: 13px">{{ detailItem.sender_name }} · {{ formatTime(detailItem.created_at) }}</span>
      </p>
      <el-divider />
      <div style="white-space: pre-wrap; background: #f5f7fa; padding: 16px; border-radius: 4px; min-height: 100px">
        {{ detailItem.content || '无内容' }}
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import api from '../../api'
import { useWebSocket } from '../../composables/useWebSocket'

const messages = ref([])
const loading = ref(false)
const detailVisible = ref(false)
const detailItem = ref(null)
const unreadCount = ref(0)

function visibilityType(v) {
  return { public: 'success', delegation: 'warning', private: 'danger' }[v] || 'info'
}

function visibilityLabel(v) {
  return { public: '公开', delegation: '代表团', private: '私密' }[v] || v
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
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

async function showDetail(item) {
  detailItem.value = item
  detailVisible.value = true
}

async function markRead() {
  if (!detailItem.value || detailItem.value.is_read) return
  try {
    await api.put(`/api/delegate/async-messages/${detailItem.value.id}/read`)
    detailItem.value.is_read = true
    loadData() // 刷新未读数
  } catch (e) {
    // 忽略
  }
}

async function markAllRead() {
  try {
    await Promise.all(
      messages.value
        .filter(m => !m.is_read)
        .map(m => api.put(`/api/delegate/async-messages/${m.id}/read`))
    )
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
  const handler = (data) => {
    if (data.type === 'new_async_message') {
      loadData()
    }
  }
  ws.on('*', handler)
  wsCleanup = () => ws.off('*', handler)
})

onUnmounted(() => {
  if (wsCleanup) wsCleanup()
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.message-item {
  padding: 16px 0;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background 0.2s;
}
.message-item:last-child { border-bottom: none; }
.message-item:hover { background: #f5f7fa; margin: 0 -16px; padding: 16px; border-radius: 4px; }
.message-item.unread {
  background: #f0f9ff;
  margin: 0 -16px;
  padding: 16px;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}
.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.message-tags { display: flex; gap: 6px; align-items: center; }
.message-title {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}
.message-preview { color: #909399; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.message-time { color: #909399; font-size: 12px; }
</style>
