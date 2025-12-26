<template>
  <div class="app-layout">
    <aside class="sidebar">
      <h2>TBSL ERP</h2>
      <nav>
        <NuxtLink to="/">Dashboard</NuxtLink>
        <NuxtLink to="/items">Items</NuxtLink>
        <NuxtLink to="/customers">Customers</NuxtLink>
        <NuxtLink to="/suppliers">Suppliers</NuxtLink>
        <NuxtLink to="/inventory">Inventory</NuxtLink>
        <NuxtLink to="/alerts">Alerts</NuxtLink>
        <NuxtLink to="/reorder-rules">Reorder Rules</NuxtLink>
        <NuxtLink to="/ai-invoice">AI Invoice</NuxtLink>
      </nav>
    </aside>
    <div class="main-area">
      <header class="topbar">
        <div>{{ pageTitle }}</div>
        <div class="topbar-user">
          <span v-if="authStore.user">{{ authStore.user.full_name }} ({{ authStore.user.role }})</span>
          <button @click="authStore.logout()">Logout</button>
        </div>
      </header>
      <main class="content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const authStore = useAuthStore()
const route = useRoute()

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/': 'Dashboard',
    '/items': 'Items',
    '/customers': 'Customers',
    '/suppliers': 'Suppliers',
    '/inventory': 'Inventory',
    '/alerts': 'Alerts',
    '/reorder-rules': 'Reorder Rules',
    '/ai-invoice': 'AI Invoice',
  }
  return titles[route.path] || 'TBSL ERP'
})
</script>

