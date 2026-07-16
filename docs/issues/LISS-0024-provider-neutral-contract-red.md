# LISS-0024: Provider-neutral contract Red tests

## Metadata

- Local issue ID: LISS-0024
- GitHub issue: none
- Status: done
- Phase: phase-1-red
- Type: feature
- Priority: high
- Owner/agent: AI agent
- Related branch: feature/sakana-ollama-interchangeability

## Summary

Add tests for the reviewed provider-neutral generation, capability, and
prompt-cache contracts. The Red slice is complete and now backed by the Green
implementation.

## Acceptance Notes

- Tests prove the unchanged task package can target Ollama or Sakana by config.
- Tests define provider-managed cache policy and stable/dynamic input data.
- Tests prove the request is not rejected when the provider does not report
  cache usage.
- Tests preserve `null` for unavailable cached-token usage.
- Tests classify authentication, invalid request, rate limit, timeout,
  connection, and server failures.
- Tests enforce a configurable retry count from 0 through 3, defaulting to 3.
- Tests prove retry exhaustion never invokes another provider or mock provider.
- Tests prove secrets and full prompts do not appear in errors or metadata.
- Existing Ollama behavior assertions are preserved; fallback assertions are
  replaced only where the reviewed no-fallback contract requires it.

## Dependencies

- Parent: LISS-0023
- Depends on: LISS-0023 approval, LISS-0017 or equivalent accepted types boundary
- Blocks: LISS-0025
- Related: `docs/specs/sakana-ollama-interchangeability.md`

## Verification

- Expected Red: new Sakana/provider-neutral tests fail because the provider
  adapter and DTO/capability boundary do not yet exist.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`
