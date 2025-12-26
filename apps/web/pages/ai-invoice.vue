<template>
  <div>
    <!-- Upload/Paste Step -->
    <div v-if="!document" class="card">
      <h2>Upload or Paste Invoice</h2>
      <div class="form-group">
        <label>Upload PDF/Image</label>
        <input type="file" accept=".pdf,.png,.jpg,.jpeg" @change="handleFileUpload" />
      </div>
      <p class="text-center">— OR —</p>
      <div class="form-group">
        <label>Paste Invoice Text</label>
        <textarea v-model="pastedText" rows="8" placeholder="Paste invoice content here..."></textarea>
      </div>
      <button class="btn btn-primary" :disabled="!pastedText && !selectedFile" @click="submitExtract">
        {{ loading ? 'Extracting...' : 'Extract Invoice' }}
      </button>
      <div v-if="error" class="error-message mt-1">{{ error }}</div>
    </div>

    <!-- Extracted Preview Step -->
    <div v-else-if="document.status === 'EXTRACTED'" class="card">
      <h2>Extracted Invoice Preview</h2>
      <div class="extracted-preview">
        <p><strong>Supplier:</strong> {{ document.extracted_json?.supplier || 'Unknown' }}</p>
        <p><strong>Invoice #:</strong> {{ document.extracted_json?.invoice_number || '-' }}</p>
        <p><strong>Date:</strong> {{ document.extracted_json?.invoice_date || '-' }}</p>
        <p><strong>Subtotal:</strong> {{ document.extracted_json?.subtotal ?? '-' }}</p>
        <p><strong>Tax:</strong> {{ document.extracted_json?.tax ?? '-' }}</p>
        <p><strong>Total:</strong> {{ document.extracted_json?.total ?? '-' }}</p>
      </div>

      <h3>Line Items</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th class="text-right">Qty</th>
            <th class="text-right">Unit Cost</th>
            <th>Matched Item</th>
            <th>Confidence</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(line, idx) in mappedLines" :key="idx" :class="line.confidence < 0.8 ? 'confidence-low' : 'confidence-high'">
            <td>{{ line.name }}</td>
            <td class="text-right">{{ line.qty }}</td>
            <td class="text-right">{{ line.unit_cost }}</td>
            <td>{{ line.item_name || 'Not matched' }}</td>
            <td>
              <span :class="['badge', line.confidence >= 0.8 ? 'badge-success' : 'badge-warning']">
                {{ (line.confidence * 100).toFixed(0) }}%
              </span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="lowConfidenceCount > 0" class="error-message mt-1">
        {{ lowConfidenceCount }} line(s) have low confidence matches. Please review before confirming.
      </div>

      <div class="flex gap-1 mt-1">
        <button class="btn btn-success" @click="confirmInvoice" :disabled="confirming">
          {{ confirming ? 'Creating GRN...' : 'Confirm & Create GRN' }}
        </button>
        <button class="btn btn-secondary" @click="reset">Start Over</button>
      </div>
    </div>

    <!-- Confirmed Step -->
    <div v-else-if="document.status === 'CONFIRMED'" class="card">
      <h2>Invoice Confirmed</h2>
      <p>A draft Goods Receipt has been created.</p>
      <button class="btn btn-primary" @click="reset">Process Another</button>
    </div>

    <!-- Failed -->
    <div v-else-if="document.status === 'FAILED'" class="card">
      <h2>Extraction Failed</h2>
      <p>Could not extract invoice data. Please try again.</p>
      <button class="btn btn-secondary" @click="reset">Start Over</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AIDocument, MappedLine } from '~/types'

const api = useApi()

const document = ref<AIDocument | null>(null)
const mappedLines = ref<MappedLine[]>([])
const pastedText = ref('')
const selectedFile = ref<File | null>(null)
const loading = ref(false)
const confirming = ref(false)
const error = ref('')

const lowConfidenceCount = computed(() => mappedLines.value.filter(l => l.confidence < 0.8).length)

function handleFileUpload(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.length) {
    selectedFile.value = target.files[0]
  }
}

async function submitExtract() {
  error.value = ''
  loading.value = true

  try {
    let doc: AIDocument
    if (selectedFile.value) {
      doc = await api.upload<AIDocument>('/ai/invoices/extract', selectedFile.value)
    } else {
      doc = await api.post<AIDocument>('/ai/invoices/extract', { text: pastedText.value })
    }
    document.value = doc

    if (doc.status === 'EXTRACTED' && doc.extracted_json?.lines) {
      // Fetch mapped lines
      const mapped = await api.post<MappedLine[]>(`/ai/invoices/${doc.id}/map-lines`, {
        lines: doc.extracted_json.lines,
      })
      mappedLines.value = mapped
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Extraction failed'
  } finally {
    loading.value = false
  }
}

async function confirmInvoice() {
  if (!document.value) return
  confirming.value = true

  try {
    await api.post(`/ai/invoices/${document.value.id}/confirm`, {
      lines: mappedLines.value,
    })
    document.value = { ...document.value, status: 'CONFIRMED' }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Confirm failed'
  } finally {
    confirming.value = false
  }
}

function reset() {
  document.value = null
  mappedLines.value = []
  pastedText.value = ''
  selectedFile.value = null
  error.value = ''
}
</script>

