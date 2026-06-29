<template>
  <div class="orders-page">
    <h2>我的订单</h2>

    <el-tabs v-model="activeTab" @tab-change="loadOrders">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="进行中" name="active" />
      <el-tab-pane label="已完成" name="completed" />
      <el-tab-pane label="已取消" name="cancelled" />
    </el-tabs>

    <el-table :data="orders" v-loading="loading" stripe>
      <el-table-column prop="order_code" label="订单号" width="160" />
      <el-table-column prop="trip_title" label="行程" min-width="200">
        <template #default="{ row }">
          <strong>{{ row.trip_title }}</strong>
          <div style="font-size:12px;color:#909399">{{ row.trip_destination }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="departure_date" label="出发日期" width="120" />
      <el-table-column label="人数" width="80">
        <template #default="{ row }">{{ row.num_adults + row.num_children }}人</template>
      </el-table-column>
      <el-table-column label="金额" width="120">
        <template #default="{ row }">
          <span v-if="row.total_price" class="price">¥{{ row.total_price }}</span>
          <span v-else class="na">待确认</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="付款" width="80">
        <template #default="{ row }">
          <el-tag :type="row.payment_status === 'paid' ? 'success' : 'warning'" size="small">
            {{ row.payment_status === 'paid' ? '已付' : '待付' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/user/orders/${row.id}`)">详情</el-button>
          <el-button v-if="row.status === 'completed'" size="small" type="warning" @click="showFeedback(row)">
            评价
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && orders.length === 0" description="暂无订单" />

    <!-- Feedback Dialog -->
    <el-dialog v-model="feedbackVisible" title="行程评价" width="500px">
      <el-form :model="feedbackForm">
        <el-form-item label="总体评分">
          <el-rate v-model="feedbackForm.rating_overall" :max="5" show-score />
        </el-form-item>
        <el-form-item label="导游服务">
          <el-rate v-model="feedbackForm.rating_guide" :max="5" />
        </el-form-item>
        <el-form-item label="住宿条件">
          <el-rate v-model="feedbackForm.rating_accommodation" :max="5" />
        </el-form-item>
        <el-form-item label="优点">
          <el-input v-model="feedbackForm.positive_points" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="建议">
          <el-input v-model="feedbackForm.suggestions" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feedbackVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFeedback">提交评价</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { orderApi } from '@/api/auth'

const loading = ref(false)
const orders = ref<any[]>([])
const activeTab = ref('')
const feedbackVisible = ref(false)
const currentOrderId = ref('')

const feedbackForm = reactive({
  rating_overall: 5,
  rating_guide: 5,
  rating_accommodation: 5,
  rating_transport: 5,
  rating_food: 5,
  positive_points: '',
  negative_points: '',
  suggestions: '',
})

const statusMap: Record<string, string> = {
  inquiry: '咨询中', reserved: '已预订', confirmed: '已确认',
  paid: '已付款', pre_trip: '待出发', in_trip: '旅行中',
  completed: '已完成', cancelled: '已取消', refunded: '已退款',
}

function statusLabel(s: string) { return statusMap[s] || s }
function statusType(s: string) {
  if (['completed', 'in_trip'].includes(s)) return 'success'
  if (['reserved', 'confirmed', 'paid', 'pre_trip'].includes(s)) return 'primary'
  if (['cancelled', 'refunded'].includes(s)) return 'danger'
  return 'info'
}

onMounted(() => loadOrders())

async function loadOrders() {
  loading.value = true
  try {
    let status: string | undefined
    if (activeTab.value === 'active') {
      // Fetch multiple active statuses
      const res = await orderApi.myOrders({})
      orders.value = (res.items || []).filter((o: any) =>
        ['reserved', 'confirmed', 'paid', 'pre_trip', 'in_trip'].includes(o.status)
      )
      return
    }
    if (activeTab.value === 'completed') status = 'completed'
    if (activeTab.value === 'cancelled') status = 'cancelled'
    const res = await orderApi.myOrders({ status })
    orders.value = res.items || []
  } finally { loading.value = false }
}

function showFeedback(row: any) {
  currentOrderId.value = row.id
  feedbackVisible.value = true
}

async function submitFeedback() {
  try {
    await orderApi.submitFeedback(currentOrderId.value, { ...feedbackForm })
    ElMessage.success('评价提交成功')
    feedbackVisible.value = false
  } catch { /* handled */ }
}
</script>

<style scoped>
.price { color:#e53935; font-weight:600; }
.na { color:#909399; }
</style>
