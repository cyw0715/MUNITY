<template>
  <el-card class="animate-fade-in">
    <template #header>
      <div class="card-header">
        <span>局势更新</span>
        <div style="display: flex; align-items: center; gap: 8px">
          <el-input
            v-model="keyword"
            placeholder="搜索标题、内容、附件…"
            clearable
            style="width: 240px"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button type="primary" @click="showCreateDialog">发布更新</el-button>
        </div>
      </div>
    </template>

    <div v-for="item in updates" :key="item.id" class="update-item">
      <div class="update-header">
        <span class="update-title" @click="showDetail(item)">{{ item.title }}</span>
        <div>
          <span class="update-time">{{ new Date(item.created_at).toLocaleString('zh-CN') }}</span>
          <el-button type="danger" link size="small" style="margin-left: 12px" @click="handleDelete(item)">撤回</el-button>
        </div>
      </div>
      <div class="update-meta">
        <span style="color: #909399; font-size: 12px">全体代表可见</span>
      </div>
    </div>
    <el-empty v-if="!updates.length" description="暂无局势更新" />
  </el-card>

  <!-- 创建对话框 -->
  <el-dialog v-model="createDialogVisible" title="发布局势更新" width="600px">
    <el-form :model="form">
      <el-form-item label="标题" required>
        <el-input v-model="form.title" />
      </el-form-item>
      <el-form-item label="内容" required>
        <el-input v-model="form.content" type="textarea" :rows="6" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="createDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="createLoading" @click="handleCreate">发布</el-button>
    </template>
  </el-dialog>

  <!-- 详情对话框 -->
  <el-dialog v-model="detailVisible" title="更新详情" width="600px">
    <div v-if="detailItem">
      <p><strong>标题：</strong>{{ detailItem.title }}</p>
      <p><strong>发布时间：</strong>{{ new Date(detailItem.created_at).toLocaleString('zh-CN') }}</p>
      <el-divider />
      <div style="white-space: pre-wrap; background: #f5f7fa; padding: 16px; border-radius: 4px">
        {{ detailItem.content || '无内容' }}
      </div>
    </div>
  </el-dialog>

  <!-- 搜索结果对话框 -->
  <el-dialog v-model="searchDialogVisible" title="搜索结果" width="650px">
    <div v-if="searchLoading" style="text-align: center; padding: 40px">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      <p style="color: #909399; margin-top: 8px">搜索中...</p>
    </div>
    <div v-else-if="searchResults.length">
      <div
        v-for="item in searchResults"
        :key="item.id"
        class="search-result-item"
        @click="searchDialogVisible = false; showDetail(item)"
      >
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span style="font-size: 15px; font-weight: 500; color: #303133">{{ item.title }}</span>
          <span style="color: #909399; font-size: 12px">{{ new Date(item.created_at).toLocaleString('zh-CN') }}</span>
        </div>
        <div style="color: #606266; font-size: 13px; margin-top: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
          {{ (item.content || '').substring(0, 100) }}{{ (item.content || '').length > 100 ? '...' : '' }}
        </div>
      </div>
      <p style="color: #909399; font-size: 12px; margin-top: 12px; text-align: right">共 {{ searchResults.length }} 条结果</p>
    </div>
    <el-empty v-else description="未找到匹配的局势更新" />
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Loading } from '@element-plus/icons-vue'
import api from '../../api'
import { useWebSocket } from '../../composables/useWebSocket'

const updates = ref([])
const keyword = ref('')
const searchResults = ref([])
const searchLoading = ref(false)
const searchDialogVisible = ref(false)
const createDialogVisible = ref(false)
const createLoading = ref(false)
const detailVisible = ref(false)
const detailItem = ref(null)
const form = ref({ title: '', content: '' })

async function loadData() {
  try {
    const uRes = await api.get('/api/staff/updates')
    updates.value = uRes.data.filter(u => u.type === 'text')
  } catch (e) {}
}

async function handleSearch() {
  if (!keyword.value) {
    searchDialogVisible.value = false
    searchResults.value = []
    return
  }
  searchLoading.value = true
  searchDialogVisible.value = true
  try {
    const res = await api.get('/api/staff/updates?keyword=' + encodeURIComponent(keyword.value))
    searchResults.value = res.data.filter(u => u.type === 'text')
  } catch (e) {
    ElMessage.error('搜索失败')
  } finally {
    searchLoading.value = false
  }
}

function showCreateDialog() {
  form.value = { title: '', content: '' }
  createDialogVisible.value = true
}

function showDetail(item) {
  detailItem.value = item
  detailVisible.value = true
}

async function handleCreate() {
  if (!form.value.title || !form.value.content) {
    ElMessage.warning('请输入标题和内容')
    return
  }
  createLoading.value = true
  try {
    await api.post('/api/staff/updates', {
      title: form.value.title,
      content: form.value.content
    })
    ElMessage.success('发布成功')
    createDialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '发布失败')
  } finally {
    createLoading.value = false
  }
}

async function handleDelete(item) {
  await ElMessageBox.confirm('确定撤回该局势更新？撤回后代表将无法看到。', '提示', { type: 'warning' })
  try {
    await api.delete(`/api/staff/updates/${item.id}`)
    ElMessage.success('撤回成功')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '撤回失败')
  }
}

onMounted(() => {
  loadData()
  const ws = useWebSocket()
  ws.on('updates_changed', loadData)
})
onUnmounted(() => {
  const ws = useWebSocket()
  ws.off('updates_changed', loadData)
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.update-item {
  padding: 16px 0;
  border-bottom: 1px solid #ebeef5;
}
.update-item:last-child { border-bottom: none; }
.update-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.update-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  cursor: pointer;
}
.update-title:hover { color: #5b92e5; }
.update-time { color: #909399; font-size: 12px; }
.update-meta { margin-top: 8px; }
.search-result-item {
  padding: 14px 16px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}
.search-result-item:last-child { border-bottom: none; }
.search-result-item:hover { background: #f5f7fa; }
</style>
