<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>代表管理</span>
          <div>
            <el-tooltip :content="delegations.length === 0 ? '请先创建代表团' : ''" :disabled="delegations.length > 0">
              <el-button @click="showBatchDialog" :disabled="delegations.length === 0">批量导入</el-button>
            </el-tooltip>
            <el-tooltip :content="delegations.length === 0 ? '请先创建代表团' : ''" :disabled="delegations.length > 0">
              <el-button type="primary" @click="showAddDialog" :disabled="delegations.length === 0">添加代表</el-button>
            </el-tooltip>
          </div>
        </div>
      </template>

      <el-table :data="delegates" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="账号" width="120" />
        <el-table-column label="席位" min-width="120">
          <template #default="{ row }">
            <span>{{ row.seat || getDelegationName(row.delegation_id) || '未分配' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="代表团" width="120">
          <template #default="{ row }">
            {{ getDelegationName(row.delegation_id) }}
          </template>
        </el-table-column>
        <el-table-column label="阁首" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_leader ? 'success' : 'info'" size="small">
              {{ row.is_leader ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="380">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" @click="showEditSeatDialog(row)">编辑席位</el-button>
              <el-button size="small" @click="showAssignDialog(row)">分配代表团</el-button>
              <el-button size="small" :type="row.is_leader ? 'warning' : 'success'" @click="toggleLeader(row)">
                {{ row.is_leader ? '取消阁首' : '设为阁首' }}
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加代表对话框 -->
    <el-dialog v-model="addDialogVisible" title="添加代表" width="400px">
      <el-form :model="addForm" :rules="addRules" ref="addFormRef">
        <el-form-item label="账号" prop="username">
          <el-input v-model="addForm.username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="addForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="席位" prop="seat">
          <el-input v-model="addForm.seat" />
        </el-form-item>
        <el-form-item label="代表团">
          <el-select v-model="addForm.delegation_id" placeholder="选择代表团（可选）" clearable style="width: 100%">
            <el-option v-for="d in delegations" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否阁首">
          <el-switch v-model="addForm.is_leader" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addLoading" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑席位对话框 -->
    <el-dialog v-model="editSeatDialogVisible" title="编辑席位" width="400px">
      <el-form>
        <el-form-item label="当前账号">
          <el-input :model-value="editSeatDelegate?.username" disabled />
        </el-form-item>
        <el-form-item label="席位">
          <el-input v-model="editSeatValue" placeholder="如：中国代表1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editSeatDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSeatLoading" @click="handleEditSeat">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分配代表团对话框 -->
    <el-dialog v-model="assignDialogVisible" title="分配代表团" width="400px">
      <el-select v-model="selectedDelegationId" placeholder="选择代表团" style="width: 100%">
        <el-option v-for="d in delegations" :key="d.id" :label="d.name" :value="d.id" />
      </el-select>
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="assignLoading" @click="handleAssign">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <el-dialog v-model="batchDialogVisible" title="批量导入代表" width="500px">
      <p style="margin-bottom: 12px; color: #909399; font-size: 13px">
        每行一个用户，格式：<code>账号 密码 席位 代表团</code>（空格分隔，代表团可选）
      </p>
      <el-input
        v-model="batchText"
        type="textarea"
        :rows="10"
        placeholder="user1 pass123 中国代表1 中国&#10;user2 pass456 美国代表1 美国&#10;user3 pass789 英国代表1 英国"
      />
      <el-form style="margin-top: 12px">
        <el-form-item label="默认代表团">
          <el-select v-model="batchDelegationId" placeholder="未指定代表团时使用（可选）" clearable style="width: 100%">
            <el-option v-for="d in delegations" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
      </el-form>
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

const delegates = ref([])
const delegations = ref([])
const addDialogVisible = ref(false)
const editSeatDialogVisible = ref(false)
const assignDialogVisible = ref(false)
const batchDialogVisible = ref(false)
const addLoading = ref(false)
const editSeatLoading = ref(false)
const assignLoading = ref(false)
const batchLoading = ref(false)
const addFormRef = ref(null)
const selectedDelegateId = ref(null)
const selectedDelegationId = ref(null)
const editSeatDelegate = ref(null)
const editSeatValue = ref('')
const batchText = ref('')
const batchDelegationId = ref(null)

const addForm = ref({ username: '', password: '', seat: '', delegation_id: null, is_leader: false })
const addRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  seat: [{ required: true, message: '请输入席位', trigger: 'blur' }]
}

function getDelegationName(id) {
  const d = delegations.value.find(d => d.id === id)
  return d ? d.name : '未分配'
}

async function loadData() {
  const [dRes, delRes] = await Promise.all([
    api.get('/api/staff/delegates'),
    api.get('/api/staff/delegations')
  ])
  delegates.value = dRes.data
  delegations.value = delRes.data
}

function showAddDialog() {
  addForm.value = { username: '', password: '', seat: '', delegation_id: null, is_leader: false }
  addDialogVisible.value = true
}

function showEditSeatDialog(delegate) {
  editSeatDelegate.value = delegate
  editSeatValue.value = delegate.seat || ''
  editSeatDialogVisible.value = true
}

function showAssignDialog(delegate) {
  selectedDelegateId.value = delegate.id
  selectedDelegationId.value = delegate.delegation_id
  assignDialogVisible.value = true
}

function showBatchDialog() {
  batchText.value = ''
  batchDelegationId.value = null
  batchDialogVisible.value = true
}

async function handleAdd() {
  await addFormRef.value.validate()
  addLoading.value = true
  try {
    await api.post('/api/staff/delegates', addForm.value)
    ElMessage.success('添加成功')
    addDialogVisible.value = false
    loadData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '添加失败')
  } finally {
    addLoading.value = false
  }
}

async function handleEditSeat() {
  editSeatLoading.value = true
  try {
    await api.put(`/api/staff/delegates/${editSeatDelegate.value.id}/seat`, { seat: editSeatValue.value })
    ElMessage.success('修改成功')
    editSeatDialogVisible.value = false
    loadData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '修改失败')
  } finally {
    editSeatLoading.value = false
  }
}

async function handleAssign() {
  assignLoading.value = true
  try {
    await api.put(`/api/staff/delegates/${selectedDelegateId.value}/assign/${selectedDelegationId.value}`)
    ElMessage.success('分配成功')
    assignDialogVisible.value = false
    loadData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '分配失败')
  } finally {
    assignLoading.value = false
  }
}

