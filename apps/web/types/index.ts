// Auth
export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  role: string
}

export interface User {
  id: string
  email: string
  full_name: string
  role: 'CASHIER' | 'MANAGER' | 'ADMIN' | 'AUDITOR'
}

// Core entities
export interface Item {
  id: string
  item_code: string
  sku: string
  name: string
  short_name?: string
  barcode?: string
  uom?: string
  brand?: string
  active: boolean
  created_at: string
}

export interface Customer {
  id: string
  customer_code: string
  name: string
  phone?: string
  email?: string
  address?: string
  credit_limit?: number
  credit_days?: number
  status: string
  type?: string
  created_at: string
}

export interface Supplier {
  id: string
  supplier_code: string
  name: string
  phone?: string
  email?: string
  address?: string
  payment_terms?: string
  created_at: string
}

export interface StoreLocation {
  id: string
  code: string
  name: string
}

// Inventory
export interface StockBalance {
  item_id: string
  item_code: string
  item_name: string
  location_id: string
  location_name: string
  available: number
  min_level?: number
  max_level?: number
}

// Alerts
export type AlertType = 'LOW_STOCK' | 'NEGATIVE_STOCK' | 'DEAD_STOCK' | 'SPIKE_SALES' | 'COST_CHANGE' | 'SUPPLIER_DELAY'
export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL'
export type AlertStatus = 'OPEN' | 'ACK' | 'DONE'

export interface Alert {
  id: string
  type: AlertType
  severity: AlertSeverity
  status: AlertStatus
  message: string
  context: Record<string, unknown>
  item_id?: string
  location_id?: string
  created_at: string
  ack_by?: string
  ack_at?: string
}

// Reorder
export interface ReorderRule {
  id: string
  item_id: string
  location_id: string
  min_level: number
  max_level: number
  reorder_qty: number
  preferred_supplier_id?: string
  lead_time_days: number
  active: boolean
}

export interface ReorderRuleCreate {
  item_id: string
  location_id: string
  min_level: number
  max_level: number
  reorder_qty: number
  preferred_supplier_id?: string
  lead_time_days: number
  active?: boolean
}

// AI Invoice
export type AIDocumentStatus = 'PENDING' | 'EXTRACTED' | 'CONFIRMED' | 'FAILED'

export interface AIDocument {
  id: string
  type: string
  filename?: string
  mime?: string
  raw_text?: string
  extracted_json?: ExtractedInvoice
  status: AIDocumentStatus
  created_at: string
}

export interface ExtractedInvoice {
  supplier?: string
  invoice_number?: string
  invoice_date?: string
  lines: ExtractedLine[]
  subtotal?: number
  tax?: number
  total?: number
}

export interface ExtractedLine {
  name: string
  qty: number
  unit_cost: number
}

export interface MappedLine {
  name: string
  qty: number
  unit_cost: number
  item_id?: string
  item_name?: string
  confidence: number
  match_type?: string
}

// Paginated response
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
}

// Dashboard
export interface DashboardStats {
  sales_today: number
  low_stock_count: number
  negative_stock_count: number
}

