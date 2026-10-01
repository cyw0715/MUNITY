<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>文件类型管理</span>
          <div>
            <el-button @click="resetBuiltins">恢复默认</el-button>
            <el-button type="primary" @click="showAddDialog">添加文件类型</el-button>
          </div>
        </div>
      </template>

      <el-alert type="info" :closable="false" style="margin-bottom: 12px">
        每种文件类型可单独决定：是否需要联署（强制/可选/不需要）、是否显示密级、是否显示涉及部门。
        代表提交文件时会按此处配置动态显示对应字段。
      </el-alert>

      <el-table :data="documentTypes" style="width: 100%">
        <el-table-column label="类型名称" min-width="160">
          <template #default="{ row }">
            <span>{{ row.name }}</span>
            <el-tag v-if="isBuiltinDocTypeName(row.name)" size="small" type="info" style="margin-left: 6px">内置</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="联署" width="130">
          <template #default="{ row }">
            <el-tag :type="endorsementTagType(row.endorsement)" size="small">
              {{ ENDORSEMENT_LABELS[row.endorsement] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="可选字段" min-width="200">
          <template #default="{ row }">
            <el-tag v-if="row.need_secrecy" type="warning" size="small" style="margin-right: 4px">密级</el-tag>
            <el-tag v-if="row.need_departments" type="success" size="small" style="margin-right: 4px">涉及部门</el-tag>
            <span v-if="!row.need_secrecy && !row.need_departments" style="color: #c0c4cc">无</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row, $index }">
            <el-button size="small" @click="showEditDialog(row, $index)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!documentTypes.length" description="暂无文件类型，点击上方添加" />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editIndex === null ? '添加文件类型' : '编辑文件类型'" width="520px">
      <el-form :model="form" label-position="top">
        <el-form-item label="类型名称" required>
          <el-input
            v-model="form.name"
            placeholder="如：决议草案、联合声明"
            :disabled="isBuiltinDocTypeName(form.name) && !isNameEditable"
          />
          <span v-if="isBuiltinDocTypeName(form.name)" style="color: #909399; font-size: 12px">
            内置类型的名称不可修改
          </span>
        </el-form-item>

        <el-divider>联署</el-divider>
        <el-form-item label="联署方式">
          <el-radio-group v-model="form.endorsement">
            <el-radio value="required">强制联署</el-radio>
            <el-radio value="optional">可选联署</el-radio>
            <el-radio value="none">不需要联署</el-radio>
          </el-radio-group>
          <span style="color: #909399; font-size: 12px; display: block; margin-top: 4px">
            强制联署：未选择联署代表团无法提交；可选联署：可留空；不需要联署：不显示该字段
          </span>
        </el-form-item>

        <el-divider>可选字段</el-divider>
        <el-form-item label="是否选择密级">
          <el-switch v-model="form.need_secrecy" active-text="显示密级选择" inactive-text="一律按公开处理" />
        </el-form-item>
        <el-form-item label="是否选择涉及部门">
          <el-switch v-model="form.need_departments" active-text="显示涉及部门" inactive-text="不显示" />
        </el-form-item>
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
import {
  ENDORSEMENT_LABELS,
  defaultDocumentTypes,
  resolveDocumentTypes,
  toStoredDocumentTypes,
  isBuiltinDocTypeName,
} from '../../constants/documentTypes'

const documentTypes = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const editIndex = ref(null)
// 内置类型改名会让已提交文件失去类型归属，故不允许改名
const isNameEditable = ref(false)

const defaultForm = () => ({
  name: '',
  endorsement: 'optional',
  need_secrecy: false,
  need_departments: false,
})

const form = ref(defaultForm())

function endorsementTagType(v) {
  if (v === 'required') return 'danger'
  if (v === 'optional') return 'success'
  return 'info'
}

async function loadDocumentTypes() {
  try {
    const { data } = await api.get('/api/staff/committee')
    documentTypes.value = resolveDocumentTypes(data.document_types, data.document_types_configured)
  } catch (e) {}
}

function showAddDialog() {
  editIndex.value = null
  isNameEditable.value = true
  form.value = defaultForm()
  dialogVisible.value = true
}

function showEditDialog(row, index) {
  editIndex.value = index
  isNameEditable.value = false
  form.value = { ...row }
  dialogVisible.value = true
}

async function save(nextList, successMsg) {
  saving.value = true
  try {
    const { data } = await api.put('/api/staff/document-types', {
      document_types: toStoredDocumentTypes(nextList),
    })
    documentTypes.value = resolveDocumentTypes(data.document_types, true)
    ElMessage.success(successMsg)
    dialogVisible.value = false
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleSave() {
  const name = (form.value.name || '').trim()
  if (!name) {
    ElMessage.warning('请输入类型名称')
    return
  }
  const list = documentTypes.value.map(t => ({ ...t }))
  const dup = list.some((t, i) => t.name === name && i !== editIndex.value)
  if (dup) {
    ElMessage.warning('已存在同名文件类型')
    return
  }
  const entry = { ...form.value, name }
  if (editIndex.value !== null) {
    list[editIndex.value] = entry
  } else {
    list.push(entry)
  }
  await save(list, editIndex.value !== null ? '已更新' : '已添加')
}

async function handleDelete(index) {
  const item = documentTypes.value[index]
  const extra = isBuiltinDocTypeName(item.name)
    ? '这是内置类型，删除后刷新不会自动恢复（可用「恢复默认」找回）。'
    : ''
  await ElMessageBox.confirm(
    `确定删除文件类型「${item.name}」？${extra}已提交的历史文件不受影响。`,
    '删除文件类型',
    { type: 'warning', confirmButtonText: '确定删除' }
  )
  const list = documentTypes.value.filter((_, i) => i !== index)
  await save(list, '已删除')
}

async function resetBuiltins() {
  await ElMessageBox.confirm('恢复默认将重置内置文件类型，自定义类型将保留。', '确认', { type: 'info' })
  const custom = documentTypes.value.filter(t => !isBuiltinDocTypeName(t.name))
  await save([...defaultDocumentTypes(), ...custom], '已恢复默认')
}

onMounted(loadDocumentTypes)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
