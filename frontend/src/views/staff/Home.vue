<template>
  <div class="home-page animate-fade-in">
    <!-- 委员会信息卡 -->
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><OfficeBuilding /></el-icon>
            委员会信息
          </span>
          <el-tag v-if="committee" size="small" type="primary" effect="plain">{{ committee.name }}</el-tag>
        </div>
      </template>
      <div v-if="committee" class="info-body">
        <div class="info-row">
          <span class="info-key">可用功能</span>
          <span class="info-val">
            <el-tag v-for="f in committee.features" :key="f" size="small" class="feature-tag" effect="plain">
              {{ featureLabels[f] || f }}
            </el-tag>
            <span v-if="!committee.features?.length" class="text-muted">默认功能已启用</span>
          </span>
        </div>
      </div>
      <el-empty v-else description="您尚未分配到任何委员会" :image-size="60" />
    </el-card>

    <!-- 统计卡片 -->
    <div class="stat-grid">
      <div class="stat-card" @click="$router.push('/staff/delegates')">
        <div class="stat-icon" style="background: linear-gradient(135deg, #5b92e5, #3d7ed9)">
          <el-icon :size="24"><User /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.delegates }}</div>
          <div class="stat-label">代表人数</div>
        </div>
        <el-icon class="stat-arrow"><ArrowRight /></el-icon>
      </div>
      <div class="stat-card" @click="$router.push('/staff/delegations')">
        <div class="stat-icon" style="background: linear-gradient(135deg, #e84393, #d6336c)">
          <el-icon :size="24"><Avatar /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.delegations }}</div>
          <div class="stat-label">代表团数量</div>
        </div>
        <el-icon class="stat-arrow"><ArrowRight /></el-icon>
      </div>
      <div class="stat-card" @click="$router.push('/staff/agenda')">
        <div class="stat-icon" style="background: linear-gradient(135deg, #00b894, #00a381)">
          <el-icon :size="24"><List /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.agenda }}</div>
          <div class="stat-label">议程数量</div>
        </div>
        <el-icon class="stat-arrow"><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
import { OfficeBuilding, User, Avatar, List, ArrowRight } from '@element-plus/icons-vue'

const committee = ref(null)
const stats = ref({ delegates: 0, delegations: 0, agenda: 0 })

const featureLabels = {
  roll_call: '点名', agenda: '议程管理', motions: '动议管理',
  speakers_list: '发言名单', directives: '指令管理', documents: '文件管理',
  updates: '局势更新', timeline: '时间线'
}

onMounted(async () => {
  try {
    const [cRes, dRes, delRes, aRes] = await Promise.all([
      api.get('/api/staff/committee'),
      api.get('/api/staff/delegates'),
      api.get('/api/staff/delegations'),
      api.get('/api/staff/agenda')
    ])
    committee.value = cRes.data
    stats.value.delegates = dRes.data.length
    stats.value.delegations = delRes.data.length
    stats.value.agenda = aRes.data.length
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
.home-page {
  max-width: 900px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}
.card-title .el-icon { color: var(--brand-primary); font-size: 20px; }

.info-card {
  margin-bottom: 24px;
}
.info-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.info-row {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}
.info-key {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
  min-width: 72px;
  padding-top: 4px;
}
.info-val {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.feature-tag {
  margin: 0 !important;
}
.text-muted { color: #94a3b8; font-size: 13px; }

.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.stat-card {
  background: #fff;
  border-radius: 14px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
}
.stat-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}
.stat-card:hover .stat-arrow {
  opacity: 1;
  transform: translateX(0);
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
.stat-body { flex: 1; }
.stat-value { font-size: 32px; font-weight: 700; color: #0f172a; line-height: 1.2; }
.stat-label { font-size: 14px; color: #64748b; margin-top: 2px; }
.stat-arrow {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  color: #cbd5e1;
  font-size: 18px;
  opacity: 0;
  transition: all 0.2s ease;
}
</style>
