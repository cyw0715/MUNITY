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

    <!-- 服务器资源监控看板 -->
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Monitor /></el-icon>
            服务器资源监控
          </span>
          <div class="monitor-controls">
            <el-radio-group v-model="scope" size="small" @change="fetchMonitor">
              <el-radio-button value="1m">最近1分钟</el-radio-button>
              <el-radio-button value="24h">过去24小时</el-radio-button>
            </el-radio-group>
            <el-tooltip content="刷新" placement="bottom">
              <el-button :icon="Refresh" circle size="small" text @click="fetchMonitor" />
            </el-tooltip>
          </div>
        </div>
      </template>

      <div class="monitor-grid">
        <!-- CPU -->
        <div class="gauge-card">
          <div class="gauge-header">
            <span class="gauge-label">CPU</span>
            <span class="gauge-value" :style="{ color: cpuColor }">{{ monitorData.current?.cpu_percent ?? '—' }}%</span>
          </div>
          <div class="gauge-bar">
            <div class="gauge-track">
              <div class="gauge-fill" :style="{ width: (monitorData.current?.cpu_percent ?? 0) + '%', background: cpuGradient }" />
            </div>
          </div>
          <div v-if="scope === '24h' && chartData.cpu.length" class="sparkline">
            <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" preserveAspectRatio="none" class="sparkline-svg">
              <defs>
                <linearGradient id="cpu-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#5b92e5" stop-opacity="0.3" />
                  <stop offset="100%" stop-color="#5b92e5" stop-opacity="0.02" />
                </linearGradient>
              </defs>
              <path :d="cpuPath" fill="none" stroke="#5b92e5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
              <path :d="cpuAreaPath" fill="url(#cpu-grad)" />
            </svg>
          </div>
        </div>

        <!-- 内存 -->
        <div class="gauge-card">
          <div class="gauge-header">
            <span class="gauge-label">内存</span>
            <span class="gauge-value" :style="{ color: memColor }">{{ monitorData.current?.mem_percent ?? '—' }}%</span>
          </div>
          <div class="gauge-bar">
            <div class="gauge-track">
              <div class="gauge-fill" :style="{ width: (monitorData.current?.mem_percent ?? 0) + '%', background: memGradient }" />
            </div>
          </div>
          <div class="mem-detail">
            <span>{{ formatBytes(monitorData.current?.mem_used ?? 0) }}</span>
            <span class="mem-divider">/</span>
            <span>{{ formatBytes(monitorData.current?.mem_total ?? 0) }}</span>
          </div>
          <div v-if="scope === '24h' && chartData.mem.length" class="sparkline">
            <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" preserveAspectRatio="none" class="sparkline-svg">
              <defs>
                <linearGradient id="mem-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#e84393" stop-opacity="0.3" />
                  <stop offset="100%" stop-color="#e84393" stop-opacity="0.02" />
                </linearGradient>
              </defs>
              <path :d="memPath" fill="none" stroke="#e84393" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
              <path :d="memAreaPath" fill="url(#mem-grad)" />
            </svg>
          </div>
          <div v-if="scope === '1m'" class="mem-detail">
            <span class="mem-hint">每60秒自动采集</span>
          </div>
        </div>

        <!-- 磁盘 -->
        <div class="gauge-card">
          <div class="gauge-header">
            <span class="gauge-label">磁盘</span>
            <span class="gauge-value" :style="{ color: diskColor }">{{ monitorData.current?.disk_percent ?? '—' }}%</span>
          </div>
          <div class="gauge-bar">
            <div class="gauge-track">
              <div class="gauge-fill" :style="{ width: (monitorData.current?.disk_percent ?? 0) + '%', background: diskGradient }" />
            </div>
          </div>
          <div class="mem-detail">
            <span>{{ formatBytes(monitorData.current?.disk_used ?? 0) }}</span>
            <span class="mem-divider">/</span>
            <span>{{ formatBytes(monitorData.current?.disk_total ?? 0) }}</span>
          </div>
        </div>
      </div>
    </el-card>

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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../../api'
import { OfficeBuilding, User, Plus, Monitor, Refresh } from '@element-plus/icons-vue'

const stats = ref({ committees: 0, staff: 0 })
const monitorData = ref({ current: null })
const scope = ref('1m')
const chartWidth = 240
const chartHeight = 48
let refreshTimer = null

const chartData = computed(() => {
  const cpu = monitorData.value.cpu || []
  const mem = monitorData.value.mem || []
  return { cpu, mem }
})

