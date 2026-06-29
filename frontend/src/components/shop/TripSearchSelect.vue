<template>
  <el-select
    v-model="selectedId"
    filterable
    remote
    :remote-method="searchTrips"
    :loading="loading"
    placeholder="搜索并选择一个行程"
    size="large"
    style="width: 100%"
    @change="$emit('select', selectedTrip)"
  >
    <el-option
      v-for="t in trips"
      :key="t.id"
      :label="`${t.title} (${t.destination})`"
      :value="t.id"
    >
      <div class="option-item">
        <span class="title">{{ t.title }}</span>
        <span class="meta">
          <el-tag size="small">{{ t.category }}</el-tag>
          {{ t.destination }} · {{ t.duration_days }}天
          <span v-if="t.price_adult" style="color:#e53935">· &yen;{{ t.price_adult }}</span>
        </span>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { tripApi } from '@/api/auth'

const emit = defineEmits<{ select: [trip: any] }>()
const selectedId = ref('')
const trips = ref<any[]>([])
const loading = ref(false)

const selectedTrip = computed(() => trips.value.find(t => t.id === selectedId.value) || null)

async function searchTrips(query: string) {
  if (!query || query.length < 1) return
  loading.value = true
  try {
    const res = await tripApi.list({ search: query, page_size: 10, status: 'active' })
    trips.value = res.items || []
  } finally { loading.value = false }
}

// Initial load
searchTrips('')
</script>

<style scoped>
.option-item { display: flex; flex-direction: column; gap: 4px; }
.title { font-weight: 500; }
.meta { font-size: 12px; color: #909399; display: flex; align-items: center; gap: 4px; }
</style>
