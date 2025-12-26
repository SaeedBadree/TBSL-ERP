<template>
  <div>
    <div class="filters">
      <input v-model="search" type="text" placeholder="Search by name or code..." @input="debouncedFetch" />
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th>Code</th>
          <th>SKU</th>
          <th>Name</th>
          <th>Barcode</th>
          <th>UOM</th>
          <th>Brand</th>
          <th>Active</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" @click="navigateTo(`/items/${item.id}`)" style="cursor: pointer">
          <td>{{ item.item_code }}</td>
          <td>{{ item.sku }}</td>
          <td>{{ item.name }}</td>
          <td>{{ item.barcode || '-' }}</td>
          <td>{{ item.uom || '-' }}</td>
          <td>{{ item.brand || '-' }}</td>
          <td>
            <span :class="['badge', item.active ? 'badge-success' : 'badge-danger']">
              {{ item.active ? 'Yes' : 'No' }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <button :disabled="page <= 1" @click="page--; fetchItems()">Prev</button>
      <span>Page {{ page }} of {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="page++; fetchItems()">Next</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Item } from '~/types'

const api = useApi()

const items = ref<Item[]>([])
const page = ref(1)
const perPage = 20
const total = ref(0)
const search = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / perPage)))

let debounceTimer: ReturnType<typeof setTimeout>
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    fetchItems()
  }, 300)
}

async function fetchItems() {
  try {
    const data = await api.get<{ items: Item[]; total: number }>('/items', {
      offset: (page.value - 1) * perPage,
      limit: perPage,
      search: search.value || undefined,
    })
    items.value = data.items ?? []
    total.value = data.total ?? 0
  } catch (e) {
    console.error('Failed to load items', e)
  }
}

onMounted(fetchItems)
</script>