function buildPath(data, smooth = true) {
  if (!data.length) return ''
  const w = chartWidth
  const h = chartHeight
  const values = data.map(d => d[1])
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const pad = 4
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1 || 1)) * w
    const y = h - pad - ((d[1] - min) / range) * (h - pad * 2)
    return [x, y]
  })
  if (points.length < 2) return ''
  // 简单折线
  return points.map((p, i) => (i === 0 ? `M${p[0]},${p[1]}` : `L${p[0]},${p[1]}`)).join(' ')
}

function buildAreaPath(data) {
  if (!data.length) return ''
  const path = buildPath(data)
  const last = data[data.length - 1]
  const first = data[0]
  if (!last || !first) return ''
  const w = chartWidth
  const h = chartHeight
  const lastIdx = (data.length - 1) / (data.length - 1 || 1) * w
  return `${path} L${lastIdx},${h} L0,${h} Z`
}

const cpuPath = computed(() => buildPath(chartData.value.cpu))
const cpuAreaPath = computed(() => buildAreaPath(chartData.value.cpu))
const memPath = computed(() => buildPath(chartData.value.mem))
const memAreaPath = computed(() => buildAreaPath(chartData.value.mem))

function cpuColor() {
  const v = monitorData.value.current?.cpu_percent ?? 0
  if (v > 85) return '#f56c6c'
  if (v > 65) return '#e6a23c'
  return '#67c23a'
}
function memColor() {
  const v = monitorData.value.current?.mem_percent ?? 0
  if (v > 85) return '#f56c6c'
  if (v > 65) return '#e6a23c'
  return '#67c23a'
}
function diskColor() {
  const v = monitorData.value.current?.disk_percent ?? 0
  if (v > 85) return '#f56c6c'
  if (v > 65) return '#e6a23c'
  return '#67c23a'
}
const cpuGradient = computed(() => `linear-gradient(90deg, ${cpuColor()}88, ${cpuColor()})`)
const memGradient = computed(() => `linear-gradient(90deg, ${memColor()}88, ${memColor()})`)
const diskGradient = computed(() => `linear-gradient(90deg, ${diskColor()}88, ${diskColor()})`)

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  let val = bytes
  while (val >= 1024 && i < units.length - 1) { val /= 1024; i++ }
  return `${val.toFixed(i > 0 ? 1 : 0)} ${units[i]}`
}

async function fetchMonitor() {
  try {
    const res = await api.get(`/api/system/monitor?scope=${scope.value}`)
    monitorData.value = res.data
  } catch (e) { console.error(e) }
}

onMounted(async () => {
  try {
    const [cRes, sRes] = await Promise.all([
      api.get('/api/admin/committees'),
      api.get('/api/admin/staff')
    ])
    stats.value.committees = cRes.data.length
    stats.value.staff = sRes.data.length
  } catch (e) { console.error(e) }
  fetchMonitor()
  // 每30秒自动刷新当前数据
  refreshTimer = setInterval(fetchMonitor, 30000)
})

onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<style scoped>
.home-page { max-width: 900px; margin: 0 auto; }

.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
.stat-card {
  background: #fff; border-radius: 14px; padding: 24px;
  display: flex; align-items: center; gap: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06); cursor: pointer;
  transition: all 0.25s ease;
}
.stat-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); transform: translateY(-2px); }
.stat-icon {
  width: 52px; height: 52px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; flex-shrink: 0;
}
.stat-body { flex: 1; }
.stat-value { font-size: 32px; font-weight: 700; color: #0f172a; line-height: 1.2; }
.stat-label { font-size: 14px; color: #64748b; margin-top: 2px; }

/* ===== 监控看板 ===== */
.monitor-card { margin-bottom: 24px; }
.card-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
.card-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 16px; font-weight: 600; color: #0f172a;
}
.card-title .el-icon { color: var(--brand-primary); font-size: 20px; }
.monitor-controls { display: flex; align-items: center; gap: 8px; }

.monitor-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }

/* 仪表卡片 */
.gauge-card {
  background: #f8fafc; border-radius: 12px; padding: 16px;
  border: 1px solid #eef2f6;
}
.gauge-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 10px;
}
.gauge-label { font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
.gauge-value { font-size: 24px; font-weight: 800; line-height: 1; }

/* 进度条 */
.gauge-bar { margin-bottom: 8px; }
.gauge-track {
  height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;
}
.gauge-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }

/* 内存/磁盘详情 */
.mem-detail { font-size: 12px; color: #94a3b8; margin-top: 6px; }
.mem-divider { margin: 0 4px; color: #cbd5e1; }
.mem-hint { color: #cbd5e1; font-style: italic; }

/* 折线图 */
.sparkline { margin-top: 10px; height: 48px; }
.sparkline-svg { width: 100%; height: 100%; }

/* 快捷操作 */
.card-header:last-of-type { margin-bottom: 0; }
.quick-card { margin-top: 0; }
.quick-actions { display: flex; gap: 12px; }
</style>
