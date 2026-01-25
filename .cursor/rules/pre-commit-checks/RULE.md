---
description: "Mandatory checks before committing or pushing code to avoid breaking CI."
alwaysApply: true
---

# Pre-Commit and Pre-Push Checks

## Overview

Before committing or pushing code, **always run the appropriate checks** to avoid breaking CI and blocking other contributors.

---

## Backend (Python/API)

### Before committing changes to `api/`:

```bash
cd api

# 1. Run linter
uv tool run ruff check app/ --fix

# 2. Run formatter
uv tool run ruff format app/

# 3. Run unit tests
uv run pytest tests/unit -v
```

### Before creating a PR:

```bash
# Run full test suite (requires PostgreSQL)
uv run pytest tests/ -v
```

---

## Frontend (TypeScript/Portal)

### Before committing changes to `portal/`:

```bash
cd portal

# 1. Run linter
npm run lint

# 2. Run type check
npx tsc --noEmit

# 3. Run tests
npm run test
```

### Before creating a PR:

```bash
# Run tests with coverage
npm run test:coverage
```

---

## Quick Reference

| Component | Lint | Format | Type Check | Test |
|-----------|------|--------|------------|------|
| API | `uv tool run ruff check app/` | `uv tool run ruff format app/` | N/A | `uv run pytest tests/unit` |
| Portal | `npm run lint` | (included in lint) | `npx tsc --noEmit` | `npm run test` |

---

## Common Errors and Fixes

### Python (ruff)

| Error | Description | Fix |
|-------|-------------|-----|
| F401 | Unused import | Remove the import |
| E402 | Import not at top of file | Move import to top |
| E712 | `== True/False` comparison | Use `.is_(True)` for SQLAlchemy |
| E731 | Lambda assignment | Convert to `def` function |

### TypeScript

| Error | Description | Fix |
|-------|-------------|-----|
| TS6133 | Unused variable | Remove or prefix with `_` |
| TS2345 | Type mismatch | Fix the type annotation |
| TS2305 | Missing export | Check import path |

---

## CI Will Fail If

1. **ruff check** reports errors (no `--ignore` flags allowed)
2. **ruff format --check** detects unformatted files
3. **tsc --noEmit** reports TypeScript errors
4. **pytest** or **npm test** has failures
5. **Trivy** detects critical/high vulnerabilities

---

## Recommended Workflow

1. **Before each commit:**
   - Run lint + format for the component you changed
   - Fix any errors before committing

2. **Before pushing:**
   - Run unit tests for the component you changed
   - Run type check (frontend only)

3. **Before creating PR:**
   - Run full test suite
   - Ensure CI passes on your branch

---

## Tips

- Use `--fix` flag with ruff to auto-fix most lint errors
- If you see many formatting changes, the file was not formatted before
- Run checks from the correct directory (`api/` or `portal/`)
- When in doubt, run all checks — it's faster than waiting for CI to fail
