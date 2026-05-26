<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>会议文件</span>
          <div style="display: flex; gap: 8px;">
            <el-input
              v-model="keyword"
              placeholder="搜索文件（标题/正文/附件内容）..."
              clearable
              style="width: 260px;"
              @keyup.enter="handleSearch"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
          </div>
        </div>
      </template>

      <div v-for="item in files" :key="item.id" class="file-item">
        <div class="file-header">
          <span class="file-title" @click="showDetail(item)">{{ item.title }}</span>
          <div>
            <el-button v-if="item.file_path" type="primary" link size="small" @click="downloadFile(item.file_path)">
              下载附件
            </el-button>
            <span class="file-time">{{ new Date(item.created_at).toLocaleString('zh-CN') }}</span>
          </div>
        </div>
      </div>
      <el-empty v-if="!files.length" description="暂无会议文件" />
    </el-card>

    <!-- 搜索结果对话框 -->
    <el-dialog v-model="searchDialogVisible" title="搜索结果" width="600px">
      <div v-if="searchResults.length">
        <div v-for="item in searchResults" :key="item.id" class="search-result-item" @click="showDetail(item)">
          <div class="search-result-title">{{ item.title }}</div>
          <div class="search-result-time">{{ new Date(item.created_at).toLocaleString('zh-CN') }}</div>
          <div class="search-result-preview">{{ item.content ? item.content.substring(0, 100) + (item.content.length > 100 ? '...' : '') : '无内容' }}</div>
        </div>
      </div>
      <el-empty v-else description="未找到匹配的结果" />
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" :title="detailItem?.title" width="600px">
      <div v-if="detailItem">
        <div style="white-space: pre-wrap; margin-bottom: 16px">{{ detailItem.content }}</div>
        <el-button v-if="detailItem.file_path" type="primary" @click="downloadFile(detailItem.file_path)">
          下载附件
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
import { Search } from '@element-plus/icons-vue'

const files = ref([])
const keyword = ref('')
const detailVisible = ref(false)
const detailItem = ref(null)
const searchResults = ref([])
const searchDialogVisible = ref(false)

function showDetail(item) {
  detailItem.value = item
  detailVisible.value = true
}

function downloadFile(filename) {
  const token = localStorage.getItem('token')
  const link = document.createElement('a')
  link.href = `/api/delegate/download/${filename}?token=${token}`
  link.download = filename
  link.click()
}

async function handleSearch() {
  if (!keyword.value.trim()) return
  try {
    const params = `?keyword=${encodeURIComponent(keyword.value)}`
    const { data } = await api.get('/api/delegate/meeting-files' + params)
    searchResults.value = data
    searchDialogVisible.value = true
  } catch (e) {}
}

async function loadData() {
  try {
    const { data } = await api.get('/api/delegate/meeting-files')
    files.value = data
  } catch (e) {}
}

onMounted(loadData)
</script>

<style scoped>
.file-item { padding: 12px 0; border-bottom: 1px solid #eee; }
.file-item:last-child { border-bottom: none; }
.file-header { display: flex; justify-content: space-between; align-items: center; }
.file-title { font-size: 16px; font-weight: bold; color: #303133; cursor: pointer; }
.file-title:hover { color: #409eff; }
.file-time { color: #909399; font-size: 12px; margin-left: 12px; }
.search-result-item {
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background-color 0.2s;
}
.search-result-item:hover { background-color: #f5f7fa; }
.search-result-item:last-child { border-bottom: none; }
.search-result-title { font-size: 15px; font-weight: 500; color: #303133; }
.search-result-time { font-size: 12px; color: #909399; margin-top: 4px; }
.search-result-preview { font-size: 13px; color: #606266; margin-top: 6px; line-height: 1.4; }
</style>
