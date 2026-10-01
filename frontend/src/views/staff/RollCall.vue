<template>
  <div class="animate-fade-in">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>点名</span>
          <div class="header-actions">
            <el-tag :type="allPresent ? 'success' : 'warning'" style="margin-right: 12px">
              出席 {{ presentCount }} / {{ totalCount }}
            </el-tag>
            <el-button
              type="primary"
              size="small"
              :loading="markingAll"
              :disabled="!totalCount || allPresent"
              @click="setAllPresent(true)"
            >
              一键全部出席
            </el-button>
            <el-button
              size="small"
              :loading="markingAll"
              :disabled="!totalCount || presentCount === 0"
              @click="setAllPresent(false)"
            >
              全部未出席
            </el-button>
          </div>
        </div>
      </template>

      <el-collapse v-model="activeDelegations">
        <el-collapse-item
          v-for="delegation in groupedData"
          :key="delegation.delegation_id"
          :name="delegation.delegation_id"
        >
          <template #title>
            <div class="delegation-header">
              <span class="delegation-name">{{ delegation.delegation_name }}</span>
              <el-tag size="small" :type="getDelegationStatus(delegation).type">
                {{ getDelegationStatus(delegation).text }}
              </el-tag>
            </div>
          </template>

          <div class="members-grid">
            <div
              v-for="member in delegation.members"
              :key="member.id"
              class="member-item"
              :class="{ present: member.is_present }"
              @click="toggleDelegate(member.id, member.is_present)"
            >
              <el-icon class="check-icon" :class="{ checked: member.is_present }">
                <Check v-if="member.is_present" />
                <Close v-else />
              </el-icon>
              <div class="member-info">
                <span class="member-name">{{ member.seat }}</span>
                <el-tag v-if="member.is_leader" size="small" type="success" style="margin-left: 4px">阁首</el-tag>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <el-empty v-if="!rollcallData.length" description="暂无代表" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Close } from '@element-plus/icons-vue'
import api from '../../api'
import { useWebSocket } from '../../composables/useWebSocket'

const rollcallData = ref([])
const activeDelegations = ref([])
const markingAll = ref(false)

// WebSocket 监听点名更新
let wsCleanup = null
onMounted(() => {
  loadRollCall()
  const ws = useWebSocket()
  const handler = (data) => {
    if (data.type === 'rollcall_updated') {
      // scope=all 是整表变更（一键出席），重新拉取；否则就地更新单个代表
      if (data.scope === 'all') {
        loadRollCall()
        return
      }
      const found = rollcallData.value.find(d => d.id === data.delegate_id)
      if (found) {
        found.is_present = data.is_present
      }
    }
  }
  ws.on('*', handler)
  wsCleanup = () => ws.off('*', handler)
})
onUnmounted(() => {
  if (wsCleanup) wsCleanup()
})
const groupedData = computed(() => {
  const map = new Map()
  for (const item of rollcallData.value) {
    if (!map.has(item.delegation_id)) {
      map.set(item.delegation_id, {
        delegation_id: item.delegation_id,
        delegation_name: item.delegation_name,
        members: []
      })
    }
    map.get(item.delegation_id).members.push(item)
  }
  return Array.from(map.values())
})

const totalCount = computed(() => rollcallData.value.length)

const presentCount = computed(() => rollcallData.value.filter(d => d.is_present).length)

const allPresent = computed(() => totalCount.value > 0 && presentCount.value === totalCount.value)

function getDelegationStatus(delegation) {
  const total = delegation.members.length
  const present = delegation.members.filter(m => m.is_present).length
  if (present === 0) return { type: 'info', text: `0/${total}` }
  if (present === total) return { type: 'success', text: `${present}/${total}` }
  return { type: 'warning', text: `${present}/${total}` }
}

async function loadRollCall() {
  try {
    const { data } = await api.get('/api/staff/rollcall')
    rollcallData.value = data
  } catch (e) {
    ElMessage.error('加载点名数据失败')
  }
}

async function toggleDelegate(delegateId, currentState) {
  try {
    await api.put(`/api/staff/rollcall/${delegateId}`, { is_present: !currentState })
    // 不调用 loadRollCall() — WS 会更新
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

// 一键设置全部代表的出席状态（后端单次批量更新 + 一次广播）
async function setAllPresent(isPresent) {
  markingAll.value = true
  try {
    const { data } = await api.put('/api/staff/rollcall/all', { is_present: isPresent })
    // 本地立即反映，不依赖 WS 回环
    rollcallData.value.forEach(d => { d.is_present = isPresent })
    ElMessage.success(isPresent
      ? `已将 ${data.updated ?? totalCount.value} 位代表标记为出席`
      : `已取消全部出席标记`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    markingAll.value = false
  }
}
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.header-actions { display: flex; align-items: center; }

.delegation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 16px;
}

.delegation-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.members-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  padding: 8px 0;
}

.member-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.member-item:hover {
  background: #f5f7fa;
}

.member-item.present {
  background: #f0f9eb;
  border-color: #67c23a;
}

.check-icon {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  font-size: 14px;
  background: #dcdfe6;
  color: white;
  transition: all 0.2s;
  flex-shrink: 0;
}

.check-icon.checked {
  background: #67c23a;
}

.member-info {
  display: flex;
  align-items: center;
}

.member-name {
  font-size: 14px;
  color: #303133;
}
</style>
