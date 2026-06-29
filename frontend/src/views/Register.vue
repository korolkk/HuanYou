<template>
  <div class="register-page">
    <div class="register-card">
      <div class="header">
        <h1>🏔️ 注册欢游</h1>
        <p>开启智能旅行之旅</p>
      </div>

      <el-form :model="form" size="large" @submit.prevent="handleRegister">
        <el-form-item>
          <el-input v-model="form.phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.name" placeholder="姓名" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码(6位以上)" show-password />
        </el-form-item>
        <el-form-item>
          <el-radio-group v-model="form.role">
            <el-radio value="user">我是游客</el-radio>
            <el-radio value="shop_owner">我是店长</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister" style="width: 100%">
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <div class="footer">
        <span>已有账号？</span>
        <router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

const form = reactive({
  phone: '',
  name: '',
  password: '',
  role: 'user',
})

async function handleRegister() {
  loading.value = true
  try {
    await authStore.register(form)
    const target = form.role === 'shop_owner' ? '/shop/dashboard' : '/user/home'
    router.push(target)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}
.register-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}
.header { text-align: center; margin-bottom: 32px; }
.header h1 { margin: 0; color: #1a1a2e; }
.header p { color: #909399; margin-top: 8px; }
.footer { text-align: center; margin-top: 16px; color: #909399; font-size: 14px; }
</style>
