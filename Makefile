.PHONY: help up down logs test backend frontend build-frontend clean

help:
	@echo "ADDMAI Development Automation Commands"
	@echo "========================================"
	@echo "make up             - Start Docker Compose stack in background"
	@echo "make down           - Stop Docker Compose stack"
	@echo "make logs           - Stream Docker Compose logs"
	@echo "make test           - Run backend unit tests"
	@echo "make backend        - Run FastAPI API locally with auto-reload"
	@echo "make frontend       - Run React Vite dev server"
	@echo "make build-frontend - Build React frontend static bundle"
	@echo "make clean          - Remove temporary and cache files"

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

test:
	python -m unittest discover -s apps/api/tests
	python -m unittest discover -s tests

backend:
	python -m uvicorn app.main:app --app-dir apps/api --reload --port 8000

frontend:
	npm --prefix apps/web run dev

build-frontend:
	npm --prefix apps/web run build

clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
