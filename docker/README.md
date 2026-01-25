# Docker Configuration

This directory contains Docker Compose configurations for running Tron in different environments.

## Files

| File | Description |
|------|-------------|
| `docker-compose.yaml` | Development environment with local builds and hot-reload |
| `docker-compose.prod.yaml` | Production environment with pre-built images from GHCR |
| `.env.example` | Example environment variables for production |
| `nginx/nginx.conf` | Nginx configuration for HTTP |
| `nginx/nginx-ssl.conf` | Nginx configuration for HTTPS with Let's Encrypt |

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

The production environment uses pre-built images from GitHub Container Registry with Nginx as a reverse proxy.

### Architecture

```
                    ┌─────────────┐
                    │   Internet  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Nginx    │ :80 (HTTP) / :443 (HTTPS)
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐  ┌──▼──┐  ┌─────▼─────┐
       │   Portal    │  │ API │  │  Certbot  │
       │   (React)   │  │     │  │ (optional)│
       └─────────────┘  └──┬──┘  └───────────┘
                           │
                    ┌──────▼──────┐
                    │  PostgreSQL │
                    └─────────────┘
```

### Quick Start (HTTP)

```bash
cd docker

# 1. Create environment file
cp .env.example .env

# 2. Edit .env with your production values
#    - Set a strong DB_PASSWORD
#    - Set a secure SECRET_KEY (minimum 32 characters)

# 3. Start all services
docker compose -f docker-compose.prod.yaml --profile full up -d

# 4. Check status
docker compose -f docker-compose.prod.yaml ps

# 5. Access the application
#    - Portal: http://localhost
#    - API: http://localhost/api/
```

### HTTPS with Let's Encrypt

For production deployments with HTTPS:

```bash
cd docker

# 1. Create environment file
cp .env.example .env

# 2. Edit .env with your domain and email
#    - DOMAIN=your-domain.com
#    - CERTBOT_EMAIL=admin@your-domain.com
#    - CORS_ORIGINS=https://your-domain.com

# 3. Start services with SSL profile
docker compose -f docker-compose.prod.yaml --profile full --profile ssl up -d

# 4. First time setup: wait for certbot to obtain certificate
docker compose -f docker-compose.prod.yaml logs certbot

# 5. Restart nginx to load the certificate
docker compose -f docker-compose.prod.yaml restart nginx-ssl

# 6. Access the application
#    - Portal: https://your-domain.com
#    - API: https://your-domain.com/api/
```

**Note:** When using `--profile ssl`, use `nginx-ssl` instead of `nginx` for commands.

### Production Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| `db` | PostgreSQL | External app servers |
| `app` | API, Portal, Nginx | External database |
| `full` | All (db + app) | Complete deployment |
| `ssl` | Nginx-SSL, Certbot | HTTPS with Let's Encrypt |

```bash
# HTTP deployment (full stack)
docker compose -f docker-compose.prod.yaml --profile full up -d

# HTTPS deployment (full stack + SSL)
docker compose -f docker-compose.prod.yaml --profile full --profile ssl up -d

# Database only
docker compose -f docker-compose.prod.yaml --profile db up -d

# Application only (external DB)
docker compose -f docker-compose.prod.yaml --profile app up -d
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_PASSWORD` | Yes | - | Database password |
| `SECRET_KEY` | Yes | - | API secret key (min 32 chars) |
| `DB_USER` | No | `tron` | Database username |
| `API_IMAGE_TAG` | No | `latest` | API Docker image tag |
| `PORTAL_IMAGE_TAG` | No | `latest` | Portal Docker image tag |
| `HTTP_PORT` | No | `80` | Host port for HTTP |
| `HTTPS_PORT` | No | `443` | Host port for HTTPS |
| `CORS_ORIGINS` | No | `http://localhost` | Allowed CORS origins |
| `API_URL` | No | `/api` | API URL for Portal |
| `DOMAIN` | SSL only | - | Domain for SSL certificate |
| `CERTBOT_EMAIL` | SSL only | - | Email for Let's Encrypt |

### Using Specific Versions

For production stability, always use specific image versions:

```bash
# In .env file
API_IMAGE_TAG=0.3.0
PORTAL_IMAGE_TAG=0.3.0
```

Or via command line:

```bash
API_IMAGE_TAG=0.3.0 PORTAL_IMAGE_TAG=0.3.0 \
  docker compose -f docker-compose.prod.yaml --profile full up -d
```

### Available Images

Images are published to GitHub Container Registry:

- `ghcr.io/grid-labs-tech/tron-api:latest`
- `ghcr.io/grid-labs-tech/tron-api:0.3.0`
- `ghcr.io/grid-labs-tech/tron-portal:latest`
- `ghcr.io/grid-labs-tech/tron-portal:0.3.0`

### SSL Certificate Renewal

The `certbot-renew` service automatically renews certificates every 12 hours. To manually renew:

```bash
docker compose -f docker-compose.prod.yaml run --rm certbot renew
docker compose -f docker-compose.prod.yaml restart nginx-ssl
```

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
docker compose -f docker-compose.prod.yaml logs database

# Verify database is healthy
docker compose -f docker-compose.prod.yaml exec database pg_isready -U tron -d api
```

### API not starting

```bash
# Check API logs
docker compose -f docker-compose.prod.yaml logs api

# Run migrations manually
docker compose -f docker-compose.prod.yaml --profile db up -d
docker compose -f docker-compose.prod.yaml run --rm api-migrate
```

### Nginx issues

```bash
# Check nginx logs
docker compose -f docker-compose.prod.yaml logs nginx

# Test nginx configuration
docker compose -f docker-compose.prod.yaml exec nginx nginx -t
```

### SSL Certificate issues

```bash
# Check certbot logs
docker compose -f docker-compose.prod.yaml logs certbot

# Verify certificate exists
docker compose -f docker-compose.prod.yaml exec nginx-ssl ls -la /etc/letsencrypt/live/

# Force certificate renewal
docker compose -f docker-compose.prod.yaml run --rm certbot certonly --force-renewal \
  --webroot -w /var/www/certbot -d your-domain.com
```

### PostgreSQL Performance

The database is configured with optimized settings for production:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `max_connections` | 100 | Maximum concurrent connections |
| `shared_buffers` | 128MB | Memory for caching data |
| `work_mem` | 4MB | Memory per query operation |
| `maintenance_work_mem` | 64MB | Memory for maintenance operations |
| `effective_cache_size` | 512MB | Planner's assumption about cache |

For high-traffic deployments, consider increasing these values based on available memory.

### Reset everything

```bash
# Development
docker compose down -v

# Production (preserves SSL certificates)
docker compose -f docker-compose.prod.yaml down -v --remove-orphans

# Production (including SSL certificates)
docker compose -f docker-compose.prod.yaml down -v --remove-orphans
docker volume rm docker_certbot_certs docker_certbot_webroot
```
