<template>
  <div class="user-home">
    <div class="hero">
      <h1>🌍 你好，{{ authStore.user?.name }}</h1>
      <p>想去哪里旅行？让AI为你推荐最合适的行程</p>
      <el-input v-model="query" size="large" placeholder="例如：暑假想带家人去海边，预算5000，5天左右"
                @keyup.enter="goRecommend" class="search-input">
        <template #append>
          <el-button type="primary" @click="goRecommend">智能推荐</el-button>
        </template>
      </el-input>
    </div>

    <el-row :gutter="20" style="margin-top: 32px;">
      <el-col :span="16">
        <el-card>
          <template #header><span>💬 AI旅行管家</span></template>
          <div class="chat-area">
            <el-input v-model="chatMsg" placeholder="随时问我：行程推荐、注意事项、天气查询..."
                      @keyup.enter="sendMsg" />
            <div v-if="chatReply" class="reply">{{ chatReply }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>⚡ 快捷服务</span></template>
          <el-space direction="vertical" :size="12" style="width: 100%;">
            <el-button @click="$router.push('/user/orders')" style="width: 100%;">我的订单</el-button>
            <el-button @click="$router.push('/user/history')" style="width: 100%;">旅行足迹</el-button>
            <el-button @click="$router.push('/user/chat')" style="width: 100%;">AI智能客服</el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const query = ref('')
const chatMsg = ref('')
const chatReply = ref('')

function goRecommend() {
  if (query.value) {
    router.push(`/user/recommend?q=${encodeURIComponent(query.value)}`)
  } else {
    router.push('/user/recommend')
  }
}

async function sendMsg() {
  if (!chatMsg.value) return
  chatReply.value = 'AI正在处理您的请求... (配置API Key后启用完整功能)'
}
</script>

<style scoped>
.hero {
  text-align: center;
  padding: 48px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: #fff;
  margin-bottom: 24px;
}
.hero h1 { margin: 0 0 12px; font-size: 32px; }
.hero p { margin: 0 0 24px; opacity: 0.9; }
.search-input { max-width: 600px; margin: 0 auto; }
.chat-area { min-height: 200px; }
.reply { margin-top: 16px; padding: 12px; background: #f5f7fa; border-radius: 8px; white-space: pre-wrap; }
</style>
