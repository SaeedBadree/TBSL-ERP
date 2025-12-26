<template>
  <div>
    <div class="filters">
      <select v-model="statusFilter" @change="fetchAlerts">
        <option value="">All Statuses</option>
        <option value="OPEN">Open</option>
        <option value="ACK">Acknowledged</option>
        <option value="DONE">Done</option>
      </select>
      <select v-model="typeFilter" @change="fetchAlerts">
        <option value="">All Types</option>
        <option value="LOW_STOCK">Low Stock</option>
        <option value="NEGATIVE_STOCK">Negative Stock</option>
        <option value="DEAD_STOCK">Dead Stock</option>
        <option value="SPIKE_SALES">Spike Sales</option>
        <option value="COST_CHANGE">Cost Change</option>
      </select>
      <select v-model="severityFilter" @change="fetchAlerts">
        <option value="">All Severities</option>
        <option value="INFO">Info</option>
        <option value="WARNING">Warning</option>
        <option value="CRITICAL">Critical</option>
      </select>
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th>Type</th>
          <th>Severity</th>
          <th>Message</th>
          <th>Status</th>
          <th>Created</th>
          <th>Actions</th>
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
          <td>
            <button
              v-if="alert.status === 'OPEN'"
              class="btn btn-secondary"
              @click="ackAlert(alert.id)"
            >
              Ack
            </button>
            <button
              v-if="alert.status !== 'DONE'"
              class="btn btn-success"
              @click="resolveAlert(alert.id)"
            >
              Resolve
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <button :disabled="page <= 1" @click="page--; fetchAlerts()">Prev</button>
      <span>Page {{ page }} of {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="page++; fetchAlerts()">Next</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Alert } from '~/types'

const api = useApi()

const alerts = ref<Alert[]>([])
const page = ref(1)
const perPage = 20
const total = ref(0)
const statusFilter = ref('')
const typeFilter = ref('')
const severityFilter = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / perPage)))

async function fetchAlerts() {
  try {
    const data = await api.get<Alert[]>('/alerts', {
      offset: (page.value - 1) * perPage,
      limit: perPage,
      status: statusFilter.value || undefined,
      type: typeFilter.value || undefined,
      severity: severityFilter.value || undefined,
    })
    alerts.value = data
    total.value = data.length >= perPage ? (page.value * perPage) + 1 : data.length
  } catch (e) {
    console.error('Failed to load alerts', e)
  }
}

async function ackAlert(id: string) {
  try {
    await api.post(`/alerts/${id}/ack`)
    fetchAlerts()
  } catch (e) {
    console.error('Failed to ack alert', e)
  }
}

async function resolveAlert(id: string) {
  try {
    await api.post(`/alerts/${id}/resolve`)
    fetchAlerts()
  } catch (e) {
    console.error('Failed to resolve alert', e)
  }
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

onMounted(fetchAlerts)
</script>

