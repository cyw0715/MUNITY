<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>存档/恢复</span>
          <el-button type="primary" @click="handleArchive">存档当前会议状态</el-button>
        </div>
      </template>

      <el-table :data="archives" style="width: 100%">
        <el-table-column prop="filename" label="存档文件" />
        <el-table-column label="大小" width="120">
          <template #default="{ row }">
            {{ (row.size / 1024).toFixed(1) }} KB
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="200">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="warning" @click="handleRestore(row.filename)">恢复</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!archives.length" description="暂无存档" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const archives = ref([])

async function loadArchives() {
  try {
    const { data } = await api.get('/api/staff/archives')
    archives.value = data
  } catch (e) {}
}

async function handleArchive() {
  try {
    const { data } = await api.post('/api/staff/archive')
    ElMessage.success(`存档成功：${data.filename}`)
    loadArchives()
  } catch (e) {
    ElMessage.error('存档失败')
  }
}

async function handleRestore(filename) {
  await ElMessageBox.confirm('确定从该存档恢复？当前点名状态将被覆盖。', '提示', { type: 'warning' })
  try {
    await api.post(`/api/staff/archives/${filename}/restore`)
    ElMessage.success('恢复成功')
  } catch (e) {
    ElMessage.error('恢复失败')
  }
}

onMounted(loadArchives)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
