# Use docker-compose or docker compose based on availability
DOCKER_COMPOSE := $(shell command -v docker-compose 2>/dev/null || echo "docker compose")

restart:
	@make stop
	@make start

start:
	@$(DOCKER_COMPOSE) -f docker/docker-compose.yaml up -d
	@make load-fixtures
	@make setup-dev-cluster

api-migrate:
	@$(DOCKER_COMPOSE) -f docker/docker-compose.yaml run --rm api sh -c 'alembic revision --autogenerate'

api-migration:
	@$(DOCKER_COMPOSE) -f docker/docker-compose.yaml run --rm api sh -c 'alembic upgrade head'

api-test:
	@$(DOCKER_COMPOSE) -f docker/docker-compose.yaml run --rm api-test

portal-test:
	@$(DOCKER_COMPOSE) -f docker/docker-compose.yaml run --rm portal-test

test:
	@echo "========================================="
	@echo "Running API tests..."
	@echo "========================================="
	@make api-test
	@echo ""
	@echo "========================================="
	@echo "Running Portal tests..."
	@echo "========================================="
	@make portal-test
	@echo ""
	@echo "========================================="
	@echo "All tests completed!"
	@echo "========================================="

build:
	@$(DOCKER_COMPOSE) -f docker/docker-compose.yaml build

stop:
	@$(DOCKER_COMPOSE) -f docker/docker-compose.yaml down -v --remove-orphans

logs:
	@$(DOCKER_COMPOSE) -f docker/docker-compose.yaml logs -f

status:
	@$(DOCKER_COMPOSE) -f docker/docker-compose.yaml ps

setup-dev-cluster:
	@./scripts/setup-k3s-cluster.sh

load-fixtures:
	@$(DOCKER_COMPOSE) -f docker/docker-compose.yaml run --rm api sh -c 'python scripts/load_initial_templates.py'
	@$(DOCKER_COMPOSE) -f docker/docker-compose.yaml run --rm api sh -c 'python scripts/load_initial_user.py'

reset-migrations:
	@$(DOCKER_COMPOSE) -f docker/docker-compose.yaml run --rm api sh -c 'python scripts/reset_alembic_history.py'
