<template>
  <div class="admin-layout">
    <el-container>
      <el-aside v-if="!isFullscreen" width="200px" class="sidebar">
        <div class="logo">MUNITY OS</div>
        <el-menu :default-active="activeMenu" router class="admin-menu">
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
      </el-aside>
      <el-container>
        <el-header>
          <div class="header-content">
            <div class="header-left">
              <el-tooltip v-if="isFullscreen" content="返回" placement="bottom">
                <el-button :icon="Back" circle size="small" @click="exitFullscreen" style="margin-right: 12px" />
              </el-tooltip>
              <span>管理员控制台</span>
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
import { HomeFilled, User, OfficeBuilding, ArrowDown, FullScreen, Aim, Back } from '@element-plus/icons-vue'
import ChangePassword from '../../components/ChangePassword.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isFullscreen = ref(false)
const changePasswordRef = ref(null)

const activeMenu = computed(() => route.path)

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
  if (document.fullscreenElement) {
    document.exitFullscreen()
  }
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

onMounted(() => {
  document.addEventListener('fullscreenchange', onFullscreenChange)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', onFullscreenChange)
})
</script>

<style scoped>
.admin-layout {
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

.admin-menu {
  border: none;
  background: #304156;
}

.admin-menu .el-menu-item {
  color: #bfcbd9;
}

.admin-menu .el-menu-item:hover {
  background: #263445;
}

.admin-menu .el-menu-item.is-active {
  color: #409eff;
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
