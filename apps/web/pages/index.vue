<template>
  <div>
    <div class="dashboard-tiles">
      <div class="tile">
        <h3>Sales Today</h3>
        <div class="value">{{ formatCurrency(stats.sales_today) }}</div>
      </div>
      <div class="tile" :class="{ warning: stats.low_stock_count > 0 }">
        <h3>Low Stock Items</h3>
        <div class="value">{{ stats.low_stock_count }}</div>
      </div>
      <div class="tile" :class="{ danger: stats.negative_stock_count > 0 }">
        <h3>Negative Stock</h3>
        <div class="value">{{ stats.negative_stock_count }}</div>
      </div>
    </div>

    <div class="card">
      <h2>Recent Alerts</h2>
      <table v-if="alerts.length" class="data-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Severity</th>
            <th>Message</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="alert in alerts" :key="alert.id">
            <td>{{ alert.type }}</td>
            <td>
              <span :class="['badge', severityClass(alert.severity)]">{{ alert.severity }}</span>
            </td>
            <td>{{ alert.message }}</td>
            <td>
              <span :class="['badge', statusClass(alert.status)]">{{ alert.status }}</span>
            </td>
            <td>{{ formatDate(alert.created_at) }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else>No recent alerts.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Alert, DashboardStats } from '~/types'

const api = useApi()

const stats = ref<DashboardStats>({
  sales_today: 0,
  low_stock_count: 0,
  negative_stock_count: 0,
})

const alerts = ref<Alert[]>([])

onMounted(async () => {
  try {
    const [lowStock, negStock, alertsData] = await Promise.all([
      api.get<{ items: unknown[] }>('/dashboard/low-stock', { limit: 1000 }),
      api.get<Alert[]>('/alerts', { status: 'OPEN', type: 'NEGATIVE_STOCK', limit: 1000 }),
      api.get<Alert[]>('/alerts', { status: 'OPEN', limit: 5 }),
    ])
    stats.value.low_stock_count = lowStock.items?.length ?? 0
    stats.value.negative_stock_count = negStock.length ?? 0
    alerts.value = alertsData
  } catch (e) {
    console.error('Failed to load dashboard', e)
  }
})

function formatCurrency(val: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString()
}

function severityClass(severity: string) {
  const map: Record<string, string> = { INFO: 'badge-info', WARNING: 'badge-warning', CRITICAL: 'badge-danger' }
  return map[severity] ?? 'badge-info'
}

function statusClass(status: string) {
  const map: Record<string, string> = { OPEN: 'badge-warning', ACK: 'badge-info', DONE: 'badge-success' }
  return map[status] ?? ''
}
</script>

