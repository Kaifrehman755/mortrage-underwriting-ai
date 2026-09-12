.PHONY: help setup dev-backend dev-frontend docker-up docker-down test lint clean

help:
	@echo "Available commands:"
	@echo "  make setup          - Install dependencies for backend and frontend"
	@echo "  make dev-backend    - Run FastAPI backend locally with uvicorn"
	@echo "  make dev-frontend   - Run Next.js frontend locally"
	@echo "  make docker-up      - Build and start all services via Docker Compose"
	@echo "  make docker-down    - Stop all Docker Compose services"
	@echo "  make test           - Run backend test suite"
	@echo "  make lint           - Run linting with Ruff and TypeScript checks"
	@echo "  make clean          - Remove temporary files, caches, and test artifacts"

setup:
	@echo "Installing backend dependencies..."
	pip install -r backend/requirements.txt -r backend/requirements-dev.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

test:
	cd backend && pytest tests/ -v

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
