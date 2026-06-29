<template>
  <div class="trip-detail" v-loading="loading">
    <el-page-header @back="$router.push('/shop/trips')" :content="trip?.title || '行程详情'" />

    <template v-if="trip">
      <el-row :gutter="24" style="margin-top: 24px;">
        <el-col :span="16">
          <!-- Basic Info -->
          <el-card class="section">
            <template #header><span>基本信息</span></template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="编号">{{ trip.code }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="trip.status === 'active' ? 'success' : 'info'">
                  {{ trip.status === 'active' ? '上架中' : trip.status }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="目的地">{{ trip.destination }}</el-descriptions-item>
              <el-descriptions-item label="类型">{{ trip.category }}</el-descriptions-item>
              <el-descriptions-item label="天数">{{ trip.duration_days }}天{{ trip.duration_nights }}晚</el-descriptions-item>
              <el-descriptions-item label="出发地">{{ trip.departure_city || '全国出发' }}</el-descriptions-item>
              <el-descriptions-item label="最佳季节">{{ trip.best_season || '全年' }}</el-descriptions-item>
              <el-descriptions-item label="成团人数">{{ trip.group_size_min }}-{{ trip.group_size_max || '不限' }}人</el-descriptions-item>
              <el-descriptions-item label="成人价"><span style="color:#e53935;font-weight:700;font-size:18px">¥{{ trip.price_adult }}</span></el-descriptions-item>
              <el-descriptions-item label="儿童价">¥{{ trip.price_child || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- AI Summary -->
          <el-card class="section" v-if="trip.summary">
            <template #header><span>AI概要</span></template>
            <p class="summary-text">{{ trip.summary }}</p>
          </el-card>

          <!-- Highlights & Recommendations -->
          <el-card class="section" v-if="trip.highlights?.length">
            <template #header><span>特色亮点</span></template>
            <el-tag v-for="(h,i) in trip.highlights" :key="i" size="large" type="success" effect="plain" style="margin:4px">
              {{ h }}
            </el-tag>
          </el-card>

          <el-card class="section" v-if="trip.recommendation_reasons?.length">
            <template #header><span>推荐理由</span></template>
            <ul>
              <li v-for="(r,i) in trip.recommendation_reasons" :key="i">{{ r }}</li>
            </ul>
          </el-card>

          <!-- Day-by-Day Schedule -->
          <el-card class="section">
            <template #header><span>每日行程 ({{ trip.schedules?.length || 0 }}天)</span></template>
            <el-timeline v-if="trip.schedules?.length">
              <el-timeline-item
                v-for="s in trip.schedules"
                :key="s.id"
                :timestamp="`第${s.day_number}天`"
                placement="top"
                :color="s.schedule_type === '景点' ? '#409EFF' : s.schedule_type === '交通' ? '#E6A23C' : '#67C23A'"
              >
                <el-card shadow="hover">
                  <h4>{{ s.theme || '行程安排' }}</h4>
                  <el-tag size="small" style="margin-bottom:8px">{{ s.schedule_type }}</el-tag>
                  <p v-if="s.description">{{ s.description }}</p>
                  <el-row :gutter="12" v-if="s.location || s.hotel_name">
                    <el-col :span="12" v-if="s.location">📍 {{ s.location }}</el-col>
                    <el-col :span="12" v-if="s.hotel_name">🏨 {{ s.hotel_name }}</el-col>
                    <el-col :span="12" v-if="s.meal_included">🍽️ {{ s.meal_included }}</el-col>
                    <el-col :span="12" v-if="s.transport_type">🚌 {{ s.transport_type }}</el-col>
                  </el-row>
                  <div v-if="s.tips" class="tips">💡 {{ s.tips }}</div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无日程安排" />
          </el-card>
        </el-col>

        <!-- Sidebar -->
        <el-col :span="8">
          <el-card>
            <template #header><span>费用说明</span></template>
            <h4>费用包含</h4>
            <ul><li v-for="(item,i) in trip.price_includes||[]" :key="i">{{ item }}</li></ul>
            <h4>费用不含</h4>
            <ul><li v-for="(item,i) in trip.price_excludes||[]" :key="i">{{ item }}</li></ul>
            <el-divider v-if="trip.single_room_supplement" />
            <p v-if="trip.single_room_supplement">单房差: ¥{{ trip.single_room_supplement }}</p>
          </el-card>

          <el-card style="margin-top:16px">
            <template #header><span>出发日期</span></template>
            <el-tag v-for="(d,i) in trip.departure_dates||[]" :key="i" style="margin:4px">{{ d }}</el-tag>
            <el-empty v-if="!trip.departure_dates?.length" description="暂无排期" :image-size="60" />
          </el-card>

          <el-card style="margin-top:16px">
            <template #header><span>操作</span></template>
            <el-space direction="vertical" :size="12" style="width:100%">
              <el-button type="primary" style="width:100%" @click="generateScript">生成视频脚本</el-button>
              <el-button style="width:100%" @click="generateSummary">重新生成概要</el-button>
            </el-space>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { tripApi } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const trip = ref<any>(null)

onMounted(async () => {
  const id = route.params.id as string
  if (!id) return
  loading.value = true
  try {
    trip.value = await tripApi.get(id)
  } catch { /* handled */ } finally { loading.value = false }
})

function generateScript() {
  if (trip.value) {
    router.push(`/shop/scripts?trip_id=${trip.value.id}&title=${encodeURIComponent(trip.value.title)}`)
  }
}

async function generateSummary() {
  ElMessage.info('概要生成需要配置AI API Key后启用')
}
</script>

<style scoped>
.section { margin-bottom: 20px; }
.summary-text { line-height: 1.8; color: #606266; }
.tips { margin-top: 8px; padding: 8px; background: #fdf6ec; border-radius: 6px; font-size: 13px; color: #e6a23c; }
h4 { margin: 12px 0 6px; color: #303133; }
ul { margin: 0; padding-left: 18px; }
li { line-height: 1.8; color: #606266; }
</style>
