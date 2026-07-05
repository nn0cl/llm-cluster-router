# Project Structure

This document defines the target repository shape for implementation. Create
directories only when a Phase 1 or Phase 2 task needs them.

## Target Layout

Replace this with your project's real layout once the stack is chosen. Keep
the domain/application/ports/adapters split regardless of language or
framework:

```text
.
├── docs/
├── <frontend-dir>/
│   └── src/
│       ├── app/
│       ├── features/
│       ├── entities/
│       └── shared/
└── <backend-dir>/
    └── src/
        ├── delivery/            # HTTP/RPC handlers, CLI entry points, UI glue
        ├── core/
        │   ├── domain/
        │   ├── application/
        │   └── ports/
        └── adapters/
            ├── persistence/
            ├── settings/
            └── <external-service>/
```

## Ownership

`<frontend-dir>/` owns UI rendering and presentation state.

`<backend-dir>/src/core/domain/` owns pure domain types and domain behavior.

`<backend-dir>/src/core/application/` owns use cases and application
orchestration.

`<backend-dir>/src/core/ports/` owns interfaces for external resources.

`<backend-dir>/src/adapters/` owns concrete implementations of ports.

`<backend-dir>/src/delivery/` owns request/command handlers and DTO
conversion.

## Forbidden Placement

Do not put business rules in:

- UI component files.
- delivery/request handlers.
- adapters.
- persistence structs.
- provider SDK clients.

Do not put framework, file-system, network, or database imports in:

- `core/domain/`.
- `core/application/`, except through core-owned ports.

## Creation Rule

Create the smallest directory and module set needed by the current AT-TDD phase.
Do not scaffold unused adapters, providers, or UI features.

Smallest does not mean densest. Split files and modules when it reduces human
review cost or separates architectural responsibilities. Do not split only to
create speculative layers.
