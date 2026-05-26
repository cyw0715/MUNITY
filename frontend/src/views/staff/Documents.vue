<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>文件管理</span>
          <div style="display: flex; align-items: center; gap: 8px">
            <el-input
              v-model="keyword"
              placeholder="搜索文件（标题、正文、附件内容）"
              clearable
              style="width: 280px"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button type="primary" @click="showCreateDialog">发布新文件</el-button>
          </div>
        </div>
      </template>

      <el-table :data="documents" style="width: 100%" stripe>
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="delegation_name" label="来源代表团" width="140" />
        <el-table-column prop="drafter" label="起草人" width="120" />
        <el-table-column prop="doc_type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ docTypeLabels[row.doc_type] || row.doc_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
        <el-table-column label="签署国家" min-width="140">
          <template #default="{ row }">
            <template v-if="row.doc_type === 'agreement'">
              <el-tag v-for="name in row.signing_country_names" :key="name" size="small" style="margin-right: 4px">
                {{ name }}
              </el-tag>
            </template>
            <span v-else style="color: #999">-</span>
          </template>
        </el-table-column>
        <el-table-column label="密级" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.doc_type === 'agreement'" :type="row.secrecy === 'secret' ? 'danger' : 'success'" size="small">
              {{ row.secrecy === 'secret' ? '秘密' : '公开' }}
            </el-tag>
            <span v-else style="color: #999">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.recalled" type="danger" size="small">已撤回</el-tag>
            <el-tag v-else-if="row.published" type="success" size="small">已发布</el-tag>
            <el-tag v-else type="info" size="small">未发布</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">查看</el-button>
            <el-button v-if="row.file_path" size="small" type="primary" @click="downloadFile(row.file_path)">下载</el-button>
            <template v-if="row.recalled">
              <el-button size="small" type="success" @click="handleRestore(row)">恢复</el-button>
            </template>
            <template v-else>
              <template v-if="!row.published">
                <el-tooltip
                  v-if="row.doc_type === 'agreement' && row.secrecy === 'secret'"
                  content="秘密协定不能发布"
                  placement="top"
                >
                  <el-button size="small" type="success" disabled>发布</el-button>
                </el-tooltip>
                <el-button v-else size="small" type="success" @click="showPublishDialog(row)">发布</el-button>
              </template>
              <el-button size="small" type="danger" @click="handleRecall(row)">撤回</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!documents.length" description="暂无文件" />
    </el-card>

    <!-- 发布新文件对话框 -->
    <el-dialog v-model="createDialogVisible" title="发布新文件" width="600px">
      <el-form :model="createForm">
        <el-form-item label="标题" required>
          <el-input v-model="createForm.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="createForm.content" type="textarea" :rows="6" />
        </el-form-item>
        <el-form-item label="附件">
          <el-upload
            ref="createUploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".docx"
            :on-change="handleCreateFileChange"
            :on-remove="() => createSelectedFile = null"
          >
            <el-button size="small">选择文件</el-button>
            <template #tip>
              <div style="color: #909399; font-size: 12px">可选，只能上传 .docx 文件</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">发布</el-button>
      </template>
    </el-dialog>

    <!-- 文件详情 -->
    <el-dialog v-model="detailVisible" title="文件详情" width="600px">
      <div v-if="detailItem">
        <p><strong>来源：</strong>{{ detailItem.delegation_name }}</p>
        <p><strong>起草人：</strong>{{ detailItem.drafter }}</p>
        <p><strong>类型：</strong>
          <el-tag>{{ docTypeLabels[detailItem.doc_type] || detailItem.doc_type }}</el-tag>
          <el-tag v-if="detailItem.published" type="success" style="margin-left: 8px">已发布</el-tag>
        </p>
        <p><strong>标题：</strong>{{ detailItem.title }}</p>
        <template v-if="detailItem.doc_type === 'agreement'">
          <p><strong>签署国家：</strong>{{ detailItem.signing_country_names?.join('、') || '无' }}</p>
          <p><strong>密级：</strong>{{ detailItem.secrecy === 'secret' ? '秘密' : '公开' }}</p>
        </template>
        <el-divider />
        <div style="white-space: pre-wrap; background: #f5f7fa; padding: 16px; border-radius: 4px">
          {{ detailItem.content || '无内容' }}
        </div>
        <el-button v-if="detailItem.file_path" type="primary" style="margin-top: 16px" @click="downloadFile(detailItem.file_path)">
          下载附件
        </el-button>
      </div>
    </el-dialog>

    <!-- 发布对话框 -->
    <el-dialog v-model="publishDialogVisible" title="发布文件" width="600px">
      <div v-if="publishItem">
        <p style="margin-bottom: 16px">
          <strong>发布文件：</strong>{{ publishItem.title }}
          <el-tag size="small" style="margin-left: 8px">{{ docTypeLabels[publishItem.doc_type] }}</el-tag>
        </p>
      </div>

      <el-form>
        <el-form-item label="可见代表">
          <div style="width: 100%">
            <div v-if="selectedDelegations.length" style="margin-bottom: 8px">
              <el-tag
                v-for="dId in selectedDelegations"
                :key="dId"
                closable
                @close="removeDelegation(dId)"
                style="margin-right: 8px; margin-bottom: 4px"
              >
                {{ getDelegationName(dId) }}
              </el-tag>
            </div>
            <el-select
              v-model="currentDelegationId"
              placeholder="选择代表团添加"
              clearable
              style="width: 100%; margin-bottom: 8px"
              @change="addDelegation"
            >
              <el-option
                v-for="d in availableDelegations"
                :key="d.id"
                :label="d.name"
                :value="d.id"
              />
            </el-select>
            <el-select
              v-model="selectedVisibility"
              multiple
              placeholder="留空则所有人可见"
              style="width: 100%"
              :disabled="!selectedDelegations.length"
            >
              <el-option-group
                v-for="dId in selectedDelegations"
                :key="dId"
                :label="getDelegationName(dId)"
              >
                <el-option
                  v-for="m in getDelegationMembers(dId)"
                  :key="m.id"
                  :label="m.username + (m.is_leader ? ' (阁首)' : '')"
                  :value="m.id"
                />
              </el-option-group>
            </el-select>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="publishDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="publishLoading" @click="handlePublish">发布</el-button>
      </template>
    </el-dialog>

    <!-- 搜索结果对话框 -->
    <el-dialog v-model="searchDialogVisible" title="搜索结果" width="700px">
      <el-table :data="searchResults" style="width: 100%" stripe @row-click="showSearchDetail">
        <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
        <el-table-column prop="delegation_name" label="来源代表团" width="140" />
        <el-table-column prop="drafter" label="起草人" width="120" />
        <el-table-column prop="doc_type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ docTypeLabels[row.doc_type] || row.doc_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="内容预览" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.content?.substring(0, 100) || '无内容' }}{{ row.content?.length > 100 ? '...' : '' }}
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!searchResults.length" description="未找到匹配的文件" />
      <template #footer>
        <el-button @click="searchDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import api from '../../api'

