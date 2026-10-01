import { ref } from 'vue'
import api from '../api'

/**
 * 当前会场启用的功能列表（委员会 features）。
 *
 * null 表示「未知」——尚未加载或加载失败。此时一律放行，
 * 宁可多显示也不要误藏功能；真正的拦截由后端 require_feature 兜底。
 */
const features = ref(null)
let cachedUserId = null

/** 由各端 Dashboard 在拿到委员会信息后写入，避免重复请求 */
export function setCommitteeFeatures(list, userId) {
  features.value = Array.isArray(list) ? list : []
  cachedUserId = userId ?? null
}

export function getCommitteeFeatures() {
  return features
}

/** 供路由守卫使用：未知时按角色拉取一次；失败保持未知 */
export async function ensureCommitteeFeatures(role, userId) {
  if (features.value !== null && cachedUserId === userId) return features.value
  cachedUserId = userId ?? null
  try {
    const url = role === 'delegate' ? '/api/delegate/me' : '/api/staff/committee'
    const { data } = await api.get(url)
    features.value = data.committee_features || data.features || []
  } catch (e) {
    features.value = null
  }
  return features.value
}

export function hasFeature(feature) {
  if (features.value === null) return true
  return features.value.includes(feature)
}
