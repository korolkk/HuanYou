<template>
  <div class="history-page">
    <h2>🧭 旅行足迹</h2>

    <!-- Stats Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-item">
          <div class="stat-num">{{ stats.completed_orders || 0 }}</div>
          <div class="stat-label">完成行程</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-item">
          <div class="stat-num">{{ stats.destinations_visited || 0 }}</div>
          <div class="stat-label">到访目的地</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-item">
          <div class="stat-num">¥{{ (stats.total_spend || 0).toLocaleString() }}</div>
          <div class="stat-label">旅行消费</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-item">
          <div class="stat-num">{{ stats.destinations_list?.length || 0 }}</div>
          <div class="stat-label">打卡城市</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Timeline -->
    <el-card v-if="timeline.length > 0" class="timeline-card">
      <template #header><span>旅行时间线</span></template>
      <el-timeline>
        <el-timeline-item
          v-for="item in timeline"
          :key="item.order_id"
          :timestamp="item.departure_date || '待定'"
          placement="top"
          :color="item.status === 'completed' ? '#67C23A' : '#409EFF'"
        >
          <el-card shadow="hover" class="timeline-item">
            <div class="tl-header">
              <h4>{{ item.trip_title }}</h4>
              <el-tag :type="item.status === 'completed' ? 'success' : 'primary'" size="small">
                {{ item.status === 'completed' ? '已完成' : item.status }}
              </el-tag>
            </div>
            <p>📍 {{ item.trip_destination }} · {{ item.duration_days }}天</p>
            <div class="tl-footer">
              <span v-if="item.total_price">💰 ¥{{ item.total_price }}</span>
              <span>📋 {{ item.order_code }}</span>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <el-empty v-else description="还没有旅行记录，去发现你的第一个目的地吧！">
      <el-button type="primary" @click="$router.push('/user/recommend')">查看推荐</el-button>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import client from '@/api/client'

const stats = reactive<any>({})
const timeline = ref<any[]>([])

onMounted(async () => {
  try {
    const [statsRes, timelineRes] = await Promise.all([
      client.get('/user/history/stats'),
      client.get('/user/history/timeline'),
    ])
    Object.assign(stats, statsRes.data)
    timeline.value = timelineRes.data.timeline || []
  } catch { /* use defaults */ }
})
</script>

<style scoped>
.stats-row { margin-bottom: 24px; }
.stat-item { text-align: center; padding: 8px; }
.stat-num { font-size: 28px; font-weight: 700; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.timeline-card { margin-top: 24px; }
.timeline-item { margin-bottom: 8px; }
.tl-header { display: flex; justify-content: space-between; align-items: center; }
.tl-header h4 { margin: 0; }
.tl-footer { display: flex; gap: 16px; margin-top: 8px; font-size: 13px; color: #909399; }
</style>
