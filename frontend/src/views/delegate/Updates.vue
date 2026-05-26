<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>局势更新</span>
          <div style="display: flex; gap: 8px;">
            <el-input
              v-model="keyword"
              placeholder="搜索更新..."
              clearable
              style="width: 200px;"
              @keyup.enter="handleSearch"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
          </div>
        </div>
      </template>

      <div v-for="item in updates" :key="item.id" class="update-item">
        <div class="update-header">
          <span class="update-title" @click="showDetail(item)">{{ item.title }}</span>
          <span class="update-time">{{ new Date(item.created_at).toLocaleString('zh-CN') }}</span>
        </div>
      </div>
      <el-empty v-if="!updates.length" description="暂无局势更新" />
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
        <p><strong>发布时间：</strong>{{ new Date(detailItem.created_at).toLocaleString('zh-CN') }}</p>
        <el-divider />
        <div style="white-space: pre-wrap; background: #f5f7fa; padding: 16px; border-radius: 4px">
          {{ detailItem.content || '无内容' }}
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
import { Search } from '@element-plus/icons-vue'

const updates = ref([])
const keyword = ref('')
const detailVisible = ref(false)
const detailItem = ref(null)
const searchResults = ref([])
const searchDialogVisible = ref(false)

function showDetail(item) {
  detailItem.value = item
  detailVisible.value = true
}

async function handleSearch() {
  if (!keyword.value.trim()) return
  try {
    const params = `?keyword=${encodeURIComponent(keyword.value)}`
    const { data } = await api.get('/api/delegate/updates' + params)
    searchResults.value = data.filter(u => u.type === 'text')
    searchDialogVisible.value = true
  } catch (e) {}
}

async function loadData() {
  try {
    const { data } = await api.get('/api/delegate/updates')
    updates.value = data.filter(u => u.type === 'text')
  } catch (e) {}
}

onMounted(loadData)
</script>

<style scoped>
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
.update-title:hover { color: #409eff; }
.update-time { color: #909399; font-size: 12px; margin-left: 12px; }
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
