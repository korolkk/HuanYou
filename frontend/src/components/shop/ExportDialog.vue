<template>
  <el-dialog
    v-model="visible"
    title="导出到剪映 (CapCut)"
    width="520px"
    :close-on-click-modal="false"
  >
    <div v-if="!exporting && !exportDone">
      <el-form label-position="top">
        <el-form-item label="分辨率">
          <el-radio-group v-model="resolution">
            <el-radio value="1080p">1080p (推荐)</el-radio>
            <el-radio value="720p">720p</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="包含图片占位">
          <el-switch v-model="includeImages" active-text="是" inactive-text="否" />
          <span style="margin-left:8px;color:#909399;font-size:12px">图片需在剪映中手动替换</span>
        </el-form-item>
      </el-form>

      <el-alert type="info" :closable="false" show-icon style="margin-top:12px">
        <template #title>
          导出后请将ZIP解压到剪映草稿目录：
          <br/><code>文档\CapCut\User Data\Projects\com.lveditor.draft\</code>
        </template>
      </el-alert>
    </div>

    <div v-else-if="exporting" class="exporting">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在生成剪映草稿文件...</p>
      <el-progress :percentage="100" :indeterminate="true" :stroke-width="4" />
    </div>

    <div v-else class="export-done">
      <el-result icon="success" title="导出成功" sub-title="草稿文件已下载，请按说明导入剪映">
        <template #extra>
          <el-button type="primary" @click="downloadAgain" :loading="downloading">
            再次下载
          </el-button>
        </template>
      </el-result>

      <el-alert type="success" :closable="false" style="margin-top:16px">
        <template #title>
          <strong>使用步骤：</strong>
          <ol style="margin:8px 0 0;padding-left:18px;line-height:1.8">
            <li>将下载的ZIP解压</li>
            <li>复制整个文件夹到：<br/><code>{{ capcutPath }}</code></li>
            <li>打开<strong>剪映桌面版</strong></li>
            <li>在草稿列表中找到「<strong>{{ draftName }}</strong>」</li>
            <li>替换图片、选择BGM后导出视频</li>
          </ol>
        </template>
      </el-alert>
    </div>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
      <el-button v-if="!exporting && !exportDone" type="primary" @click="startExport" :loading="exporting">
        开始导出
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { scriptApi } from '@/api/auth'

const props = defineProps<{ modelValue: boolean; scriptId: string; draftName: string }>()
const emit = defineEmits<{ 'update:modelValue': [v: boolean] }>()

const visible = ref(false)
const resolution = ref('1080p')
const includeImages = ref(true)
const exporting = ref(false)
const exportDone = ref(false)
const downloading = ref(false)
const capcutPath = ref('文档\\CapCut\\User Data\\Projects\\com.lveditor.draft\\')

watch(() => props.modelValue, v => { visible.value = v; if (v) { exporting.value = false; exportDone.value = false } })
watch(visible, v => emit('update:modelValue', v))

async function startExport() {
  exporting.value = true
  try {
    await scriptApi.exportCapcut(props.scriptId, {
      include_images: includeImages.value,
      resolution: resolution.value,
    })
    exportDone.value = true
  } catch (e: any) {
    // Error handled by interceptor
  } finally {
    exporting.value = false
  }
}

async function downloadAgain() {
  downloading.value = true
  try {
    await scriptApi.exportCapcut(props.scriptId, {
      include_images: includeImages.value,
      resolution: resolution.value,
    })
  } finally { downloading.value = false }
}
</script>

<style scoped>
.exporting { text-align: center; padding: 40px; }
.exporting p { margin: 16px 0; color: #606266; }
.export-done { text-align: center; }
code { background: #f5f7fa; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
</style>
