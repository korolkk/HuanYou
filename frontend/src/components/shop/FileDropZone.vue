<template>
  <div
    class="drop-zone"
    :class="{ 'drag-over': dragging }"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="handleDrop"
    @click="triggerInput"
  >
    <input ref="fileInput" type="file" :accept="accept" @change="handleFileChange" style="display:none" />
    <div v-if="!file">
      <div class="drop-icon">📁</div>
      <p class="drop-text">拖拽文件到此处，或点击选择文件</p>
      <p class="drop-hint">支持 {{ acceptLabel }}</p>
    </div>
    <div v-else class="file-info">
      <div class="file-icon">📄</div>
      <div class="file-name">{{ file.name }}</div>
      <div class="file-size">{{ formatSize(file.size) }}</div>
      <el-button size="small" text @click.stop="clearFile">移除</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = withDefaults(defineProps<{
  accept?: string
  acceptLabel?: string
}>(), {
  accept: '.xlsx,.json',
  acceptLabel: '.xlsx / .json (最大20MB)',
})

const emit = defineEmits<{ 'update:file': [file: File | null] }>()

const dragging = ref(false)
const file = ref<File | null>(null)
const fileInput = ref<HTMLInputElement>()

function triggerInput() { fileInput.value?.click() }

function handleDrop(e: DragEvent) {
  dragging.value = false
  const files = e.dataTransfer?.files
  if (files?.[0]) setFile(files[0])
}

function handleFileChange(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files?.[0]) setFile(files[0])
}

function setFile(f: File) {
  if (f.size > 20 * 1024 * 1024) {
    alert('文件大小不能超过20MB')
    return
  }
  file.value = f
  emit('update:file', f)
}

function clearFile() {
  file.value = null
  emit('update:file', null)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / (1024 * 1024)).toFixed(1) + 'MB'
}
</script>

<style scoped>
.drop-zone {
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all .3s;
  background: #fafbfc;
}
.drop-zone:hover, .drop-zone.drag-over {
  border-color: #409eff;
  background: #ecf5ff;
}
.drop-icon { font-size: 48px; margin-bottom: 12px; }
.drop-text { font-size: 15px; color: #606266; margin: 0; }
.drop-hint { font-size: 12px; color: #c0c4cc; margin: 8px 0 0; }
.file-info { display: flex; align-items: center; gap: 12px; }
.file-icon { font-size: 32px; }
.file-name { font-weight: 500; flex: 1; text-align: left; }
.file-size { font-size: 12px; color: #909399; }
</style>
