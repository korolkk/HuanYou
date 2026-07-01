<template>
  <div class="script-studio">
    <h2>脚本工作台</h2>
    <p class="subtitle">AI短视频脚本生成 · 一键导出剪映</p>

    <!-- Progress Steps -->
    <el-steps :active="currentStep" align-center style="margin-bottom: 32px">
      <el-step title="选择行程" />
      <el-step title="配置参数" />
      <el-step title="AI生成" />
      <el-step title="预览导出" />
    </el-steps>

    <!-- Step 1: Select Trip -->
    <el-card v-if="currentStep === 1">
      <template #header>选择行程</template>
      <el-row :gutter="20">
        <el-col :span="16">
          <TripSearchSelect @select="onTripSelect" />
        </el-col>
        <el-col :span="8">
          <el-card v-if="selectedTrip" shadow="never" class="trip-preview">
            <h4>{{ selectedTrip.title }}</h4>
            <p>📍 {{ selectedTrip.destination }} · {{ selectedTrip.duration_days }}天 · {{ selectedTrip.category }}</p>
            <p v-if="selectedTrip.price_adult">💰 ¥{{ selectedTrip.price_adult }}/人</p>
            <el-tag v-for="h in (selectedTrip.highlights || []).slice(0, 3)" :key="h" size="small" type="success" style="margin:2px">
              {{ h.slice(0, 25) }}
            </el-tag>
          </el-card>
          <el-empty v-else description="请选择一个行程" :image-size="80" />
        </el-col>
      </el-row>
      <div style="margin-top:20px;text-align:right">
        <el-button type="primary" :disabled="!selectedTrip" @click="currentStep = 2">下一步</el-button>
      </div>
    </el-card>

    <!-- Step 2: Configure -->
    <el-card v-if="currentStep === 2">
      <template #header>配置脚本参数</template>
      <el-form label-width="100px">
        <el-form-item label="发布平台">
          <el-radio-group v-model="config.platform">
            <el-radio-button value="抖音">抖音</el-radio-button>
            <el-radio-button value="快手">快手</el-radio-button>
            <el-radio-button value="视频号">视频号</el-radio-button>
            <el-radio-button value="小红书">小红书</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="视频时长">
          <el-slider v-model="config.duration_seconds" :min="60" :max="600" :step="30" show-input style="max-width:400px" />
          <span style="margin-left:8px;color:#909399">秒 ({{ Math.floor(config.duration_seconds / 60) }}分{{ config.duration_seconds % 60 }}秒)</span>
        </el-form-item>
        <el-form-item label="脚本风格">
          <el-radio-group v-model="config.style">
            <el-radio-button value="活泼">活泼</el-radio-button>
            <el-radio-button value="文艺">文艺</el-radio-button>
            <el-radio-button value="专业">专业</el-radio-button>
            <el-radio-button value="感性">感性</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <div style="margin-top:20px;text-align:right">
        <el-button @click="currentStep = 1">上一步</el-button>
        <el-button type="primary" @click="handleGenerate">开始生成脚本</el-button>
      </div>
    </el-card>

    <!-- Step 3: Generation Progress -->
    <GenerationProgress
      v-if="currentStep === 3"
      :stage="genStage"
      :status="genStatus"
    />

    <!-- Step 4: Preview & Export -->
    <div v-if="currentStep === 4 && currentScript">
      <el-row :gutter="24">
        <el-col :span="16">
          <el-card>
            <template #header>
              <span>脚本编辑</span>
              <el-tag :type="currentScript.status === 'completed' ? 'success' : 'warning'" style="margin-left:12px">
                {{ currentScript.status === 'completed' ? '已完成' : '需修改' }}
              </el-tag>
            </template>
            <ScriptSegmentEditor
              :segments="segments"
              :polishing="polishing"
              @polish="handlePolish"
              @delete-segment="handleDeleteSegment"
              @update:segments="segments = $event"
            />
          </el-card>
        </el-col>

        <el-col :span="8">
          <!-- Quality -->
          <el-card>
            <template #header>质量评估</template>
            <QualityRadar
              v-if="currentScript.quality_score"
              :engagement_score="currentScript.engagement_score || 0"
              :accuracy_score="currentScript.accuracy_score || 0"
              :completeness_score="currentScript.completeness_score || 0"
              :quality_score="currentScript.quality_score"
              :passed="currentScript.status === 'completed'"
            />
            <el-button type="warning" style="width:100%;margin-top:12px" @click="handleEvaluate" :loading="evaluating">
              重新评估
            </el-button>
          </el-card>

          <!-- Actions -->
          <el-card style="margin-top:16px">
            <template #header>操作</template>
            <el-space direction="vertical" :size="12" style="width:100%">
              <el-button style="width:100%" @click="handleRegenerate" :loading="regenerating">
                重新生成
              </el-button>
              <el-button type="success" size="large" style="width:100%" @click="showExportDialog = true">
                导出到剪映
              </el-button>
            </el-space>
          </el-card>

          <!-- Info -->
          <el-card style="margin-top:16px">
            <template #header>脚本信息</template>
            <el-descriptions :column="1" size="small">
              <el-descriptions-item label="平台">{{ currentScript.platform }}</el-descriptions-item>
              <el-descriptions-item label="时长">{{ currentScript.duration_seconds }}s</el-descriptions-item>
              <el-descriptions-item label="风格">{{ currentScript.style || '活泼' }}</el-descriptions-item>
              <el-descriptions-item label="版本">v{{ currentScript.generation_version }}</el-descriptions-item>
              <el-descriptions-item label="润色次数">{{ currentScript.polish_iterations }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- History Panel -->
    <el-card v-if="scriptHistory.length > 0" style="margin-top:24px">
      <template #header>历史脚本 ({{ scriptHistory.length }})</template>
      <el-table :data="scriptHistory" stripe @row-click="loadScript" style="cursor:pointer">
        <el-table-column prop="title" label="名称" min-width="150" />
        <el-table-column prop="platform" label="平台" width="80" />
        <el-table-column label="时长" width="80">
          <template #default="{ row }">{{ row.duration_seconds }}s</template>
        </el-table-column>
        <el-table-column label="评分" width="80">
          <template #default="{ row }">
            <el-tag :type="(row.quality_score || 0) >= 0.7 ? 'success' : 'warning'" size="small">
              {{ row.quality_score ? Math.round(row.quality_score * 100) + '%' : '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : 'info'" size="small">
              {{ row.status === 'completed' ? '完成' : row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="导出" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.export_status === 'completed'" type="success" size="small">已导出</el-tag>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="140">
          <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Export Dialog -->
    <ExportDialog
      v-if="currentScript"
      v-model="showExportDialog"
      :script-id="currentScript.id"
      :draft-name="currentScript.title || '脚本'"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { scriptApi, tripApi } from '@/api/auth'
import type { ScriptSegment, VideoScript } from '@/types/trip'

import TripSearchSelect from '@/components/shop/TripSearchSelect.vue'
import GenerationProgress from '@/components/shop/GenerationProgress.vue'
import ScriptSegmentEditor from '@/components/shop/ScriptSegmentEditor.vue'
import QualityRadar from '@/components/shop/QualityRadar.vue'
import ExportDialog from '@/components/shop/ExportDialog.vue'

const route = useRoute()

// Steps
const currentStep = ref(1)
const selectedTrip = ref<any>(null)
const config = reactive({ platform: '抖音', duration_seconds: 300, style: '活泼' })

// Generation
const genStage = ref(0)
const genStatus = ref('running')
const currentScript = ref<VideoScript | null>(null)
const segments = ref<ScriptSegment[]>([])
const polishing = ref(false)
const regenerating = ref(false)
const evaluating = ref(false)
const showExportDialog = ref(false)
const scriptHistory = ref<any[]>([])

onMounted(async () => {
  loadHistory()
  // Check if trip_id passed in URL
  const tripId = route.query.trip_id as string
  if (tripId) {
    try {
      selectedTrip.value = await tripApi.get(tripId)
      config.platform = (route.query.platform as string) || '抖音'
      currentStep.value = 2
    } catch { /* ignore */ }
  }
})

function onTripSelect(trip: any) { selectedTrip.value = trip }

async function handleGenerate() {
  if (!selectedTrip.value) return
  currentStep.value = 3
  genStage.value = 1
  genStatus.value = 'running'

  // Animate stages: 研究(2s) → 生成(5s) → 润色(8s) → 评估(wait for API)
  const stageDelays = [2000, 5000, 8000]
  const stageTimers: number[] = []
  for (let i = 0; i < stageDelays.length; i++) {
    stageTimers.push(window.setTimeout(() => {
      genStage.value = i + 1
    }, stageDelays[i]))
  }
  // Stage 4 (评估中) — show after 10s, but still waiting for API
  stageTimers.push(window.setTimeout(() => {
    if (genStatus.value === 'running') genStage.value = 4
  }, 10000))

  try {
    const script = await scriptApi.generate({
      trip_id: selectedTrip.value.id,
      platform: config.platform,
      duration_seconds: config.duration_seconds,
      style: config.style,
    })
    currentScript.value = script
    segments.value = script.segments || []
    genStage.value = 5
    genStatus.value = script.status
    loadHistory()
  } catch (e: any) {
    genStatus.value = 'failed'
    ElMessage.error(e?.response?.data?.detail || '生成失败')
  } finally {
    stageTimers.forEach(t => clearTimeout(t))
    setTimeout(() => { if (currentScript.value) currentStep.value = 4 }, 600)
  }
}

async function handlePolish() {
  if (!currentScript.value) return
  polishing.value = true
  try {
    const script = await scriptApi.polish(currentScript.value.id, { focus_areas: ['engagement', 'transitions', 'sensory_language', 'hooks'] })
    currentScript.value = script
    segments.value = script.segments || []
    ElMessage.success('润色完成')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '润色失败')
  } finally { polishing.value = false }
}

async function handleEvaluate() {
  if (!currentScript.value) return
  evaluating.value = true
  try {
    const result = await scriptApi.evaluate(currentScript.value.id)
    if (currentScript.value) {
      Object.assign(currentScript.value, result)
    }
    ElMessage.success(`评估完成: ${Math.round(result.quality_score * 100)}%`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '评估失败')
  } finally { evaluating.value = false }
}

async function handleRegenerate() {
  if (!selectedTrip.value) return
  regenerating.value = true
  currentStep.value = 3
  genStage.value = 1
  genStatus.value = 'running'
  try {
    const script = await scriptApi.generate({
      trip_id: selectedTrip.value.id,
      platform: config.platform,
      duration_seconds: config.duration_seconds,
      style: config.style,
    })
    currentScript.value = script
    segments.value = script.segments || []
    genStage.value = 5
    genStatus.value = script.status
    currentStep.value = 4
  } catch { /* handled */ } finally { regenerating.value = false }
}

function handleDeleteSegment(idx: number) {
  segments.value.splice(idx, 1)
  // Recalculate timecodes
  let time = 0
  for (const s of segments.value) {
    s.timecode_start = `${String(Math.floor(time / 60)).padStart(2, '0')}:${String(time % 60).padStart(2, '0')}`
    time += s.duration_seconds
    s.timecode_end = `${String(Math.floor(time / 60)).padStart(2, '0')}:${String(time % 60).padStart(2, '0')}`
  }
}

async function loadHistory() {
  try {
    const res = await scriptApi.list({ page_size: 10 })
    scriptHistory.value = res.items || []
  } catch { /* ignore */ }
}

async function loadScript(row: any) {
  try {
    const script = await scriptApi.get(row.id)
    currentScript.value = script
    segments.value = script.segments || []
    // Find the trip
    if (script.trip_id) {
      try { selectedTrip.value = await tripApi.get(script.trip_id) } catch { /* ignore */ }
    }
    config.platform = script.platform
    config.duration_seconds = script.duration_seconds
    currentStep.value = 4
  } catch { /* ignore */ }
}
</script>

<style scoped>
.subtitle { color: #909399; margin-top: -12px; margin-bottom: 24px; }
.trip-preview { background: #fafbfc; }
.trip-preview h4 { margin: 0 0 8px; }
.trip-preview p { margin: 4px 0; font-size: 13px; color: #606266; }
</style>
