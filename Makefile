.PHONY: help setup infra-up infra-down test lint format clean

# Default target
help:
	@echo "Open Forge - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  setup          - Set up development environment"
	@echo "  infra-up       - Start infrastructure services"
	@echo "  infra-down     - Stop infrastructure services"
	@echo "  infra-test     - Test infrastructure health"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests"
	@echo "  test-int       - Run integration tests"
	@echo "  test-core      - Run core package tests"
	@echo "  test-agents    - Run agent tests"
	@echo "  test-orchestration - Run orchestration tests"
	@echo "  e2e-test       - Run end-to-end tests"
	@echo ""
	@echo "Checkpoints:"
	@echo "  test-checkpoint-1  - Test Checkpoint 1 (Infrastructure)"
	@echo "  test-checkpoint-2  - Test Checkpoint 2 (Agent Clusters)"
	@echo "  test-checkpoint-3  - Test Checkpoint 3 (Orchestration)"
	@echo "  test-checkpoint-4  - Test Checkpoint 4 (Production)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint           - Run linters"
	@echo "  format         - Format code"
	@echo "  typecheck      - Run type checking"
	@echo ""
	@echo "Utilities:"
	@echo "  clean          - Clean build artifacts"
	@echo "  reset-db       - Reset database"

# ============================================================
# SETUP
# ============================================================

setup:
	@echo "Setting up development environment..."
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "Setup complete!"

# ============================================================
# INFRASTRUCTURE
# ============================================================

infra-up:
	@echo "Starting infrastructure services..."
	docker compose -f infrastructure/docker/docker-compose.yml up -d
	@echo "Waiting for services to be healthy..."
	@sleep 15
	docker compose -f infrastructure/docker/docker-compose.yml ps
	@echo "Infrastructure is ready!"

infra-down:
	@echo "Stopping infrastructure services..."
	docker compose -f infrastructure/docker/docker-compose.yml down
	@echo "Infrastructure stopped."

infra-test:
	@echo "Testing infrastructure health..."
	@echo "Testing PostgreSQL..."
	docker compose -f infrastructure/docker/docker-compose.yml exec -T postgres pg_isready -U foundry
	@echo "Testing Redis..."
	docker compose -f infrastructure/docker/docker-compose.yml exec -T redis redis-cli ping
	@echo "Testing MinIO..."
	curl -sf http://localhost:9000/minio/health/live > /dev/null && echo "MinIO: OK"
	@echo ""
	@echo "All services healthy!"

reset-db:
	@echo "Resetting database..."
	docker compose -f infrastructure/docker/docker-compose.yml down -v
	docker compose -f infrastructure/docker/docker-compose.yml up -d postgres
	@sleep 10
	@echo "Database reset complete."

# ============================================================
# TESTING
# ============================================================

test: test-unit test-int

test-unit:
	pytest packages/*/tests/unit -v --tb=short

test-int:
	pytest packages/*/tests/integration -v --tb=short

test-core:
	pytest packages/core/tests -v

test-agents:
	pytest packages/agents/tests -v

test-orchestration:
	pytest packages/orchestration/tests -v

e2e-test:
	pytest tests/e2e -v --tb=long

# ============================================================
# CHECKPOINT TESTS
# ============================================================

test-checkpoint-1:
	@echo "=========================================="
	@echo "Testing Checkpoint 1: Infrastructure Ready"
	@echo "=========================================="
	$(MAKE) infra-test
	pytest packages/core/tests -v
	pytest packages/ontology/tests -v
	pytest packages/connectors/tests -v
	pytest packages/agent-framework/tests -v
	@echo ""
	@echo "Checkpoint 1: PASSED"

test-checkpoint-2:
	@echo "=========================================="
	@echo "Testing Checkpoint 2: Agent Clusters"
	@echo "=========================================="
	pytest packages/agents/tests/discovery -v
	pytest packages/agents/tests/data_architect -v
	pytest packages/agents/tests/app_builder -v
	pytest packages/human-interaction/tests -v
	@echo ""
	@echo "Checkpoint 2: PASSED"

test-checkpoint-3:
	@echo "=========================================="
	@echo "Testing Checkpoint 3: Full Orchestration"
	@echo "=========================================="
	pytest packages/orchestration/tests -v
	python scripts/integration/checkpoint_3_test.py
	@echo ""
	@echo "Checkpoint 3: PASSED"

test-checkpoint-4:
	@echo "=========================================="
	@echo "Testing Checkpoint 4: Production Ready"
	@echo "=========================================="
	$(MAKE) e2e-test
	./scripts/security_audit.sh
	./scripts/performance_benchmark.sh
	@echo ""
	@echo "Checkpoint 4: PASSED"

# ============================================================
# CODE QUALITY
# ============================================================

lint:
	ruff check packages/

format:
	ruff format packages/
	isort packages/

typecheck:
	mypy packages/

# ============================================================
# UTILITIES
# ============================================================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned build artifacts."

# ============================================================
# MERGE COMMANDS (for parallel development)
# ============================================================

merge-checkpoint-1:
	git checkout main
	git merge ws1/core-infrastructure --no-ff -m "Merge WS1: Core Infrastructure"
	git merge ws2/agent-framework --no-ff -m "Merge WS2: Agent Framework"
	git merge ws3/data-connectors --no-ff -m "Merge WS3: Data Connectors"
	git merge ws4/ontology-compiler --no-ff -m "Merge WS4: Ontology Compiler"

merge-checkpoint-2:
	git checkout main
	git merge ws5/discovery-agents --no-ff -m "Merge WS5: Discovery Agents"
	git merge ws6/data-architect-agents --no-ff -m "Merge WS6: Data Architect Agents"
	git merge ws7/app-builder-agents --no-ff -m "Merge WS7: App Builder Agents"
	git merge ws8/human-interaction --no-ff -m "Merge WS8: Human Interaction"
