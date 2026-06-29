<template>
  <div class="quality-radar">
    <div ref="chartRef" style="width: 100%; height: 280px;"></div>
    <div class="score-summary">
      <div class="overall-score" :class="passed ? 'passed' : 'failed'">
        {{ Math.round((quality_score || 0) * 100) }}
      </div>
      <div class="score-label">综合评分</div>
      <el-tag :type="passed ? 'success' : 'danger'" size="small">
        {{ passed ? '通过' : '需修改' }}
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  engagement_score: number
  accuracy_score: number
  completeness_score: number
  quality_score: number
  passed: boolean
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const passed = computed(() => props.passed || (props.quality_score || 0) >= 0.7)

function renderChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  chart.setOption({
    radar: {
      center: ['50%', '50%'],
      radius: '65%',
      indicator: [
        { name: '吸引力', max: 1 },
        { name: '准确性', max: 1 },
        { name: '完整度', max: 1 },
      ],
      axisName: { fontSize: 12, color: '#606266' },
    },
    series: [{
      type: 'radar',
      data: [{
        value: [props.engagement_score || 0, props.accuracy_score || 0, props.completeness_score || 0],
        name: '脚本质量',
        areaStyle: { color: 'rgba(79, 195, 247, 0.3)' },
        lineStyle: { color: '#4fc3f7', width: 2 },
        itemStyle: { color: '#4fc3f7' },
      }],
    }],
  })
}

onMounted(() => renderChart())
watch(() => [props.engagement_score, props.accuracy_score, props.completeness_score], renderChart)
</script>

<style scoped>
.quality-radar { position: relative; }
.score-summary { text-align: center; margin-top: -20px; }
.overall-score { font-size: 40px; font-weight: 700; }
.overall-score.passed { color: #67c23a; }
.overall-score.failed { color: #f56c6c; }
.score-label { font-size: 13px; color: #909399; margin: 4px 0 8px; }
</style>
