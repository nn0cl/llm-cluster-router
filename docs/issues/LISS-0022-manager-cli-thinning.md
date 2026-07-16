# LISS-0022: Manager orchestration and CLI thinning

## Metadata

- Local issue ID: LISS-0022
- Status: in_progress
- Phase: phase-3-refactor
- Type: refactor
- Priority: medium
- Related branch: feature/sakana-ollama-interchangeability

## Scope

- Move `OllamaClusterManager` orchestration to `scripts/router/manager.py`.
- Keep `scripts/ollama_cluster_manager.py` as the public compatibility and CLI
  entry point.
- Preserve CLI, MCP, task-package, output-path, retry, cache, and no-fallback
  behavior.
- Keep all tests on replaceable provider doubles; do not add real provider calls.

## Blocking Risks

- The current public module is loaded directly by tests and external skill
  callers, so import compatibility must be preserved during the move.
- CLI and MCP entry points must not gain provider-specific policy.
