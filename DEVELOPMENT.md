# Development Guide

This guide covers setting up and running Tron locally for development.

## Prerequisites

- Docker
- Docker Compose
- Make (optional, but recommended)

## Quick Start

Run a single command to start the entire development environment:

```bash
make start
```

This command will:
- ✅ Start the FastAPI API (http://localhost:8000)
- ✅ Start the React Portal (http://localhost:3000)
- ✅ Start the PostgreSQL database
- ✅ Start the Kubernetes cluster (K3s)
- ✅ Run database migrations
- ✅ Load initial templates
- ✅ Create default administrator user
- ✅ Configure API token
- ✅ Create "local" environment
- ✅ Configure local cluster

## Access the Portal

After running `make start`, access:

**URL**: [http://localhost:3000](http://localhost:3000)

**Default credentials**:
- **Email**: `admin@example.com`
- **Password**: `admin`

**API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Available Commands

```bash
# Start environment
make start

# Stop environment
make stop

# Restart environment
make restart

# View logs
make logs

# Check service status
make status

# Rebuild images
make build

# Run all tests
make test

# Run API tests only
make api-test

# Run Portal tests only
make portal-test

# Create new migration
make api-migration

# Apply migrations
make api-migrate
```

## Using Docker Compose Directly

If you prefer not to use Make:

```bash
cd docker

# Start all services
docker compose up -d

# Start specific services
docker compose up -d database api

# View logs
docker compose logs -f api

# Run tests
docker compose run --rm api-test
docker compose run --rm portal-test

# Stop all services
docker compose down
```

## Using kubectl with K3s

To interact with the local K3s cluster:

```bash
export KUBECONFIG=./volumes/kubeconfig/kubeconfig.yaml
kubectl get nodes
kubectl get pods -A
```

## Project Structure

```
tron/
├── api/                    # FastAPI backend
│   ├── app/               # Application code
│   ├── tests/             # API tests
│   ├── Dockerfile         # Development Dockerfile
│   └── Dockerfile.prod    # Production Dockerfile
├── portal/                 # React frontend
│   ├── src/               # Source code
│   ├── Dockerfile         # Development Dockerfile
│   └── Dockerfile.prod    # Production Dockerfile
├── docker/                 # Docker Compose configurations
│   ├── docker-compose.yaml      # Development
│   └── docker-compose.prod.yaml # Production
├── scripts/               # Automation scripts
└── volumes/               # Persistent volumes (kubeconfig, tokens)
```

## Development vs Production

### Development Environment

The development environment uses Dockerfiles optimized for local development:

- **API**: `api/Dockerfile` - Development server with hot reload
- **Portal**: `portal/Dockerfile` - Development server with Vite HMR

**Features:**
- Hot reload enabled
- Volume mounts for live code changes
- Development dependencies included
- No optimization (faster builds)

### Production Environment

Production builds use separate Dockerfiles with `.prod` suffix:

- **API**: `api/Dockerfile.prod` - Optimized multi-stage build
- **Portal**: `portal/Dockerfile.prod` - Production build with Nginx

**Features:**
- Multi-stage builds (smaller images)
- Production optimizations
- No development dependencies
- Health checks configured
- Non-root user execution

## Environment Variables

Main environment variables can be configured in `docker/docker-compose.yaml`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | Database host | `database` |
| `DB_USER` | Database user | `tron` |
| `DB_PASSWORD` | Database password | `tron` |
| `DB_PORT` | Database port | `5432` |
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | API secret key | (see compose file) |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

## Running Tests

### API Tests

```bash
# Via Make
make api-test

# Via Docker Compose
docker compose run --rm api-test

# Specific test file
docker compose run --rm api-test pytest tests/test_auth.py -v
```

### Portal Tests

```bash
# Via Make
make portal-test

# Via Docker Compose
docker compose run --rm portal-test
```

### Linting

```bash
# API (Python - ruff)
cd api
uv tool run ruff check app/
uv tool run ruff format app/ --check

# Portal (TypeScript - ESLint)
cd portal
npm run lint
npx tsc --noEmit
```

## Database Migrations

Using Alembic for database migrations:

```bash
# Create a new migration
make api-migration

# Or manually
docker compose run --rm api alembic revision --autogenerate -m "description"

# Apply migrations
make api-migrate

# Or manually
docker compose run --rm api alembic upgrade head
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
docker compose logs api

# Run migrations manually
docker compose run --rm api-migrate
```

### K3s cluster issues

```bash
# Check K3s logs
docker compose logs k3s-server

# Verify kubeconfig
cat ./volumes/kubeconfig/kubeconfig.yaml
```

### Reset everything

```bash
# Stop and remove all containers and volumes
docker compose down -v

# Start fresh
make start
```

## Creating Releases

When ready to create a new release:

```bash
# Create and push tags for API and Portal
git tag -a api/v0.4.0 -m "Release API v0.4.0"
git tag -a portal/v0.4.0 -m "Release Portal v0.4.0"
git push origin api/v0.4.0 portal/v0.4.0
```

This will:
- Build production images
- Push to GitHub Container Registry
- Create GitHub Releases
- **NOT affect your local development environment**
