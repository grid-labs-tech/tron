# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the Tron project.

## Workflows

### Tests (`tests.yml`)

Runs unit tests and generates coverage reports for the API.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests targeting `main` branch

**Features:**
- Runs pytest with coverage reporting
- Uploads coverage to Codecov
- Stores HTML coverage reports as artifacts
- **Blocks PR merge if tests fail** (requires branch protection setup)

## Branch Protection Setup

To ensure PRs cannot be merged when tests fail, configure branch protection rules:

1. Go to **Settings** → **Branches** in your GitHub repository
2. Click **Add rule** or edit the rule for `main` branch
3. Enable **Require status checks to pass before merging**
4. Select **Tests** from the list of status checks
5. Optionally enable **Require branches to be up to date before merging**

This ensures that:
- PRs targeting `main` must have all tests passing
- The workflow status check must be successful before merge
- PRs cannot be merged if tests fail

## Status Checks

The `Tests` workflow creates a status check that must pass before PRs can be merged when branch protection is enabled.
