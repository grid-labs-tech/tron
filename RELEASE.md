# Release Process

This document describes the release process for Tron, including building Docker images, creating releases, and updating the Helm chart.

## Overview

The release process is automated using GitHub Actions workflows:

1. **Build and Push** - Automatically builds and pushes Docker images on every push
2. **Release** - Creates GitHub releases when tags are pushed
3. **Helm Chart Update** - Updates the Helm chart repository with new versions

## Docker Images

### Production Images

- **API**: `ghcr.io/grid-labs-tech/tron-api`
- **Portal**: `ghcr.io/grid-labs-tech/tron-portal`

### Image Tags

Images are tagged with:
- `latest` - Latest build from main branch
- `v1.0.0` - Semantic version tags
- `main-<sha>` - Branch builds with commit SHA
- `pr-<number>` - Pull request builds

## Creating a Release

### Step 1: Update Version

Update the version in relevant files if needed:
- `api/app/main.py` - FastAPI app version
- `portal/package.json` - Package version

### Step 2: Create and Push Tag

```bash
# Create an annotated tag (starting with v0.1.0)
git tag -a v0.1.0 -m "Release version 0.1.0"

# Push the tag
git push origin v0.1.0
```

### Step 3: Automatic Release

When you push a tag matching `v*.*.*` (e.g., v0.1.0, v0.2.0, v1.0.0):
1. The `release.yml` workflow triggers
2. Docker images are built and pushed to GHCR
3. A GitHub Release is created
4. Release notes are generated

### Step 4: Update Helm Chart (Optional)

The Helm chart can be updated automatically or manually:

**Automatic:**
- Configure `update-helm-chart.yml` to trigger on releases
- Ensure `GH_PAT` secret is configured

**Manual:**
1. Go to Actions → Update Helm Chart
2. Click "Run workflow"
3. Enter the version number
4. The workflow updates the charts repository

## Workflow Details

### build-and-push.yml

**Triggers:**
- Push to `main` branch
- Push of tags matching `v*`
- Pull requests to `main`

**What it does:**
- Builds multi-arch Docker images (amd64, arm64)
- Pushes to GitHub Container Registry
- Uses build cache for faster builds
- Tags images appropriately

### release.yml

**Triggers:**
- Push of tags matching `v*.*.*`

**What it does:**
- Builds production Docker images
- Pushes images with version and `latest` tags
- Creates GitHub Release with release notes
- Includes installation instructions in release notes

### update-helm-chart.yml

**Triggers:**
- Manual workflow dispatch
- Published releases (if configured)

**What it does:**
- Checks out the charts repository
- Updates Chart.yaml version
- Updates values.yaml with new image tags
- Packages the Helm chart
- Commits and pushes changes

## Required Secrets

Configure these secrets in GitHub repository settings:

- `GITHUB_TOKEN` - Automatically provided by GitHub Actions
- `GH_PAT` - Personal Access Token with write access to `grid-labs-tech/charts` repository

## Dockerfiles

### Production Dockerfiles

- `api/Dockerfile.prod` - Multi-stage build for API
- `portal/Dockerfile.prod` - Multi-stage build for Portal (React + Nginx)

### Features

- Multi-stage builds for smaller images
- Non-root user execution
- Health checks configured
- Optimized layer caching
- Multi-arch support (amd64, arm64)

## Testing Locally

### Build Production Images

```bash
# Build API image
docker build -f api/Dockerfile.prod -t tron-api:local ./api

# Build Portal image
docker build -f portal/Dockerfile.prod -t tron-portal:local ./portal
```

### Run Images

```bash
# Run API
docker run -p 8000:8000 \
  -e DB_HOST=host.docker.internal \
  -e DB_USER=tron \
  -e DB_PASSWORD=tron \
  -e DB_NAME=api \
  tron-api:local

# Run Portal
docker run -p 3000:80 tron-portal:local
```

## Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR** - Breaking changes (starts at 0 for initial development)
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes (backward compatible)

**Initial version:** `v0.1.0`

Examples:
- `v0.1.0` - Initial release
- `v0.1.1` - Patch release
- `v0.2.0` - Minor release
- `v1.0.0` - First stable release

## Troubleshooting

### Images not building

- Check GitHub Actions logs
- Verify Dockerfile syntax
- Ensure all dependencies are in requirements.txt/package.json

### Release not created

- Verify tag format matches `v*.*.*`
- Check workflow permissions
- Review GitHub Actions logs

### Helm chart not updating

- Verify `GH_PAT` secret is configured
- Check charts repository permissions
- Review workflow logs for errors
