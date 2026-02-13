DOCKER_COMPOSE := docker compose
COMPOSE_FILE := docker/docker-compose.yaml
COMPOSE_TEST_FILE := docker/docker-compose.test.yaml
COMPOSE_CLUSTER2_FILE := docker/docker-compose.cluster2.yaml

.PHONY: start stop restart build logs status test api-test portal-test setup-cluster setup-cluster2 clean help

help:
	@echo "Tron Development Commands:"
	@echo "  make start          - Start all services (API, Portal, Database, K3s)"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - Follow logs from all services"
	@echo "  make status         - Show status of all services"
	@echo "  make test           - Run all tests (API + Portal)"
	@echo "  make api-test       - Run API tests only"
	@echo "  make portal-test    - Run Portal tests only"
	@echo "  make setup-cluster  - Setup k3s cluster with Tron (run after start)"
	@echo "  make setup-cluster2 - Setup k3s cluster2 with Tron (run after start)"
	@echo "  make clean          - Stop services and remove volumes"
	@echo "  make build          - Rebuild Docker images"

start:
	@echo "🚀 Starting Tron development environment..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d
	@echo ""
	@echo "✅ Services started!"
	@echo ""
	@echo "📝 Default credentials:"
	@echo "   Email: admin@example.com"
	@echo "   Password: admin"
	@echo ""
	@echo "🌐 Access:"
	@echo "   Portal: http://localhost:3000"
	@echo "   API:    http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"
	@echo "   Run 'make setup-cluster' to setup k3s cluster with Tron"

stop:
	@echo "🛑 Stopping services..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down

restart:
	@make stop
	@make start

clean:
	@echo "🧹 Cleaning up..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down -v --remove-orphans
	@$(DOCKER_COMPOSE) -f $(COMPOSE_TEST_FILE) down -v --remove-orphans 2>/dev/null || true
	@$(DOCKER_COMPOSE) -f $(COMPOSE_CLUSTER2_FILE) down -v --remove-orphans 2>/dev/null || true
	@rm -rf docker/volumes/postgres docker/volumes/postgres-test docker/volumes/kubeconfig docker/volumes/kubeconfig2 docker/volumes/token
	@echo "✅ Cleaned!"

build:
	@echo "🔨 Building images..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) build
	@$(DOCKER_COMPOSE) -f $(COMPOSE_TEST_FILE) build

logs:
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f

status:
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) ps

setup-cluster:
	@echo "🔧 Setting up local k3s cluster..."
	@cd docker && ./scripts/setup-k3s-cluster.sh 2>/dev/null || ../scripts/setup-k3s-cluster.sh

setup-cluster2:
	@echo "🔧 Setting up k3s cluster2..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_CLUSTER2_FILE) up -d
	@sleep 5
	@cd docker && ./scripts/setup-k3s-cluster2.sh 2>/dev/null || ../scripts/setup-k3s-cluster2.sh
	@echo "✅ Cluster2 setup completed!"

api-test:
	@echo "🧪 Running API tests..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_TEST_FILE) run --rm api-test

portal-test:
	@echo "🧪 Running Portal tests..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_TEST_FILE) run --rm portal-test

test:
	@echo "========================================="
	@echo "🧪 Running API tests..."
	@echo "========================================="
	@make api-test
	@echo ""
	@echo "========================================="
	@echo "🧪 Running Portal tests..."
	@echo "========================================="
	@make portal-test
	@echo ""
	@echo "========================================="
	@echo "✅ All tests completed!"
	@echo "========================================="

# Development helpers
api-migrate:
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) exec api alembic revision --autogenerate

api-shell:
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) exec api sh

db-shell:
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) exec database psql -U tron -d api
