# TBSL ERP Web Frontend

Nuxt 3 frontend for the ERP system.

## Setup

```bash
cd apps/web
npm install
npm run dev
```

The app runs on http://localhost:3000 by default.

## Configuration

Set the API base URL via environment variable:

```bash
NUXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

## Pages

- `/login` - Staff login
- `/` - Dashboard with tiles (sales today, low stock, negative stock) and recent alerts
- `/items` - Items list with search and pagination
- `/items/:id` - Item detail
- `/customers` - Customers list
- `/customers/:id` - Customer detail
- `/suppliers` - Suppliers list
- `/suppliers/:id` - Supplier detail
- `/inventory` - Stock balances with filters
- `/alerts` - Alerts list with ack/resolve actions
- `/reorder-rules` - CRUD for reorder rules
- `/ai-invoice` - AI-assisted invoice entry (upload/paste → preview → confirm)

## Tech Stack

- Nuxt 3
- TypeScript
- Pinia (state management)
- Pico CSS (minimal styling)

## Building

```bash
npm run build
npm run preview
```
