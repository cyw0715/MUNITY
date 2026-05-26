<template>
  <el-card>
    <template #header>
      <span>指令管理</span>
    </template>

    <el-table :data="directives" style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="delegation_name" label="来源代表团" width="120" />
      <el-table-column prop="drafter" label="起草人" width="100" />
      <el-table-column prop="admin_points" label="行政点数" width="90" />
      <el-table-column prop="secrecy" label="密级" width="80">
        <template #default="{ row }">
          <el-tag :type="row.secrecy === 'secret' ? 'danger' : 'success'" size="small">
            {{ row.secrecy === 'secret' ? '秘密' : '公开' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="涉及部门" min-width="150">
        <template #default="{ row }">
          <el-tag v-for="dept in row.departments" :key="dept" size="small" style="margin-right: 4px; margin-bottom: 4px">
            {{ dept }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusColors[row.status]" size="small">
            {{ statusLabels[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="350">
        <template #default="{ row }">
          <el-button size="small" @click="showDetail(row)">查看</el-button>
          <el-dropdown @command="(cmd) => updateStatus(row.id, cmd)" trigger="click">
            <el-button size="small" type="primary">
              设置状态 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="no_simulate">不推演</el-dropdown-item>
                <el-dropdown-item command="pending_simulate">未推演</el-dropdown-item>
                <el-dropdown-item command="simulated">已推演</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!directives.length" description="暂无指令" />
  </el-card>

  <!-- 详情对话框 -->
  <el-dialog v-model="detailVisible" title="指令详情" width="600px">
    <div v-if="detailItem">
      <p><strong>来源代表团：</strong>{{ detailItem.delegation_name }}</p>
      <p><strong>起草人：</strong>{{ detailItem.drafter }}</p>
      <p><strong>行政点数：</strong>{{ detailItem.admin_points }}</p>
      <p><strong>密级：</strong>
        <el-tag :type="detailItem.secrecy === 'secret' ? 'danger' : 'success'" size="small">
          {{ detailItem.secrecy === 'secret' ? '秘密' : '公开' }}
        </el-tag>
      </p>
      <p><strong>涉及部门：</strong>
        <el-tag v-for="dept in detailItem.departments" :key="dept" size="small" style="margin-right: 4px">
          {{ dept }}
        </el-tag>
      </p>
      <p><strong>状态：</strong>
        <el-tag :type="statusColors[detailItem.status]" size="small">
          {{ statusLabels[detailItem.status] || detailItem.status }}
        </el-tag>
      </p>
      <el-divider />
      <div style="white-space: pre-wrap; background: #f5f7fa; padding: 16px; border-radius: 4px">
        {{ detailItem.content || '无内容' }}
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import api from '../../api'

const directives = ref([])
const detailVisible = ref(false)
const detailItem = ref(null)

const statusLabels = {
  unread: '未读',
  no_simulate: '不推演',
  pending_simulate: '未推演',
  simulated: '已推演'
}

const statusColors = {
  unread: 'info',
  no_simulate: 'danger',
  pending_simulate: 'warning',
  simulated: 'success'
}

async function loadDirectives() {
  try {
    const { data } = await api.get('/api/staff/directives')
    directives.value = data
  } catch (e) {}
}

function showDetail(item) {
  detailItem.value = item
  detailVisible.value = true
}

async function updateStatus(id, status) {
  try {
    await api.put(`/api/staff/directives/${id}/status?status=${status}`)
    ElMessage.success('状态更新成功')
    loadDirectives()
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

onMounted(loadDirectives)
</script>
