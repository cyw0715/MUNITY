<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span>会议时间线</span>
        <el-tag v-if="timeline" type="success" size="small">运行中</el-tag>
        <el-tag v-else type="info" size="small">未设置</el-tag>
      </div>
    </template>

    <div v-if="timeline" style="text-align: center; margin-bottom: 20px;">
      <div style="font-size: 32px; font-weight: bold; color: #409eff;">
        {{ formatDate(timeline.current_date) }}
      </div>
      <div style="color: #909399; margin-top: 8px;">
        已经过 {{ elapsedDays }} 个会议天 / {{ elapsedHours }} 个现实小时
      </div>
      <div style="color: #909399; margin-top: 4px; font-size: 12px;">
        基准日期：{{ formatDate(timeline.conference_date) }} | 流速：{{ timeline.days_per_hour }} 天/小时
      </div>
    </div>

    <el-form :model="form" label-width="100px">
      <el-form-item label="会议日期">
        <el-date-picker
          v-model="form.conference_date"
          type="date"
          placeholder="选择会议当前日期"
          format="YYYY年MM月DD日"
          value-format="YYYY-MM-DD"
          style="width: 240px"
        />
      </el-form-item>
      
      <el-form-item label="时间流速">
        <el-input-number 
          v-model="form.days_per_hour" 
          :min="0.01" 
          :precision="2"
          :step="0.1"
        />
        <span style="margin-left: 10px; color: #909399;">会议天 / 现实小时</span>
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="saveTimeline">
          {{ timeline ? '更新时间线' : '启动时间线' }}
        </el-button>
        <el-button v-if="timeline" @click="refreshTimeline">刷新</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api'

const timeline = ref(null)
const form = ref({
  conference_date: '',
  days_per_hour: 1.0
})
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

const fetchTimeline = async () => {
  try {
    const res = await api.get('/api/staff/timeline')
    timeline.value = res.data.conference_date ? res.data : null
    if (timeline.value && !form.value.conference_date) {
      form.value.conference_date = timeline.value.conference_date
      form.value.days_per_hour = timeline.value.days_per_hour
    }
  } catch (e) {}
}

const saveTimeline = async () => {
  if (!form.value.conference_date) {
    ElMessage.warning('请选择会议日期')
    return
  }
  try {
    const res = await api.put('/api/staff/timeline', form.value)
    timeline.value = res.data
    ElMessage.success('时间线已更新')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const refreshTimeline = async () => {
  await fetchTimeline()
  ElMessage.success('已刷新')
}

onMounted(() => {
  fetchTimeline()
  refreshTimer = setInterval(fetchTimeline, 60000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>
