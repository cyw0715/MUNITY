<template>
  <div>
    <el-tabs v-model="activeTab">
      <!-- 发言历史 -->
      <el-tab-pane label="发言历史" name="speech">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>发言统计</span>
              </template>
              <el-table :data="speechStats" style="width: 100%">
                <el-table-column prop="delegation_name" label="代表团" />
                <el-table-column prop="count" label="发言次数" width="100" sortable />
                <el-table-column label="总时长" width="100" sortable>
                  <template #default="{ row }">
                    {{ formatDuration(row.total_duration) }}
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="!speechStats.length" description="暂无发言记录" />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>发言历史</span>
              </template>
              <el-table :data="speechRecords" style="width: 100%" max-height="500">
                <el-table-column prop="delegation_name" label="代表团" />
                <el-table-column label="时长" width="80">
                  <template #default="{ row }">
                    {{ formatDuration(row.duration) }}
                  </template>
                </el-table-column>
                <el-table-column label="内容" min-width="150">
                  <template #default="{ row }">
                    <el-button v-if="row.content" size="small" text @click="showSpeechContent(row)">查看</el-button>
                    <span v-else style="color: #999">无</span>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="时间" width="160">
                  <template #default="{ row }">
                    {{ new Date(row.created_at).toLocaleString('zh-CN') }}
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 指令/文件历史 -->
      <el-tab-pane label="指令/文件历史" name="docs">
        <el-card>
          <template #header>
            <span>指令/文件历史</span>
          </template>
          <el-table :data="allDocs" style="width: 100%" max-height="600">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="delegation_name" label="来源代表团" width="120" />
            <el-table-column prop="drafter" label="起草人" width="100" />
            <el-table-column label="类型" width="80">
              <template #default="{ row }">
                <el-tag size="small">{{ typeLabels[row.doc_type] || '指令' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" />
            <el-table-column label="状态/密级" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.status" :type="statusColors[row.status]" size="small">
                  {{ statusLabels[row.status] }}
                </el-tag>
                <el-tag v-else-if="row.secrecy === 'secret'" type="danger" size="small">秘密</el-tag>
                <el-tag v-else type="success" size="small">公开</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="160">
              <template #default="{ row }">
                {{ new Date(row.created_at).toLocaleString('zh-CN') }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 代表团统计 -->
      <el-tab-pane label="代表团统计" name="delegation_stats">
        <el-card>
          <template #header>
            <span>代表团指令/文件统计</span>
          </template>
          <el-table :data="delegationStats" style="width: 100%">
            <el-table-column prop="delegation_name" label="代表团" />
            <el-table-column prop="directives" label="指令数" width="100" sortable />
            <el-table-column prop="documents" label="文件数" width="100" sortable />
            <el-table-column prop="total" label="总计" width="100" sortable />
          </el-table>
          <el-empty v-if="!delegationStats.length" description="暂无数据" />
        </el-card>
      </el-tab-pane>

      <!-- 代表统计 -->
      <el-tab-pane label="代表统计" name="delegate_stats">
        <el-card>
          <template #header>
            <span>代表指令/文件统计</span>
          </template>
          <el-table :data="delegateStats" style="width: 100%">
            <el-table-column prop="delegation_name" label="代表团" width="120" />
            <el-table-column prop="username" label="代表" />
            <el-table-column prop="directives" label="指令数" width="100" sortable />
            <el-table-column prop="documents" label="文件数" width="100" sortable />
            <el-table-column prop="total" label="总计" width="100" sortable />
          </el-table>
          <el-empty v-if="!delegateStats.length" description="暂无数据" />
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 发言内容详情 -->
    <el-dialog v-model="speechContentVisible" title="发言内容" width="600px">
      <div v-if="speechContentItem">
        <p><strong>代表团：</strong>{{ speechContentItem.delegation_name }}</p>
        <p><strong>发言时长：</strong>{{ formatDuration(speechContentItem.duration) }}</p>
        <p><strong>发言内容：</strong></p>
        <div style="white-space: pre-wrap; background: #f5f5f5; padding: 12px; border-radius: 4px; margin-top: 8px">
          {{ speechContentItem.content }}
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api'

const activeTab = ref('speech')
const speechStats = ref([])
const speechRecords = ref([])
const directives = ref([])
const documents = ref([])
const delegations = ref([])
const delegates = ref([])

const speechContentVisible = ref(false)
const speechContentItem = ref(null)

const statusLabels = { unread: '未读', no_simulate: '不推演', pending_simulate: '未推演', simulated: '已推演' }
const statusColors = { unread: 'info', no_simulate: 'danger', pending_simulate: 'warning', simulated: 'success' }
const typeLabels = { declaration: '声明', memorandum: '备忘录', agreement: '协定' }

function formatDuration(seconds) {
  if (!seconds) return '0秒'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m > 0) return `${m}分${s}秒`
  return `${s}秒`
}

function showSpeechContent(item) {
  speechContentItem.value = item
  speechContentVisible.value = true
}

const allDocs = computed(() => {
  const list = [
    ...directives.value.map(d => ({ ...d, _type: 'directive' })),
    ...documents.value.map(d => ({ ...d, _type: 'document' }))
  ]
  return list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
})

const delegationStats = computed(() => {
  const stats = {}
  for (const d of directives.value) {
    if (!stats[d.delegation_id]) {
      stats[d.delegation_id] = { delegation_name: d.delegation_name, directives: 0, documents: 0 }
    }
    stats[d.delegation_id].directives++
  }
  for (const d of documents.value) {
    if (!stats[d.delegation_id]) {
      stats[d.delegation_id] = { delegation_name: d.delegation_name, directives: 0, documents: 0 }
    }
    stats[d.delegation_id].documents++
  }
  return Object.values(stats).map(s => ({ ...s, total: s.directives + s.documents }))
})

const delegateStats = computed(() => {
  const stats = {}
  for (const d of directives.value) {
    const key = `${d.delegation_id}_${d.drafter}`
    if (!stats[key]) {
      stats[key] = { delegation_name: d.delegation_name, username: d.drafter, directives: 0, documents: 0 }
    }
    stats[key].directives++
  }
  for (const d of documents.value) {
    const key = `${d.delegation_id}_${d.drafter}`
    if (!stats[key]) {
      stats[key] = { delegation_name: d.delegation_name, username: d.drafter, directives: 0, documents: 0 }
    }
    stats[key].documents++
  }
  return Object.values(stats).map(s => ({ ...s, total: s.directives + s.documents }))
})

async function loadData() {
  try {
    const [sRes, rRes, dRes, docRes, delRes, delegateRes] = await Promise.all([
      api.get('/api/staff/records/stats'),
      api.get('/api/staff/records'),
      api.get('/api/staff/directives'),
      api.get('/api/staff/documents'),
      api.get('/api/staff/delegations'),
      api.get('/api/staff/delegates')
    ])
    speechStats.value = sRes.data
    speechRecords.value = rRes.data
    directives.value = dRes.data
    documents.value = docRes.data
    delegations.value = delRes.data
    delegates.value = delegateRes.data
  } catch (e) {
    console.error(e)
  }
}

onMounted(loadData)
</script>
