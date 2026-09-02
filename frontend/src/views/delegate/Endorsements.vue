<template>
  <div class="animate-fade-in">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>联署审批</span>
          <el-radio-group v-model="activeTab" size="small">
            <el-radio-button value="pending">待审批</el-radio-button>
            <el-radio-button value="my">我的文件</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <!-- 待审批 -->
      <div v-if="activeTab === 'pending'">
        <div v-if="!isLeader" class="not-leader-hint">
          <el-alert title="仅阁首可查看联署审批" type="info" show-icon :closable="false" />
        </div>
        <template v-else>
          <div v-if="loading" style="text-align:center;padding:40px">
            <el-icon class="is-loading" :size="24"><Loading /></el-icon>
            <p style="color:#909399;margin-top:8px">加载中...</p>
          </div>
          <div v-else-if="!pendingEndorsements.length" style="padding:40px 0">
            <el-empty description="暂无待审批的联署请求" :image-size="80" />
          </div>
          <div v-else class="endorsement-list">
            <div v-for="item in pendingEndorsements" :key="item.id" class="endorsement-card">
              <div class="endorsement-header">
                <el-tag size="small">{{ docTypeLabels[item.doc_type] || item.doc_type }}</el-tag>
                <span class="endorsement-from">{{ item.delegation_name }} · {{ item.drafter }}</span>
              </div>
              <div class="endorsement-title" @click="showDetail(item)">{{ item.title }}</div>
              <div class="endorsement-meta" v-if="item.signing_countries?.length">
                签署国家：{{ getDelegationNames(item.signing_countries) }}
              </div>
              <div class="endorsement-preview">{{ truncate(item.content, 120) }}</div>
              <div class="endorsement-actions" v-if="item.status === 'pending'">
                <el-button type="success" size="small" @click="handleReview(item, 'approved')">通过</el-button>
                <el-button type="danger" size="small" @click="handleReview(item, 'rejected')">拒绝</el-button>
                <span class="endorsement-time">{{ formatTime(item.created_at) }}</span>
              </div>
              <div v-else class="endorsement-status">
                <el-tag :type="item.status === 'approved' ? 'success' : 'danger'" size="small" effect="plain">
                  {{ item.status === 'approved' ? '已通过' : '已拒绝' }}{{ item.note ? '：' + item.note : '' }}
                </el-tag>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 我的文件联署状态 -->
      <div v-else>
        <div v-if="loadingMy" style="text-align:center;padding:40px">
          <el-icon class="is-loading" :size="24"><Loading /></el-icon>
          <p style="color:#909399;margin-top:8px">加载中...</p>
        </div>
        <div v-else-if="!myFiles.length" style="padding:40px 0">
          <el-empty description="暂无需要联署的文件" :image-size="80" />
        </div>
        <div v-else class="my-files-list">
          <div v-for="file in myFiles" :key="file.id" class="my-file-card">
            <div class="file-header">
              <el-tag size="small">{{ docTypeLabels[file.doc_type] || file.doc_type }}</el-tag>
              <span class="file-title">{{ file.title }}</span>
            </div>
            <div class="file-endorsements">
              <div v-for="e in file.endorsements" :key="e.delegation_id" class="endorser-row">
                <span class="endorser-name">{{ e.delegation_name }}</span>
                <el-tag v-if="e.status === 'approved'" type="success" size="small" effect="plain">通过</el-tag>
                <el-tag v-else-if="e.status === 'rejected'" type="danger" size="small" effect="plain">拒绝{{ e.note ? '：' + e.note : '' }}</el-tag>
                <el-tag v-else type="warning" size="small" effect="plain">待审批</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" :title="detailItem?.title || '文件详情'" width="600px">
      <div v-if="detailItem">
        <p><strong>来源：</strong>{{ detailItem.delegation_name }}</p>
        <p><strong>起草人：</strong>{{ detailItem.drafter }}</p>
        <p><strong>类型：</strong><el-tag>{{ docTypeLabels[detailItem.doc_type] }}</el-tag></p>
        <p><strong>密级：</strong>{{ detailItem.secrecy === 'secret' ? '秘密' : '公开' }}</p>
        <p v-if="detailItem.signing_countries?.length"><strong>签署国家：</strong>{{ getDelegationNames(detailItem.signing_countries) }}</p>
        <el-divider />
        <div style="white-space: pre-wrap; background: #f5f7fa; padding: 16px; border-radius: 4px">
          {{ detailItem.content || '无内容' }}
        </div>
        <el-button v-if="detailItem.file_path" type="primary" style="margin-top:16px" @click="downloadFile(detailItem.file_path)">
          下载附件
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import api from '../../api'

