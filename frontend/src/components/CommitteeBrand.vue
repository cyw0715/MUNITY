<template>
  <div class="sidebar-brand">
    <div class="brand-icon-small">
      <!-- 上传的图标优先，其次徽标文字，最后默认的 M -->
      <img v-if="logoSrc" :src="logoSrc" class="brand-img" alt="" />
      <span v-else-if="icon" class="brand-badge">{{ icon }}</span>
      <svg v-else width="28" height="28" viewBox="0 0 40 40" fill="none">
        <rect width="40" height="40" rx="10" fill="url(#brand-grad-default)" />
        <text x="20" y="27" text-anchor="middle" fill="white" font-size="20" font-weight="700">M</text>
        <defs>
          <linearGradient id="brand-grad-default" x1="0" y1="0" x2="40" y2="40">
            <stop stop-color="#5b92e5" />
            <stop offset="1" stop-color="#3d7ed9" />
          </linearGradient>
        </defs>
      </svg>
    </div>
    <span class="brand-text">{{ title || 'MUNITY OS' }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 徽标文字（1–2 字符，可为 emoji）
  icon: { type: String, default: '' },
  // 上传的图标文件名；非空表示已设置图标
  logoImage: { type: String, default: '' },
  // 委员会 id，用于拼接图标地址
  committeeId: { type: [Number, String], default: null },
  // 侧边栏标题
  title: { type: String, default: '' },
})

// 带上文件名做缓存标识，避免替换图标后浏览器仍用旧图
const logoSrc = computed(() => {
  if (!props.logoImage || !props.committeeId) return ''
  return `/api/committee-logo/${props.committeeId}?v=${encodeURIComponent(props.logoImage)}`
})
</script>

<style scoped>
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.brand-icon-small { display: flex; }
.brand-img {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  object-fit: cover;
  display: block;
}
.brand-badge {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, #5b92e5, #3d7ed9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  line-height: 1;
  overflow: hidden;
}
.brand-text {
  font-size: 18px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: -0.02em;
}
</style>
