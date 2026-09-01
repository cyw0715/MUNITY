<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>动议类型管理</span>
          <div>
            <el-button @click="resetBuiltins">恢复默认</el-button>
            <el-button type="primary" @click="showAddDialog">添加动议类型</el-button>
          </div>
        </div>
      </template>

      <el-table :data="motionTypes" style="width: 100%">
        <el-table-column label="类型名称" min-width="160">
          <template #default="{ row }">
            <span>{{ row.name }}</span>
            <el-tag v-if="row.is_builtin" size="small" type="info" style="margin-left: 6px">内置</el-tag>
          </template>
        </el-table-column>
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
        <el-table-column label="默认值" width="220">
          <template #default="{ row }">
            <span v-if="row.default_unit_duration" style="margin-right: 8px; color: #606266">单位: {{ row.default_unit_duration }}s</span>
            <span v-if="row.default_total_duration" style="color: #606266">总计: {{ row.default_total_duration }}s</span>
            <span v-if="!row.default_unit_duration && !row.default_total_duration" style="color: #c0c4cc">无</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row, $index }">
            <el-button size="small" @click="showEditDialog(row, $index)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!motionTypes.length" description="暂无动议类型，点击上方添加" />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editIndex === null ? '添加动议类型' : '编辑动议类型'" width="500px">
      <el-form :model="form" label-position="top">
        <el-form-item label="类型名称" required>
          <el-input v-model="form.name" placeholder="如：危机磋商、紧急动议" :disabled="form.is_builtin" />
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

const BUILTIN_TYPES = [
  { name: '有主持核心磋商', is_builtin: true, need_speakers_list: true, need_unit_duration: true, need_total_duration: true, default_unit_duration: 60, default_total_duration: 300 },
  { name: '自由辩论', is_builtin: true, need_speakers_list: true, need_unit_duration: true, need_total_duration: true, default_unit_duration: 60, default_total_duration: 300 },
  { name: '自由磋商', is_builtin: true, need_speakers_list: false, need_unit_duration: false, need_total_duration: true, default_unit_duration: 0, default_total_duration: 600 },
  { name: '轮席发言', is_builtin: true, need_speakers_list: true, need_unit_duration: true, need_total_duration: true, default_unit_duration: 120, default_total_duration: 600 },
]

const motionTypes = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const editIndex = ref(null)

const defaultForm = () => ({
  name: '',
  is_builtin: false,
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
    const custom = data.motion_types || []
    // Merge builtins with custom — custom overrides builtins with same name
    const merged = [...BUILTIN_TYPES]
    for (const c of custom) {
      const idx = merged.findIndex(m => m.name === c.name && m.is_builtin)
      if (idx >= 0) {
        // Custom version overrides builtin
        merged[idx] = { ...merged[idx], ...c, is_builtin: true }
      } else {
        merged.push(c)
      }
    }
    motionTypes.value = merged
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
    // Strip frontend-only is_builtin flag before saving
    const saveList = newList.map(({ is_builtin, ...rest }) => rest)
    await api.put('/api/staff/motion-types', { motion_types: saveList })
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
  const item = motionTypes.value[index]
  if (item.is_builtin) {
    await ElMessageBox.confirm(`确定删除「${item.name}」？该类型将从本委员会移除。`, '删除内置类型', { type: 'warning' })
  } else {
    await ElMessageBox.confirm('确定删除该动议类型？', '提示', { type: 'warning' })
  }
  try {
    const newList = motionTypes.value.filter((_, i) => i !== index)
    // Strip frontend-only is_builtin flag before saving
    const saveList = newList.map(({ is_builtin, ...rest }) => rest)
    await api.put('/api/staff/motion-types', { motion_types: saveList })
    motionTypes.value = newList
    ElMessage.success('已删除')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

async function resetBuiltins() {
  await ElMessageBox.confirm('恢复默认将重置所有动议类型为系统内置配置，自定义类型将保留。', '确认', { type: 'info' })
  try {
    const custom = motionTypes.value.filter(m => !m.is_builtin)
    const newList = [...BUILTIN_TYPES, ...custom]
    const saveList = newList.map(({ is_builtin, ...rest }) => rest)
    await api.put('/api/staff/motion-types', { motion_types: saveList })
    motionTypes.value = newList
    ElMessage.success('已恢复默认')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '恢复失败')
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
</style>