const keyword = ref('')
const documents = ref([])
const delegations = ref([])
const allDelegates = ref([])

const detailVisible = ref(false)
const detailItem = ref(null)
const publishDialogVisible = ref(false)
const publishItem = ref(null)
const publishLoading = ref(false)
const selectedDelegations = ref([])
const currentDelegationId = ref(null)
const selectedVisibility = ref([])

const createDialogVisible = ref(false)
const createLoading = ref(false)
const createUploadRef = ref(null)
const createSelectedFile = ref(null)
const createForm = ref({
  title: '',
  content: ''
})

const searchResults = ref([])
const searchDialogVisible = ref(false)

const docTypeLabels = { declaration: '声明', memorandum: '备忘录', agreement: '协定' }

const availableDelegations = computed(() => {
  return delegations.value.filter(d => !selectedDelegations.value.includes(d.id))
})

function getDelegationName(id) {
  const d = delegations.value.find(d => d.id === id)
  return d ? d.name : '未知'
}

function getDelegationMembers(delegationId) {
  return allDelegates.value.filter(d => d.delegation_id === delegationId)
}

function addDelegation(dId) {
  if (dId && !selectedDelegations.value.includes(dId)) {
    selectedDelegations.value.push(dId)
  }
  currentDelegationId.value = null
}

