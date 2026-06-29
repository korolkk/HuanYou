<template>
  <div class="trip-list-page">
    <div class="page-header">
      <h2>行程管理</h2>
      <el-button type="primary" @click="$router.push('/shop/import')">导入行程</el-button>
    </div>
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="目的地">
          <el-input v-model="filters.search" placeholder="搜索" clearable @clear="loadTrips" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.category" placeholder="全部" clearable @change="loadTrips">
            <el-option label="国内游" value="国内游" />
            <el-option label="出境游" value="出境游" />
            <el-option label="周边游" value="周边游" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTrips">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card>
      <el-table :data="trips" v-loading="loading" stripe>
        <el-table-column prop="code" label="编号" width="140" />
        <el-table-column prop="title" label="行程名称" min-width="200">
          <template #default="{ row }">
            <router-link :to="`/shop/trips/${row.id}`" class="trip-link">{{ row.title }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="destination" label="目的地" width="120" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_days" label="天数" width="70" />
        <el-table-column label="价格" width="130">
          <template #default="{ row }">
            <span v-if="row.price_adult" class="price">¥{{ row.price_adult }}</span>
            <span v-else class="na">详询</span>
          </template>
        </el-table-column>
        <el-table-column label="特色" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="(h,i) in (row.highlights||[]).slice(0,2)" :key="i" size="small" type="success" style="margin:2px">
              {{ h.slice(0, 20) }}{{ h.length>20?'...':'' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status==='active'?'success':'info'">{{ row.status==='active'?'上架':'草稿' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="$router.push(`/shop/trips/${row.id}`)">详情</el-button>
            <el-button size="small" type="warning" @click="goScript(row)">脚本</el-button>
            <el-button size="small" type="danger" @click="archiveTrip(row)">下架</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="page" :page-size="pageSize" :total="total"
        layout="total, prev, pager, next" @current-change="loadTrips" style="margin-top:20px;justify-content:flex-end"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { tripApi } from '@/api/auth'

const router = useRouter()
const loading = ref(false)
const trips = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = reactive({ search: '', category: '' })

onMounted(() => loadTrips())

async function loadTrips() {
  loading.value = true
  try {
    const res = await tripApi.list({ page: page.value, page_size: pageSize.value, search: filters.search || undefined, category: filters.category || undefined })
    trips.value = res.items || []
    total.value = res.total || 0
  } catch { trips.value = [] } finally { loading.value = false }
}

function resetFilters() { filters.search = ''; filters.category = ''; page.value = 1; loadTrips() }
function goScript(row: any) { router.push(`/shop/scripts?trip_id=${row.id}`) }

async function archiveTrip(row: any) {
  await ElMessageBox.confirm(`下架「${row.title}」？`, '确认', { type: 'warning' })
  try { await tripApi.delete(row.id); ElMessage.success('已下架'); loadTrips() } catch { /* handled */ }
}
</script>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
.page-header h2 { margin:0; }
.filter-card { margin-bottom:16px; }
.trip-link { color:#1976d2; font-weight:500; text-decoration:none; }
.price { color:#e53935; font-weight:600; }
.na { color:#909399; }
</style>
