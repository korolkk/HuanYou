<template>
  <div class="trip-import">
    <div class="page-header">
      <h2>导入行程</h2>
      <el-button @click="downloadTemplate">
        <el-icon><Download /></el-icon> 下载导入模板
      </el-button>
    </div>

    <el-row :gutter="24">
      <el-col :span="12">
        <el-card>
          <template #header>上传文件</template>
          <FileDropZone
            accept=".xlsx,.json"
            accept-label=".xlsx / .json (最大20MB)"
            @update:file="handleFile"
          />

          <div v-if="file" style="margin-top:16px;text-align:right">
            <el-button type="primary" :loading="uploading" @click="handleUpload">
              确认导入
            </el-button>
          </div>

          <el-alert type="info" :closable="false" show-icon style="margin-top:16px">
            <template #title>
              <strong>支持格式：</strong>
              <ul style="margin:8px 0 0;padding-left:16px;line-height:1.8">
                <li><strong>Excel (.xlsx)</strong> — Sheet「行程概要」+「行程安排」</li>
                <li><strong>Word (.docx)</strong> — 旅行社行程文档，自动提取行程/价格</li>
                <li><strong>PDF (.pdf)</strong> — PDF行程文件，自动提取文本和表格</li>
                <li><strong>JSON (.json)</strong> — 结构化行程数据</li>
                <li>建议先下载模板参考Excel格式</li>
              </ul>
            </template>
          </el-alert>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card v-if="importResult">
          <template #header>导入结果</template>
          <el-result
            icon="success"
            :title="importResult.message"
            :sub-title="`行程: ${importResult.trip_title} · ${importResult.schedules_count}天日程`"
          >
            <template v-if="importResult.validation_warnings?.length" #extra>
              <el-alert
                v-for="(w, i) in importResult.validation_warnings"
                :key="i"
                :title="w"
                type="warning"
                :closable="false"
                style="margin-top:8px"
              />
            </template>
            <template #extra>
              <el-space>
                <el-button type="primary" @click="$router.push('/shop/trips')">查看行程列表</el-button>
                <el-button @click="resetImport">继续导入</el-button>
              </el-space>
            </template>
          </el-result>
        </el-card>

        <el-card v-else-if="uploadError">
          <template #header>导入失败</template>
          <el-result icon="error" :title="uploadError">
            <template #extra>
              <el-button @click="resetImport">重新上传</el-button>
            </template>
          </el-result>
        </el-card>

        <el-empty v-else description="上传文件后将在此显示导入结果" :image-size="120" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { importApi } from '@/api/auth'
import FileDropZone from '@/components/shop/FileDropZone.vue'

const file = ref<File | null>(null)
const uploading = ref(false)
const importResult = ref<any>(null)
const uploadError = ref('')

function handleFile(f: File | null) {
  file.value = f
  importResult.value = null
  uploadError.value = ''
}

async function handleUpload() {
  if (!file.value) return
  uploading.value = true
  uploadError.value = ''
  try {
    importResult.value = await importApi.uploadFile(file.value)
    ElMessage.success('导入成功！')
  } catch (e: any) {
    uploadError.value = e?.response?.data?.detail || '导入失败'
  } finally { uploading.value = false }
}

function resetImport() {
  file.value = null
  importResult.value = null
  uploadError.value = ''
}

function downloadTemplate() {
  importApi.downloadTemplate()
  ElMessage.success('模板下载中...')
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { margin: 0; }
</style>
