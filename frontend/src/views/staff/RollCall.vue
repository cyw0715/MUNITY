<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>点名</span>
          <div>
            <el-tag :type="allPresent ? 'success' : 'warning'" style="margin-right: 12px">
              出席 {{ presentCount }} / {{ totalCount }}
            </el-tag>
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
            <div class="delegation-header" @click.stop>
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Close } from '@element-plus/icons-vue'
import api from '../../api'

const rollcallData = ref([])
const activeDelegations = ref([])

// 按代表团分组
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
    await api.put(`/api/staff/rollcall/${delegateId}?is_present=${!currentState}`)
    loadRollCall()
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

onMounted(loadRollCall)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }

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