function removeDelegation(dId) {
  selectedDelegations.value = selectedDelegations.value.filter(id => id !== dId)
  const memberIds = allDelegates.value.filter(d => d.delegation_id === dId).map(d => d.id)
  selectedVisibility.value = selectedVisibility.value.filter(id => !memberIds.includes(id))
}

async function loadData() {
  try {
    const [docRes, dRes, delRes] = await Promise.all([
      api.get('/api/staff/documents'),
      api.get('/api/staff/delegations'),
      api.get('/api/staff/delegates')
    ])
    documents.value = docRes.data
    delegations.value = dRes.data
    allDelegates.value = delRes.data
  } catch (e) {}
}

async function handleSearch() {
  if (!keyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  try {
    const res = await api.get('/api/staff/documents?keyword=' + encodeURIComponent(keyword.value))
    searchResults.value = res.data
    searchDialogVisible.value = true
  } catch (e) {
    ElMessage.error('搜索失败')
  }
}

function showSearchDetail(row) {
  detailItem.value = row
  detailVisible.value = true
  searchDialogVisible.value = false
}

function showDetail(item) {
  detailItem.value = item
  detailVisible.value = true
}

function showCreateDialog() {
  createForm.value = { title: '', content: '' }
  createSelectedFile.value = null
  createDialogVisible.value = true
}

function handleCreateFileChange(file) {
  createSelectedFile.value = file.raw
}

function downloadFile(filename) {
  const token = localStorage.getItem('token')
  const link = document.createElement('a')
  link.href = `/api/staff/download/${filename}?token=${token}`
  link.download = filename
  link.click()
}

async function handleCreate() {
  if (!createForm.value.title) {
    ElMessage.warning('请输入标题')
    return
  }
  createLoading.value = true
  try {
    const formData = new FormData()
    formData.append('title', createForm.value.title)
    formData.append('content', createForm.value.content || '')
    if (createSelectedFile.value) {
      formData.append('file', createSelectedFile.value)
    }
    await api.post('/api/staff/publish-with-file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('发布成功')
    createDialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '发布失败')
  } finally {
    createLoading.value = false
  }
}

function showPublishDialog(item) {
  publishItem.value = item
  selectedDelegations.value = []
  currentDelegationId.value = null
  selectedVisibility.value = []
  publishDialogVisible.value = true
}

async function handlePublish() {
  publishLoading.value = true
  try {
    await api.post(`/api/staff/documents/${publishItem.value.id}/publish`, {
      visibility: selectedVisibility.value
    })
    ElMessage.success('发布成功')
    publishDialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '发布失败')
  } finally {
    publishLoading.value = false
  }
}

async function handleRecall(item) {
  await ElMessageBox.confirm('确定撤回该文件？撤回后代表将无法看到。', '提示', { type: 'warning' })
  try {
    await api.put(`/api/staff/documents/${item.id}/recall`)
    ElMessage.success('撤回成功')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '撤回失败')
  }
}

async function handleRestore(item) {
  await ElMessageBox.confirm('确定恢复该文件？恢复后代表将可以看到。', '提示', { type: 'info' })
  try {
    await api.put(`/api/staff/documents/${item.id}/restore`)
    ElMessage.success('恢复成功')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '恢复失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
:deep(.el-card) {
  margin-bottom: 20px;
}
:deep(.el-card__header) {
  padding: 16px 20px;
}
:deep(.el-card__body) {
  padding: 20px;
}
:deep(.el-table) {
  margin-top: 8px;
}
:deep(.el-table th) {
  background-color: #f5f7fa;
}
:deep(.el-table .cell) {
  padding: 8px 12px;
}
</style>

