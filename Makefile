# Convenience commands for the Sistema de Gestão de Estoque.
.PHONY: help up down logs build test lint backend-test frontend-build migrate seed

help:
	@echo "Targets:"
	@echo "  up             - docker compose up --build"
	@echo "  down           - docker compose down"
	@echo "  logs           - tail service logs"
	@echo "  test           - run backend tests"
	@echo "  lint           - run backend ruff lint"
	@echo "  frontend-build - typecheck + build frontend"
	@echo "  migrate        - alembic upgrade head"
	@echo "  seed           - init_db + sample_data"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

test:
	cd backend && pytest

lint:
	cd backend && ruff check app tests

frontend-build:
	cd frontend && npm run typecheck && npm run build

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.db.init_db && python -m app.db.sample_data
