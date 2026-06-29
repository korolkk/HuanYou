import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

interface UserInfo {
  id: string
  phone: string
  name: string
  role: string
  email?: string
  gender?: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')

  const isLoggedIn = computed(() => !!accessToken.value && !!user.value)
  const isShopOwner = computed(() => user.value?.role === 'shop_owner')

  async function login(phone: string, password: string) {
    const res = await authApi.login(phone, password)
    accessToken.value = res.access_token
    refreshToken.value = res.refresh_token
    user.value = res.user
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('refresh_token', res.refresh_token)
    localStorage.setItem('user_role', res.user.role)
    return res
  }

  async function register(data: { phone: string; name: string; password: string; role: string }) {
    const res = await authApi.register(data)
    accessToken.value = res.access_token
    refreshToken.value = res.refresh_token
    user.value = res.user
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('refresh_token', res.refresh_token)
    localStorage.setItem('user_role', res.user.role)
    return res
  }

  async function fetchMe() {
    try {
      const res = await authApi.getMe()
      user.value = res
    } catch {
      logout()
    }
  }

  function logout() {
    user.value = null
    accessToken.value = ''
    refreshToken.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_role')
  }

  return { user, accessToken, refreshToken, isLoggedIn, isShopOwner, login, register, fetchMe, logout }
})