async function toggleLeader(delegate) {
  try {
    await api.put(`/api/staff/delegates/${delegate.id}/leader?is_leader=${!delegate.is_leader}`)
    ElMessage.success('设置成功')
    loadData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '设置失败')
  }
}

async function handleDelete(delegate) {
  await ElMessageBox.confirm('确定删除该代表？', '提示', { type: 'warning' })
  try {
    await api.delete(`/api/staff/delegates/${delegate.id}`)
    ElMessage.success('删除成功')
    loadData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

async function handleBatchImport() {
  const lines = batchText.value.trim().split('\n').filter(l => l.trim())
  if (!lines.length) {
    ElMessage.warning('请输入要导入的用户')
    return
  }

  let success = 0
  let fail = 0
  const errors = []

  batchLoading.value = true
  for (const line of lines) {
    const parts = line.trim().split(/\s+/)
    if (parts.length < 3) {
      errors.push(`${line}: 格式错误（需要 账号 密码 席位 [代表团]）`)
      fail++
      continue
    }
    const [username, password, seat, delegationName] = parts
    
    // 查找代表团ID
    let delegationId = batchDelegationId.value
    if (delegationName) {
      const delegation = delegations.value.find(d => d.name === delegationName)
      if (delegation) {
        delegationId = delegation.id
      } else {
        errors.push(`${username}: 代表团"${delegationName}"不存在`)
        fail++
        continue
      }
    }
    
    try {
      await api.post('/api/staff/delegates', {
        username,
        password,
        seat,
        delegation_id: delegationId,
        is_leader: false
      })
      success++
    } catch (err) {
      errors.push(`${username}: ${err.response?.data?.detail || '导入失败'}`)
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
code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-size: 12px; }
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
