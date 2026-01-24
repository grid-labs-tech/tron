# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the Tron project following CI/CD best practices.

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CI/CD Pipeline                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Push to main/develop          Pull Request              Push Tag            │
│         │                           │                        │               │
│         ▼                           ▼                        ▼               │
│  ┌─────────────┐            ┌─────────────┐          ┌─────────────┐        │
│  │   Tests     │            │   Tests     │          │   Tests     │        │
│  │  (changed   │            │  (changed   │          │ (component) │        │
│  │ components) │            │ components) │          └──────┬──────┘        │
│  └──────┬──────┘            └──────┬──────┘                 │               │
│         │                          │                        │ ✓             │
│         ▼                          │                        ▼               │
│  ┌─────────────┐                   │               ┌─────────────┐          │
│  │   Build &   │                   │               │  Security   │          │
│  │    Push     │                   │               │    Scan     │          │
│  │   Images    │                   │               └──────┬──────┘          │
│  └─────────────┘                   │                      │                 │
│                                    │                      ▼                 │
│                                    │               ┌─────────────┐          │
│                                    │               │   Build &   │          │
│                                    │               │    Push     │          │
│                                    │               │   Images    │          │
│                                    │               └──────┬──────┘          │
│                                    │                      │                 │
│                                    │                      ▼                 │
│                                    │               ┌─────────────┐          │
│                                    │               │   GitHub    │          │
│                                    │               │   Release   │          │
│                                    │               └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Best Practices Implemented

### ✅ Quality Gates
- **Tests run before releases** - Releases are blocked if tests fail
- **Reusable workflows** - Tests workflow is called by release workflows
- **Path-based filtering** - Only test/build changed components

### ✅ Security
- **Trivy vulnerability scanning** - Scans code and container images
- **SBOM generation** - Software Bill of Materials for supply chain security
- **Provenance attestation** - Cryptographic proof of build origin
- **SARIF reports** - Security findings uploaded to GitHub Security tab

### ✅ Testing
- **Unit tests** - Fast, isolated tests
- **Integration tests** - Tests with real database
- **Frontend tests** - React component and utility tests
- **Linting** - Code style enforcement (ruff for Python, ESLint for TypeScript)
- **Type checking** - TypeScript strict mode

### ✅ Versioning
- **Semantic versioning** - MAJOR.MINOR.PATCH format
- **Independent releases** - API and Portal can be versioned separately
- **Prerelease support** - Beta, RC, and alpha versions supported
- **Multiple tags** - `1.2.3`, `1.2`, and `latest` tags generated

### ✅ Caching
- **pip cache** - Python dependencies cached
- **npm cache** - Node.js dependencies cached
- **Docker layer cache** - Build layers cached via GitHub Actions cache
- **Scoped caches** - Separate cache scopes for API and Portal

## Workflows

### Tests (`tests.yml`)

Runs all quality checks for the project. Can be triggered directly or called by other workflows.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests targeting `main`
- Called by release workflows (via `workflow_call`)

**Jobs:**
| Job | Description | When |
|-----|-------------|------|
| `unit-tests` | Python unit tests with coverage | API changes |
| `integration-tests` | Python integration tests with PostgreSQL | API changes |
| `frontend-tests` | TypeScript tests, linting, type-check | Portal changes |
| `security-scan` | Trivy filesystem vulnerability scan | Any changes |
| `test` | Aggregator - ensures all tests pass | Always |

### Build and Push (`build-and-push.yml`)

Builds development images when changes are pushed to branches.

**Triggers:**
- Push to `main` or `develop` branches (with changes in `api/` or `portal/`)
- Pull requests targeting `main`

**Features:**
- Path-based filtering - only builds changed components
- Branch-specific tags (e.g., `main`, `develop`)
- SHA-based tags for traceability

### Release API (`release-api.yml`)

Releases the API component independently.

**Triggers:**
- Push tags matching `api/v*` (e.g., `api/v1.0.0`)

**Pipeline:**
1. ✅ Run API tests (unit + integration)
2. ✅ Security scan
3. 📦 Build and push Docker image
4. 🔍 Scan container image for vulnerabilities
5. 📝 Generate changelog
6. 🚀 Create GitHub Release

