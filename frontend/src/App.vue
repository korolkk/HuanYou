<template>
  <div id="app" class="app-container">
    <!-- Loading: 恢复登录状态中 -->
    <div v-if="!appReady" class="app-loading">
      <el-icon class="is-loading" :size="36"><Loading /></el-icon>
    </div>

    <!-- Shop Owner Layout -->
    <template v-if="authStore.user?.role === 'shop_owner'">
      <el-container class="layout">
        <el-aside width="220px" class="sidebar">
          <div class="logo">
            <h2>🏔️ 欢游</h2>
            <span class="subtitle">AI旅游助手 · 店长端</span>
          </div>
          <el-menu
            :default-active="currentRoute"
            router
            background-color="#1a1a2e"
            text-color="#b8b8d0"
            active-text-color="#4fc3f7"
          >
            <el-menu-item index="/shop/dashboard">
              <el-icon><DataBoard /></el-icon>
              <span>工作台</span>
            </el-menu-item>
            <el-menu-item index="/shop/trips">
              <el-icon><MapLocation /></el-icon>
              <span>行程管理</span>
            </el-menu-item>
            <el-menu-item index="/shop/import">
              <el-icon><Upload /></el-icon>
              <span>导入行程</span>
            </el-menu-item>
            <el-menu-item index="/shop/scripts">
              <el-icon><VideoCamera /></el-icon>
              <span>脚本工作台</span>
            </el-menu-item>
            <el-menu-item index="/shop/customers">
              <el-icon><UserFilled /></el-icon>
              <span>客户管理</span>
            </el-menu-item>
          </el-menu>
          <div class="user-info">
            <span>{{ authStore.user?.name }}</span>
            <el-button text @click="logout">退出</el-button>
          </div>
        </el-aside>
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </template>

    <!-- User Layout -->
    <template v-else-if="authStore.user?.role === 'user'">
      <el-container class="layout">
        <el-header class="user-header">
          <div class="header-left">
            <h2>🏔️ 欢游</h2>
            <el-menu mode="horizontal" :default-active="currentRoute" router>
              <el-menu-item index="/user/home">首页</el-menu-item>
              <el-menu-item index="/user/recommend">智能推荐</el-menu-item>
              <el-menu-item index="/user/orders">我的订单</el-menu-item>
              <el-menu-item index="/user/history">旅行足迹</el-menu-item>
            </el-menu>
          </div>
          <div class="header-right">
            <span class="username">{{ authStore.user?.name }}</span>
            <el-button text @click="logout">退出</el-button>
          </div>
        </el-header>
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </template>

    <!-- Login Page -->
    <template v-else>
      <router-view />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const currentRoute = computed(() => route.path)
const appReady = ref(false)

onMounted(async () => {
  // 页面刷新后恢复用户信息（token在localStorage但user已丢失）
  const token = localStorage.getItem('access_token')
  if (token && !authStore.user) {
    try {
      await authStore.fetchMe()
    } catch {
      // token过期或无效，清除并跳转登录
      authStore.logout()
    }
  }
  appReady.value = true
})

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style lang="scss">
.app-container {
  min-height: 100vh;
  background: #f5f7fa;
}
.app-loading {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.layout {
  min-height: 100vh;
}

.sidebar {
  background: #1a1a2e;
  display: flex;
  flex-direction: column;

  .logo {
    padding: 20px;
    text-align: center;
    color: #fff;

    h2 { margin: 0; font-size: 22px; }
    .subtitle { font-size: 12px; color: #b8b8d0; }
  }

  .el-menu {
    border-right: none;
    flex: 1;
  }

  .user-info {
    padding: 16px 20px;
    color: #b8b8d0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #2a2a4a;
  }
}

.user-header {
  background: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  padding: 0 24px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 24px;

    h2 { margin: 0; color: #1a1a2e; }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.main-content {
  padding: 24px;
  background: #f5f7fa;
}
</style>
