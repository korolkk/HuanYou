<template>
  <div class="gen-progress">
    <el-steps :active="Math.min(stage, 5)" finish-status="success" align-center>
      <el-step title="研究行程" description="加载行程数据" />
      <el-step title="生成脚本" description="AI创作脚本内容" />
      <el-step title="润色优化" description="提升表达质量" />
      <el-step title="质量评估" description="三维度评分" />
      <el-step title="完成" description="脚本已就绪" />
    </el-steps>
    <div class="stage-detail">
      <el-alert :title="stageText" :type="stageType" :closable="false" show-icon />
    </div>
    <el-progress
      v-if="!done"
      :percentage="Math.round((Math.min(stage, 4) / 5) * 100)"
      :stroke-width="6"
      :indeterminate="stage > 0 && stage < 5 && status === 'running'"
    />
    <el-result
      v-if="done"
      icon="success"
      title="脚本生成完成"
      sub-title="可以预览编辑脚本或导出到剪映"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ stage: number; status: string }>()

const done = computed(() => props.stage >= 5 || props.status === 'completed' || props.status === 'needs_revision')

const stageType = computed(() => {
  if (done.value) return 'success' as const
  if (props.status === 'failed') return 'error' as const
  return 'info' as const
})

const stageText = computed(() => {
  if (props.status === 'failed') return '脚本生成失败，请重试'
  if (done.value) return '脚本已生成，正在进入编辑页面...'
  const texts = [
    '正在加载行程数据，构建上下文...',
    'AI正在创作脚本，生成结构化内容...',
    'AI正在润色优化，提升吸引力和流畅度...',
    'AI正在评估脚本质量，三维度打分...',
    '等待评估结果...',
    '脚本生成完成！',
  ]
  return texts[Math.min(props.stage, 5)] || texts[0]
})
</script>

<style scoped>
.gen-progress { padding: 24px; }
.stage-detail { margin: 24px 0; max-width: 500px; margin-left: auto; margin-right: auto; }
</style>