### Release Portal (`release-portal.yml`)

Releases the Portal component independently.

**Triggers:**
- Push tags matching `portal/v*` (e.g., `portal/v1.0.0`)

**Pipeline:**
1. ✅ Run frontend tests
2. ✅ Security scan
3. 📦 Build and push Docker image
4. 🔍 Scan container image for vulnerabilities
5. 📝 Generate changelog
6. 🚀 Create GitHub Release

### Release Combined (`release.yml`)

Releases both API and Portal together with the same version.

**Triggers:**
- Push tags matching `v*` (e.g., `v1.0.0`)

**Pipeline:**
1. ✅ Run ALL tests (API + Portal)
2. ✅ Security scan
3. 📦 Build and push both Docker images
4. 🔍 Scan both container images
5. 📝 Generate changelog
6. 🚀 Create GitHub Release

## Tag Format

| Type | Format | Example | Use Case |
|------|--------|---------|----------|
| API Release | `api/v<semver>` | `api/v1.2.3` | Independent API release |
| Portal Release | `portal/v<semver>` | `portal/v2.0.0` | Independent Portal release |
| Combined Release | `v<semver>` | `v1.0.0` | Synchronized release |
| Prerelease | `*-<prerelease>` | `api/v1.0.0-beta.1` | Testing before stable |

## Docker Images

Images are published to GitHub Container Registry (ghcr.io):

| Component | Image | Available Tags |
|-----------|-------|----------------|
| API | `ghcr.io/<owner>/tron-api` | `1.2.3`, `1.2`, `latest`, `main`, `develop` |
| Portal | `ghcr.io/<owner>/tron-portal` | `1.2.3`, `1.2`, `latest`, `main`, `develop` |

## Required Secrets

| Secret | Required | Description |
|--------|----------|-------------|
| `GITHUB_TOKEN` | Auto | Automatically provided by GitHub |
| `CODECOV_TOKEN` | Optional | For uploading coverage reports to Codecov |

## Branch Protection Setup

To enforce quality gates on PRs:

1. Go to **Settings** → **Branches**
2. Add/edit rule for `main` branch
3. Enable:
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
4. Add required status checks:
   - `All Tests`
   - `Backend Unit Tests`
   - `Backend Integration Tests`
   - `Frontend Tests`
   - `Security Scan`

## Usage Examples

### Release a new API version

```bash
# Ensure you're on main with latest changes
git checkout main
git pull origin main

# Create and push the API tag
git tag api/v1.2.0
git push origin api/v1.2.0

# The pipeline will:
# 1. Run API tests
# 2. Build and push ghcr.io/<owner>/tron-api:1.2.0
# 3. Create GitHub Release "API v1.2.0"
```

### Release a new Portal version

```bash
git checkout main
git pull origin main

git tag portal/v2.1.0
git push origin portal/v2.1.0

# The pipeline will:
# 1. Run frontend tests
# 2. Build and push ghcr.io/<owner>/tron-portal:2.1.0
# 3. Create GitHub Release "Portal v2.1.0"
```

### Create a prerelease

```bash
# API beta
git tag api/v1.3.0-beta.1
git push origin api/v1.3.0-beta.1

# Portal release candidate
git tag portal/v2.2.0-rc.1
git push origin portal/v2.2.0-rc.1

# Prereleases:
# - Won't update 'latest' tag
# - Marked as prerelease on GitHub
```

### Synchronized release

```bash
# Only use when both components need same version
git tag v2.0.0
git push origin v2.0.0

# Creates:
# - ghcr.io/<owner>/tron-api:2.0.0
# - ghcr.io/<owner>/tron-portal:2.0.0
# - Single GitHub Release with both images
```

## Troubleshooting

### Tests failing before release

If tests fail, the release won't proceed. Check the workflow run logs to identify failing tests.

### Security vulnerabilities found

Trivy scans are uploaded to GitHub Security tab. Review and fix CRITICAL/HIGH vulnerabilities before releasing.

### Cache issues

Clear GitHub Actions cache if builds behave unexpectedly:
1. Go to **Actions** → **Caches**
2. Delete relevant caches
