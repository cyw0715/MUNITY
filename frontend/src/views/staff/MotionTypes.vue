<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>动议类型管理</span>
          <el-button type="primary" @click="showAddDialog">添加自定义类型</el-button>
        </div>
      </template>

      <div class="builtin-info">
        <el-alert title="内置动议类型始终可用" type="info" :closable="false" show-icon>
          <template #default>
            <el-tag size="small" class="builtin-tag">有主持核心磋商</el-tag>
            <el-tag size="small" class="builtin-tag">自由辩论</el-tag>
            <el-tag size="small" class="builtin-tag">自由磋商</el-tag>
            <el-tag size="small" class="builtin-tag">轮席发言</el-tag>
          </template>
        </el-alert>
      </div>

      <el-table :data="motionTypes" style="width: 100%">
        <el-table-column prop="name" label="类型名称" min-width="160" />
        <el-table-column label="配置" min-width="300">
          <template #default="{ row }">
            <el-tag v-if="row.need_speakers_list" type="success" size="small" style="margin-right: 4px">发言名单</el-tag>
            <el-tag v-else type="info" size="small" style="margin-right: 4px">无发言名单</el-tag>
            <el-tag v-if="row.need_unit_duration" type="warning" size="small" style="margin-right: 4px">单位时长</el-tag>
            <el-tag v-else type="info" size="small" style="margin-right: 4px">无单位时长</el-tag>
            <el-tag v-if="row.need_total_duration" type="danger" size="small" style="margin-right: 4px">总时长</el-tag>
            <el-tag v-else type="info" size="small" style="margin-right: 4px">无总时长</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="默认值" width="200">
          <template #default="{ row }">
            <span v-if="row.default_unit_duration" style="margin-right: 8px; color: #606266">单位: {{ row.default_unit_duration }}s</span>
            <span v-if="row.default_total_duration" style="color: #606266">总计: {{ row.default_total_duration }}s</span>
            <span v-if="!row.default_unit_duration && !row.default_total_duration" style="color: #c0c4cc">无</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row, $index }">
            <el-button size="small" @click="showEditDialog(row, $index)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editIndex === null ? '添加动议类型' : '编辑动议类型'" width="500px">
      <el-form :model="form" label-position="top">
        <el-form-item label="类型名称" required>
          <el-input v-model="form.name" placeholder="如：危机磋商、紧急动议" />
        </el-form-item>

        <el-divider>功能配置</el-divider>

        <el-form-item label="发言名单">
          <el-switch v-model="form.need_speakers_list" active-text="需要发言名单" inactive-text="不需要发言名单" />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="单位时长">
              <el-switch v-model="form.need_unit_duration" active-text="启用" inactive-text="禁用" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="总时长">
              <el-switch v-model="form.need_total_duration" active-text="启用" inactive-text="禁用" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider>默认值</el-divider>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="默认单位时长（秒）">
              <el-input-number v-model="form.default_unit_duration" :min="0" :step="10" controls-position="right" style="width: 100%" :disabled="!form.need_unit_duration" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="默认总时长（秒）">
              <el-input-number v-model="form.default_total_duration" :min="0" :step="30" controls-position="right" style="width: 100%" :disabled="!form.need_total_duration" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const motionTypes = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const editIndex = ref(null)

const defaultForm = () => ({
  name: '',
  need_speakers_list: true,
  need_unit_duration: true,
  need_total_duration: true,
  default_unit_duration: 60,
  default_total_duration: 300
})

const form = ref(defaultForm())

async function loadMotionTypes() {
  try {
    const { data } = await api.get('/api/staff/committee')
    motionTypes.value = data.motion_types || []
  } catch (e) {}
}

function showAddDialog() {
  editIndex.value = null
  form.value = defaultForm()
  dialogVisible.value = true
}

function showEditDialog(row, index) {
  editIndex.value = index
  form.value = { ...row }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入类型名称')
    return
  }
  saving.value = true
  try {
    const newList = [...motionTypes.value]
    if (editIndex.value !== null) {
      newList[editIndex.value] = { ...form.value }
    } else {
      newList.push({ ...form.value })
    }
    await api.put('/api/staff/motion-types', { motion_types: newList })
    motionTypes.value = newList
    ElMessage.success(editIndex.value !== null ? '已更新' : '已添加')
    dialogVisible.value = false
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(index) {
  await ElMessageBox.confirm('确定删除该动议类型？', '提示', { type: 'warning' })
  try {
    const newList = motionTypes.value.filter((_, i) => i !== index)
    await api.put('/api/staff/motion-types', { motion_types: newList })
    motionTypes.value = newList
    ElMessage.success('已删除')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

onMounted(loadMotionTypes)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.builtin-info {
  margin-bottom: 16px;
}
.builtin-tag {
  margin-right: 6px;
  margin-top: 4px;
}
</style>
