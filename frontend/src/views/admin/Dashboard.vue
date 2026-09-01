<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" v-if="!isFullscreen">
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
        <el-menu-item index="/admin">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/admin/staff">
          <el-icon><User /></el-icon>
          <span>学团管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/committees">
          <el-icon><OfficeBuilding /></el-icon>
          <span>委员会管理</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 主区域 -->
    <div class="main-area">
      <header class="topbar">
        <div class="topbar-left">
          <el-tooltip v-if="isFullscreen" content="返回" placement="bottom">
            <el-button :icon="Back" circle size="small" @click="exitFullscreen" style="margin-right: 12px" />
          </el-tooltip>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>管理员控制台</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentPage">{{ currentPage }}</el-breadcrumb-item>
          </el-breadcrumb>
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
                <el-dropdown-item command="password"><el-icon><Edit /></el-icon>修改密码</el-dropdown-item>
                <el-dropdown-item command="logout" divided><el-icon><SwitchButton /></el-icon>退出登录</el-dropdown-item>
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
import { HomeFilled, User, OfficeBuilding, ArrowDown, FullScreen, Aim, Back, Edit, SwitchButton, Plus } from '@element-plus/icons-vue'
import ChangePassword from '../../components/ChangePassword.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isFullscreen = ref(false)
const changePasswordRef = ref(null)

const activeMenu = computed(() => route.path)

const pageNames = {
  '/admin': '首页',
  '/admin/staff': '学团管理',
  '/admin/committees': '委员会管理',
}
const currentPage = computed(() => pageNames[route.path] || '')

function handleCommand(command) {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  } else if (command === 'password') {
    changePasswordRef.value.show()
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

function exitFullscreen() {
  if (document.fullscreenElement) document.exitFullscreen()
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

onMounted(() => document.addEventListener('fullscreenchange', onFullscreenChange))
onUnmounted(() => document.removeEventListener('fullscreenchange', onFullscreenChange))
</script>

<style scoped>
.admin-layout { display: flex; height: 100vh; width: 100vw; overflow: hidden; }

/* ===== 侧边栏 ===== */
.sidebar {
  width: 220px; min-width: 220px;
  background: var(--sidebar-bg, #1e293b);
  display: flex; flex-direction: column;
  overflow-y: auto; z-index: 10;
}
.sidebar-brand {
  display: flex; align-items: center; gap: 10px;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.brand-icon-small { display: flex; }
.brand-text { font-size: 18px; font-weight: 700; color: #f1f5f9; letter-spacing: -0.02em; }

.sidebar-menu {
  flex: 1; background: transparent !important; border: none !important;
  padding: 8px 0;
}
.sidebar-menu .el-menu-item {
  display: flex; align-items: center; gap: 10px;
  height: 44px !important; line-height: 44px !important;
  margin: 2px 8px; padding: 0 12px !important;
  border-radius: 8px;
  color: #94a3b8 !important;
  transition: all var(--transition-fast);
}
.sidebar-menu .el-menu-item:hover { background: #334155 !important; color: #e2e8f0 !important; }
.sidebar-menu .el-menu-item.is-active { background: #5b92e5 !important; color: #fff !important; font-weight: 600; }
.sidebar-menu .el-menu-item .el-icon { font-size: 18px; color: #38bdf8; transition: color var(--transition-fast); }
.sidebar-menu .el-menu-item.is-active .el-icon { color: #fff; }
.sidebar-menu .el-menu-item:hover .el-icon { color: #7dd3fc; }

/* ===== 主区域 ===== */
.main-area { flex: 1; display: flex; flex-direction: column; min-width: 0; }

/* ===== 顶部栏 ===== */
.topbar {
  height: 60px; min-height: 60px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 28px;
  background: var(--header-bg, #fff);
  border-bottom: 1px solid var(--header-border, #e2e8f0);
  z-index: 5;
}
.topbar-left { display: flex; align-items: center; gap: 12px; }
.topbar-left :deep(.el-breadcrumb__inner) { font-weight: 500 !important; font-size: 14px; }
.topbar-left :deep(.el-breadcrumb__inner.is-link) { color: #64748b !important; }
.topbar-left :deep(.el-breadcrumb__inner.is-link:hover) { color: var(--brand-primary) !important; }

.topbar-right { display: flex; align-items: center; gap: 8px; }

.user-btn {
  display: flex; align-items: center; gap: 8px;
  cursor: pointer; padding: 4px 8px; border-radius: 8px;
  transition: background 0.15s;
}
.user-btn:hover { background: #f1f5f9; }
.user-name { font-size: 14px; font-weight: 500; color: #1e293b; }

/* ===== 内容区 ===== */
.content {
  flex: 1; padding: 24px 28px; overflow-y: auto;
  background: var(--content-bg, #f1f5f9);
}
</style>
