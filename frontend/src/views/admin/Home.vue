<template>
  <div class="home-page animate-fade-in">
    <!-- 统计卡片 -->
    <div class="stat-grid">
      <div class="stat-card" @click="$router.push('/admin/committees')">
        <div class="stat-icon" style="background: linear-gradient(135deg, #5b92e5, #3d7ed9)">
          <el-icon :size="22"><OfficeBuilding /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.committees }}</div>
          <div class="stat-label">委员会</div>
        </div>
      </div>
      <div class="stat-card" @click="$router.push('/admin/staff')">
        <div class="stat-icon" style="background: linear-gradient(135deg, #e84393, #d6336c)">
          <el-icon :size="22"><User /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.staff }}</div>
          <div class="stat-label">学团成员</div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <el-card class="quick-card">
      <template #header>
        <div class="card-header">
          <span>快捷操作</span>
        </div>
      </template>
      <div class="quick-actions">
        <el-button type="primary" size="large" @click="$router.push('/admin/committees')">
          <el-icon><Plus /></el-icon>管理委员会
        </el-button>
        <el-button size="large" @click="$router.push('/admin/staff')">
          <el-icon><Plus /></el-icon>管理学团
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
import { OfficeBuilding, User, Plus } from '@element-plus/icons-vue'

const stats = ref({ committees: 0, staff: 0 })

onMounted(async () => {
  try {
    const [cRes, sRes] = await Promise.all([
      api.get('/api/admin/committees'),
      api.get('/api/admin/staff')
    ])
    stats.value.committees = cRes.data.length
    stats.value.staff = sRes.data.length
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
.home-page {
  max-width: 800px;
  margin: 0 auto;
}

.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 14px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: all 0.25s ease;
}
.stat-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.stat-body {
  flex: 1;
}
.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}
.stat-label {
  font-size: 14px;
  color: #64748b;
  margin-top: 2px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quick-card {
  margin-top: 0;
}

.quick-actions {
  display: flex;
  gap: 12px;
}
</style>
