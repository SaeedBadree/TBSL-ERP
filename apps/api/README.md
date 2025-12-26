# TBSL ERP API

FastAPI backend for the monorepo. Key commands assume you are inside `apps/api`.

## Setup (local)
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
uvicorn app.main:app --reload
```

## Alembic
```bash
alembic revision -m "message"
alembic upgrade head
```

## Data model
- Core tables use UUID primary keys and unique legacy codes (item/customer/supplier).
- Raw source payloads are preserved in JSONB companion tables (`*_source_fields`).
- See `app/models/entities.py` for schema definitions; migrations live in `alembic/versions/`.

## Environment
See `.env.example` for defaults used by docker-compose.

