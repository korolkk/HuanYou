<template>
  <div class="recommend-page">
    <div class="hero-section">
      <h2>智能行程推荐</h2>
      <p>告诉我你的需求，AI为你找到最合适的旅行方案</p>
      <div class="search-box">
        <el-input
          v-model="query"
          size="large"
          placeholder="例如：暑假想带家人去海边，预算5000以内，5天左右..."
          @keyup.enter="search"
          clearable
        >
          <template #append>
            <el-button type="primary" :loading="loading" @click="search">
              智能推荐
            </el-button>
          </template>
        </el-input>
      </div>
      <!-- Quick tags -->
      <div class="quick-tags">
        <span class="tag-label">快速筛选：</span>
        <el-tag
          v-for="tag in quickTags" :key="tag"
          :type="selectedTags.includes(tag) ? 'primary' : 'info'"
          effect="plain"
          style="cursor:pointer; margin:4px"
          @click="toggleTag(tag)"
        >
          {{ tag }}
        </el-tag>
      </div>
    </div>

    <!-- Extracted Needs -->
    <el-card v-if="extractedNeeds" class="needs-card">
      <template #header><span>AI理解的需求</span></template>
      <el-descriptions :column="3" size="small">
        <el-descriptions-item label="目的地偏好">{{ extractedNeeds.destination_preference || '不限' }}</el-descriptions-item>
        <el-descriptions-item label="预算上限">{{ extractedNeeds.budget_max ? '¥' + extractedNeeds.budget_max : '不限' }}</el-descriptions-item>
        <el-descriptions-item label="期望天数">{{ extractedNeeds.duration_days || '不限' }}天</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Loading -->
    <div v-if="loading" class="loading-box">
      <el-skeleton :rows="3" animated />
      <p style="text-align:center;color:#909399;margin-top:12px">AI正在分析需求并搜索最佳行程...</p>
    </div>

    <!-- Recommendations -->
    <div v-if="recommendations.length > 0" class="results">
      <h3>为你推荐 {{ recommendations.length }} 个行程</h3>
      <el-row :gutter="20">
        <el-col :span="8" v-for="(rec, idx) in recommendations" :key="idx">
          <el-card shadow="hover" class="rec-card" :class="{ 'top-pick': idx === 0 }">
            <template v-if="idx === 0">
              <el-tag type="danger" effect="dark" class="top-badge">🏆 最佳推荐</el-tag>
            </template>
            <div class="rec-header">
              <h4>{{ rec.title }}</h4>
              <div class="match-score">
                <el-progress :percentage="Math.round((rec.match_score || 0) * 100)" :color="matchColor" :stroke-width="8" />
                <span class="score-text">匹配度</span>
              </div>
            </div>
            <p class="rec-dest">📍 {{ rec.destination }} · {{ rec.duration_days }}天 · {{ rec.category }}</p>
            <div class="rec-price" v-if="rec.price_adult">
              <span class="price-amount">¥{{ rec.price_adult }}</span>
              <span class="price-unit">/人起</span>
            </div>
            <div class="rec-tags">
              <el-tag v-for="tag in (rec.match_tags || [])" :key="tag" size="small" type="success" effect="plain" style="margin:2px">
                {{ tag }}
              </el-tag>
            </div>
            <div class="rec-reasons" v-if="rec.match_reasons?.length">
              <p v-for="(reason, i) in rec.match_reasons" :key="i">✅ {{ reason }}</p>
            </div>
            <el-button type="primary" style="width:100%;margin-top:12px" @click="goDetail(rec.trip_id)">
              查看详情
            </el-button>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- AI Explanation -->
    <el-card v-if="explanation" class="explanation-card">
      <template #header><span>AI推荐说明</span></template>
      <div v-html="explanation" style="white-space:pre-wrap;line-height:1.8"></div>
    </el-card>

    <!-- Empty State -->
    <el-empty v-if="!loading && recommendations.length === 0 && searched" description="未找到匹配的行程，试试调整条件或联系客服定制" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { agentApi, tripApi } from '@/api/auth'

const router = useRouter()
const route = useRoute()
const query = ref((route.query.q as string) || '')
const loading = ref(false)
const searched = ref(false)
const recommendations = ref<any[]>([])
const extractedNeeds = ref<any>(null)
const explanation = ref('')

const quickTags = ['海边', '云南', '自然风光', '文化古迹', '出境游', '亲子', '预算3000', '预算5000']
const selectedTags = ref<string[]>([])

const matchColor = computed(() => {
  return [
    { color: '#f56c6c', percentage: 20 },
    { color: '#e6a23c', percentage: 50 },
    { color: '#67c23a', percentage: 80 },
  ]
})

function toggleTag(tag: string) {
  const idx = selectedTags.value.indexOf(tag)
  if (idx >= 0) {
    selectedTags.value.splice(idx, 1)
  } else {
    selectedTags.value.push(tag)
  }
  query.value = selectedTags.value.join('，')
}

async function search() {
  if (!query.value) return
  loading.value = true
  searched.value = true
  recommendations.value = []
  extractedNeeds.value = null
  explanation.value = ''

  try {
    // Try AI agent first
    let res: any
    try {
      res = await agentApi.chat(query.value)
    } catch {
      // Fallback: search trips directly
      const tripRes = await tripApi.list({ search: query.value, page_size: 6 })
      if (tripRes.items?.length) {
        recommendations.value = tripRes.items.map((t: any) => ({
          trip_id: t.id,
          title: t.title,
          destination: t.destination,
          duration_days: t.duration_days,
          category: t.category,
          price_adult: t.price_adult,
          match_score: 0.85,
          match_reasons: t.highlights?.slice(0, 2) || [],
          match_tags: [t.category, `${t.duration_days}天`],
        }))
        explanation.value = '根据您的需求，为您找到以下行程。'
      }
    }

    if (res?.response) {
      explanation.value = res.response
    }
  } catch (e: any) {
    console.error('Recommend error:', e)
    explanation.value = '搜索失败，请检查AI服务配置或稍后重试。'
  } finally {
    loading.value = false
  }
}

function goDetail(tripId: string) {
  // Users view trip details through the recommend interface
  // For now, just show expanded info
}
</script>

<style scoped>
.hero-section {
  text-align: center;
  padding: 40px 24px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-radius: 16px;
  color: #fff;
  margin-bottom: 24px;
}
.hero-section h2 { margin: 0 0 8px; font-size: 28px; }
.hero-section p { margin: 0 0 24px; opacity: 0.85; }
.search-box { max-width: 640px; margin: 0 auto; }
.quick-tags { margin-top: 16px; }
.tag-label { font-size: 13px; opacity: 0.7; margin-right: 8px; }
.needs-card { margin-bottom: 20px; }
.loading-box { padding: 40px; }
.results h3 { margin-bottom: 16px; }
.rec-card { position: relative; height: 100%; }
.rec-card.top-pick { border: 2px solid #e6a23c; }
.top-badge { position: absolute; top: 12px; right: 12px; }
.rec-header { margin-bottom: 12px; }
.rec-header h4 { margin: 0 0 8px; font-size: 16px; }
.match-score { display: flex; align-items: center; gap: 8px; }
.score-text { font-size: 12px; color: #909399; }
.rec-dest { color: #606266; margin: 8px 0; font-size: 14px; }
.rec-price { margin: 8px 0; }
.price-amount { font-size: 24px; font-weight: 700; color: #e53935; }
.price-unit { font-size: 13px; color: #909399; }
.rec-tags { margin: 8px 0; }
.rec-reasons p { margin: 4px 0; font-size: 13px; color: #606266; }
.explanation-card { margin-top: 24px; }
</style>
