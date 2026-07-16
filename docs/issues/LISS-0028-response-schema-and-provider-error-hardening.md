# LISS-0028: Response schema and provider error hardening

## Metadata

- Local issue ID: LISS-0028
- GitHub issue: none
- Status: done
- Phase: phase-2-green / phase-3-refactor
- Type: feature
- Priority: high
- Related branch: feature/sakana-ollama-interchangeability

## Summary

Add a provider-neutral response-schema data object and harden provider error
classification. Ollama transient failures, high-load responses, timeouts, and
connection failures must be handled with bounded retries. OpenAI and Anthropic
must use replaceable test doubles only; no real connection test is in scope.

## Acceptance Criteria

- `response_schema` accepts a JSON Schema object without exposing provider
  request-shape details to callers.
- Ollama maps the schema to `format`; Responses-compatible providers map it to
  `text.format`.
- Provider error messages do not include raw response bodies or full prompts.
- Status classification preserves provider HTTP status and safe request ID.
- 408/425/429 and 5xx, timeouts, connection resets, and unavailable Ollama
  responses are retryable; authentication and invalid-request responses are not.
- Retry count remains configurable from 0 through 3, with no provider or mock
  fallback.
- README, Japanese README, task schema, and feature spec document the contract.
- No OpenAI or Anthropic real-network test is added.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/ollama_cluster_manager.py scripts/mcp_server.py scripts/install_skill.py`
- `python3 -m json.tool references/agent_tool_schema.json >/dev/null`
- `git diff --check`
