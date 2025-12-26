<template>
  <div>
    <div class="flex justify-between items-center mb-1">
      <h2>Reorder Rules</h2>
      <button class="btn btn-primary" @click="showForm = true">+ Add Rule</button>
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th>Item</th>
          <th>Location</th>
          <th class="text-right">Min Level</th>
          <th class="text-right">Max Level</th>
          <th class="text-right">Reorder Qty</th>
          <th>Lead Days</th>
          <th>Active</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="rule in rules" :key="rule.id">
          <td>{{ rule.item_id }}</td>
          <td>{{ rule.location_id }}</td>
          <td class="text-right">{{ rule.min_level }}</td>
          <td class="text-right">{{ rule.max_level }}</td>
          <td class="text-right">{{ rule.reorder_qty }}</td>
          <td>{{ rule.lead_time_days }}</td>
          <td>
            <span :class="['badge', rule.active ? 'badge-success' : 'badge-danger']">
              {{ rule.active ? 'Yes' : 'No' }}
            </span>
          </td>
          <td>
            <button class="btn btn-secondary" @click="editRule(rule)">Edit</button>
            <button class="btn btn-danger" @click="deleteRule(rule.id)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <button :disabled="page <= 1" @click="page--; fetchRules()">Prev</button>
      <span>Page {{ page }}</span>
      <button @click="page++; fetchRules()">Next</button>
    </div>

    <!-- Modal Form -->
    <div v-if="showForm" class="card" style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 400px; z-index: 100; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
      <h3>{{ editingId ? 'Edit Rule' : 'Add Rule' }}</h3>
      <form @submit.prevent="saveRule">
        <div class="form-group">
          <label>Item ID</label>
          <input v-model="form.item_id" required />
        </div>
        <div class="form-group">
          <label>Location ID</label>
          <input v-model="form.location_id" required />
        </div>
        <div class="form-group">
          <label>Min Level</label>
          <input v-model.number="form.min_level" type="number" required />
        </div>
        <div class="form-group">
          <label>Max Level</label>
          <input v-model.number="form.max_level" type="number" required />
        </div>
        <div class="form-group">
          <label>Reorder Qty</label>
          <input v-model.number="form.reorder_qty" type="number" required />
        </div>
        <div class="form-group">
          <label>Lead Time Days</label>
          <input v-model.number="form.lead_time_days" type="number" required />
        </div>
        <div class="form-group">
          <label>
            <input type="checkbox" v-model="form.active" /> Active
          </label>
        </div>
        <div class="flex gap-1">
          <button type="submit" class="btn btn-primary">Save</button>
          <button type="button" class="btn btn-secondary" @click="closeForm">Cancel</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ReorderRule, ReorderRuleCreate } from '~/types'

const api = useApi()

const rules = ref<ReorderRule[]>([])
const page = ref(1)
const perPage = 20
const showForm = ref(false)
const editingId = ref<string | null>(null)

const form = ref<ReorderRuleCreate>({
  item_id: '',
  location_id: '',
  min_level: 0,
  max_level: 0,
  reorder_qty: 0,
  lead_time_days: 0,
  active: true,
})

async function fetchRules() {
  try {
    const data = await api.get<ReorderRule[]>('/reorder-rules', {
      offset: (page.value - 1) * perPage,
      limit: perPage,
    })
    rules.value = data
  } catch (e) {
    console.error('Failed to load rules', e)
  }
}

function editRule(rule: ReorderRule) {
  editingId.value = rule.id
  form.value = {
    item_id: rule.item_id,
    location_id: rule.location_id,
    min_level: rule.min_level,
    max_level: rule.max_level,
    reorder_qty: rule.reorder_qty,
    lead_time_days: rule.lead_time_days,
    active: rule.active,
  }
  showForm.value = true
}

async function saveRule() {
  try {
    if (editingId.value) {
      await api.put(`/reorder-rules/${editingId.value}`, form.value)
    } else {
      await api.post('/reorder-rules', form.value)
    }
    closeForm()
    fetchRules()
  } catch (e) {
    console.error('Failed to save rule', e)
  }
}

async function deleteRule(id: string) {
  if (!confirm('Delete this rule?')) return
  try {
    await api.delete(`/reorder-rules/${id}`)
    fetchRules()
  } catch (e) {
    console.error('Failed to delete rule', e)
  }
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  form.value = {
    item_id: '',
    location_id: '',
    min_level: 0,
    max_level: 0,
    reorder_qty: 0,
    lead_time_days: 0,
    active: true,
  }
}

onMounted(fetchRules)
</script>

