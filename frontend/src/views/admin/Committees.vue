<template>
  <div class="animate-fade-in">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>委员会管理</span>
          <el-button type="primary" @click="showAddDialog">创建委员会</el-button>
        </div>
      </template>

      <el-table :data="committees" style="width: 100%">

        <el-table-column prop="name" label="委员会名称" />
        <el-table-column label="侧边栏品牌" min-width="190">
          <template #default="{ row }">
            <div class="brand-preview">
              <img
                v-if="row.logo_image"
                :src="`/api/committee-logo/${row.id}?v=${encodeURIComponent(row.logo_image)}`"
                class="brand-preview-img"
                alt=""
              />
              <span v-else class="brand-preview-badge">{{ row.logo_icon || 'M' }}</span>
              <span class="brand-preview-text">{{ row.display_title || 'MUNITY OS' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="可选功能" min-width="200">
          <template #default="{ row }">
            <div class="features-tags">
              <el-tag v-for="f in row.features" :key="f" class="feature-tag">
                {{ featureLabels[f] || f }}
              </el-tag>
            </div>
            <span v-if="!row.features?.length" style="color: #999">无</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" @click="showCopyDialog(row)">复制</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑委员会对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑委员会' : '创建委员会'" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef">
        <el-form-item label="委员会名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>

        <el-divider content-position="left">侧边栏品牌</el-divider>

        <el-form-item label="标题">
          <el-input v-model="form.display_title" placeholder="留空显示 MUNITY OS" maxlength="20" />
        </el-form-item>
        <el-form-item label="徽标文字">
          <el-input v-model="form.logo_icon" placeholder="留空显示 M" maxlength="2" style="width: 150px" />
          <span class="form-hint">1–2 个字符，可为 emoji；上传图标后此项不生效</span>
        </el-form-item>
        <el-form-item label="图标图片">
          <div class="logo-uploader">
            <img v-if="logoPreview" :src="logoPreview" class="logo-preview" alt="" />
            <span v-else class="logo-preview logo-preview-empty">{{ form.logo_icon || 'M' }}</span>
            <div class="logo-actions">
              <el-upload
                :auto-upload="false"
                :show-file-list="false"
                accept=".png,.jpg,.jpeg,.webp,.gif"
                :on-change="handleLogoChange"
              >
                <el-button size="small">选择图片</el-button>
              </el-upload>
              <el-button v-if="logoPreview" size="small" text type="danger" @click="clearLogo">移除</el-button>
            </div>
          </div>
          <span class="form-hint">支持 png / jpg / webp / gif，2MB 以内</span>
        </el-form-item>

        <el-form-item label="可选功能">
          <div style="color: #909399; font-size: 12px; margin-bottom: 8px">
            点名、动议管理、发言名单、文件管理 默认启用
          </div>
          <div class="features-grid">
            <el-checkbox
              v-for="(label, key) in featureLabels"
              :key="key"
              :label="key"
              v-model="form.features"
              border
              class="feature-item"
            >
              {{ label }}
            </el-checkbox>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 复制委员会对话框 -->
    <el-dialog v-model="copyDialogVisible" title="复制委员会" width="400px">
      <el-form :model="copyForm" :rules="copyRules" ref="copyFormRef">
        <el-form-item label="新委员会名称" prop="name">
          <el-input v-model="copyForm.name" :placeholder="copySourceName + ' - 副本'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="copyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="copyLoading" @click="handleCopy">复制</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const committees = ref([])
const dialogVisible = ref(false)
const copyDialogVisible = ref(false)
const loading = ref(false)
const copyLoading = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)
const copyFormRef = ref(null)
const copySourceId = ref(null)
const copySourceName = ref('')

// 图标改动在点「确定」时统一生效：新选的图片保存后上传，移除则保存后删除
const pendingLogoFile = ref(null)
const pendingLogoUrl = ref('')
const logoRemoved = ref(false)

const form = ref({ name: '', features: [], logo_icon: '', display_title: '', logo_image: null })
const copyForm = ref({ name: '' })
const rules = {
  name: [{ required: true, message: '请输入委员会名称', trigger: 'blur' }]
}
const copyRules = {
  name: [{ required: true, message: '请输入新委员会名称', trigger: 'blur' }]
}

// 优先显示新选的图片，其次显示已保存的图片
const logoPreview = computed(() => {
  if (pendingLogoFile.value) return pendingLogoUrl.value
  if (!logoRemoved.value && isEdit.value && form.value.logo_image && editId.value) {
    return `/api/committee-logo/${editId.value}?v=${encodeURIComponent(form.value.logo_image)}`
  }
  return ''
})

function resetLogoState() {
  if (pendingLogoUrl.value) URL.revokeObjectURL(pendingLogoUrl.value)
  pendingLogoFile.value = null
  pendingLogoUrl.value = ''
  logoRemoved.value = false
}

function handleLogoChange(file) {
  if (pendingLogoUrl.value) URL.revokeObjectURL(pendingLogoUrl.value)
  pendingLogoFile.value = file.raw
  pendingLogoUrl.value = URL.createObjectURL(file.raw)
  logoRemoved.value = false
}

function clearLogo() {
  if (pendingLogoUrl.value) {
    URL.revokeObjectURL(pendingLogoUrl.value)
    pendingLogoUrl.value = ''
  }
  pendingLogoFile.value = null
  // 仅当原本存有图片时才需要真正删除
  logoRemoved.value = !!(isEdit.value && form.value.logo_image)
}

async function applyLogoChanges(committeeId) {
  if (pendingLogoFile.value) {
    const fd = new FormData()
    fd.append('file', pendingLogoFile.value)
    await api.post(`/api/admin/committees/${committeeId}/logo`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  } else if (logoRemoved.value) {
    await api.delete(`/api/admin/committees/${committeeId}/logo`)
  }
}

// 只显示可选功能，默认功能不在这里显示
const featureLabels = {
  agenda: '议程管理',
  directives: '指令管理',
  updates: '局势更新',
  timeline: '时间线'
}

async function loadCommittees() {
  const { data } = await api.get('/api/admin/committees')
  committees.value = data
}

function showAddDialog() {
  isEdit.value = false
  editId.value = null
  resetLogoState()
  form.value = { name: '', features: [], logo_icon: '', display_title: '', logo_image: null }
  dialogVisible.value = true
}

function showEditDialog(committee) {
  isEdit.value = true
  editId.value = committee.id
  resetLogoState()
  form.value = {
    name: committee.name,
    features: [...(committee.features || [])],
    logo_icon: committee.logo_icon || '',
    display_title: committee.display_title || '',
    logo_image: committee.logo_image || null,
  }
  dialogVisible.value = true
}

function showCopyDialog(committee) {
  copySourceId.value = committee.id
  copySourceName.value = committee.name
  copyForm.value = { name: `${committee.name} - 副本` }
  copyDialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    // logo_image 不随本表单提交，由图标接口单独管理
    const payload = {
      name: form.value.name,
      features: form.value.features,
      logo_icon: form.value.logo_icon,
      display_title: form.value.display_title,
    }
    let committeeId = editId.value
    if (isEdit.value) {
      await api.put(`/api/admin/committees/${committeeId}`, payload)
      ElMessage.success('更新成功')
    } else {
      const { data } = await api.post('/api/admin/committees', payload)
      committeeId = data.id
      ElMessage.success('创建成功')
    }
    await applyLogoChanges(committeeId)
    resetLogoState()
    dialogVisible.value = false
    loadCommittees()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    loading.value = false
  }
}

async function handleCopy() {
  await copyFormRef.value.validate()
  copyLoading.value = true
  try {
    await api.post(`/api/admin/committees/${copySourceId.value}/copy`, { name: copyForm.value.name })
    ElMessage.success('复制成功')
    copyDialogVisible.value = false
    loadCommittees()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '复制失败')
  } finally {
    copyLoading.value = false
  }
}

