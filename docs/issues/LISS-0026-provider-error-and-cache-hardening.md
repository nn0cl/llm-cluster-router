# LISS-0026: Provider error and cache-usage hardening

## Metadata

- Local issue ID: LISS-0026
- GitHub issue: none
- Status: done
- Phase: phase-2-green
- Type: feature
- Priority: high
- Owner/agent: AI agent
- Related branch: feature/sakana-ollama-interchangeability

## Summary

Harden provider error handling, bounded retry, and Fugu prompt-cache usage
reporting to product quality after the Sakana adapter is Green. This slice is
complete and does not add or invoke runtime provider fallback.

## Acceptance Notes

- 401/403 and invalid-request errors do not retry by default.
- 429, timeout, connection, and transient 5xx errors follow bounded retry
  policy with Retry-After support where available.
- Retry count is configurable from 0 through 3, defaults to 3, and retry
  exhaustion fails on the selected provider without provider or mock
  substitution.
- Error details include provider, status class, request identifier when safe,
  and retry state, without credentials or prompt body.
- Missing cache usage is represented as unavailable (`null`).
- Malformed usage payloads are handled as protocol errors, not fabricated data.

## Dependencies

- Parent: LISS-0023
- Depends on: LISS-0025 verified Green
- Blocks: LISS-0027
- Related: `docs/specs/sakana-ollama-interchangeability.md`,
  `docs/architecture/adr/0008-provider-neutral-sakana-ollama-interchangeability.md`

## Verification

- Unit tests cover the HTTP error matrix with injected fake transport/time.
- Test doubles are test-only; runtime fallback to a mock provider is forbidden.
- No real provider calls.
- Full unittest and compile checks pass.
