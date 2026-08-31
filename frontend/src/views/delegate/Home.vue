<template>
  <div class="home-page animate-fade-in">
    <!-- 时间线显示 -->
    <el-card v-if="timeline && timeline.has_timeline" class="timeline-card">
      <div class="timeline-content">
        <div class="timeline-label">会议时间</div>
        <div class="timeline-date">{{ formatDate(timeline.current_date) }}</div>
        <div class="timeline-meta">
          已过 {{ elapsedDays }} 个会议天 / {{ elapsedHours }} 个现实小时
          <span class="timeline-divider">·</span>
          流速：{{ timeline.days_per_hour }} 天/时
        </div>
      </div>
    </el-card>

    <!-- 代表信息 -->
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Avatar /></el-icon>
            代表信息
          </span>
          <el-tag v-if="userInfo" :type="userInfo.is_leader ? 'success' : 'info'" size="small" effect="light">
            {{ userInfo.is_leader ? '阁首' : '代表' }}
          </el-tag>
        </div>
      </template>
      <div v-if="userInfo" class="info-grid">
        <div class="info-item">
          <span class="info-key">账号</span>
          <span class="info-val">{{ userInfo.username }}</span>
        </div>
        <div class="info-item">
          <span class="info-key">席位</span>
          <span class="info-val">{{ userInfo.seat || '未设置' }}</span>
        </div>
        <div class="info-item">
          <span class="info-key">代表团</span>
          <span class="info-val highlight">{{ userInfo.delegation_name || '未分配' }}</span>
        </div>
      </div>
      <el-empty v-else description="暂无代表信息" :image-size="60" />
    </el-card>

    <!-- 统计卡片 -->
    <div class="stat-grid">
      <div class="stat-card" @click="$router.push('/delegate/submit')">
        <div class="stat-icon" style="background: linear-gradient(135deg, #5b92e5, #3d7ed9)">
          <el-icon :size="24"><Edit /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.directives }}</div>
          <div class="stat-label">已提交指令</div>
        </div>
        <el-icon class="stat-arrow"><ArrowRight /></el-icon>
      </div>
      <div class="stat-card" @click="$router.push('/delegate/submit')">
        <div class="stat-icon" style="background: linear-gradient(135deg, #6c5ce7, #5a4bd1)">
          <el-icon :size="24"><Document /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.documents }}</div>
          <div class="stat-label">已提交文件</div>
        </div>
        <el-icon class="stat-arrow"><ArrowRight /></el-icon>
      </div>
      <div class="stat-card" @click="$router.push('/delegate/updates')">
        <div class="stat-icon" style="background: linear-gradient(135deg, #e84393, #d6336c)">
          <el-icon :size="24"><Bell /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.updates }}</div>
          <div class="stat-label">局势更新</div>
        </div>
        <el-icon class="stat-arrow"><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../../api'
import { Avatar, Edit, Document, Bell, ArrowRight } from '@element-plus/icons-vue'

const userInfo = ref(null)
const stats = ref({ directives: 0, documents: 0, updates: 0 })
const timeline = ref(null)
let refreshTimer = null

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

const elapsedDays = computed(() => {
  if (!timeline.value) return 0
  const diff = new Date(timeline.value.current_date) - new Date(timeline.value.conference_date)
  return Math.round(diff / (1000 * 60 * 60 * 24) * 10) / 10
})

const elapsedHours = computed(() => {
  if (!timeline.value) return 0
  const diffDays = (new Date(timeline.value.current_date) - new Date(timeline.value.conference_date)) / (1000 * 60 * 60 * 24)
  const diffHours = diffDays / timeline.value.days_per_hour
  return Math.round(diffHours * 10) / 10
})

async function refreshTimeline() {
  try {
    const tRes = await api.get('/api/delegate/timeline')
    timeline.value = tRes.data
  } catch (e) {}
}

onMounted(async () => {
  try {
    const [meRes, dRes, docRes, uRes, tRes] = await Promise.all([
      api.get('/api/delegate/me'),
      api.get('/api/delegate/directives'),
      api.get('/api/delegate/documents'),
      api.get('/api/delegate/updates'),
      api.get('/api/delegate/timeline')
    ])
    userInfo.value = meRes.data
    stats.value.directives = dRes.data.length
    stats.value.documents = docRes.data.length
    stats.value.updates = uRes.data.length
    timeline.value = tRes.data
  } catch (e) {}
  refreshTimer = setInterval(refreshTimeline, 60000)
})

onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<style scoped>
.home-page {
  max-width: 900px;
  margin: 0 auto;
}

/* 时间线卡片 */
.timeline-card {
  margin-bottom: 20px;
}
.timeline-content {
  text-align: center;
  padding: 8px 0;
}
.timeline-label {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 6px;
}
.timeline-date {
  font-size: 34px;
  font-weight: 800;
  color: var(--brand-primary);
  line-height: 1.2;
}
.timeline-meta {
  font-size: 13px;
  color: #64748b;
  margin-top: 6px;
}
.timeline-divider {
  margin: 0 6px;
  color: #cbd5e1;
}

/* 代表信息 */
.info-card {
  margin-bottom: 24px;
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

.info-grid {
  display: flex;
  gap: 32px;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-key {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}
.info-val {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}
.info-val.highlight {
  color: var(--brand-primary);
}

/* 统计卡片 */
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
