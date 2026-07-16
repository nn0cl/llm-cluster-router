# LISS-0021: Provider adapter extraction

## Metadata

- Local issue ID: LISS-0021
- Status: done
- Phase: phase-3-refactor
- Type: refactor
- Priority: high
- Related branch: feature/sakana-ollama-interchangeability

## Acceptance Notes

- Provider wire-format mapping lives under `scripts/adapters/`.
- HTTP transport is replaceable and lives in `scripts/adapters/http.py`.
- Ollama, OpenAI Responses, Anthropic Messages, Sakana Responses, and Codex
  execution do not implement routing or fallback policy.
- Manager retains retry and no-fallback policy and delegates provider execution.
- Existing public helper names remain compatibility wrappers while callers
  migrate to adapter modules.
- No real OpenAI or Anthropic connection test is added.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/ollama_cluster_manager.py scripts/mcp_server.py`
