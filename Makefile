COMPOSE = docker compose -f infra/docker-compose.yml

.PHONY: dev api-shell migrate test lint

dev:
	$(COMPOSE) up --build

api-shell:
	$(COMPOSE) run --rm api bash

migrate:
	$(COMPOSE) run --rm api alembic upgrade head

test:
	$(COMPOSE) run --rm api pytest

lint:
	$(COMPOSE) run --rm api ruff check .


