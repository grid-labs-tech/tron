# Docker Configuration

This directory contains Docker Compose configurations for running Tron in different environments.

## Files

| File | Description |
|------|-------------|
| `docker-compose.yaml` | Development environment with local builds and hot-reload |
| `docker-compose.prod.yaml` | Production environment with pre-built images from GHCR |
| `.env.example` | Example environment variables for production |

## Development Environment

The development environment builds images locally and mounts source code for hot-reload.

### Using Makefile (recommended)

```bash
# From repository root
make start          # Start all services + load fixtures + setup k3s
make stop           # Stop all services
make restart        # Restart all services
make logs           # Follow logs
make status         # Show service status
make test           # Run all tests
make api-test       # Run API tests only
make portal-test    # Run Portal tests only
make build          # Build images
```

### Using Docker Compose directly

```bash
cd docker

# Start all development services
docker-compose up -d

# Start only database and API
docker-compose up -d database api

# View logs
docker-compose logs -f api

# Run tests
docker-compose run --rm api-test
docker-compose run --rm portal-test

# Stop all services
docker-compose down
```

## Production Environment

The production environment uses pre-built images from GitHub Container Registry.

### Quick Start

```bash
# 1. Create environment file
cp .env.example .env

# 2. Edit .env with your production values
#    - Set a strong DB_PASSWORD
#    - Set a secure SECRET_KEY (minimum 32 characters)
#    - Configure CORS_ORIGINS for your domain

# 3. Start all services
docker compose -f docker-compose.prod.yaml --profile full up -d

# 4. Check status
docker compose -f docker-compose.prod.yaml ps
```

### Production Profiles

Use profiles to control which services to start:

```bash
# Database only (useful when using external app servers)
docker compose -f docker-compose.prod.yaml --profile db up -d

# Application only (useful when using external database)
docker compose -f docker-compose.prod.yaml --profile app up -d

# Full stack (database + application)
docker compose -f docker-compose.prod.yaml --profile full up -d
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_PASSWORD` | Yes | - | Database password |
| `SECRET_KEY` | Yes | - | API secret key (min 32 chars) |
| `DB_USER` | No | `tron` | Database username |
| `API_IMAGE_TAG` | No | `latest` | API Docker image tag |
| `PORTAL_IMAGE_TAG` | No | `latest` | Portal Docker image tag |
| `API_PORT` | No | `8000` | Host port for API |
| `PORTAL_PORT` | No | `80` | Host port for Portal |
| `CORS_ORIGINS` | No | `http://localhost` | Allowed CORS origins |
| `API_URL` | No | `http://api:8000` | API URL for Portal |

### Using Specific Versions

For production stability, always use specific image versions:

```bash
# In .env file
API_IMAGE_TAG=0.2.0
PORTAL_IMAGE_TAG=0.2.0
```

Or via command line:

```bash
API_IMAGE_TAG=0.2.0 PORTAL_IMAGE_TAG=0.2.0 \
  docker compose -f docker-compose.prod.yaml --profile full up -d
```

### Available Images

Images are published to GitHub Container Registry:

- `ghcr.io/grid-labs-tech/tron-api:latest`
- `ghcr.io/grid-labs-tech/tron-api:0.2.0`
- `ghcr.io/grid-labs-tech/tron-api:0.2`
- `ghcr.io/grid-labs-tech/tron-portal:latest`
- `ghcr.io/grid-labs-tech/tron-portal:0.2.0`
- `ghcr.io/grid-labs-tech/tron-portal:0.2`

## Kubernetes (K3s)

For local Kubernetes development, a K3s cluster is included:

```bash
# Start K3s cluster
docker compose up -d k3s-server k3s-agent

# Get kubeconfig
export KUBECONFIG=${PWD}/volumes/kubeconfig/kubeconfig.yaml

# Verify cluster
kubectl get nodes
```

## Troubleshooting

### Database connection issues

```bash
# Check database logs
docker compose logs database

# Verify database is healthy
docker compose exec database pg_isready -U tron -d api
```

### API not starting

```bash
# Check API logs
docker compose -f docker-compose.prod.yaml logs api

# Run migrations manually
docker compose -f docker-compose.prod.yaml --profile db up -d
docker compose -f docker-compose.prod.yaml run --rm api-migrate
```

### Reset everything

```bash
# Development
docker compose down -v

# Production
docker compose -f docker-compose.prod.yaml down -v
```
