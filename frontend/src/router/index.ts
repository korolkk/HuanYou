import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  // Auth
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录 - 欢游' },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册 - 欢游' },
  },

  // Shop Owner Routes
  {
    path: '/shop',
    redirect: '/shop/dashboard',
    meta: { role: 'shop_owner' },
    children: [
      {
        path: 'dashboard',
        name: 'ShopDashboard',
        component: () => import('@/views/shop/Dashboard.vue'),
        meta: { title: '工作台 - 欢游店长端' },
      },
      {
        path: 'trips',
        name: 'ShopTrips',
        component: () => import('@/views/shop/TripList.vue'),
        meta: { title: '行程管理' },
      },
      {
        path: 'trips/:id',
        name: 'ShopTripDetail',
        component: () => import('@/views/shop/TripDetail.vue'),
        meta: { title: '行程详情' },
      },
      {
        path: 'import',
        name: 'ShopImport',
        component: () => import('@/views/shop/TripImport.vue'),
        meta: { title: '导入行程' },
      },
      {
        path: 'scripts',
        name: 'ShopScripts',
        component: () => import('@/views/shop/ScriptStudio.vue'),
        meta: { title: '脚本工作台' },
      },
      {
        path: 'customers',
        name: 'ShopCustomers',
        component: () => import('@/views/shop/CustomerList.vue'),
        meta: { title: '客户管理' },
      },
      {
        path: 'customers/:id',
        name: 'ShopCustomerProfile',
        component: () => import('@/views/shop/CustomerProfile.vue'),
        meta: { title: '客户画像' },
      },
    ],
  },

  // User Routes
  {
    path: '/user',
    redirect: '/user/home',
    meta: { role: 'user' },
    children: [
      {
        path: 'home',
        name: 'UserHome',
        component: () => import('@/views/user/Home.vue'),
        meta: { title: '首页 - 欢游' },
      },
      {
        path: 'recommend',
        name: 'UserRecommend',
        component: () => import('@/views/user/Recommend.vue'),
        meta: { title: '智能推荐' },
      },
      {
        path: 'orders',
        name: 'UserOrders',
        component: () => import('@/views/user/MyOrders.vue'),
        meta: { title: '我的订单' },
      },
      {
        path: 'orders/:id',
        name: 'UserOrderDetail',
        component: () => import('@/views/user/OrderDetail.vue'),
        meta: { title: '订单详情' },
      },
      {
        path: 'history',
        name: 'UserHistory',
        component: () => import('@/views/user/History.vue'),
        meta: { title: '旅行足迹' },
      },
      {
        path: 'chat',
        name: 'UserChat',
        component: () => import('@/views/user/TripChat.vue'),
        meta: { title: 'AI旅行管家' },
      },
    ],
  },

  // Default redirect
  { path: '/', redirect: '/login' },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Auth guard
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('access_token')
  const role = localStorage.getItem('user_role')

  document.title = (to.meta.title as string) || '欢游 HuanYou'

  if (to.path === '/login' || to.path === '/register') {
    if (token) {
      next(role === 'shop_owner' ? '/shop/dashboard' : '/user/home')
      return
    }
    next()
    return
  }

  if (!token) {
    next('/login')
    return
  }

  const requiredRole = to.matched[0]?.meta?.role
  if (requiredRole && requiredRole !== role) {
    next(role === 'shop_owner' ? '/shop/dashboard' : '/user/home')
    return
  }

  next()
})

export default router
