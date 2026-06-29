<template>
  <div class="dashboard">
    <h2>📊 工作台概览</h2>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #e3f2fd; color: #1976d2;">📋</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.tripCount }}</div>
            <div class="stat-label">行程总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #e8f5e9; color: #388e3c;">📝</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.orderCount }}</div>
            <div class="stat-label">本月订单</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #fff3e0; color: #f57c00;">👥</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.customerCount }}</div>
            <div class="stat-label">客户总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #fce4ec; color: #c62828;">💰</div>
          <div class="stat-info">
            <div class="stat-value">¥{{ stats.revenue }}</div>
            <div class="stat-label">本月营收</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 24px;">
      <el-col :span="16">
        <el-card>
          <template #header><span>💬 AI助手快速入口</span></template>
          <div class="quick-actions">
            <el-input v-model="chatMessage" placeholder="对AI助手说：帮我分析云南线路的客户反馈..."
                      @keyup.enter="sendChat" />
            <el-button type="primary" @click="sendChat" style="margin-left: 12px;">发送</el-button>
          </div>
          <div v-if="chatResponse" class="chat-response">
            <el-divider />
            <div v-html="chatResponse" style="white-space: pre-wrap;"></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>⚡ 快捷操作</span></template>
          <el-space direction="vertical" :size="12" style="width: 100%;">
            <el-button type="primary" @click="$router.push('/shop/import')" style="width: 100%;">
              导入新行程
            </el-button>
            <el-button @click="$router.push('/shop/trips')" style="width: 100%;">
              管理行程
            </el-button>
            <el-button @click="$router.push('/shop/scripts')" style="width: 100%;">
              生成短视频脚本
            </el-button>
            <el-button @click="$router.push('/shop/customers')" style="width: 100%;">
              查看客户画像
            </el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { agentApi } from '@/api/auth'

const stats = reactive({
  tripCount: 3,
  orderCount: 12,
  customerCount: 45,
  revenue: '45,800',
})

const chatMessage = ref('')
const chatResponse = ref('')

async function sendChat() {
  if (!chatMessage.value) return
  try {
    const res = agentApi.chat(chatMessage.value)
    chatResponse.value = (await res).response || ''
  } catch { /* handled */ }
}
</script>

<style scoped>
.stats-row { margin-bottom: 24px; }
.stat-card { display: flex; align-items: center; padding: 8px; }
.stat-icon { width: 56px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 28px; margin-right: 16px; }
.stat-value { font-size: 24px; font-weight: bold; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.quick-actions { display: flex; }
.chat-response { margin-top: 12px; }
</style>
