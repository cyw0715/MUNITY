<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>非对称消息（危机联动）</span>
        <el-button type="primary" @click="showCreateDialog">发送消息</el-button>
      </div>
    </template>

    <!-- 标签页：收件/发件/全部 -->
    <el-tabs v-model="activeTab" @tab-change="loadData">
      <el-tab-pane label="全部消息" name="all" />
      <el-tab-pane label="公开消息" name="public" />
      <el-tab-pane label="代表团消息" name="delegation" />
      <el-tab-pane label="私密消息" name="private" />
    </el-tabs>

    <div v-if="loading" style="text-align: center; padding: 40px">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      <p style="color: #909399; margin-top: 8px">加载中...</p>
    </div>

    <div v-else-if="filteredMessages.length">
      <div
        v-for="item in filteredMessages"
        :key="item.id"
        class="message-item"
        :class="{ 'unread': !item.is_read && item.visibility !== 'public' }"
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
            <el-tag v-if="item.sender_name" type="info" size="small" effect="plain">
              {{ item.sender_name }}
            </el-tag>
          </div>
          <div class="message-actions">
            <span class="message-time">{{ formatTime(item.created_at) }}</span>
            <el-button type="danger" link size="small" @click="handleDelete(item)">撤回</el-button>
          </div>
        </div>
        <div class="message-title" @click="showDetail(item)">{{ item.title }}</div>
        <div class="message-meta">
          <template v-if="item.receiver_delegation_name">
            发送至：<strong>{{ item.receiver_delegation_name }}</strong>
          </template>
          <template v-else-if="item.receiver_name">
            发送至：<strong>{{ item.receiver_name }}</strong>
          </template>
          <template v-else>
            发送至：<strong>所有人</strong>
          </template>
        </div>
      </div>
    </div>
    <el-empty v-else description="暂无非对称消息" />
  </el-card>

  <!-- 发送消息对话框 -->
  <el-dialog v-model="createDialogVisible" title="发送非对称消息" width="650px">
    <el-form :model="form" label-position="top">
      <el-form-item label="可见性" required>
        <el-radio-group v-model="form.visibility">
          <el-radio value="private">私密（指定代表）</el-radio>
          <el-radio value="delegation">代表团（指定代表团）</el-radio>
          <el-radio value="public">公开（所有人可见）</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="form.visibility === 'private'" label="接收代表" required>
        <el-select v-model="form.receiver_id" filterable placeholder="选择接收代表" style="width: 100%">
          <el-option-group
            v-for="d in delegations"
            :key="d.id"
            :label="d.name"
          >
            <el-option
              v-for="m in getDelegationMembers(d.id)"
              :key="m.id"
              :label="m.seat + (m.is_leader ? ' (阁首)' : '')"
              :value="m.id"
            />
          </el-option-group>
        </el-select>
      </el-form-item>

      <el-form-item v-if="form.visibility === 'delegation'" label="接收代表团" required>
        <el-select v-model="form.receiver_delegation_id" filterable placeholder="选择代表团" style="width: 100%">
          <el-option
            v-for="d in delegations"
            :key="d.id"
            :label="d.name"
            :value="d.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="标题" required>
        <el-input v-model="form.title" placeholder="消息标题" />
      </el-form-item>
      <el-form-item label="内容" required>
        <el-input v-model="form.content" type="textarea" :rows="6" placeholder="消息正文" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="createDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="createLoading" @click="handleCreate">发送</el-button>
    </template>
  </el-dialog>

  <!-- 详情对话框 -->
  <el-dialog v-model="detailVisible" title="消息详情" width="600px">
    <div v-if="detailItem">
      <p><el-tag :type="visibilityType(detailItem.visibility)" size="small" effect="dark">{{ visibilityLabel(detailItem.visibility) }}</el-tag></p>
      <p><strong>标题：</strong>{{ detailItem.title }}</p>
      <p><strong>发送者：</strong>{{ detailItem.sender_name }}</p>
      <p v-if="detailItem.receiver_name"><strong>接收者：</strong>{{ detailItem.receiver_name }}</p>
      <p v-if="detailItem.receiver_delegation_name"><strong>接收代表团：</strong>{{ detailItem.receiver_delegation_name }}</p>
      <p><strong>时间：</strong>{{ formatTime(detailItem.created_at) }}</p>
      <el-divider />
      <div style="white-space: pre-wrap; background: #f5f7fa; padding: 16px; border-radius: 4px">
        {{ detailItem.content || '无内容' }}
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
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
  visibility: 'private',
  receiver_id: null,
  receiver_delegation_id: null,
  title: '',
  content: ''
})

const filteredMessages = computed(() => {
  if (activeTab.value === 'all') return messages.value
  return messages.value.filter(m => m.visibility === activeTab.value)
})

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

function getDelegationMembers(delegationId) {
  return allDelegates.value.filter(d => d.delegation_id === delegationId)
}

async function loadData() {
  loading.value = true
  try {
    const params = activeTab.value !== 'all' ? { visibility: activeTab.value } : {}
    const [mRes, dRes, delRes] = await Promise.all([
      api.get('/api/staff/async-messages', { params }),
      api.get('/api/staff/delegations'),
      api.get('/api/staff/delegates')
    ])
    messages.value = mRes.data
    delegations.value = dRes.data
    allDelegates.value = delRes.data
  } catch (e) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  form.value = { visibility: 'private', receiver_id: null, receiver_delegation_id: null, title: '', content: '' }
  createDialogVisible.value = true
}

function showDetail(item) {
  detailItem.value = item
  detailVisible.value = true
}

async function handleCreate() {
  if (!form.value.title || !form.value.content) {
    ElMessage.warning('请输入标题和内容')
    return
  }
  if (form.value.visibility === 'private' && !form.value.receiver_id) {
    ElMessage.warning('请选择接收代表')
    return
  }
  if (form.value.visibility === 'delegation' && !form.value.receiver_delegation_id) {
    ElMessage.warning('请选择接收代表团')
    return
  }
  createLoading.value = true
  try {
    await api.post('/api/staff/async-messages', form.value)
    ElMessage.success('消息已发送')
    createDialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '发送失败')
  } finally {
    createLoading.value = false
  }
}

async function handleDelete(item) {
  await ElMessageBox.confirm('确定撤回此消息？', '提示', { type: 'warning' })
  try {
    await api.delete(`/api/staff/async-messages/${item.id}`)
    ElMessage.success('撤回成功')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '撤回失败')
  }
}

let wsCleanup = null

onMounted(() => {
  loadData()
  // 监听 WebSocket 新消息通知
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
  transition: background 0.2s;
}
.message-item:last-child { border-bottom: none; }
.message-item.unread { background: #f0f9ff; margin: 0 -16px; padding: 16px; border-radius: 4px; }
.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.message-tags { display: flex; gap: 6px; align-items: center; }
.message-title {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  cursor: pointer;
  margin-bottom: 4px;
}
.message-title:hover { color: #409eff; }
.message-meta { color: #909399; font-size: 12px; }
.message-time { color: #909399; font-size: 12px; margin-right: 12px; }
</style>
