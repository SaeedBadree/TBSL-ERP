<template>
  <div>
    <button class="btn btn-secondary mb-1" @click="navigateTo('/suppliers')">← Back to Suppliers</button>

    <div v-if="supplier" class="card">
      <h2>{{ supplier.name }}</h2>
      <table class="data-table">
        <tbody>
          <tr><td><strong>Supplier Code</strong></td><td>{{ supplier.supplier_code }}</td></tr>
          <tr><td><strong>Phone</strong></td><td>{{ supplier.phone || '-' }}</td></tr>
          <tr><td><strong>Email</strong></td><td>{{ supplier.email || '-' }}</td></tr>
          <tr><td><strong>Address</strong></td><td>{{ supplier.address || '-' }}</td></tr>
          <tr><td><strong>Payment Terms</strong></td><td>{{ supplier.payment_terms || '-' }}</td></tr>
          <tr><td><strong>Created</strong></td><td>{{ formatDate(supplier.created_at) }}</td></tr>
        </tbody>
      </table>
    </div>

    <div v-else class="card">
      <p>Loading...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Supplier } from '~/types'

const route = useRoute()
const api = useApi()

const supplier = ref<Supplier | null>(null)

onMounted(async () => {
  try {
    supplier.value = await api.get<Supplier>(`/suppliers/${route.params.id}`)
  } catch (e) {
    console.error('Failed to load supplier', e)
  }
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString()
}
</script>

