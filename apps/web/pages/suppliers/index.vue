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
          <th>Payment Terms</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in suppliers" :key="s.id" @click="navigateTo(`/suppliers/${s.id}`)" style="cursor: pointer">
          <td>{{ s.supplier_code }}</td>
          <td>{{ s.name }}</td>
          <td>{{ s.phone || '-' }}</td>
          <td>{{ s.email || '-' }}</td>
          <td>{{ s.payment_terms || '-' }}</td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <button :disabled="page <= 1" @click="page--; fetchSuppliers()">Prev</button>
      <span>Page {{ page }} of {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="page++; fetchSuppliers()">Next</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Supplier } from '~/types'

const api = useApi()

const suppliers = ref<Supplier[]>([])
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
    fetchSuppliers()
  }, 300)
}

async function fetchSuppliers() {
  try {
    const data = await api.get<{ items: Supplier[]; total: number }>('/suppliers', {
      offset: (page.value - 1) * perPage,
      limit: perPage,
      search: search.value || undefined,
    })
    suppliers.value = data.items ?? []
    total.value = data.total ?? 0
  } catch (e) {
    console.error('Failed to load suppliers', e)
  }
}

onMounted(fetchSuppliers)
</script>

