<template>
  <div class="staff-layout">
    <el-container>
      <el-aside v-if="!isFullscreen" width="200px" class="sidebar">
        <div class="logo">MUNITY OS</div>
        <el-menu :default-active="activeMenu" router class="staff-menu">
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
          <el-divider style="margin: 8px 0; border-color: #4a5568" />
          <!-- 默认功能 -->
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
          <el-menu-item index="/staff/directives" :class="{ 'has-notification': notifications.directives }" @click="clearNotification('directives')">
            <el-icon><Document /></el-icon>
            <span>指令管理</span>
            <span v-if="notifications.directives" class="notification-dot"></span>
          </el-menu-item>
          <el-menu-item index="/staff/documents" :class="{ 'has-notification': notifications.documents }" @click="clearNotification('documents')">
            <el-icon><FolderOpened /></el-icon>
            <span>文件管理</span>
            <span v-if="notifications.documents" class="notification-dot"></span>
          </el-menu-item>
          <!-- 可选功能 -->
          <el-menu-item index="/staff/updates" v-if="hasFeature('updates')" :class="{ 'has-notification': notifications.updates }" @click="clearNotification('updates')">
            <el-icon><Bell /></el-icon>
            <span>局势更新</span>
            <span v-if="notifications.updates" class="notification-dot"></span>
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
      </el-aside>
      <el-container>
        <el-header>
          <div class="header-content">
            <div class="header-left">
              <el-tooltip v-if="isFullscreen" content="返回" placement="bottom">
                <el-button :icon="Back" circle size="small" @click="exitFullscreen" style="margin-right: 12px" />
              </el-tooltip>
              <span>学团控制台{{ committeeName ? ' - ' + committeeName : '' }}</span>
            </div>
            <div class="header-right">
              <el-tooltip :content="isFullscreen ? '退出全屏' : '全屏'" placement="bottom">
                <el-button :icon="isFullscreen ? Aim : FullScreen" circle size="small" @click="toggleFullscreen" />
              </el-tooltip>
              <el-dropdown @command="handleCommand">
                <span class="user-info">
                  {{ authStore.user?.username }}
                  <el-icon><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="password">修改密码</el-dropdown-item>
                    <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
    <ChangePassword ref="changePasswordRef" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { HomeFilled, User, Avatar, List, Checked, VideoCamera, Document, FolderOpened, Bell, DataAnalysis, Folder, ArrowDown, FullScreen, Aim, Back, Clock, Select } from '@element-plus/icons-vue'
import api from '../../api'
import ChangePassword from '../../components/ChangePassword.vue'
import { useNotification } from '../../composables/useNotification'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const committeeName = ref('')
const committeeFeatures = ref([])
const isFullscreen = ref(false)
const changePasswordRef = ref(null)

const { notifications, clearNotification, startPolling, stopPolling } = useNotification('staff')

const activeMenu = computed(() => route.path)

function hasFeature(feature) {
  return committeeFeatures.value.includes(feature)
}

function handleCommand(command) {
  if (command === 'password') {
    changePasswordRef.value.show()
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

function exitFullscreen() {
  if (document.fullscreenElement) {
    document.exitFullscreen()
  }
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

onMounted(async () => {
  document.addEventListener('fullscreenchange', onFullscreenChange)
  try {
    const { data } = await api.get('/api/staff/committee')
    committeeName.value = data.name
    committeeFeatures.value = data.features || []
  } catch (e) {}
  startPolling()
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  stopPolling()
})
</script>

<style scoped>
.staff-layout {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.el-container {
  height: 100%;
}

.sidebar {
  background: #304156;
  overflow-y: auto;
  height: 100%;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  font-weight: bold;
  background: #263445;
}

.staff-menu {
  border: none;
  background: #304156;
}

.staff-menu .el-menu-item {
  color: #bfcbd9;
}

.staff-menu .el-menu-item:hover {
  background: #263445;
}

.staff-menu .el-menu-item.is-active {
  color: #409eff;
}

/* 通知动画 */
.staff-menu .el-menu-item.has-notification {
  animation: notification-flash 1.5s ease-in-out infinite;
}

.notification-dot {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  background-color: #f56c6c;
  border-radius: 50%;
  animation: dot-pulse 1.5s ease-in-out infinite;
}

@keyframes notification-flash {
  0%, 100% {
    background-color: transparent;
  }
  50% {
    background-color: rgba(245, 108, 108, 0.15);
  }
}

@keyframes dot-pulse {
  0%, 100% {
    opacity: 1;
    transform: translateY(-50%) scale(1);
  }
  50% {
    opacity: 0.5;
    transform: translateY(-50%) scale(1.3);
  }
}

.el-header {
  background: white;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #606266;
}

.el-main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
