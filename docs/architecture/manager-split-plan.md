# Manager Module Split Plan

This document plans an early split of `scripts/ollama_cluster_manager.py` into
explicit responsibilities without changing CLI behavior, MCP behavior, or test
assertions.

## Goal

Reduce human review cost and prepare for future provider adapters by separating
routing policy from provider clients and delivery glue. Runtime provider
fallback is intentionally out of scope.

## Non-Goals

- Changing external CLI arguments or MCP tool contracts.
- Introducing a package manager or third-party dependency for the core router.
- Full Clean Architecture directory scaffolding before the split is needed.

## Current State

- One Python module (`scripts/ollama_cluster_manager.py`, ~588 lines) contains:
  - config loading and validation helpers
  - profile and model routing policy
  - provider-specific HTTP/SDK calls
  - output-path safety and file writing
  - CLI argument parsing and command dispatch
- Tests live in `tests/test_ollama_cluster_router_skill.py` and exercise the
  manager through the current import surface.

## Target Layout (incremental)

The first slices now create the router and adapter boundaries below. The
remaining orchestration move is tracked by LISS-0022:

```text
scripts/
├── ollama_cluster_manager.py      # thin CLI entry; imports orchestration API
├── router/
│   ├── __init__.py
│   ├── models.py                  # task package / result / config datatypes
│   ├── routing.py                 # profile, complexity, priority policy
│   ├── safety.py                  # allowed-root validation, fence stripping
│   └── manager.py                 # OllamaClusterManager orchestration
└── adapters/
    ├── __init__.py
    ├── ollama_http.py
    ├── openai_responses.py
    ├── anthropic_messages.py
    └── codex_sdk.py
```

Delivery adapters (`scripts/mcp_server.py`, install/setup scripts) keep calling the
same public manager API.

## Split Order

1. **Types and pure helpers** – move dataclasses, small validators, and
   fence-stripping helpers to `router/models.py` and `router/safety.py`.
2. **Routing policy** – move profile and complexity resolution to
   `router/routing.py`; do not add fallback handling.
3. **Provider clients** – move HTTP/SDK code to `adapters/*` with no business
   policy beyond transport.
4. **Orchestration** – keep `OllamaClusterManager` in `router/manager.py`.
5. **CLI shell** – leave argparse and `main()` in `ollama_cluster_manager.py`.

Each step is a Phase 3 Refactor slice: behavior and tests must remain green
after every step.

## Dependency Rules

- `router/routing.py` must not import adapter modules.
- `adapters/*` must not choose profiles or fallback chains.
- `router/manager.py` coordinates routing decisions and adapter calls through
  narrow functions or port-like interfaces.
- CLI and MCP delivery remain thin.

## Testing Strategy

- Keep existing tests importing the same public entry points during the split.
- Add no new external-network tests.
- Run after every slice:
  - `python3 -m unittest discover -s tests`
  - `python3 -m py_compile scripts/ollama_cluster_manager.py scripts/mcp_server.py`

## Risks

- Large single PR increases review cost; prefer 3–5 small refactor PRs.
- Circular imports if routing and manager both import adapters too early.
- Renaming the historical `OllamaClusterManager` symbol may break skill docs;
  keep the public class name unless an ADR says otherwise.

## Recommended Issues

- LISS-0017: types and safety extraction
- LISS-0020: routing policy extraction
- LISS-0021: provider adapter extraction
- LISS-0022: CLI shell thinning and docs update

The fallback-routing proposal (LISS-0016/LISS-0018/LISS-0019) is withdrawn.
Provider failures remain on the selected provider and are handled only by its
bounded retry policy.
