<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>投票表决</span>
          <el-button type="primary" @click="showCreateDialog" :disabled="hasActiveVote">发起投票</el-button>
        </div>
      </template>

      <!-- 进行中的投票 -->
      <div v-if="activeVote" class="active-vote">
        <div class="vote-header">
          <h3>{{ activeVote.title }}</h3>
          <el-tag :type="statusTagType" size="large">
            {{ statusTagText }}
          </el-tag>
        </div>

        <div class="vote-info">
          <span>投票规则：{{ ruleLabels[activeVote.rule] }}</span>
          <span v-if="activeVote.veto_enabled" style="margin-left: 16px; color: #f56c6c">已启用一票否决权</span>
        </div>

        <!-- 待开始状态 -->
        <div v-if="activeVote.status === 'pending'" class="pending-actions">
          <el-alert title="投票已创建，点击下方按钮开始投票" type="info" show-icon :closable="false" />
          <el-button type="primary" size="large" @click="handleStartVote" style="margin-top: 16px">开始投票</el-button>
        </div>

        <!-- 投票进度 (仅投票中显示) -->
        <div v-if="activeVote.status === 'voting'" class="vote-progress">
          <div class="progress-item">
            <span class="progress-label">已投票</span>
            <span class="progress-value">{{ activeVote.voted }} / {{ activeVote.can_vote }}</span>
          </div>
          <div class="segmented-bar">
            <div
              v-if="yesPct > 0"
              class="seg-bar-yes"
              :style="{ width: yesPct + '%' }"
            >
              <span v-if="yesPct >= 12" class="seg-label">赞成 {{ yesPct }}%</span>
            </div>
            <div
              v-if="noPct > 0"
              class="seg-bar-no"
              :style="{ width: noPct + '%' }"
            >
              <span v-if="noPct >= 12" class="seg-label">反对 {{ noPct }}%</span>
            </div>
            <div
              v-if="abstainPct > 0"
              class="seg-bar-abstain"
              :style="{ width: abstainPct + '%' }"
            >
              <span v-if="abstainPct >= 12" class="seg-label">弃权 {{ abstainPct }}%</span>
            </div>
          </div>
          <div v-if="yesPct > 0 && yesPct < 12" class="seg-label-outside yes-outside">赞成 {{ yesPct }}%</div>
          <div v-if="noPct > 0 && noPct < 12" class="seg-label-outside no-outside">反对 {{ noPct }}%</div>
          <div v-if="abstainPct > 0 && abstainPct < 12" class="seg-label-outside abstain-outside">弃权 {{ abstainPct }}%</div>
        </div>

        <!-- 投票统计 -->
        <div class="vote-stats">
          <div class="stat-item yes">
            <span class="stat-value">{{ activeVote.yes_count }}</span>
            <span class="stat-label">赞成</span>
          </div>
          <div class="stat-item no">
            <span class="stat-value">{{ activeVote.no_count }}</span>
            <span class="stat-label">反对</span>
          </div>
          <div class="stat-item abstain">
            <span class="stat-value">{{ activeVote.abstain_count }}</span>
            <span class="stat-label">弃权</span>
          </div>
        </div>

        <!-- 代表团投票列表 (仅投票中显示) -->
        <el-table v-if="activeVote.status === 'voting'" :data="voteRecords" style="width: 100%; margin-top: 16px" stripe>
          <el-table-column prop="delegation_name" label="代表团" width="150" />
          <el-table-column label="权限" width="120" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_observer" type="info" size="small">观察员</el-tag>
              <el-tag v-else-if="row.has_veto" type="danger" size="small">否决权</el-tag>
              <el-tag v-else type="success" size="small">投票权</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="投票" width="200" align="center">
            <template #default="{ row }">
              <template v-if="row.is_observer">
                <span style="color: #909399">不参与</span>
              </template>
              <template v-else-if="activeVote.status === 'voting'">
                <el-radio-group v-model="row.choice" @change="(val) => handleVote(row.delegation_id, val)">
                  <el-radio-button value="yes">赞成</el-radio-button>
                  <el-radio-button value="no">反对</el-radio-button>
                  <el-radio-button value="abstain">弃权</el-radio-button>
                </el-radio-group>
              </template>
              <template v-else>
                <el-tag v-if="row.choice === 'yes'" type="success">赞成</el-tag>
                <el-tag v-else-if="row.choice === 'no'" type="danger">反对</el-tag>
                <el-tag v-else-if="row.choice === 'abstain'" type="warning">弃权</el-tag>
                <span v-else style="color: #909399">未投票</span>
              </template>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.choice" type="success" size="small">已投</el-tag>
              <el-tag v-else-if="row.is_observer" type="info" size="small">-</el-tag>
              <el-tag v-else type="warning" size="small">待投</el-tag>
            </template>
          </el-table-column>
        </el-table>

        <!-- 操作按钮 -->
        <div class="vote-actions">
          <el-button v-if="activeVote.status === 'voting'" type="danger" @click="handleEndVote">结束投票</el-button>
          <el-button type="info" @click="handleDelete(activeVote)">删除投票</el-button>
        </div>
      </div>

      <!-- 无投票时显示历史 -->
      <div v-else>
        <el-empty v-if="!votes.length" description="暂无投票记录" />
        <div v-else class="vote-history">
          <h4>历史投票</h4>
          <div v-for="vote in votes" :key="vote.id" class="history-item" @click="showVoteDetail(vote)">
            <div class="history-header">
              <span class="history-title">{{ vote.title }}</span>
              <el-tag :type="vote.status === 'passed' ? 'success' : 'danger'" size="small">
                {{ vote.status === 'passed' ? '通过' : '未通过' }}
              </el-tag>
            </div>
            <div class="history-info">
              <span>赞成: {{ vote.yes_count }}</span>
              <span>反对: {{ vote.no_count }}</span>
              <span>弃权: {{ vote.abstain_count }}</span>
              <span>{{ new Date(vote.created_at).toLocaleString('zh-CN') }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 投票详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="投票详情" width="700px">
      <div v-if="detailVote">
        <div class="detail-header">
          <h3>{{ detailVote.title }}</h3>
          <el-tag :type="detailVote.status === 'passed' ? 'success' : 'danger'" size="large">
            {{ detailVote.status === 'passed' ? '通过' : '未通过' }}
          </el-tag>
        </div>

        <div class="detail-info">
          <p><strong>投票规则：</strong>{{ ruleLabels[detailVote.rule] }}</p>
          <p v-if="detailVote.veto_enabled"><strong>一票否决权：</strong>已启用</p>
          <p><strong>投票时间：</strong>{{ new Date(detailVote.created_at).toLocaleString('zh-CN') }}</p>
          <p v-if="detailVote.ended_at"><strong>结束时间：</strong>{{ new Date(detailVote.ended_at).toLocaleString('zh-CN') }}</p>
        </div>

        <!-- 投票结果统计 -->
        <div class="detail-stats">
          <div class="stat-item yes">
            <span class="stat-value">{{ detailVote.yes_count }}</span>
            <span class="stat-label">赞成</span>
          </div>
          <div class="stat-item no">
            <span class="stat-value">{{ detailVote.no_count }}</span>
            <span class="stat-label">反对</span>
          </div>
          <div class="stat-item abstain">
            <span class="stat-value">{{ detailVote.abstain_count }}</span>
            <span class="stat-label">弃权</span>
          </div>
        </div>

        <!-- 代表团投票明细 -->
        <el-table :data="detailRecords" style="width: 100%; margin-top: 16px" stripe>
          <el-table-column prop="delegation_name" label="代表团" width="150" />
          <el-table-column label="权限" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_observer" type="info" size="small">观察员</el-tag>
              <el-tag v-else-if="row.has_veto" type="danger" size="small">否决权</el-tag>
              <el-tag v-else type="success" size="small">投票权</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="投票结果" width="120" align="center">
            <template #default="{ row }">
              <template v-if="row.is_observer">
                <span style="color: #909399">不参与</span>
              </template>
              <template v-else>
                <el-tag v-if="row.choice === 'yes'" type="success">赞成</el-tag>
                <el-tag v-else-if="row.choice === 'no'" type="danger">反对</el-tag>
                <el-tag v-else-if="row.choice === 'abstain'" type="warning">弃权</el-tag>
                <span v-else style="color: #909399">未投票</span>
              </template>
            </template>
          </el-table-column>
          <el-table-column label="投票时间" min-width="180">
            <template #default="{ row }">
              {{ row.voted_at ? new Date(row.voted_at).toLocaleString('zh-CN') : '-' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 创建投票对话框 -->
    <el-dialog v-model="createDialogVisible" title="发起投票" width="600px">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef">
        <el-form-item label="投票主题" prop="title">
          <el-input v-model="createForm.title" />
        </el-form-item>
        <el-form-item label="投票规则" prop="rule">
          <el-select v-model="createForm.rule" style="width: 100%">
            <el-option label="绝对多数 (2/3赞成，且弃权不过半)" value="qualified_majority" />
            <el-option label="简单多数 (赞成>反对)" value="simple_majority" />
            <el-option label="自定义规则" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.rule === 'custom'" label="通过阈值">
          <el-slider v-model="customThreshold" :min="0" :max="100" :format-tooltip="val => `${val}%`" />
          <span style="margin-left: 8px">赞成比例 ≥ {{ customThreshold }}% 时通过</span>
        </el-form-item>
        <el-form-item label="一票否决权">
          <el-switch v-model="createForm.veto_enabled" />
        </el-form-item>
        <el-divider>代表团设置</el-divider>
        <el-form-item label="否决权国家">
          <el-select v-model="createForm.veto_delegations" multiple style="width: 100%">
            <el-option v-for="d in delegations" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="观察员国家">
          <el-select v-model="createForm.excluded_delegations" multiple style="width: 100%">
            <el-option v-for="d in delegations" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const votes = ref([])
const delegations = ref([])
const createDialogVisible = ref(false)
const createLoading = ref(false)
const createFormRef = ref(null)
const customThreshold = ref(50)
const detailDialogVisible = ref(false)
const detailVote = ref(null)
const detailRecords = ref([])

const createForm = ref({
  title: '',
  rule: 'qualified_majority',
  veto_enabled: false,
  excluded_delegations: [],
  veto_delegations: []
})

const createRules = {
  title: [{ required: true, message: '请输入投票主题', trigger: 'blur' }],
  rule: [{ required: true, message: '请选择投票规则', trigger: 'change' }]
}

const ruleLabels = {
  qualified_majority: '绝对多数',
  simple_majority: '简单多数',
  custom: '自定义规则'
}

const activeVote = computed(() => votes.value.find(v => v.status === 'pending' || v.status === 'voting'))
const hasActiveVote = computed(() => !!activeVote.value)

const statusTagType = computed(() => {
  if (!activeVote.value) return 'info'
  const map = { pending: 'info', voting: 'warning' }
  return map[activeVote.value.status] || 'info'
})

const statusTagText = computed(() => {
  if (!activeVote.value) return ''
  const map = { pending: '待开始', voting: '投票进行中' }
  return map[activeVote.value.status] || ''
})

const voteRecords = ref([])

const voteProgress = computed(() => {
  if (!activeVote.value || activeVote.value.can_vote === 0) return 0
  return Math.round((activeVote.value.voted / activeVote.value.can_vote) * 100)
})

const votedTotal = computed(() => {
  if (!activeVote.value) return 0
  return (activeVote.value.yes_count || 0) + (activeVote.value.no_count || 0) + (activeVote.value.abstain_count || 0)
})

const yesPct = computed(() => {
  if (!activeVote.value || !votedTotal.value) return 0
  return Math.round(((activeVote.value.yes_count || 0) / votedTotal.value) * 100)
})

const noPct = computed(() => {
  if (!activeVote.value || !votedTotal.value) return 0
  return Math.round(((activeVote.value.no_count || 0) / votedTotal.value) * 100)
})

const abstainPct = computed(() => {
  if (!activeVote.value || !votedTotal.value) return 0
  const pct = Math.round(((activeVote.value.abstain_count || 0) / votedTotal.value) * 100)
  const remaining = 100 - yesPct.value - noPct.value
  return remaining > 0 ? remaining : pct
})

async function loadData() {
  try {
    const [vRes, dRes] = await Promise.all([
      api.get('/api/staff/votes'),
      api.get('/api/staff/delegations')
    ])
    votes.value = vRes.data
    delegations.value = dRes.data

    // 如果有活跃投票，加载详情
    if (activeVote.value) {
      await loadVoteDetail(activeVote.value.id)
    }
  } catch (e) {}
}

async function loadVoteDetail(voteId) {
  try {
    const { data } = await api.get(`/api/staff/votes/${voteId}`)
    voteRecords.value = data.records
  } catch (e) {}
}

function showCreateDialog() {
  createForm.value = {
    title: '',
    rule: 'qualified_majority',
    veto_enabled: false,
    excluded_delegations: [],
    veto_delegations: []
  }
  customThreshold.value = 50
  createDialogVisible.value = true
}

async function handleCreate() {
  await createFormRef.value.validate()
  createLoading.value = true
  try {
    const payload = {
      ...createForm.value,
      custom_rule: createForm.value.rule === 'custom' ? { threshold: customThreshold.value / 100 } : null
    }
    await api.post('/api/staff/votes', payload)
    ElMessage.success('投票创建成功')
    createDialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    createLoading.value = false
  }
}

async function handleStartVote() {
  if (!activeVote.value) return
  try {
    await api.put(`/api/staff/votes/${activeVote.value.id}/start`)
    ElMessage.success('投票已开始')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function handleVote(delegationId, choice) {
  if (!activeVote.value) return
  try {
    await api.put(`/api/staff/votes/${activeVote.value.id}/vote?delegation_id=${delegationId}&choice=${choice}`)
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '投票失败')
  }
}

async function handleEndVote() {
  if (!activeVote.value) return
  await ElMessageBox.confirm('确定结束投票？结束后无法再修改。', '提示', { type: 'warning' })
  try {
    const { data } = await api.put(`/api/staff/votes/${activeVote.value.id}/end`)
    ElMessage.success(`投票已结束 - ${data.passed ? '通过' : '未通过'}`)
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function handleDelete(vote) {
  await ElMessageBox.confirm('确定删除该投票？删除后不可恢复。', '提示', { type: 'warning' })
  try {
    await api.delete(`/api/staff/votes/${vote.id}`)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

function showVoteDetail(vote) {
  detailVote.value = vote
  detailDialogVisible.value = true
  // 加载详情数据
  api.get(`/api/staff/votes/${vote.id}`).then(({ data }) => {
    detailRecords.value = data.records
    // 更新统计信息
    detailVote.value = {
      ...detailVote.value,
      ...data
    }
  }).catch(() => {})
}

onMounted(loadData)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.active-vote {
  padding: 16px 0;
}

.vote-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.vote-header h3 {
  margin: 0;
  font-size: 20px;
}

.vote-info {
  color: #606266;
  margin-bottom: 16px;
}
/* 投票进度 - 色块占比条 */
.vote-progress {
  margin-bottom: 24px;
}

.progress-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-label {
  color: #909399;
}

.progress-value {
  font-weight: 500;
}

.segmented-bar {
  display: flex;
  height: 28px;
  border-radius: 14px;
  overflow: hidden;
  background: #ebeef5;
  margin-bottom: 4px;
}

.seg-bar-yes {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.3s ease;
  min-width: 0;
}

.seg-bar-no {
  background: linear-gradient(135deg, #f56c6c, #f89898);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.3s ease;
  min-width: 0;
}

.seg-bar-abstain {
  background: linear-gradient(135deg, #e6a23c, #f0c78a);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.3s ease;
  min-width: 0;
}

.seg-label {
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.seg-label-outside {
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 2px;
}
.seg-label-outside.yes-outside { color: #67c23a; }
.seg-label-outside.no-outside { color: #f56c6c; }
.seg-label-outside.abstain-outside { color: #e6a23c; }

.vote-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.stat-item {
  flex: 1;
  text-align: center;
  padding: 16px;
  border-radius: 8px;
  background: #f5f7fa;
}

.stat-item.yes {
  background: #f0f9eb;
  color: #67c23a;
}

.stat-item.no {
  background: #fef0f0;
  color: #f56c6c;
}

.stat-item.abstain {
  background: #fdf6ec;
  color: #e6a23c;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
}

.stat-label {
  display: block;
  margin-top: 4px;
  font-size: 14px;
}

.vote-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.pending-actions {
  text-align: center;
  padding: 24px 0;
}

.vote-history {
  margin-top: 16px;
}

.vote-history h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.history-item {
  padding: 12px 16px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  border-color: #5b92e5;
  background: #f5f7fa;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.history-title {
  font-weight: 500;
  color: #303133;
}

.history-info {
  display: flex;
  gap: 16px;
  color: #909399;
  font-size: 12px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.detail-header h3 {
  margin: 0;
  font-size: 18px;
}

.detail-info {
  margin-bottom: 16px;
  line-height: 1.8;
}

.detail-info p {
  margin: 4px 0;
}

.detail-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}
</style>
