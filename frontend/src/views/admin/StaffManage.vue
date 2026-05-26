<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>学团管理</span>
          <el-button type="primary" @click="showAddDialog">添加学团</el-button>
        </div>
      </template>

      <el-table :data="staffList" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column label="所属委员会">
          <template #default="{ row }">
            {{ getCommitteeName(row.committee_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="showAssignDialog(row)">分配委员会</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加学团对话框 -->
    <el-dialog v-model="addDialogVisible" title="添加学团" width="400px">
      <el-form :model="addForm" :rules="addRules" ref="addFormRef">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="addForm.username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="addForm.password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addLoading" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分配委员会对话框 -->
    <el-dialog v-model="assignDialogVisible" title="分配委员会" width="400px">
      <el-select v-model="selectedCommitteeId" placeholder="选择委员会" style="width: 100%">
        <el-option
          v-for="c in committees"
          :key="c.id"
          :label="c.name"
          :value="c.id"
        />
      </el-select>
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="assignLoading" @click="handleAssign">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const staffList = ref([])
const committees = ref([])
const addDialogVisible = ref(false)
const assignDialogVisible = ref(false)
const addLoading = ref(false)
const assignLoading = ref(false)
const addFormRef = ref(null)
const selectedStaffId = ref(null)
const selectedCommitteeId = ref(null)

const addForm = ref({ username: '', password: '' })
const addRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

function getCommitteeName(id) {
  const c = committees.value.find(c => c.id === id)
  return c ? c.name : '未分配'
}

async function loadData() {
  const [staffRes, committeeRes] = await Promise.all([
    api.get('/api/admin/staff'),
    api.get('/api/admin/committees')
  ])
  staffList.value = staffRes.data
  committees.value = committeeRes.data
}

function showAddDialog() {
  addForm.value = { username: '', password: '' }
  addDialogVisible.value = true
}

function showAssignDialog(staff) {
  selectedStaffId.value = staff.id
  selectedCommitteeId.value = staff.committee_id
  assignDialogVisible.value = true
}

async function handleAdd() {
  await addFormRef.value.validate()
  addLoading.value = true
  try {
    await api.post('/api/admin/staff', {
      ...addForm.value,
      role: 'staff'
    })
    ElMessage.success('添加成功')
    addDialogVisible.value = false
    loadData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '添加失败')
  } finally {
    addLoading.value = false
  }
}

async function handleAssign() {
  assignLoading.value = true
  try {
    await api.put(`/api/admin/staff/${selectedStaffId.value}/assign/${selectedCommitteeId.value}`)
    ElMessage.success('分配成功')
    assignDialogVisible.value = false
    loadData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '分配失败')
  } finally {
    assignLoading.value = false
  }
}

async function handleDelete(staff) {
  await ElMessageBox.confirm('确定删除该学团账号？', '提示', { type: 'warning' })
  try {
    await api.delete(`/api/admin/staff/${staff.id}`)
    ElMessage.success('删除成功')
    loadData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
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
</style>
