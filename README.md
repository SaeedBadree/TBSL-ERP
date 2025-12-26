# TBSL ERP Monorepo

Modern ERP scaffold with a FastAPI backend, Nuxt frontend placeholder, shared package space, and infra for local development.

## Structure
- `apps/api` – FastAPI backend (Python 3.12, SQLAlchemy async, Alembic, Ruff, Pytest).
- `apps/web` – Nuxt frontend placeholder (to be implemented).
- `packages/shared` – Shared libraries/types placeholder.
- `infra` – Docker Compose for Postgres, Redis, and the API.

## Quick start
```bash
make dev          # start Postgres, Redis, API via docker compose
make api-shell    # interactive shell in the api container
make migrate      # run Alembic migrations
make test         # run backend tests
make lint         # run ruff on the backend
```

## Local (without Docker)
```bash
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

## Configuration
Environment variables:
- `APP_NAME` (default `tbslerp-api`)
- `APP_ENV` (default `local`)
- `LOG_LEVEL` (default `INFO`)
- `DATABASE_URL` (default `postgresql+asyncpg://erp:erp@localhost:5432/erp`)
- `REDIS_URL` (default `redis://localhost:6379/0`)

## Notes
- Alembic is wired for async SQLAlchemy via `app.core.db.Base`.
- Problem+JSON error responses are registered globally.
- Security hooks are stubbed in `app/core/security/__init__.py` for future auth.

## Data import (legacy exports)
- Items: `python -m scripts.import_items --items /mnt/data/3320_Item_List__6_2025_12_13_092401.csv`
- Customers: `python -m scripts.import_customers --customers /mnt/data/3322_Customer_L_tomer_List_6_2025_12_13_153515.zip`
- Suppliers: `python -m scripts.import_suppliers --suppliers /mnt/data/3281_Distributo_butor_List_6_2025_12_13_154139.zip`
- Or run combined: `python -m scripts.import_all --items ... --customers ... --suppliers ...`
- Rejects are logged to `rejects.log`; files may contain leading report headers and are auto-detected.