async function handleDelete(committee) {
  await ElMessageBox.confirm('确定删除该委员会？删除后不可恢复。', '提示', { type: 'warning' })
  try {
    await api.delete(`/api/admin/committees/${committee.id}`)
    ElMessage.success('删除成功')
    loadCommittees()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

onMounted(loadCommittees)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.el-table {
  border-radius: 10px;
}

.features-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 4px 0;
}

.feature-item {
  margin: 0 !important;
}

.features-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feature-tag {
  margin: 0 !important;
}

/* ===== 侧边栏品牌 ===== */
.brand-preview {
  display: flex;
  align-items: center;
  gap: 8px;
}
.brand-preview-img {
  width: 24px;
  height: 24px;
  border-radius: 7px;
  object-fit: cover;
  display: block;
}
.brand-preview-badge {
  width: 24px;
  height: 24px;
  border-radius: 7px;
  background: linear-gradient(135deg, #5b92e5, #3d7ed9);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}
.brand-preview-text {
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form-hint {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}

.logo-uploader {
  display: flex;
  align-items: center;
  gap: 12px;
}
.logo-preview {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  object-fit: cover;
  display: block;
  border: 1px solid #ebeef5;
}
.logo-preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #5b92e5, #3d7ed9);
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  overflow: hidden;
}
.logo-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
