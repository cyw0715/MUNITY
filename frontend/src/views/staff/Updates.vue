<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>局势更新</span>
        <el-input
          v-model="keyword"
          placeholder="搜索标题"
          clearable
          style="width: 240px; margin: 0 12px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="showCreateDialog">发布更新</el-button>
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
        <span v-if="item.visibility?.length" style="color: #909399; font-size: 12px">
          可见：{{ item.visibility.length }} 个代表
        </span>
        <span v-else style="color: #909399; font-size: 12px">所有人可见</span>
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
      <el-form-item label="可见代表">
        <div style="width: 100%">
          <div v-if="selectedDelegations.length" style="margin-bottom: 8px">
            <el-tag
              v-for="dId in selectedDelegations"
              :key="dId"
              closable
              @close="removeDelegation(dId)"
              style="margin-right: 8px; margin-bottom: 4px"
            >
              {{ getDelegationName(dId) }}
            </el-tag>
          </div>
          <el-select
            v-model="currentDelegationId"
            placeholder="选择代表团添加"
            clearable
            style="width: 100%; margin-bottom: 8px"
            @change="addDelegation"
          >
            <el-option
              v-for="d in availableDelegations"
              :key="d.id"
              :label="d.name"
              :value="d.id"
            />
          </el-select>
          <el-select
            v-model="selectedVisibility"
            multiple
            placeholder="留空则所有人可见"
            style="width: 100%"
            :disabled="!selectedDelegations.length"
          >
            <el-option-group
              v-for="dId in selectedDelegations"
              :key="dId"
              :label="getDelegationName(dId)"
            >
              <el-option
                v-for="m in getDelegationMembers(dId)"
                :key="m.id"
                :label="m.username + (m.is_leader ? ' (阁首)' : '')"
                :value="m.id"
              />
            </el-option-group>
          </el-select>
        </div>
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { Loading } from '@element-plus/icons-vue'
import api from '../../api'

const updates = ref([])
const keyword = ref('')
const delegations = ref([])
const allDelegates = ref([])

const createDialogVisible = ref(false)
const createLoading = ref(false)
const detailVisible = ref(false)
const detailItem = ref(null)
const searchDialogVisible = ref(false)
const searchResults = ref([])
const searchLoading = ref(false)
const selectedDelegations = ref([])
const currentDelegationId = ref(null)
const selectedVisibility = ref([])

const form = ref({
  title: '',
  content: ''
})

const availableDelegations = computed(() => {
  return delegations.value.filter(d => !selectedDelegations.value.includes(d.id))
})

function getDelegationName(id) {
  const d = delegations.value.find(d => d.id === id)
  return d ? d.name : '未知'
}

function getDelegationMembers(delegationId) {
  return allDelegates.value.filter(d => d.delegation_id === delegationId)
}

function addDelegation(dId) {
  if (dId && !selectedDelegations.value.includes(dId)) {
    selectedDelegations.value.push(dId)
  }
  currentDelegationId.value = null
}

function removeDelegation(dId) {
  selectedDelegations.value = selectedDelegations.value.filter(id => id !== dId)
  const memberIds = allDelegates.value.filter(d => d.delegation_id === dId).map(d => d.id)
  selectedVisibility.value = selectedVisibility.value.filter(id => !memberIds.includes(id))
}

async function loadData() {
  try {
    const [uRes, dRes, delRes] = await Promise.all([
      api.get('/api/staff/updates'),
      api.get('/api/staff/delegations'),
      api.get('/api/staff/delegates')
    ])
    // 只显示文本类型的更新，过滤掉会议文件
    updates.value = uRes.data.filter(u => u.type === 'text')
    delegations.value = dRes.data
    allDelegates.value = delRes.data
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
  selectedDelegations.value = []
  currentDelegationId.value = null
  selectedVisibility.value = []
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
      content: form.value.content,
      visibility: selectedVisibility.value
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

onMounted(loadData)
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
.update-title:hover { color: #409eff; }
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
