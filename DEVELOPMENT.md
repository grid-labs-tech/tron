# Development Environment

This document explains the development setup and how it differs from production builds.

## Development vs Production

### Development (Current Setup)

The development environment uses **separate Dockerfiles** that are optimized for local development:

- **API**: `api/Dockerfile` - Development server with hot reload
- **Portal**: `portal/Dockerfile` - Development server with Vite HMR

**Used by:**
- `docker-compose.yaml` - Uses `Dockerfile` (not `Dockerfile.prod`)
- `make start` - Builds and runs development containers
- All development workflows remain unchanged

**Features:**
- Hot reload enabled
- Volume mounts for live code changes
- Development dependencies included
- No optimization (faster builds)

### Production

Production builds use **separate Dockerfiles** with `.prod` suffix:

- **API**: `api/Dockerfile.prod` - Optimized multi-stage build
- **Portal**: `portal/Dockerfile.prod` - Production build with Nginx

**Used by:**
- GitHub Actions workflows only
- CI/CD pipelines
- Helm chart deployments

**Features:**
- Multi-stage builds (smaller images)
- Production optimizations
- No development dependencies
- Health checks configured
- Non-root user execution

## Guarantee

✅ **Your current development environment is NOT affected:**

- `docker-compose.yaml` explicitly uses `Dockerfile` (not `Dockerfile.prod`)
- `make start` continues to work exactly as before
- All development workflows remain unchanged
- Production Dockerfiles are only used by CI/CD

## File Structure

```
api/
├── Dockerfile          # Development (used by docker-compose)
└── Dockerfile.prod     # Production (used by CI/CD)

portal/
├── Dockerfile          # Development (used by docker-compose)
└── Dockerfile.prod     # Production (used by CI/CD)
```

## Development Commands

All existing commands work as before:

```bash
# Start development environment
make start

# Stop environment
make stop

# View logs
make logs

# Rebuild images
make build

# Run tests
make api-test
```

## Versioning

- **Development**: No version tags needed, uses `latest` or branch names
- **Production**: Uses semantic versioning starting with `v0.1.0`

## Creating Your First Release

When ready to create the first release:

```bash
# Create and push tag
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

This will:
- Build production images
- Push to GitHub Container Registry
- Create a GitHub Release
- **NOT affect your local development environment**
