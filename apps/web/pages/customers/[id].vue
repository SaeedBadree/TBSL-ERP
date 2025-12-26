<template>
  <div>
    <button class="btn btn-secondary mb-1" @click="navigateTo('/customers')">← Back to Customers</button>

    <div v-if="customer" class="card">
      <h2>{{ customer.name }}</h2>
      <table class="data-table">
        <tbody>
          <tr><td><strong>Customer Code</strong></td><td>{{ customer.customer_code }}</td></tr>
          <tr><td><strong>Phone</strong></td><td>{{ customer.phone || '-' }}</td></tr>
          <tr><td><strong>Email</strong></td><td>{{ customer.email || '-' }}</td></tr>
          <tr><td><strong>Address</strong></td><td>{{ customer.address || '-' }}</td></tr>
          <tr><td><strong>Credit Limit</strong></td><td>{{ customer.credit_limit ?? '-' }}</td></tr>
          <tr><td><strong>Credit Days</strong></td><td>{{ customer.credit_days ?? '-' }}</td></tr>
          <tr><td><strong>Status</strong></td><td>{{ customer.status }}</td></tr>
          <tr><td><strong>Type</strong></td><td>{{ customer.type || '-' }}</td></tr>
          <tr><td><strong>Created</strong></td><td>{{ formatDate(customer.created_at) }}</td></tr>
        </tbody>
      </table>
    </div>

    <div v-else class="card">
      <p>Loading...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Customer } from '~/types'

const route = useRoute()
const api = useApi()

const customer = ref<Customer | null>(null)

onMounted(async () => {
  try {
    customer.value = await api.get<Customer>(`/customers/${route.params.id}`)
  } catch (e) {
    console.error('Failed to load customer', e)
  }
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString()
}
</script>

