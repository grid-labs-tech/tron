---
description: "Global coding standards for all source code in this repository (frontend and backend)."
alwaysApply: true
---

# Global Coding Standards (Frontend & Backend)

## 1. Scope & Goals

These standards apply to **all source code** in this repository, regardless of language or layer (frontend, backend, infrastructure-as-code, tests, etc.).

Goals:

- Make the codebase **consistent**, **readable** and **easy to maintain**.
- Reduce cognitive load when switching between projects or stacks.
- Ensure that **any engineer** can understand and safely change any part of the codebase.

Whenever there is a conflict between these rules and a language-specific formatter/linter configuration, prefer the **project formatters/linters** and adjust this document if needed.

---

## 2. Language & Naming

### 2.1. Language of code, comments and messages

- **English is mandatory** for:
  - Identifiers (variables, functions, classes, modules, files).
  - Comments (inline comments, block comments, docstrings).
  - Log messages.
  - Error messages and exception texts.
  - Test names and descriptions.
  - Configuration and code-level documentation.

- User-facing text (UI labels, emails, push notifications, etc.) may be in the product’s target language(s), but:
  - Keep translation keys and comments in **English**.
  - Avoid mixing languages in the same file unless it is clearly intentional (e.g. translation files).

### 2.2. Naming conventions

Unless otherwise required by language idioms:

- **Classes / Components / Types**: `PascalCase`
  - Example: `UserService`, `OrderRepository`, `UserProfileCard`.

- **Functions / Methods / Variables**: `camelCase`
  - Example: `getUserById`, `calculateTotal`, `userEmail`.

- **Constants**: `CONSTANT_CASE`
  - Example: `MAX_RETRY_ATTEMPTS`, `DEFAULT_PAGE_SIZE`.

- **Private/internal helpers** (if the language allows): prefix with `_` only when idiomatic (e.g. Python), otherwise rely on module visibility.

- **Boolean variables**:
  - Use names that read naturally as **questions** or states:
    - `isActive`, `hasPermission`, `shouldRetry`, `isValidPayload`.

- **Collections**:
  - Use plural nouns for arrays/lists and clear nouns for maps:
    - `users`, `activeSessions`, `ordersByUserId`.

- Avoid abbreviations that are not universally understood.
  - Prefer `totalAmount` over `ttlAmt`, `configuration` over `cfg`.

---

## 3. Formatting & Structure

### 3.1. Formatters & linters

- Always use the **official formatter** for each language when available:
  - JavaScript/TypeScript: `prettier` (possibly with `eslint`).
  - Python: `black` + `isort` (and `ruff`/`flake8` as linter).
  - Go: `gofmt` / `goimports`.
  - Other languages: use the community-standard formatter.

- Code **must be auto-formatted** before commit. Do not manually fight the formatter.

### 3.2. General rules

- Indentation: use **spaces** (no tabs), following the project’s configuration (typically 2 or 4 spaces).
- Line length: keep lines reasonably short (e.g. 100–120 chars max). Break long expressions into multiple lines.
- Remove unused imports, variables and functions.
- One top-level abstraction/concept per file where possible:
  - Backend: a file usually contains a single main class or a small set of related functions.
  - Frontend: a file usually contains a single React/Vue component or hook.

---

## 4. Comments & Documentation

### 4.1. When to comment

- Prefer **clear code** over comments.
- Comment when:
  - The **why** is not obvious from the code.
  - There is a known constraint, workaround or external dependency.
  - You are implementing a non-trivial algorithm or domain rule.

- Avoid comments that simply repeat what the code already says.

### 4.2. Style

- Write comments in **English** and in full sentences when explaining “why”.
- Use structured comments/docstrings for public APIs:
  - Backend: document public methods and endpoints.
  - Frontend: document components’ expected props and side-effects (when not obvious).

### 4.3. TODO / FIXME / NOTE

- Use tags to mark temporary or important attention points:
  - `// TODO: explain what needs to be done`
  - `// FIXME: describe the bug or tech debt`
  - `// NOTE: important context or decision rationale`