const activeTab = ref('pending')
const loading = ref(false)
const loadingMy = ref(false)
const pendingEndorsements = ref([])
const myFiles = ref([])
const isLeader = ref(false)
const detailVisible = ref(false)
const detailItem = ref(null)

const docTypeLabels = { declaration: '声明', memorandum: '备忘录', agreement: '协定' }

function getDelegationNames(ids) {
  return ids.map(id => `ID:${id}`).join('、')
}

function truncate(text, len) {
  if (!text) return ''
  return text.length > len ? text.substring(0, len) + '...' : text
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

function showDetail(item) {
  detailItem.value = item
  detailVisible.value = true
}

function downloadFile(filename) {
  const token = localStorage.getItem('token')
  const link = document.createElement('a')
  link.href = `/api/delegate/download/${filename}?token=${token}`
  link.click()
}

async function loadPending() {
  loading.value = true
  try {
    const { data } = await api.get('/api/delegate/endorsements')
    pendingEndorsements.value = data
  } catch (e) {
    if (e.response?.status !== 403) ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadMyFiles() {
  loadingMy.value = true
  try {
    const { data } = await api.get('/api/delegate/endorsements/my-status')
    myFiles.value = data
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loadingMy.value = false
  }
}

async function handleReview(item, status) {
  const action = status === 'approved' ? '通过' : '拒绝'
  const title = `${action}「${item.title}」的联署？`
  try {
    await ElMessageBox.confirm(title, action + '确认', {
      confirmButtonText: action,
      cancelButtonText: '取消',
      type: status === 'approved' ? 'success' : 'warning'
    })
    await api.put(`/api/delegate/endorsements/${item.id}`, { status })
    ElMessage.success(`已${action}`)
    loadPending()
    loadMyFiles()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/api/delegate/me')
    isLeader.value = data.is_leader
  } catch (e) {}
  loadPending()
  loadMyFiles()
})
</script>

<style scoped>
.card-header {
  display: flex; justify-content: space-between; align-items: center;
}
.not-leader-hint { padding: 20px 0; }
.endorsement-list { display: flex; flex-direction: column; gap: 12px; }
.endorsement-card {
  border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; transition: box-shadow 0.15s;
}
.endorsement-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.endorsement-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.endorsement-from { font-size: 12px; color: #94a3b8; }
.endorsement-title { font-size: 16px; font-weight: 600; color: #1e293b; cursor: pointer; margin-bottom: 4px; }
.endorsement-title:hover { color: #5b92e5; }
.endorsement-meta { font-size: 12px; color: #64748b; margin-bottom: 6px; }
.endorsement-preview { font-size: 13px; color: #64748b; margin-bottom: 10px; }
.endorsement-actions { display: flex; align-items: center; gap: 8px; }
.endorsement-time { font-size: 11px; color: #94a3b8; margin-left: auto; }
.endorsement-status { padding-top: 4px; }
.my-files-list { display: flex; flex-direction: column; gap: 12px; }
.my-file-card {
  border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px;
}
.file-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.file-title { font-size: 15px; font-weight: 600; color: #1e293b; }
.file-endorsements { display: flex; flex-direction: column; gap: 8px; }
.endorser-row {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  background: #f8fafc; border-radius: 6px;
}
.endorser-name { font-size: 14px; font-weight: 500; color: #334155; }
</style>
