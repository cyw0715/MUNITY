<template>
  <div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="提交指令" name="directive">
        <el-card>
          <el-form :model="directiveForm" :rules="directiveRules" ref="directiveFormRef">
            <el-form-item label="起草人" prop="drafter">
              <el-input v-model="directiveForm.drafter" :placeholder="userInfo?.username" />
            </el-form-item>
            <el-form-item label="行政点数" prop="admin_points">
              <el-input-number v-model="directiveForm.admin_points" :min="0" />
              <span style="margin-left: 12px; color: #909399">
                公开至少1点，秘密至少2点
              </span>
            </el-form-item>
            <el-form-item label="密级" prop="secrecy">
              <el-radio-group v-model="directiveForm.secrecy">
                <el-radio value="public">公开</el-radio>
                <el-radio value="secret">秘密</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="涉及部门" prop="departments" required>
              <el-checkbox-group v-model="directiveForm.departments">
                <el-checkbox v-for="dept in departmentOptions" :key="dept" :value="dept">{{ dept }}</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-form-item v-if="directiveForm.departments.includes('其他')" label="其他部门">
              <el-input v-model="directiveForm.otherDepartment" placeholder="请输入部门名称" />
            </el-form-item>
            <el-form-item label="内容" prop="content">
              <el-input v-model="directiveForm.content" type="textarea" :rows="6" />
            </el-form-item>
            <el-button type="primary" :loading="loading" @click="submitDirective">提交指令</el-button>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="提交文件" name="document">
        <el-card>
          <el-form :model="documentForm" :rules="documentRules" ref="documentFormRef">
            <el-form-item label="起草人" prop="drafter">
              <el-input v-model="documentForm.drafter" :placeholder="userInfo?.username" />
            </el-form-item>
            <el-form-item label="文件类型" prop="doc_type">
              <el-select v-model="documentForm.doc_type" style="width: 100%" @change="onDocTypeChange">
                <el-option label="声明" value="declaration" />
                <el-option label="备忘录" value="memorandum" />
                <el-option label="协定" value="agreement" :disabled="!userInfo?.is_leader" />
              </el-select>
              <span v-if="!userInfo?.is_leader" style="color: #f56c6c; font-size: 12px; margin-left: 8px">
                只有阁首才能提交协定
              </span>
            </el-form-item>

            <!-- 协定专属字段 -->
            <template v-if="documentForm.doc_type === 'agreement'">
              <el-form-item label="签署国家" prop="signing_countries">
                <el-select v-model="documentForm.signing_countries" multiple placeholder="选择签署国家" style="width: 100%">
                  <el-option v-for="d in allDelegations" :key="d.id" :label="d.name" :value="d.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="密级" prop="secrecy">
                <el-radio-group v-model="documentForm.secrecy">
                  <el-radio value="public">公开</el-radio>
                  <el-radio value="secret">秘密</el-radio>
                </el-radio-group>
              </el-form-item>
            </template>

            <el-form-item label="标题" prop="title">
              <el-input v-model="documentForm.title" />
            </el-form-item>
            <el-form-item label="内容" prop="content">
              <el-input v-model="documentForm.content" type="textarea" :rows="6" />
            </el-form-item>
            <el-form-item label="附件">
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :limit="1"
                accept=".docx"
                :on-change="handleFileChange"
                :on-remove="() => selectedFile = null"
              >
                <el-button size="small">选择文件</el-button>
                <template #tip>
                  <div style="color: #909399; font-size: 12px">可选，只能上传 .docx 文件</div>
                </template>
              </el-upload>
            </el-form-item>
            <el-button type="primary" :loading="loading" @click="submitDocument">提交文件</el-button>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 我的提交历史 -->
    <el-card style="margin-top: 16px">
      <template #header>
        <div class="card-header">
          <span>我的提交记录</span>
          <el-radio-group v-model="recordFilter" size="small">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="directive">指令</el-radio-button>
            <el-radio-button value="document">文件</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <el-table :data="filteredRecords" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row._type === 'directive' ? 'warning' : 'success'" size="small">
              {{ row._type === 'directive' ? '指令' : docTypeLabels[row.doc_type] || '文件' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="drafter" label="起草人" width="120" />
        <el-table-column prop="title" label="标题" min-width="150" show-overflow-tooltip />
        <el-table-column label="密级" width="80">
          <template #default="{ row }">
            <el-tag :type="row.secrecy === 'secret' ? 'danger' : 'success'" size="small">
              {{ row.secrecy === 'secret' ? '秘密' : '公开' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag v-if="row._type === 'directive'" :type="statusColors[row.status] || 'info'" size="small">
              {{ statusLabels[row.status] || row.status }}
            </el-tag>
            <el-tag v-else type="info" size="small">已提交</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button v-if="row._type === 'document'" type="primary" link size="small" @click="showDocumentDetail(row)">
              查看
            </el-button>
            <el-button v-if="row.file_path" type="success" link size="small" @click="downloadFile(row.file_path)">
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!filteredRecords.length" description="暂无提交记录" />
    </el-card>

    <!-- 文件详情对话框 -->
    <el-dialog v-model="detailVisible" :title="detailDoc?.title || '文件详情'" width="600px">
      <div v-if="detailDoc" class="doc-detail">
        <div class="detail-item">
          <span class="detail-label">类型：</span>
          <el-tag>{{ docTypeLabels[detailDoc.doc_type] || detailDoc.doc_type }}</el-tag>
        </div>
        <div class="detail-item">
          <span class="detail-label">起草人：</span>
          <span>{{ detailDoc.drafter }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">密级：</span>
          <el-tag :type="detailDoc.secrecy === 'secret' ? 'danger' : 'success'">
            {{ detailDoc.secrecy === 'secret' ? '秘密' : '公开' }}
          </el-tag>
        </div>
        <div v-if="detailDoc.doc_type === 'agreement' && detailDoc.signing_countries?.length" class="detail-item">
          <span class="detail-label">签署国家：</span>
          <span>{{ getSigningCountryNames(detailDoc.signing_countries) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">提交时间：</span>
          <span>{{ new Date(detailDoc.created_at).toLocaleString('zh-CN') }}</span>
        </div>
        <el-divider />
        <div class="doc-content">{{ detailDoc.content }}</div>
        <el-button v-if="detailDoc.file_path" type="primary" style="margin-top: 16px" @click="downloadFile(detailDoc.file_path)">
          下载附件
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api'

const activeTab = ref('directive')
const loading = ref(false)
const directiveFormRef = ref(null)
const documentFormRef = ref(null)
const uploadRef = ref(null)
const userInfo = ref(null)
const myDirectives = ref([])
const myDocuments = ref([])
const allDelegations = ref([])
const recordFilter = ref('all')
const detailVisible = ref(false)
const detailDoc = ref(null)
const selectedFile = ref(null)

const statusLabels = {
  unread: '未读',
  no_simulate: '不推演',
  pending_simulate: '未推演',
  simulated: '已推演'
}

const statusColors = {
  unread: 'info',
  no_simulate: 'danger',
  pending_simulate: 'warning',
  simulated: 'success'
}

const docTypeLabels = {
  declaration: '声明',
  memorandum: '备忘录',
  agreement: '协定'
}

const departmentOptions = ['政治', '经济', '宣传', '军事', '其他']

const directiveForm = ref({
  drafter: '',
  admin_points: 0,
  secrecy: 'public',
  content: '',
  departments: [],
  otherDepartment: ''
})

const documentForm = ref({
  drafter: '',
  doc_type: 'declaration',
  title: '',
  content: '',
  signing_countries: [],
  secrecy: 'public'
})

const directiveRules = {
  admin_points: [{ required: true, message: '请输入行政点数', trigger: 'blur' }]
}

const documentRules = {
  doc_type: [{ required: true, message: '请选择文件类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }]
}

// 合并指令和文件记录，按时间排序
const filteredRecords = computed(() => {
  const directives = myDirectives.value.map(d => ({ ...d, _type: 'directive' }))
  const documents = myDocuments.value.map(d => ({ ...d, _type: 'document' }))
  let all = [...directives, ...documents].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  
  if (recordFilter.value === 'directive') {
    all = all.filter(r => r._type === 'directive')
  } else if (recordFilter.value === 'document') {
    all = all.filter(r => r._type === 'document')
  }
  
  return all
})

function getSigningCountryNames(ids) {
  return ids.map(id => {
    const d = allDelegations.value.find(del => del.id === id)
    return d?.name || `ID:${id}`
  }).join('、')
}

function onDocTypeChange() {
  documentForm.value.signing_countries = []
  documentForm.value.secrecy = 'public'
}

function showDocumentDetail(doc) {
  detailDoc.value = doc
  detailVisible.value = true
}

async function loadData() {
  try {
    const [meRes, dRes, docRes, delRes] = await Promise.all([
      api.get('/api/delegate/me'),
      api.get('/api/delegate/directives'),
      api.get('/api/delegate/documents'),
      api.get('/api/delegate/delegations').catch(() => ({ data: [] }))
    ])
    userInfo.value = meRes.data
    myDirectives.value = dRes.data
    myDocuments.value = docRes.data
    allDelegations.value = delRes.data
  } catch (e) {}
}

async function submitDirective() {
  loading.value = true
  try {
    const payload = {
      drafter: directiveForm.value.drafter || userInfo.value?.username || '',
      admin_points: directiveForm.value.admin_points,
      secrecy: directiveForm.value.secrecy,
      content: directiveForm.value.content,
      departments: directiveForm.value.departments.map(d => {
        if (d === '其他' && directiveForm.value.otherDepartment) {
          return directiveForm.value.otherDepartment
        }
        return d
      })
    }
    await api.post('/api/delegate/directives', payload)
    ElMessage.success('指令提交成功')
    directiveForm.value = { drafter: '', admin_points: 0, secrecy: 'public', content: '', departments: [], otherDepartment: '' }
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    loading.value = false
  }
}

function handleFileChange(file) {
  selectedFile.value = file.raw
}

async function submitDocument() {
  await documentFormRef.value.validate()
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('drafter', documentForm.value.drafter || userInfo.value?.username || '')
    formData.append('doc_type', documentForm.value.doc_type)
    formData.append('title', documentForm.value.title)
    formData.append('content', documentForm.value.content || '')
    formData.append('secrecy', documentForm.value.secrecy)
    if (documentForm.value.signing_countries?.length) {
      formData.append('signing_countries', JSON.stringify(documentForm.value.signing_countries))
    }
    if (selectedFile.value) {
      formData.append('file', selectedFile.value)
    }
    
    await api.post('/api/delegate/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('文件提交成功')
    documentForm.value = { drafter: '', doc_type: 'declaration', title: '', content: '', signing_countries: [], secrecy: 'public' }
    selectedFile.value = null
    if (uploadRef.value) uploadRef.value.clearFiles()
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    loading.value = false
  }
}

function downloadFile(filename) {
  const token = localStorage.getItem('token')
  const link = document.createElement('a')
  link.href = `/api/delegate/download/${filename}?token=${token}`
  link.download = filename
  link.click()
}

onMounted(loadData)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.doc-detail {
  line-height: 1.8;
}
.detail-item {
  margin-bottom: 12px;
}
.detail-label {
  color: #909399;
  margin-right: 8px;
}
.doc-content {
  white-space: pre-wrap;
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
}
</style>
