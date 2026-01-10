---
description: "Frontend architecture, structure and implementation rules for web applications"
alwaysApply: true
---

# Frontend Architecture & Implementation Rules

## 1. Scope

These rules apply to **all frontend code** in the Grid Labs ecosystem, including:

- All Portals (web UI for the Platforms)
- Any admin / operator UIs that interact with Core APIs or related services
- Any future SPAs/MPAs that consume backend APIs

They are **frontend-specific** and complement the backend rules.
Whenever there is overlap, **backend rules define API behavior**, and **this rule defines how the frontend consumes and presents it**.

## 2. Technology assumptions

- **Language:** TypeScript (preferred) or modern JavaScript (ES2020+)
- **UI Framework:** React or similar component-based framework
- **Styling:** Bootstrap/CoreUI/Tailwind, aligned with existing choices
- **HTTP Interaction:** Centralized API layer, no scattered fetch calls

## 3. Project structure & layering

Use clear layers to avoid fragmentation and routing logic leakage.

Recommended structure:

src/
  app/ or pages/
  features/
    clusters/
    applications/
    instances/
    billing/
    settings/
  shared/
    components/
    hooks/
    api/
    utils/
    types/
  styles/

Rules:
- Pages/routes only coordinate routing, no domain logic
- Features group domain UI + hooks + api + types
- Shared contains cross-cutting components and utilities
- Features must not depend on internals of other features

## 4. API interaction & data flow

Frontend consumes backend APIs as source of truth.

Rules:
- Each feature has its own api/ module
- No raw URLs inside components
- Use hooks for fetching (React Query, custom hooks, etc)
- Standardize error handling
- Do not leak raw backend objects directly to UI

## 5. State management

Favor simplest viable approach.

Hierarchy:
1. Local state (UI only)
2. Feature-level hooks (data + logic)
3. Global state only when multiple distant parts depend on shared data

No multiple global state libraries.

## 6. UI, UX & design system

Rules:
- Consistent table, form, layout primitives
- Predictable placement of primary actions
- Clear empty states + loading states
- Reuse patterns to make de code feel cohesive

## 7. Forms, validation & errors

Rules:
- Prefer a unified validation library (Yup/Zod/etc)
- Backend validation messages reused where possible
- Disable submit during requests
- Avoid duplicate submissions

## 8. Type safety & backend alignment

Rules:
- Use TypeScript for new modules
- Create DTOs in types/
- Mirror backend contracts
- Avoid `any` unless justified

## 9. Testing

Test where value exists:

- Unit tests for complex components and hooks
- E2E for major flows if infra exists
- AI-generated tests allowed but must match stack + be runnable

## 10. Accessibility & Internationalization

Rules:
- Semantic HTML
- Keyboard-accessible components
- Aria attributes when needed
- Centralize copy for future i18n

## 11. Performance

Rules:
- Cache API responses when feasible
- Debounce/filter inputs that trigger requests
- Virtualize large tables when needed
- Avoid unnecessary re-renders via memoization strategies

## 12. AI usage in the frontend

Rules:
- Respect existing project patterns
- Do not introduce new frameworks/libs without explicit request
- Generate changes incrementally
- Summarize intent before generating large code modifications


## 13. Component Size & Responsibility

Rules:
- Components must be small and focused on a single responsibility.
- Avoid “God Components” that handle data fetching + business logic + rendering + layout at the same time.
- Prefer composing multiple small components rather than one large one.
- Component files should generally be short and readable. When a component grows beyond ~150–200 LOC (not strict), evaluate if splitting is possible.
- Presentation (UI) and container (logic) concerns should be separated when beneficial.
- Shared primitives (buttons, inputs, cards, modals) must not embed feature-specific logic.
- Hooks should hold the logic, components the layout.

End of rule specification.
