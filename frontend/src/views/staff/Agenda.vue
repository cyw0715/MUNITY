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

      <el-table :data="agendaItems" style="width: 100%" row-key="id" :tree-props="{ children: 'children' }" default-expand-all>
        <el-table-column prop="title" label="议程标题" min-width="300">
          <template #default="{ row }">
            <span :style="{ paddingLeft: (row.level - 1) * 20 + 'px' }">
              <el-tag size="small" :type="getLevelType(row.level)" style="margin-right: 8px">L{{ row.level }}</el-tag>
              {{ row.title }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '当前' : '待定' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
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
    <el-dialog v-model="addDialogVisible" title="添加议程" width="400px">
      <el-form :model="addForm" :rules="addRules" ref="addFormRef">
        <el-form-item label="议程标题" prop="title">
          <el-input v-model="addForm.title" />
        </el-form-item>
        <el-form-item label="层级" prop="level">
          <el-input-number v-model="addForm.level" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="排序" prop="order">
          <el-input-number v-model="addForm.order" :min="0" />
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const agendaItems = ref([])
const addDialogVisible = ref(false)
const addLoading = ref(false)
const addFormRef = ref(null)
const importDialogVisible = ref(false)
const importLoading = ref(false)
const importText = ref('')
const parsedItems = ref([])

const addForm = ref({ title: '', level: 1, order: 0 })
const addRules = {
  title: [{ required: true, message: '请输入议程标题', trigger: 'blur' }]
}

function getLevelType(level) {
  const types = ['', 'success', 'warning', 'danger', 'info']
  return types[(level - 1) % types.length] || ''
}

async function loadAgenda() {
  const { data } = await api.get('/api/staff/agenda')
  agendaItems.value = buildTree(data)
}

// 构建树形结构
function buildTree(items) {
  const map = {}
  const roots = []
  
  // 先创建所有节点
  for (const item of items) {
    map[item.id] = { ...item, children: [] }
  }
  
  // 构建树
  for (const item of items) {
    const node = map[item.id]
    // 找父节点：在它之前的、level 比它小 1 的最近节点
    const parentLevel = item.level - 1
    if (parentLevel <= 0) {
      roots.push(node)
    } else {
      // 向前找最近的 level = parentLevel 的节点
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

function showAddDialog() {
  addForm.value = { title: '', level: 1, order: agendaItems.value.length }
  addDialogVisible.value = true
}

function showImportDialog() {
  importText.value = ''
  parsedItems.value = []
  importDialogVisible.value = true
}

// 解析导入文本
function parseImportText() {
  const lines = importText.value.split('\n')
  const items = []
  
  for (const line of lines) {
    if (!line.trim()) continue
    
    // 1. 检查 Markdown 标题格式
    const mdMatch = line.match(/^(#{1,10})\s+(.+)$/)
    if (mdMatch) {
      items.push({
        title: mdMatch[2].trim(),
        level: mdMatch[1].length,
        numStr: '#'.repeat(mdMatch[1].length)
      })
      continue
    }
    
    // 2. 检查编号格式
    const numMatch = line.match(/^(\s*)(\d+(?:\.\d+)*)\s*[.．]?\s*(.+)$/)
    if (numMatch) {
      const numStr = numMatch[2]
      const level = numStr.split('.').length
      items.push({
        title: numMatch[3].trim(),
        level: level,
        numStr: numStr
      })
      continue
    }
    
    // 3. 检查缩进格式
    const indentMatch = line.match(/^(\s+)(.+)$/)
    if (indentMatch) {
      const spaces = indentMatch[1].replace(/\t/g, '  ').length
      const level = Math.floor(spaces / 2) + 1
      items.push({
        title: indentMatch[2].trim(),
        level: level,
        numStr: '-'
      })
      continue
    }
    
    // 4. 默认为一级
    items.push({
      title: line.trim(),
      level: 1,
      numStr: '-'
    })
  }
  
  parsedItems.value = items
  ElMessage.success(`解析完成，共 ${items.length} 项`)
}

// 导入议程
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
    const items = parsedItems.value.map((item, i) => ({
      title: item.title,
      level: item.level,
      order: i
    }))
    
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
    await api.post('/api/staff/agenda', addForm.value)
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
