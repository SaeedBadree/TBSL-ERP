<template>
  <div>
    <button class="btn btn-secondary mb-1" @click="navigateTo('/items')">← Back to Items</button>

    <div v-if="item" class="card">
      <h2>{{ item.name }}</h2>
      <table class="data-table">
        <tbody>
          <tr><td><strong>Item Code</strong></td><td>{{ item.item_code }}</td></tr>
          <tr><td><strong>SKU</strong></td><td>{{ item.sku }}</td></tr>
          <tr><td><strong>Barcode</strong></td><td>{{ item.barcode || '-' }}</td></tr>
          <tr><td><strong>Short Name</strong></td><td>{{ item.short_name || '-' }}</td></tr>
          <tr><td><strong>UOM</strong></td><td>{{ item.uom || '-' }}</td></tr>
          <tr><td><strong>Brand</strong></td><td>{{ item.brand || '-' }}</td></tr>
          <tr><td><strong>Active</strong></td><td>{{ item.active ? 'Yes' : 'No' }}</td></tr>
          <tr><td><strong>Created</strong></td><td>{{ formatDate(item.created_at) }}</td></tr>
        </tbody>
      </table>
    </div>

    <div v-else class="card">
      <p>Loading...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Item } from '~/types'

const route = useRoute()
const api = useApi()

const item = ref<Item | null>(null)

onMounted(async () => {
  try {
    item.value = await api.get<Item>(`/items/${route.params.id}`)
  } catch (e) {
    console.error('Failed to load item', e)
  }
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString()
}
</script>

