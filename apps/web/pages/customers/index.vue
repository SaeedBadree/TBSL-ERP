<template>
  <div>
    <div class="filters">
      <input v-model="search" type="text" placeholder="Search by name or code..." @input="debouncedFetch" />
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th>Code</th>
          <th>Name</th>
          <th>Phone</th>
          <th>Email</th>
          <th>Status</th>
          <th>Type</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in customers" :key="c.id" @click="navigateTo(`/customers/${c.id}`)" style="cursor: pointer">
          <td>{{ c.customer_code }}</td>
          <td>{{ c.name }}</td>
          <td>{{ c.phone || '-' }}</td>
          <td>{{ c.email || '-' }}</td>
          <td>
            <span :class="['badge', c.status === 'active' ? 'badge-success' : 'badge-warning']">
              {{ c.status }}
            </span>
          </td>
          <td>{{ c.type || '-' }}</td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <button :disabled="page <= 1" @click="page--; fetchCustomers()">Prev</button>
      <span>Page {{ page }} of {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="page++; fetchCustomers()">Next</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Customer } from '~/types'

const api = useApi()

const customers = ref<Customer[]>([])
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
    fetchCustomers()
  }, 300)
}

async function fetchCustomers() {
  try {
    const data = await api.get<{ items: Customer[]; total: number }>('/customers', {
      offset: (page.value - 1) * perPage,
      limit: perPage,
      search: search.value || undefined,
    })
    customers.value = data.items ?? []
    total.value = data.total ?? 0
  } catch (e) {
    console.error('Failed to load customers', e)
  }
}

onMounted(fetchCustomers)
</script>

