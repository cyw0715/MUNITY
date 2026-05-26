<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>委员会管理</span>
          <el-button type="primary" @click="showAddDialog">创建委员会</el-button>
        </div>
      </template>

      <el-table :data="committees" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="委员会名称" />
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
import { ref, onMounted } from 'vue'
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

const form = ref({ name: '', features: [] })
const copyForm = ref({ name: '' })
const rules = {
  name: [{ required: true, message: '请输入委员会名称', trigger: 'blur' }]
}
const copyRules = {
  name: [{ required: true, message: '请输入新委员会名称', trigger: 'blur' }]
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
  form.value = { name: '', features: [] }
  dialogVisible.value = true
}

function showEditDialog(committee) {
  isEdit.value = true
  editId.value = committee.id
  form.value = { name: committee.name, features: [...(committee.features || [])] }
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
    if (isEdit.value) {
      await api.put(`/api/admin/committees/${editId.value}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/api/admin/committees', form.value)
      ElMessage.success('创建成功')
    }
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

.features-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 20px;
  justify-content: center;
  padding: 16px 0;
  line-height: 2;
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
</style>