- When possible, link to an issue/ticket:
  - `// TODO: Replace legacy flow (see ISSUE-123)`.

---

## 5. Functions, Classes & Modules

- Follow the **Single Responsibility Principle** at a pragmatic level:
  - A function should do **one thing well**.
  - If a function is long or has many branches, consider splitting it.

- Prefer **small, composable functions** over large monolithic blocks.
- Keep the number of parameters small. When more than 3–4 parameters are needed:
  - Use an options object/DTO instead of positional parameters.

- Avoid deep nesting:
  - Prefer early returns to reduce indentation.
  - Refactor deeply nested conditionals into smaller helpers.

---

## 6. Error Handling & Validation

- Never silently swallow errors.
  - Log them (without leaking sensitive data).
  - Return a meaningful error to the caller when appropriate.

- Validate inputs at the **boundary of the system**:
  - Backend: validate API payloads, query params, headers.
  - Frontend: validate user inputs before calling the backend, but always assume the backend is the final source of truth.

- Use **typed/structured errors** where possible (error codes, enums, or well-defined error shapes) instead of plain strings.

- Do not rely on **exceptions for control flow** in normal logic.

---

## 7. Logging

- Use consistent log levels:
  - `DEBUG`: detailed information for troubleshooting.
  - `INFO`: high-level application flow and key events.
  - `WARN`: unexpected but recoverable situations.
  - `ERROR`: failures that require attention.
  - `FATAL`/`CRITICAL`: unrecoverable failures.

- Never log:
  - Passwords or secrets.
  - Full tokens (JWT, API keys). Log at most a short prefix/suffix.
  - Sensitive personal data unless explicitly required and compliant with policy.

- Log messages in English, concise and structured:
  - Include context (IDs, counts, relevant parameters).
  - Prefer structured logging (fields) over free-form text where supported.

---

## 8. Dependencies & Imports

- Prefer **standard library and core language features** over adding new dependencies.
- Before adding a dependency:
  - Check if an existing library already solves the problem.
  - Evaluate maintenance, size, and security.
- Remove unused or obsolete dependencies as part of regular refactors.
- Keep imports ordered and grouped:
  - Standard library.
  - Third-party libraries.
  - Internal modules.

---

## 9. Testing & Test Code Style

- Tests are first-class citizens and must follow the same standards:
  - Use **English** for test names and descriptions.
  - Test names should clearly describe the behavior under test:
    - `it("returns 401 when user is not authenticated")`
    - `def test_creates_order_when_cart_is_valid():`

- Prefer **arrange–act–assert** (or equivalent) structure:
  - Clearly separate setup, execution and verification.

- Do not over-mock:
  - Mock external systems and I/O.
  - Keep domain logic tests as close to real behavior as possible.

- For every bug fixed, add or update tests to reproduce and prevent regressions.

---

## 10. Frontend-Specific Notes

These are still part of the global standard but apply more to frontend code:

- Do not place complex business rules inside UI components.
  - Move them to hooks/services/state modules.
- Keep components focused:
  - Prefer small, composable components over “god components”.
- Avoid inline object/function definitions in JSX when they cause unnecessary re-renders; extract them when it improves readability and performance.
- Prefer declarative logic and framework idioms (React hooks, etc.) over imperative DOM manipulation.

---

## 11. Backend-Specific Notes

These are still part of the global standard but apply more to backend code:

- Keep domain logic independent from transport and persistence layers when possible (e.g., HTTP, database, queues).
- Do not leak persistence models directly to external APIs:
  - Use DTOs or view models to control exposed data.
- Ensure that all externally visible APIs have:
  - Clear contracts (types/schemas).
  - Proper validation and error handling.
  - Tests covering success and failure scenarios.

---

## 12. How to Apply These Standards

- When writing or reviewing code:
  - Enforce these rules during code review.
  - Prefer refactoring toward these standards even in small steps.
- When you find code that violates these rules:
  - If you are changing the file, improve it incrementally.
  - If the violation reflects a limitation or better pattern, update this document.

If you are unsure whether your change follows the standard, prefer **consistency with existing code** and discuss with the team before introducing a new pattern.
