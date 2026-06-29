<template>
  <div class="gen-progress">
    <el-steps :active="activeStage" finish-status="success" align-center>
      <el-step title="研究行程" description="加载行程信息..." />
      <el-step title="生成脚本" description="AI创作脚本内容" />
      <el-step title="润色优化" description="提升吸引力" />
      <el-step title="质量评估" description="三维度评分" />
    </el-steps>
    <div class="stage-detail">
      <el-alert :title="stageText" :type="stageType" :closable="false" show-icon />
    </div>
    <el-progress
      v-if="stage < 4"
      :percentage="Math.round((stage / 4) * 100)"
      :stroke-width="6"
      :indeterminate="stage > 0"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'

const props = defineProps<{ stage: number; status: string }>()
const emit = defineEmits<{ done: [] }>()

const activeStage = computed(() => {
  if (props.status === 'completed') return 4
  return Math.min(props.stage, 3)
})

const stageText = computed(() => {
  const texts = [
    '正在加载行程数据，构建上下文...',
    'AI正在创作脚本，生成结构化内容...',
    'AI正在润色优化，提升表达质量...',
    'AI正在评估脚本质量，三维度打分...',
    '脚本生成完成！',
  ]
  return texts[Math.min(props.stage, 4)] || texts[0]
})

const stageType = computed(() => {
  if (props.status === 'completed') return 'success' as const
  if (props.status === 'failed') return 'error' as const
  return 'info' as const
})
</script>

<style scoped>
.gen-progress { padding: 24px; }
.stage-detail { margin: 24px 0; max-width: 500px; margin-left: auto; margin-right: auto; }
</style>
