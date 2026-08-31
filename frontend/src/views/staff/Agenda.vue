<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>议程管理</span>
          <div>
            <el-button @click="showImportDialog">导入议程</el-button>
            <el-button type="primary" @click="showAddDialog">添加议程</el-button>
          </div>
        </div>
      </template>

      <div class="drag-hint">
        <el-icon style="margin-right: 4px; vertical-align: middle"><Rank /></el-icon>
        拖动行可调整顺序，点击 <el-icon style="vertical-align: middle"><FolderOpened /></el-icon>
        <el-icon style="vertical-align: middle"><Folder /></el-icon> 可升降层级
      </div>

      <el-table
        ref="tableRef"
        :data="agendaItems"
        style="width: 100%"
        row-key="id"
        :tree-props="{ children: 'children' }"
        default-expand-all
        class="drag-table"
      >
        <el-table-column prop="title" label="议程标题" min-width="300">
          <template #default="{ row }">
            <span class="drag-handle" :style="{ paddingLeft: (row.level - 1) * 24 + 'px' }">
              <el-icon class="drag-icon"><Rank /></el-icon>
              <el-tag size="small" :type="getLevelType(row.level)" style="margin-right: 8px">L{{ row.level }}</el-tag>
              {{ row.title }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="层级" width="100">
          <template #default="{ row }">
            <el-button-group size="small">
              <el-button
                size="small"
                :disabled="row.level <= 1"
                @click="adjustLevel(row, -1)"
                title="降低层级（左移）"
              >
                <el-icon><FolderOpened /></el-icon>
              </el-button>
              <el-button
                size="small"
                :disabled="row.level >= 5"
                @click="adjustLevel(row, 1)"
                title="提升层级（右移）"
              >
                <el-icon><Folder /></el-icon>
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '当前' : '待定' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="handleActivate(row)">
              {{ row.is_active ? '已激活' : '激活' }}
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加议程对话框 -->
    <el-dialog v-model="addDialogVisible" title="添加议程" width="450px">
      <el-form :model="addForm" :rules="addRules" ref="addFormRef">
        <el-form-item label="议程标题" prop="title">
          <el-input v-model="addForm.title" placeholder="如：一般性辩论、议题讨论" />
        </el-form-item>
        <el-form-item label="父级议程">
          <el-select v-model="addForm.parent_id" placeholder="一级议程（不选）" clearable style="width: 100%">
            <el-option label="一级议程" :value="null" />
            <el-option v-for="item in flatAgendaItems" :key="item.id" :label="getIndentedLabel(item)" :value="item.id" :disabled="item.level >= 5" />
          </el-select>
          <div class="form-help">选择父议程作为子项，或不选作为一级议程</div>
        </el-form-item>
        <el-form-item v-if="addForm.parent_id" label="层级">
          <el-input :model-value="'子议程（L' + computedLevel + '）'" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addLoading" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>

    <!-- 导入议程对话框 -->
    <el-dialog v-model="importDialogVisible" title="导入议程" width="700px">
      <div class="import-hint">
        <p><strong>支持的格式：</strong></p>
        <p>1. 多级编号格式（点号分隔）：</p>
        <pre>0. 总议题
1. 第一部分
  1.1 子议题
  1.2 子议题
    1.2.1 详细议题</pre>
        <p>2. Markdown 标题格式：</p>
        <pre># 总议题
## 子议题
### 详细议题</pre>
      </div>
      <el-input
        v-model="importText"
        type="textarea"
        :rows="15"
        placeholder="请输入议程内容..."
      />
      <div v-if="parsedItems.length" class="preview">
        <div class="preview-header">
          <h4>预览 ({{ parsedItems.length }} 项)</h4>
          <el-button size="small" type="danger" @click="parsedItems = []">清空预览</el-button>
        </div>
        <div class="preview-list">
          <div v-for="(item, i) in parsedItems" :key="i" class="preview-item" :style="{ paddingLeft: (item.level - 1) * 24 + 'px' }">
            <el-tag size="small" :type="getLevelType(item.level)">L{{ item.level }}</el-tag>
            <span class="preview-title">{{ item.title }}</span>
            <span class="preview-num">{{ item.numStr }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button @click="parseImportText">预览</el-button>
        <el-button type="primary" :loading="importLoading" @click="handleImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'
import { Rank, FolderOpened, Folder } from '@element-plus/icons-vue'

let sortableInstance = null

const agendaItems = ref([])
const addDialogVisible = ref(false)
const addLoading = ref(false)
const addFormRef = ref(null)
const importDialogVisible = ref(false)
const importLoading = ref(false)
const importText = ref('')
const parsedItems = ref([])
const tableRef = ref(null)

const addForm = ref({ title: '', parent_id: null })
const addRules = {
  title: [{ required: true, message: '请输入议程标题', trigger: 'blur' }]
}

function getLevelType(level) {
  const types = ['', 'success', 'warning', 'danger', 'info']
  return types[(level - 1) % types.length] || ''
}

// 扁平化议程列表
const flatAgendaItems = computed(() => {
  const result = []
  function flatten(items) {
    for (const item of items) {
      result.push(item)
      if (item.children?.length) {
        flatten(item.children)
      }
    }
  }
  flatten(agendaItems.value)
  return result
})

// 根据父议程计算层级
const computedLevel = computed(() => {
  if (!addForm.value.parent_id) return 1
  const parent = flatAgendaItems.value.find(i => i.id === addForm.value.parent_id)
  return parent ? Math.min(parent.level + 1, 5) : 1
})

function getIndentedLabel(item) {
  return '　'.repeat(item.level - 1) + item.title
}

async function loadAgenda() {
  const { data } = await api.get('/api/staff/agenda')
  agendaItems.value = buildTree(data)
  await nextTick()
  initSortable()
}

function buildTree(items) {
  const map = {}
  const roots = []
  for (const item of items) {
    map[item.id] = { ...item, children: [] }
  }
  for (const item of items) {
    const node = map[item.id]
    const parentLevel = item.level - 1
    if (parentLevel <= 0) {
      roots.push(node)
    } else {
      const idx = items.indexOf(item)
      let parentId = null
      for (let i = idx - 1; i >= 0; i--) {
        if (items[i].level === parentLevel) {
          parentId = items[i].id
          break
        }
      }
      if (parentId && map[parentId]) {
        map[parentId].children.push(node)
      } else {
        roots.push(node)
      }
    }
  }
  return roots
}

// === 拖拽排序（SortableJS） ===

function initSortable() {
  import('sortablejs').then(({ default: Sortable }) => {
    destroySortable()
    const el = document.querySelector('.el-table__body-wrapper tbody')
    if (!el) return
    sortableInstance = new Sortable(el, {
      handle: '.drag-handle',
      animation: 200,
      ghostClass: 'drag-ghost',
      onEnd: async function (evt) {
        // 从旧列表取拖拽的条目（带子节点）
        const draggedId = parseInt(evt.item.dataset.rowKey)
        const oldIndex = evt.oldIndex
        const newIndex = evt.newIndex
        if (oldIndex === newIndex) return

        // 读取当前扁平列表（从 DOM row-key）
        const rows = el.querySelectorAll('tr')
        const idOrder = []
        for (const row of rows) {
          const id = parseInt(row.dataset.rowKey)
          if (!isNaN(id)) idOrder.push(id)
        }

        // 从当前树结构中提取完整的扁平数据（包括子节点结构）
        const allFlat = flattenDataRef(agendaItems.value)

        // 新的顺序
        const reordered = idOrder.map(id => allFlat.find(i => i.id === id)).filter(Boolean)
        await submitReorder(reordered)
      }
    })
  })
}

function destroySortable() {
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }
}

// 带深拷贝的扁平化
function flattenDataRef(tree) {
  const result = []
  function walk(items) {
    for (const item of items) {
      result.push({ id: item.id, level: item.level, order: item.order, is_active: item.is_active, title: item.title })
      if (item.children?.length) walk(item.children)
    }
  }
  walk(tree)
  return result
}

// 提交排序变更
async function submitReorder(items) {
  const updates = items.map((item, i) => ({
    id: item.id,
    order: i,
    level: item.level
  }))
  try {
    await api.put('/api/staff/agenda/reorder', { items: updates })
    ElMessage.success('排序已更新')
    loadAgenda()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '排序更新失败')
    loadAgenda() // 恢复
  }
}

