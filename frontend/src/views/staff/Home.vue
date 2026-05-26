<template>
  <div>
    <el-card>
      <template #header>
        <span>委员会信息</span>
      </template>
      <div v-if="committee">
        <p><strong>委员会名称：</strong>{{ committee.name }}</p>
        <p><strong>可用功能：</strong>
          <el-tag v-for="f in committee.features" :key="f" style="margin-right: 4px">
            {{ featureLabels[f] || f }}
          </el-tag>
          <span v-if="!committee.features?.length" style="color: #999">无</span>
        </p>
      </div>
      <el-empty v-else description="您尚未分配到任何委员会" />
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="8">
        <el-card class="stat-card" @click="$router.push('/staff/delegates')">
          <div class="stat-value">{{ stats.delegates }}</div>
          <div class="stat-label">代表人数</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card" @click="$router.push('/staff/delegations')">
          <div class="stat-value">{{ stats.delegations }}</div>
          <div class="stat-label">代表团数量</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card" @click="$router.push('/staff/agenda')">
          <div class="stat-value">{{ stats.agenda }}</div>
          <div class="stat-label">议程数量</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const committee = ref(null)
const stats = ref({ delegates: 0, delegations: 0, agenda: 0 })

const featureLabels = {
  roll_call: '点名',
  agenda: '议程管理',
  motions: '动议管理',
  speakers_list: '发言名单',
  directives: '指令管理',
  documents: '文件管理',
  updates: '局势更新',
  timeline: '时间线'
}

onMounted(async () => {
  try {
    const [cRes, dRes, delRes, aRes] = await Promise.all([
      api.get('/api/staff/committee'),
      api.get('/api/staff/delegates'),
      api.get('/api/staff/delegations'),
      api.get('/api/staff/agenda')
    ])
    committee.value = cRes.data
    stats.value.delegates = dRes.data.length
    stats.value.delegations = delRes.data.length
    stats.value.agenda = aRes.data.length
  } catch (e) {
    console.error(e)
  }
})
</script>

<style scoped>
.stat-card { cursor: pointer; text-align: center; transition: box-shadow 0.2s; }
.stat-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.stat-value { font-size: 36px; font-weight: bold; color: #409eff; }
.stat-label { color: #909399; margin-top: 8px; }
</style>
