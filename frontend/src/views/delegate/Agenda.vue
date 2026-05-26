<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>议程单</span>
        </div>
      </template>

      <el-table :data="agendaItems" style="width: 100%" row-key="id" :tree-props="{ children: 'children' }" default-expand-all>
        <el-table-column prop="title" label="议程标题" min-width="300">
          <template #default="{ row }">
            <span :style="{ paddingLeft: (row.level - 1) * 20 + 'px' }">
              <el-tag size="small" :type="getLevelType(row.level)" style="margin-right: 8px">L{{ row.level }}</el-tag>
              {{ row.title }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '当前' : '待定' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!agendaItems.length" description="暂无议程" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const agendaItems = ref([])

function getLevelType(level) {
  const types = ['', 'success', 'warning', 'danger', 'info']
  return types[(level - 1) % types.length] || ''
}

async function loadAgenda() {
  const { data } = await api.get('/api/delegate/agenda')
  agendaItems.value = buildTree(data)
}

function buildTree(items) {
  const map = {}
  const roots = []

  for (const item of items) {
    map[item.id] = { ...item, children: [] }
  }

  for (const item of items) {
    const node = map[item.id]
    const parentLevel = item.level - 1
    if (parentLevel <= 0) {
      roots.push(node)
    } else {
      const idx = items.indexOf(item)
      let parentId = null
      for (let i = idx - 1; i >= 0; i--) {
        if (items[i].level === parentLevel) {
          parentId = items[i].id
          break
        }
      }
      if (parentId && map[parentId]) {
        map[parentId].children.push(node)
      } else {
        roots.push(node)
      }
    }
  }

  return roots
}

onMounted(loadAgenda)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