// === 调整层级 ===

async function adjustLevel(row, delta) {
  const newLevel = row.level + delta
  if (newLevel < 1 || newLevel > 5) return
  try {
    await api.put(`/api/staff/agenda/${row.id}/level`, { level: newLevel })
    ElMessage.success('层级已更新')
    loadAgenda()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '更新失败')
  }
}

// === 增删改 ===

function showAddDialog() {
  addForm.value = { title: '', parent_id: null }
  addDialogVisible.value = true
}

function showImportDialog() {
  importText.value = ''
  parsedItems.value = []
  importDialogVisible.value = true
}

function parseImportText() {
  const lines = importText.value.split('\n')
  const items = []
  for (const line of lines) {
    if (!line.trim()) continue
    const mdMatch = line.match(/^(#{1,10})\s+(.+)$/)
    if (mdMatch) {
      items.push({ title: mdMatch[2].trim(), level: mdMatch[1].length, numStr: '#'.repeat(mdMatch[1].length) })
      continue
    }
    const numMatch = line.match(/^(\s*)(\d+(?:\.\d+)*)\s*[.．]?\s*(.+)$/)
    if (numMatch) {
      const numStr = numMatch[2]
      items.push({ title: numMatch[3].trim(), level: numStr.split('.').length, numStr })
      continue
    }
    const indentMatch = line.match(/^(\s+)(.+)$/)
    if (indentMatch) {
      items.push({
        title: indentMatch[2].trim(),
        level: Math.floor(indentMatch[1].replace(/\t/g, '  ').length / 2) + 1,
        numStr: '-'
      })
      continue
    }
    items.push({ title: line.trim(), level: 1, numStr: '-' })
  }
  parsedItems.value = items
  ElMessage.success(`解析完成，共 ${items.length} 项`)
}

async function handleImport() {
  if (!parsedItems.value.length) {
    parseImportText()
    if (!parsedItems.value.length) {
      ElMessage.warning('没有可导入的内容')
      return
    }
  }
  importLoading.value = true
  try {
    const items = parsedItems.value.map((item, i) => ({ title: item.title, level: item.level, order: i }))
    const { data } = await api.post('/api/staff/agenda/batch', { items })
    ElMessage.success(data.message)
    importDialogVisible.value = false
    loadAgenda()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '导入失败')
  } finally {
    importLoading.value = false
  }
}

async function handleAdd() {
  await addFormRef.value.validate()
  addLoading.value = true
  try {
    const level = computedLevel.value
    const order = flatAgendaItems.value.length
    await api.post('/api/staff/agenda', { title: addForm.value.title, level, order })
    ElMessage.success('添加成功')
    addDialogVisible.value = false
    loadAgenda()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '添加失败')
  } finally {
    addLoading.value = false
  }
}

