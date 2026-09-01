<template>
  <div class="staff-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" v-if="!isFullscreen" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-brand">
        <div class="brand-icon-small">
          <svg width="28" height="28" viewBox="0 0 40 40" fill="none">
            <rect width="40" height="40" rx="10" fill="url(#brand-grad-s)" />
            <text x="20" y="27" text-anchor="middle" fill="white" font-size="20" font-weight="700">M</text>
            <defs><linearGradient id="brand-grad-s" x1="0" y1="0" x2="40" y2="40"><stop stop-color="#5b92e5"/><stop offset="1" stop-color="#3d7ed9"/></linearGradient></defs>
          </svg>
        </div>
        <span class="brand-text">MUNITY OS</span>
      </div>

      <el-menu :default-active="activeMenu" router class="sidebar-menu">
        <el-menu-item index="/staff">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/staff/delegates">
          <el-icon><User /></el-icon>
          <span>代表管理</span>
        </el-menu-item>
        <el-menu-item index="/staff/delegations">
          <el-icon><Avatar /></el-icon>
          <span>代表团管理</span>
        </el-menu-item>
        <el-menu-item index="/staff/agenda" v-if="hasFeature('agenda')">
          <el-icon><List /></el-icon>
          <span>议程管理</span>
        </el-menu-item>

        <el-divider />

        <el-menu-item index="/staff/rollcall">
          <el-icon><Checked /></el-icon>
          <span>点名</span>
        </el-menu-item>
        <el-menu-item index="/staff/meeting">
          <el-icon><VideoCamera /></el-icon>
          <span>会议进行</span>
        </el-menu-item>
        <el-menu-item index="/staff/vote">
          <el-icon><Select /></el-icon>
          <span>投票表决</span>
        </el-menu-item>
        <el-menu-item index="/staff/motion-types">
          <el-icon><Setting /></el-icon>
          <span>动议类型</span>
        </el-menu-item>

        <!-- 非对称消息 -->
        <el-menu-item index="/staff/async-messages">
          <el-icon><Message /></el-icon>
          <span>非对称消息</span>
        </el-menu-item>

        <el-menu-item index="/staff/directives" :class="{ 'has-notification': notifications.directives }" @click="clearNotification('directives')">
          <el-icon><Document /></el-icon>
          <span>指令管理</span>
          <span v-if="notifications.directives" class="notif-dot" />
        </el-menu-item>
        <el-menu-item index="/staff/documents" :class="{ 'has-notification': notifications.documents }" @click="clearNotification('documents')">
          <el-icon><FolderOpened /></el-icon>
          <span>文件管理</span>
          <span v-if="notifications.documents" class="notif-dot" />
        </el-menu-item>
        <el-menu-item index="/staff/updates" v-if="hasFeature('updates')" :class="{ 'has-notification': notifications.updates }" @click="clearNotification('updates')">
          <el-icon><Bell /></el-icon>
          <span>局势更新</span>
          <span v-if="notifications.updates" class="notif-dot" />
        </el-menu-item>
        <el-menu-item index="/staff/records">
          <el-icon><DataAnalysis /></el-icon>
          <span>会议记录</span>
        </el-menu-item>
        <el-menu-item index="/staff/archive">
          <el-icon><Folder /></el-icon>
          <span>存档/恢复</span>
        </el-menu-item>
        <el-menu-item index="/staff/timeline" v-if="hasFeature('timeline')">
          <el-icon><Clock /></el-icon>
          <span>时间线</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 主区域 -->
    <div class="main-area">
      <!-- 顶部栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/staff' }">学团控制台</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentPage">{{ currentPage }}</el-breadcrumb-item>
          </el-breadcrumb>
          <!-- 会场切换 -->
          <el-dropdown v-if="committees.length > 0" @command="handleSwitchCommittee" trigger="click" class="committee-switcher">
            <span class="committee-badge">
              <el-icon style="margin-right: 4px; vertical-align: middle"><OfficeBuilding /></el-icon>
              {{ activeCommitteeName }}
              <el-icon style="margin-left: 2px; font-size: 12px"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="c in committees"
                  :key="c.id"
                  :command="c.id"
                  :class="{ 'is-selected': c.id === activeCommitteeId }"
                >
                  <el-icon v-if="c.id === activeCommitteeId" style="color: var(--brand-primary)"><Check /></el-icon>
                  <span :style="c.id !== activeCommitteeId ? 'padding-left: 22px' : ''">{{ c.name }}</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <div class="topbar-right">
          <el-tooltip :content="isFullscreen ? '退出全屏' : '全屏'" placement="bottom">
            <el-button :icon="isFullscreen ? Aim : FullScreen" circle size="small" text @click="toggleFullscreen" />
          </el-tooltip>
          <el-dropdown @command="handleCommand" trigger="click">
            <span class="user-btn">
              <el-avatar :size="28" style="background: linear-gradient(135deg,#5b92e5,#3d7ed9); color: #fff; font-size: 13px;">
                {{ authStore.user?.username?.charAt(0) || 'U' }}
              </el-avatar>
              <span class="user-name">{{ authStore.user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="password">
                  <el-icon><Edit /></el-icon>修改密码
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content">
        <router-view />
      </main>
    </div>

    <ChangePassword ref="changePasswordRef" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { HomeFilled, User, Avatar, List, Checked, VideoCamera, Document, FolderOpened, Bell, DataAnalysis, Folder, ArrowDown, FullScreen, Aim, Back, Clock, Select, Message, Edit, SwitchButton, OfficeBuilding, Check, Setting } from '@element-plus/icons-vue'
import api from '../../api'
import ChangePassword from '../../components/ChangePassword.vue'
import { useNotification } from '../../composables/useNotification'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const committeeName = ref('')
const activeCommitteeId = ref(null)
const activeCommitteeName = ref('')
const committees = ref([])
const committeeFeatures = ref([])
const isFullscreen = ref(false)
const changePasswordRef = ref(null)
const sidebarCollapsed = ref(false)

const { notifications, clearNotification, startPolling, stopPolling } = useNotification('staff')

const activeMenu = computed(() => route.path)

// 当前页面名称（用于面包屑）
const pageNames = {
  '/staff': '首页',
  '/staff/delegates': '代表管理',
  '/staff/delegations': '代表团管理',
  '/staff/agenda': '议程管理',
  '/staff/rollcall': '点名',
  '/staff/meeting': '会议进行',
  '/staff/vote': '投票表决',
  '/staff/async-messages': '非对称消息',
  '/staff/directives': '指令管理',
  '/staff/documents': '文件管理',
  '/staff/updates': '局势更新',
  '/staff/records': '会议记录',
  '/staff/archive': '存档/恢复',
  '/staff/timeline': '时间线',
}
const currentPage = computed(() => pageNames[route.path] || '')

function hasFeature(feature) {
  return committeeFeatures.value.includes(feature)
}

function handleCommand(command) {
  if (command === 'password') {
    changePasswordRef.value?.show()
  } else if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

onMounted(async () => {
  document.addEventListener('fullscreenchange', () => {
    isFullscreen.value = !!document.fullscreenElement
  })
  try {
    // 并行获取委员会列表和当前委员会信息
    const [committeeRes, myCommitteesRes] = await Promise.all([
      api.get('/api/staff/committee').catch(() => ({ data: null })),
      api.get('/api/staff/my-committees')
    ])
    if (committeeRes.data) {
      activeCommitteeId.value = committeeRes.data.id
      activeCommitteeName.value = committeeRes.data.name
      committeeFeatures.value = committeeRes.data.features || []
    }
    const allCommittees = myCommitteesRes.data || []
    committees.value = allCommittees

    // 从 my-committees 中匹配当前会场名称（如果 committee 接口返回了名称则优先）
    if (!activeCommitteeName.value && allCommittees.length > 0) {
      activeCommitteeId.value = allCommittees[0].id
      activeCommitteeName.value = allCommittees[0].name
    }
  } catch (e) {}
  startPolling()
})

async function handleSwitchCommittee(committeeId) {
  try {
    const { data } = await api.post('/api/staff/switch-committee', { committee_id: committeeId })
    activeCommitteeId.value = data.committee_id
    activeCommitteeName.value = data.committee_name
    committeeFeatures.value = data.features || []

    // 强制刷新当前页面（标题栏、功能标签等需要重新加载）
    const currentPath = route.path
    if (currentPath === '/staff') {
      // 首页 - 使用 router 的 replace 触发重新挂载
      const { data: cData } = await api.get('/api/staff/committee')
      // 只是更新首页组件的数据（组件自己会重新请求）
    }
    window.location.reload()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '切换失败')
  }
}

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.staff-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: 220px;
  min-width: 220px;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  z-index: 10;
}
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.brand-icon-small {
  display: flex;
}
.brand-text {
  font-size: 18px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: -0.02em;
}

.sidebar-menu {
  flex: 1;
  background: transparent !important;
  border: none !important;
  padding: 8px 0;
}
.sidebar-menu .el-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 44px !important;
  line-height: 44px !important;
  margin: 2px 8px;
  padding: 0 12px !important;
  border-radius: 8px;
  color: var(--sidebar-text) !important;
  transition: all var(--transition-fast);
}
.sidebar-menu .el-menu-item:hover {
  background: var(--sidebar-bg-hover) !important;
  color: #e2e8f0 !important;
}
.sidebar-menu .el-menu-item.is-active {
  background: var(--sidebar-bg-active) !important;
  color: var(--sidebar-text-active) !important;
  font-weight: 600;
}
.sidebar-menu .el-menu-item .el-icon {
  font-size: 18px;
  color: #38bdf8;
  transition: color var(--transition-fast);
}
.sidebar-menu .el-menu-item.is-active .el-icon {
  color: #fff;
}
.sidebar-menu .el-menu-item:hover .el-icon {
  color: #7dd3fc;
}

