<template>
  <div class="segment-editor">
    <div class="editor-toolbar">
      <span class="segment-count">{{ segments.length }} 个段落 · 总时长 {{ totalDuration }}s</span>
      <el-button size="small" @click="$emit('polish')" :loading="polishing">
        <el-icon><MagicStick /></el-icon> AI润色
      </el-button>
    </div>

    <div class="segment-list">
      <div
        v-for="(seg, idx) in segments"
        :key="idx"
        class="segment-card"
        :class="'type-' + seg.segment_type"
        @click="activeIdx = idx"
      >
        <div class="seg-header">
          <el-tag :type="segTypeColor(seg.segment_type)" size="small" effect="dark">
            {{ segTypeLabel(seg.segment_type) }}
          </el-tag>
          <span class="seg-time">{{ seg.timecode_start }} - {{ seg.timecode_end }}</span>
          <span class="seg-dur">{{ seg.duration_seconds }}s</span>
          <el-button
            v-if="activeIdx === idx"
            size="small"
            text
            type="danger"
            style="margin-left:auto"
            @click.stop="$emit('deleteSegment', idx)"
          >
            删除
          </el-button>
        </div>

        <el-input
          v-if="activeIdx === idx"
          v-model="seg.text"
          type="textarea"
          :rows="4"
          @input="$emit('update:segments', [...segments])"
          placeholder="输入脚本文字..."
        />

        <div v-else class="seg-preview">{{ seg.text.slice(0, 80) }}{{ seg.text.length > 80 ? '...' : '' }}</div>

        <div v-if="activeIdx === idx" class="seg-meta">
          <el-row :gutter="12">
            <el-col :span="12">
              <el-input v-model="seg.image_keyword" placeholder="配图关键词" size="small"
                        @input="$emit('update:segments', [...segments])" />
            </el-col>
            <el-col :span="12">
              <el-input v-model="seg.bgm_suggestion" placeholder="BGM建议" size="small"
                        @input="$emit('update:segments', [...segments])" />
            </el-col>
          </el-row>
        </div>
      </div>
    </div>

    <!-- Full text preview -->
    <el-collapse style="margin-top:12px">
      <el-collapse-item title="查看完整脚本">
        <div class="full-text">{{ fullText }}</div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ScriptSegment } from '@/types/trip'

const props = defineProps<{
  segments: ScriptSegment[]
  polishing: boolean
}>()

defineEmits<{
  polish: []
  deleteSegment: [idx: number]
  'update:segments': [segments: ScriptSegment[]]
}>()

const activeIdx = ref(0)

const totalDuration = computed(() =>
  props.segments.reduce((s, seg) => s + seg.duration_seconds, 0)
)

const fullText = computed(() =>
  props.segments.map(s => s.text).join('\n\n')
)

function segTypeLabel(t: string) {
  return { hook: '钩子', highlights: '精华', detail: '细节', cta: 'CTA' }[t] || t
}

function segTypeColor(t: string) {
  return { hook: 'danger', highlights: 'primary', detail: 'warning', cta: 'success' }[t] || 'info' as any
}
</script>

<style scoped>
.segment-editor { max-height: 70vh; overflow-y: auto; }
.editor-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.segment-count { font-size: 13px; color: #909399; }
.segment-card {
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color .2s;
}
.segment-card:hover { border-color: #409eff; }
.segment-card.type-hook { border-left: 3px solid #f56c6c; }
.segment-card.type-highlights { border-left: 3px solid #409eff; }
.segment-card.type-detail { border-left: 3px solid #e6a23c; }
.segment-card.type-cta { border-left: 3px solid #67c23a; }
.seg-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.seg-time { font-size: 12px; color: #909399; font-family: monospace; }
.seg-dur { font-size: 12px; color: #c0c4cc; }
.seg-preview { color: #606266; font-size: 13px; line-height: 1.6; }
.seg-meta { margin-top: 8px; }
.full-text { white-space: pre-wrap; line-height: 1.8; font-size: 14px; color: #303133; padding: 12px; background: #fafbfc; border-radius: 6px; }
</style>