async function handleActivate(item) {
  if (item.is_active) return
  try {
    await api.put(`/api/staff/agenda/${item.id}/activate`)
    ElMessage.success('已激活')
    loadAgenda()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  }
}

async function handleDelete(item) {
  await ElMessageBox.confirm('确定删除该议程？', '提示', { type: 'warning' })
  try {
    await api.delete(`/api/staff/agenda/${item.id}`)
    ElMessage.success('删除成功')
    loadAgenda()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

onMounted(loadAgenda)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}
.drag-hint {
  font-size: 12px;
  color: #909399;
  margin-bottom: 10px;
  padding: 6px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}
.drag-handle {
  cursor: grab;
  display: inline-flex;
  align-items: center;
  user-select: none;
}
.drag-handle:active {
  cursor: grabbing;
}
.drag-icon {
  color: #c0c4cc;
  margin-right: 6px;
  font-size: 14px;
}
:deep(.drag-ghost) {
  opacity: 0.5;
  background: #edf3fb !important;
}
:deep(.el-table__body-wrapper tbody tr.drag-ghost > td) {
  background: #edf3fb !important;
}
.import-hint {
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}
.import-hint pre {
  background: #e6e8eb;
  padding: 8px;
  border-radius: 4px;
  margin: 8px 0;
  font-family: monospace;
  font-size: 13px;
}
.import-hint p {
  margin: 8px 0 4px;
  color: #606266;
}
.preview {
  margin-top: 16px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
}
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.preview-header h4 {
  margin: 0;
  color: #303133;
}
.preview-list {
  max-height: 250px;
  overflow-y: auto;
}
.preview-item {
  padding: 4px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.preview-title {
  flex: 1;
}
.preview-num {
  color: #909399;
  font-size: 12px;
  font-family: monospace;
}
</style>
