<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="login-bg">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>

    <div class="login-card animate-slide-up">
      <!-- Logo区域 -->
      <div class="login-brand">
        <div class="brand-icon">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <rect width="40" height="40" rx="10" fill="url(#brand-grad)" />
            <text x="20" y="27" text-anchor="middle" fill="white" font-size="20" font-weight="700" font-family="system-ui">M</text>
            <defs>
              <linearGradient id="brand-grad" x1="0" y1="0" x2="40" y2="40">
                <stop stop-color="#5b92e5" />
                <stop offset="1" stop-color="#3d7ed9" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="login-title">MUNITY OS</h1>
        <p class="login-subtitle">模拟联合国会议管理系统</p>
      </div>

      <!-- 登录表单 -->
      <el-form ref="formRef" :model="form" :rules="rules" class="login-form" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            :prefix-icon="User"
            size="large"
            clearable
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            size="large"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="login-btn"
          @click="handleLogin"
        >
          <span v-if="!loading">登 录</span>
        </el-button>
      </el-form>

      <!-- 底部 -->
      <div class="login-footer">
        <span class="footer-text">MUNITY OS v2</span>
        <span class="footer-dot">·</span>
        <el-tooltip content="全屏" placement="top">
          <el-button :icon="FullScreen" circle size="small" text @click="toggleFullscreen" />
        </el-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, FullScreen } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

async function handleLogin() {
  if (!formRef.value) return
  await formRef.value.validate()
  loading.value = true

  try {
    const { data } = await api.post('/api/auth/login', form)
    authStore.setAuth(data.access_token, {
      id: data.user_id,
      username: data.username,
      role: data.role
    })

    ElMessage.success({
      message: `欢迎回来，${data.username}`,
      duration: 2000
    })

    const roleRoutes = { admin: '/admin', staff: '/staff', delegate: '/delegate' }
    setTimeout(() => {
      router.push(roleRoutes[data.role] || '/login')
    }, 300)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '用户名或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #0f172a;
}

/* 背景装饰 */
.login-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}
.bg-circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
}
.bg-circle-1 {
  width: 500px; height: 500px;
  background: #5b92e5;
  top: -150px; left: -150px;
  animation: float 8s ease-in-out infinite;
}
.bg-circle-2 {
  width: 400px; height: 400px;
  background: #5b92e5;
  bottom: -100px; right: -100px;
  animation: float 10s ease-in-out infinite reverse;
}
.bg-circle-3 {
  width: 300px; height: 300px;
  background: #7bb5f0;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  animation: float 12s ease-in-out infinite 2s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

/* 登录卡片 */
.login-card {
  position: relative;
  width: 400px;
  padding: 44px 36px 32px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  z-index: 1;
}

.login-brand {
  text-align: center;
  margin-bottom: 32px;
}
.brand-icon {
  display: inline-flex;
  margin-bottom: 12px;
}
.login-title {
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
  margin: 0;
}
.login-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 4px 0 0;
}

.login-form {
  margin-bottom: 8px;
}
.login-form :deep(.el-form-item) {
  margin-bottom: 20px !important;
}

.login-btn {
  width: 100%;
  height: 46px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 2px;
  border-radius: 10px !important;
  background: linear-gradient(135deg, #5b92e5, #3d7ed9);
  border: none;
  transition: all 0.25s ease;
}
.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(26, 115, 232, 0.35);
}
.login-btn:active {
  transform: translateY(0);
}

.login-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}
.footer-text {
  font-size: 12px;
  color: #94a3b8;
}
.footer-dot {
  color: #cbd5e1;
  font-size: 12px;
}
</style>