/* 通知红点 */
.notif-dot {
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
  margin-left: auto;
  animation: pulse 1.5s infinite;
}

.el-divider {
  margin: 6px 12px !important;
  border-color: rgba(255,255,255,0.08) !important;
  background: rgba(255,255,255,0.08) !important;
}

/* ===== 主区域 ===== */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* ===== 顶部栏 ===== */
.topbar {
  height: 60px;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  background: var(--header-bg);
  border-bottom: 1px solid var(--header-border);
  z-index: 5;
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.topbar-left :deep(.el-breadcrumb__inner) {
  font-weight: 500 !important;
  font-size: 14px;
}
.topbar-left :deep(.el-breadcrumb__inner.is-link) {
  color: #64748b !important;
}
.topbar-left :deep(.el-breadcrumb__inner.is-link:hover) {
  color: var(--brand-primary) !important;
}
.committee-badge {
  font-size: 11px;
  background: #edf3fb;
  color: var(--brand-primary);
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
}
.committee-badge:hover {
  background: #dce8f9;
}
.committee-switcher :deep(.el-dropdown-menu__item.is-selected) {
  background: #edf3fb;
  color: var(--brand-primary);
  font-weight: 600;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.15s;
}
.user-btn:hover {
  background: #f1f5f9;
}
.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
}

/* ===== 内容区 ===== */
.content {
  flex: 1;
  padding: 24px 28px;
  overflow-y: auto;
  background: var(--content-bg);
}
</style>
