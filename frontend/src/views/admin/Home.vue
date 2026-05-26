<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>委员会统计</span>
          </template>
          <div class="stat-item">
            <span class="label">委员会数量</span>
            <span class="value">{{ stats.committees }}</span>
          </div>
          <div class="stat-item">
            <span class="label">学团数量</span>
            <span class="value">{{ stats.staff }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>快捷操作</span>
          </template>
          <el-button type="primary" @click="$router.push('/admin/committees')">管理委员会</el-button>
          <el-button @click="$router.push('/admin/staff')">管理学团</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const stats = ref({ committees: 0, staff: 0 })

onMounted(async () => {
  try {
    const [cRes, sRes] = await Promise.all([
      api.get('/api/admin/committees'),
      api.get('/api/admin/staff')
    ])
    stats.value.committees = cRes.data.length
    stats.value.staff = sRes.data.length
  } catch (e) {
    console.error(e)
  }
})
</script>

<style scoped>
.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}
.stat-item:last-child { border-bottom: none; }
.label { color: #606266; }
.value { font-size: 20px; font-weight: bold; color: #409eff; }
</style>
