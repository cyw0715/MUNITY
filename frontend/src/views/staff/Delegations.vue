<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>代表团管理</span>
          <div>
            <el-button @click="showBatchDialog">批量导入</el-button>
            <el-button type="primary" @click="showAddDialog">创建代表团</el-button>
          </div>
        </div>
      </template>

      <el-table :data="delegations" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="代表团名称" />
        <el-table-column label="代表人数" width="120">
          <template #default="{ row }">
            {{ getMemberCount(row.id) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建代表团对话框 -->
    <el-dialog v-model="addDialogVisible" title="创建代表团" width="400px">
      <el-form :model="addForm" :rules="addRules" ref="addFormRef">
        <el-form-item label="代表团名称" prop="name">
          <el-input v-model="addForm.name" placeholder="例如：中国、美国、俄罗斯" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addLoading" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <el-dialog v-model="batchDialogVisible" title="批量导入代表团" width="500px">
      <p style="margin-bottom: 12px; color: #909399; font-size: 13px">
        每行一个代表团名称
      </p>
      <el-input
        v-model="batchText"
        type="textarea"
        :rows="10"
        placeholder="中国&#10;美国&#10;俄罗斯&#10;英国&#10;法国"
      />
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchLoading" @click="handleBatchImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const delegations = ref([])
const delegates = ref([])
const addDialogVisible = ref(false)
const batchDialogVisible = ref(false)
const addLoading = ref(false)
const batchLoading = ref(false)
const addFormRef = ref(null)
const batchText = ref('')

const addForm = ref({ name: '' })
const addRules = {
  name: [{ required: true, message: '请输入代表团名称', trigger: 'blur' }]
}

function getMemberCount(delegationId) {
  return delegates.value.filter(d => d.delegation_id === delegationId).length
}

async function loadData() {
  const [dRes, delRes] = await Promise.all([
    api.get('/api/staff/delegations'),
    api.get('/api/staff/delegates')
  ])
  delegations.value = dRes.data
  delegates.value = delRes.data
}

function showAddDialog() {
  addForm.value = { name: '' }
  addDialogVisible.value = true
}

function showBatchDialog() {
  batchText.value = ''
  batchDialogVisible.value = true
}

async function handleAdd() {
  await addFormRef.value.validate()
  addLoading.value = true
  try {
    await api.post('/api/staff/delegations', addForm.value)
    ElMessage.success('创建成功')
    addDialogVisible.value = false
    loadData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建失败')
  } finally {
    addLoading.value = false
  }
}

async function handleDelete(delegation) {
  await ElMessageBox.confirm('确定删除该代表团？', '提示', { type: 'warning' })
  try {
    await api.delete(`/api/staff/delegations/${delegation.id}`)
    ElMessage.success('删除成功')
    loadData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

async function handleBatchImport() {
  const lines = batchText.value.trim().split('\n').filter(l => l.trim())
  if (!lines.length) {
    ElMessage.warning('请输入要导入的代表团')
    return
  }

  let success = 0
  let fail = 0
  const errors = []

  batchLoading.value = true
  for (const line of lines) {
    const name = line.trim()
    if (!name) continue
    try {
      await api.post('/api/staff/delegations', { name })
      success++
    } catch (err) {
      errors.push(`${name}: ${err.response?.data?.detail || '导入失败'}`)
      fail++
    }
  }

  batchLoading.value = false
  batchDialogVisible.value = false

  if (fail === 0) {
    ElMessage.success(`全部导入成功，共 ${success} 个`)
  } else {
    ElMessage({
      message: `成功 ${success} 个，失败 ${fail} 个：${errors.join('；')}`,
      type: 'warning',
      duration: 8000
    })
  }
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
