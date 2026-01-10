# Contributing to Tron

Thank you for your interest in contributing to **Tron**!
We welcome contributions from the community and are committed to building a reliable, developer-friendly Internal Developer Platform.

This document explains how to get started, how to propose changes, and how to collaborate effectively with maintainers.

---

## 🚀 Development Environment Setup

### Prerequisites

- Docker
- Docker Compose
- Git

### Starting the Local Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/grid-labs-tech/tron.git
   cd tron
   ```

2. **Start the complete environment**:
   ```bash
   make start
   ```

   This command will:
   - Start all services (API, Portal, PostgreSQL, K3s)
   - Run database migrations
   - Load initial templates
   - Create default administrator user
   - Configure local cluster

3. **Access the portal**:
   - URL: http://localhost:3000
   - Email: `admin@example.com`
   - Password: `admin`

### Development Commands

```bash
# Start environment
make start

# Stop environment
make stop

# Restart environment
make restart

# View logs
make logs

# Check status
make status

# Rebuild images
make build

# Create new migration
make api-migration

# Apply migrations
make api-migrate

# Run tests
make api-test
```

### Project Structure

```
tron/
├── api/              # FastAPI backend
│   ├── app/          # Main application
│   ├── alembic/      # Database migrations
│   └── tests/        # Tests
├── portal/           # React frontend
│   └── src/          # Source code
├── scripts/          # Automation scripts
├── docker/           # Docker Compose configurations
└── volumes/          # Persistent volumes
```

### API Documentation

During development, interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧩 Types of Contributions

You can contribute in many ways, including:

- Reporting bugs
- Proposing new features
- Improving documentation
- Fixing issues
- Enhancing performance
- Adding new integrations or templates
- Sharing real-world usage feedback

All contributions are valuable — even small ones.

---

## 🐞 Reporting Issues

Before opening a new issue:

1. Check existing issues to avoid duplicates.
2. Include as much detail as possible:
   - Expected behavior
   - Actual behavior
   - Steps to reproduce
   - Environment details
   - Logs and/or screenshots (optional)

Issues that are clear and reproducible are easier to fix.

---

## 💡 Proposing Enhancements

If you want to propose a feature:

- Describe the **problem** (not only the solution)
- Explain **why** it is useful for users
- Provide **examples or use-cases**
- Reference any related issues

Features should align with Tron’s goals:

> Simplify Kubernetes
> Improve Developer Experience
> Provide consistency & automation

---

## 🔀 Pull Requests

Before submitting a Pull Request:

1. Open an issue or start a discussion (recommended for non-trivial work)
2. Ensure your branch is up-to-date with `main`
3. Add tests or update documentation if behavior changes

PR guidelines:

- Keep changes focused and incremental
- Avoid mixing refactoring and feature changes
- Write clear commit messages
- Link related issues (e.g., `Closes #123`)

Maintainers may request adjustments for clarity, scope, or quality.

---

## 📦 Project Structure

The project is evolving. Main components include:

- **Core API** (workloads, webapps, workers, cron, exposure)
- **Portal** (UI for developers & platform teams)
- **Runtime Templates** (Kubernetes resource generation)
- **Cluster Integrations**
- **Build & Deploy logic**
- **Documentation**

If uncertain where your contribution fits, open an issue to discuss.

---

## 🎨 Code Style

Tron aims to maintain:

- Readable code
- Consistent naming
- Clear abstractions
- Minimal surprises
- Good separation of concerns

Refactoring is welcome when it improves clarity and maintainability.

---

## 🧪 Testing

Tests are encouraged for:

- Business logic
- Resource/template generation
- Cluster integrations (mocked)
- Edge cases

End-to-end tests are welcome but optional at this stage.

---

## 📝 Documentation

Documentation improvements are always welcome.
Good docs reduce support burden and improve adoption.

---

## 🗺️ Roadmap Alignment

Large features should align with the project roadmap.
If unsure, discuss first to avoid duplicated or abandoned work.

---

## 🤝 Communication & Respect

We value respectful and constructive collaboration.

Arguments should remain technical and professional.

---

## 🔐 Security & Vulnerabilities

Do **not** report security issues publicly.
Please contact maintainers directly or use the security disclosure process (to be documented).

---

## 📜 License & CLA

By contributing, you agree that:

- Your contributions will be licensed under the project's license (Apache-2.0 unless otherwise noted)
- A Contributor License Agreement (CLA) may be introduced later to support commercial governance

---

## 🚀 Thank You

Thank you for helping improve Tron!
Your contributions make the project better for everyone.

---

## 👥 Contributors

We thank everyone who contributes to the Tron project! 🎉

<a href="https://github.com/grid-labs-tech/tron/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=grid-labs-tech/tron" alt="Contributors" />
</a>

Made with [contrib.rocks](https://contrib.rocks).
