<template>
  <div>
    <!-- 时间线显示 -->
    <el-card v-if="timeline && timeline.has_timeline" style="margin-bottom: 20px;">
      <div style="text-align: center;">
        <div style="font-size: 14px; color: #909399; margin-bottom: 4px;">会议时间</div>
        <div style="font-size: 36px; font-weight: bold; color: #409eff;">
          {{ formatDate(timeline.current_date) }}
        </div>
        <div style="color: #909399; margin-top: 4px;">
          已经过 {{ elapsedDays }} 个会议天 / {{ elapsedHours }} 个现实小时
        </div>
        <div style="color: #909399; margin-top: 4px; font-size: 12px;">
          流速：{{ timeline.days_per_hour }} 会议天 / 现实小时
        </div>
      </div>
    </el-card>

    <el-card>
      <template #header>
        <span>代表信息</span>
      </template>
      <div v-if="userInfo">
        <p><strong>账号：</strong>{{ userInfo.username }}</p>
        <p><strong>席位：</strong>{{ userInfo.seat || '未设置' }}</p>
        <p><strong>代表团：</strong>{{ userInfo.delegation_name || '未分配' }}</p>
        <p><strong>身份：</strong>
          <el-tag :type="userInfo.is_leader ? 'success' : 'info'" size="small">
            {{ userInfo.is_leader ? '阁首' : '代表' }}
          </el-tag>
        </p>
      </div>
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="8">
        <el-card class="stat-card" @click="$router.push('/delegate/submit')">
          <div class="stat-value">{{ stats.directives }}</div>
          <div class="stat-label">已提交指令</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card" @click="$router.push('/delegate/submit')">
          <div class="stat-value">{{ stats.documents }}</div>
          <div class="stat-label">已提交文件</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card" @click="$router.push('/delegate/updates')">
          <div class="stat-value">{{ stats.updates }}</div>
          <div class="stat-label">局势更新</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../../api'

const userInfo = ref(null)
const stats = ref({ directives: 0, documents: 0, updates: 0 })
const timeline = ref(null)
let refreshTimer = null

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

// 计算已经过的会议天数
const elapsedDays = computed(() => {
  if (!timeline.value) return 0
  const base = new Date(timeline.value.conference_date)
  const current = new Date(timeline.value.current_date)
  const diff = (current - base) / (1000 * 60 * 60 * 24)
  return Math.round(diff * 10) / 10
})

// 计算已经过的现实小时数
const elapsedHours = computed(() => {
  if (!timeline.value) return 0
  const base = new Date(timeline.value.conference_date)
  const current = new Date(timeline.value.current_date)
  const diffDays = (current - base) / (1000 * 60 * 60 * 24)
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

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.stat-card { cursor: pointer; text-align: center; transition: box-shadow 0.2s; }
.stat-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.stat-value { font-size: 36px; font-weight: bold; color: #409eff; }
.stat-label { color: #909399; margin-top: 8px; }
</style>
