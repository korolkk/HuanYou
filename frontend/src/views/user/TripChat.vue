<template>
  <div class="chat-page">
    <div class="chat-container">
      <div class="chat-header">
        <h3>💬 旅行AI管家</h3>
        <p>随时为你提供行程咨询、天气查询、注意事项等服务</p>
      </div>

      <!-- Messages -->
      <div class="chat-messages" ref="msgContainer">
        <div v-if="messages.length === 0" class="welcome">
          <div class="welcome-icon">🏔️</div>
          <h3>你好！我是你的旅行AI管家</h3>
          <p>我可以帮你：</p>
          <div class="quick-prompts">
            <el-button
              v-for="p in quickPrompts"
              :key="p"
              type="default"
              size="small"
              @click="sendMessage(p)"
            >
              {{ p }}
            </el-button>
          </div>
        </div>

        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          :class="['message', msg.role === 'user' ? 'user-msg' : 'ai-msg']"
        >
          <div class="msg-avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="msg-content">
            <div class="msg-text" v-html="formatMsg(msg.content)"></div>
            <div class="msg-time">{{ msg.time }}</div>
          </div>
        </div>

        <div v-if="streaming" class="message ai-msg">
          <div class="msg-avatar">🤖</div>
          <div class="msg-content">
            <div class="msg-text streaming">
              {{ streamText }}<span class="cursor">|</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="chat-input">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          placeholder="输入你的问题，如：丽江5日游需要注意什么？"
          @keyup.enter.exact="sendMessage()"
          :disabled="streaming"
        />
        <el-button
          type="primary"
          :loading="streaming"
          @click="sendMessage()"
          style="margin-left:12px;height:60px;"
        >
          发送
        </el-button>
      </div>
    </div>

    <!-- Side Panel: Context -->
    <div class="context-panel">
      <el-card>
        <template #header><span>📋 快捷服务</span></template>
        <el-menu>
          <el-menu-item @click="sendMessage('我想查看我的订单')">
            <el-icon><List /></el-icon> 我的订单
          </el-menu-item>
          <el-menu-item @click="sendMessage('帮我推荐一个行程')">
            <el-icon><Search /></el-icon> 推荐行程
          </el-menu-item>
          <el-menu-item @click="sendMessage('出发前需要准备什么')">
            <el-icon><Briefcase /></el-icon> 行前准备
          </el-menu-item>
          <el-menu-item @click="sendMessage('查询目的地天气')">
            <el-icon><Sunny /></el-icon> 天气查询
          </el-menu-item>
          <el-menu-item @click="sendMessage('紧急联系方式')">
            <el-icon><Phone /></el-icon> 紧急联系
          </el-menu-item>
        </el-menu>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { agentApi } from '@/api/auth'
import dayjs from 'dayjs'

interface ChatMsg {
  role: 'user' | 'assistant'
  content: string
  time: string
}

const messages = ref<ChatMsg[]>([])
const inputText = ref('')
const streaming = ref(false)
const streamText = ref('')
const msgContainer = ref<HTMLElement>()

const quickPrompts = [
  '暑假想带家人去海边，预算5000，有什么推荐？',
  '丽江5日游需要准备什么？',
  '报名日本团的签证怎么办？',
  '帮我看看我的订单',
]

function formatMsg(text: string): string {
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/###?\s(.+)/g, '<h4>$1</h4>')
}

async function sendMessage(text?: string) {
  const msgText = text || inputText.value.trim()
  if (!msgText || streaming.value) return

  messages.value.push({
    role: 'user',
    content: msgText,
    time: dayjs().format('HH:mm'),
  })
  inputText.value = ''
  await scrollToBottom()

  streaming.value = true
  streamText.value = ''

  try {
    const res = await agentApi.chat(msgText)
    if (res?.response) {
      messages.value.push({
        role: 'assistant',
        content: res.response,
        time: dayjs().format('HH:mm'),
      })
    } else {
      messages.value.push({
        role: 'assistant',
        content: '抱歉，我暂时无法处理这个请求。请确认AI服务已配置。',
        time: dayjs().format('HH:mm'),
      })
    }
  } catch (e: any) {
    const errMsg = e?.response?.data?.detail || '请求失败，请稍后重试'
    messages.value.push({
      role: 'assistant',
      content: `⚠️ ${errMsg}`,
      time: dayjs().format('HH:mm'),
    })
  } finally {
    streaming.value = false
    streamText.value = ''
    await scrollToBottom()
  }
}

async function scrollToBottom() {
  await nextTick()
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  }
}

onMounted(() => {
  messages.value.push({
    role: 'assistant',
    content: '你好！我是你的旅行AI管家 🏔️\n\n我可以帮你：\n• 智能推荐行程\n• 查询订单信息\n• 行前准备建议\n• 目的地天气和攻略\n• 紧急情况协助\n\n请随时向我提问！',
    time: dayjs().format('HH:mm'),
  })
})
</script>

<style scoped>
.chat-page {
  display: flex;
  gap: 20px;
  height: calc(100vh - 100px);
  max-width: 1200px;
  margin: 0 auto;
}
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.chat-header {
  padding: 16px 24px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
}
.chat-header h3 { margin: 0; }
.chat-header p { margin: 4px 0 0; font-size: 13px; opacity: 0.85; }
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fafbfc;
}
.welcome { text-align: center; padding: 40px 20px; }
.welcome-icon { font-size: 48px; margin-bottom: 16px; }
.welcome h3 { margin: 0; }
.quick-prompts { margin-top: 16px; display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.message {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.user-msg { flex-direction: row-reverse; }
.msg-avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.user-msg .msg-avatar { background: #e3f2fd; }
.ai-msg .msg-avatar { background: #f3e5f5; }
.msg-content { max-width: 75%; }
.user-msg .msg-content { text-align: right; }
.msg-text {
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.user-msg .msg-text { background: #1976d2; color: #fff; border-bottom-right-radius: 4px; }
.ai-msg .msg-text { background: #fff; border: 1px solid #e4e7ed; border-bottom-left-radius: 4px; }
.msg-text.streaming { border: 2px dashed #667eea; }
.cursor { animation: blink 1s infinite; color: #667eea; }
@keyframes blink { 0%,50% { opacity:1; } 51%,100% { opacity:0; } }
.msg-time { font-size: 11px; color: #c0c4cc; margin-top: 4px; }
.chat-input {
  display: flex;
  padding: 16px 24px;
  border-top: 1px solid #e4e7ed;
  background: #fff;
}
.context-panel { width: 240px; flex-shrink: 0; }
</style>
