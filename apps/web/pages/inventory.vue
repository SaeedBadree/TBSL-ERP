<template>
  <div>
    <div class="filters">
      <input v-model="search" type="text" placeholder="Search item..." @input="debouncedFetch" />
      <select v-model="locationFilter" @change="fetchBalances">
        <option value="">All Locations</option>
        <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ loc.name }}</option>
      </select>
      <label>
        <input type="checkbox" v-model="lowStockOnly" @change="fetchBalances" />
        Low Stock Only
      </label>
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th>Item Code</th>
          <th>Item Name</th>
          <th>Location</th>
          <th class="text-right">Available</th>
          <th class="text-right">Min Level</th>
          <th class="text-right">Max Level</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(b, idx) in balances" :key="idx">
          <td>{{ b.item_code }}</td>
          <td>{{ b.item_name }}</td>
          <td>{{ b.location_name }}</td>
          <td class="text-right">{{ b.available }}</td>
          <td class="text-right">{{ b.min_level ?? '-' }}</td>
          <td class="text-right">{{ b.max_level ?? '-' }}</td>
          <td>
            <span v-if="b.available < 0" class="badge badge-danger">Negative</span>
            <span v-else-if="b.min_level && b.available <= b.min_level" class="badge badge-warning">Low</span>
            <span v-else class="badge badge-success">OK</span>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <button :disabled="page <= 1" @click="page--; fetchBalances()">Prev</button>
      <span>Page {{ page }} of {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="page++; fetchBalances()">Next</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { StockBalance, StoreLocation } from '~/types'

const api = useApi()

const balances = ref<StockBalance[]>([])
const locations = ref<StoreLocation[]>([])
const page = ref(1)
const perPage = 20
const total = ref(0)
const search = ref('')
const locationFilter = ref('')
const lowStockOnly = ref(false)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / perPage)))

let debounceTimer: ReturnType<typeof setTimeout>
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    fetchBalances()
  }, 300)
}

async function fetchBalances() {
  try {
    const endpoint = lowStockOnly.value ? '/dashboard/low-stock' : '/inventory/balances'
    const data = await api.get<{ items: StockBalance[]; total: number }>(endpoint, {
      offset: (page.value - 1) * perPage,
      limit: perPage,
      search: search.value || undefined,
      location_id: locationFilter.value || undefined,
    })
    balances.value = data.items ?? []
    total.value = data.total ?? balances.value.length
  } catch (e) {
    console.error('Failed to load balances', e)
  }
}

async function fetchLocations() {
  try {
    const data = await api.get<{ items: StoreLocation[] }>('/locations')
    locations.value = data.items ?? []
  } catch (e) {
    console.error('Failed to load locations', e)
  }
}

onMounted(() => {
  fetchLocations()
  fetchBalances()
})
</script>

