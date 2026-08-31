<template>
  <div class="delegate-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
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
        <el-menu-item index="/delegate">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/delegate/submit">
          <el-icon><Edit /></el-icon>
          <span>提交指令/文件</span>
        </el-menu-item>
        <el-menu-item index="/delegate/agenda">
          <el-icon><List /></el-icon>
          <span>议程单</span>
        </el-menu-item>

        <el-divider />

        <el-menu-item index="/delegate/async-messages" class="menu-highlight">
          <el-icon><Message /></el-icon>
          <span>非对称消息</span>
        </el-menu-item>

        <el-menu-item index="/delegate/updates" :class="{ 'has-notification': notifications.updates }" @click="clearNotification('updates')">
          <el-icon><Bell /></el-icon>
          <span>局势更新</span>
          <span v-if="notifications.updates" class="notif-dot" />
        </el-menu-item>
        <el-menu-item index="/delegate/meeting-files" :class="{ 'has-notification': notifications.meetingFiles }" @click="clearNotification('meetingFiles')">
          <el-icon><Folder /></el-icon>
          <span>会议文件</span>
          <span v-if="notifications.meetingFiles" class="notif-dot" />
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 主区域 -->
    <div class="main-area">
      <header class="topbar">
        <div class="topbar-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/delegate' }">代表端</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentPage">{{ currentPage }}</el-breadcrumb-item>
          </el-breadcrumb>
          <span class="committee-badge">{{ delegationName }}</span>
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
import { HomeFilled, Edit, Bell, Folder, ArrowDown, FullScreen, Aim, Back, List, Message, Edit as EditIcon, SwitchButton } from '@element-plus/icons-vue'
import api from '../../api'
import ChangePassword from '../../components/ChangePassword.vue'
import { useNotification } from '../../composables/useNotification'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const delegationName = ref('')
const isFullscreen = ref(false)
const changePasswordRef = ref(null)

const { notifications, clearNotification, startPolling, stopPolling } = useNotification('delegate')

const activeMenu = computed(() => route.path)

const pageNames = {
  '/delegate': '首页',
  '/delegate/submit': '提交指令/文件',
  '/delegate/agenda': '议程单',
  '/delegate/async-messages': '非对称消息',
  '/delegate/updates': '局势更新',
  '/delegate/meeting-files': '会议文件',
}
const currentPage = computed(() => pageNames[route.path] || '')

function handleCommand(command) {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  } else if (command === 'password') {
    changePasswordRef.value?.show()
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
    const { data } = await api.get('/api/delegate/me')
    delegationName.value = data.delegation_name
  } catch (e) {}
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.delegate-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
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
.brand-icon-small { display: flex; }
.brand-text { font-size: 18px; font-weight: 700; color: #f1f5f9; letter-spacing: -0.02em; }

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
.sidebar-menu .el-menu-item .el-icon { font-size: 18px; }
.sidebar-menu .menu-highlight .el-icon { color: #38bdf8; }
.sidebar-menu .menu-highlight.is-active .el-icon { color: #fff; }

.notif-dot {
  width: 8px; height: 8px;
  background: #ef4444; border-radius: 50%;
  margin-left: auto;
  animation: pulse 1.5s infinite;
}

.el-divider {
  margin: 6px 12px !important;
  border-color: rgba(255,255,255,0.08) !important;
  background: rgba(255,255,255,0.08) !important;
}

/* 主区域 */
.main-area { flex: 1; display: flex; flex-direction: column; min-width: 0; }

/* 顶部栏 */
.topbar {
  height: 60px; min-height: 60px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 28px;
  background: var(--header-bg);
  border-bottom: 1px solid var(--header-border);
  z-index: 5;
}
.topbar-left { display: flex; align-items: center; gap: 12px; }
.topbar-left :deep(.el-breadcrumb__inner) { font-weight: 500 !important; font-size: 14px; }
.topbar-left :deep(.el-breadcrumb__inner.is-link) { color: #64748b !important; }
.topbar-left :deep(.el-breadcrumb__inner.is-link:hover) { color: var(--brand-primary) !important; }
.committee-badge {
  font-size: 11px; background: #edf3fb; color: var(--brand-primary);
  padding: 3px 10px; border-radius: 12px; font-weight: 600;
}
.topbar-right { display: flex; align-items: center; gap: 8px; }
.user-btn {
  display: flex; align-items: center; gap: 8px; cursor: pointer;
  padding: 4px 8px; border-radius: 8px; transition: background 0.15s;
}
.user-btn:hover { background: #f1f5f9; }
.user-name { font-size: 14px; font-weight: 500; color: #1e293b; }

/* 内容区 */
.content {
  flex: 1; padding: 24px 28px; overflow-y: auto;
  background: var(--content-bg);
}
</style>
