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
            <el-tag
              v-for="c in getStaffCommittees(row.id)"
              :key="c.id"
              size="small"
              style="margin: 2px"
            >{{ c.name }}</el-tag>
            <span v-if="getStaffCommittees(row.id).length === 0" style="color: #999">未分配</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220">
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

    <!-- 分配委员会对话框（多选） -->
    <el-dialog v-model="assignDialogVisible" title="分配委员会（可多选）" width="450px">
      <p style="color: #666; margin-bottom: 12px; font-size: 13px;">
        为 <strong>{{ assignTargetName }}</strong> 选择可管理的委员会
      </p>
      <el-select
        v-model="selectedCommitteeIds"
        multiple
        filterable
        placeholder="选择委员会..."
        style="width: 100%"
      >
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
const staffCommitteesMap = ref({})  // { staffId: [{id, name}, ...] }
const addDialogVisible = ref(false)
const assignDialogVisible = ref(false)
const addLoading = ref(false)
const assignLoading = ref(false)
const addFormRef = ref(null)
const selectedStaffId = ref(null)
const assignTargetName = ref('')
const selectedCommitteeIds = ref([])

const addForm = ref({ username: '', password: '' })
const addRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

function getStaffCommittees(staffId) {
  return staffCommitteesMap.value[staffId] || []
}

async function loadStaffCommittees() {
  const map = {}
  // 并行加载每个学团的委员会列表
  const results = await Promise.all(
    staffList.value.map(s =>
      api.get(`/api/admin/staff/${s.id}/committees`).then(r => ({ id: s.id, data: r.data })).catch(() => null)
    )
  )
  for (const r of results) {
    if (r) map[r.id] = r.data || []
  }
  staffCommitteesMap.value = map
}

async function loadData() {
  const [staffRes, committeeRes] = await Promise.all([
    api.get('/api/admin/staff'),
    api.get('/api/admin/committees')
  ])
  staffList.value = staffRes.data
  committees.value = committeeRes.data
  await loadStaffCommittees()
}

function showAddDialog() {
  addForm.value = { username: '', password: '' }
  addDialogVisible.value = true
}

function showAssignDialog(staff) {
  selectedStaffId.value = staff.id
  assignTargetName.value = staff.username
  // 预填已选委员会
  const existing = staffCommitteesMap.value[staff.id] || []
  selectedCommitteeIds.value = existing.map(c => c.id)
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
  if (!selectedCommitteeIds.value || selectedCommitteeIds.value.length === 0) {
    ElMessage.warning('请至少选择一个委员会')
    return
  }
  assignLoading.value = true
  try {
    await api.put(`/api/admin/staff/${selectedStaffId.value}/assign-committees`, {
      committee_ids: selectedCommitteeIds.value
    })
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

.el-table {
  border-radius: 10px;
}
</style>
