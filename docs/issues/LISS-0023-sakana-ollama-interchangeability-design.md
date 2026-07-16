# LISS-0023: Sakana/Ollama interchangeability design

## Metadata

- Local issue ID: LISS-0023
- GitHub issue: none
- Status: done
- Phase: phase-0-design
- Type: architecture
- Priority: high
- Owner/agent: AI agent
- Related branch: feature/sakana-ollama-interchangeability

## Summary

Define the accepted architecture and provider-neutral contract for using Sakana
Fugu (`fugu`) interchangeably with Ollama. The design phase is complete;
implementation is tracked by LISS-0024 through LISS-0027.

## Acceptance Notes

- `docs/specs/sakana-ollama-interchangeability.md` is reviewed as the target
  acceptance specification.
- `docs/architecture/adr/0008-provider-neutral-sakana-ollama-interchangeability.md`
  is accepted or explicitly amended.
- The common contract preserves task package, output path, result metadata, and
  delivery behavior; runtime fallback is prohibited globally.
- Cache semantics distinguish requested, supported, applied, and unavailable.
- Error classification and retry/no-fallback boundaries are explicit.

## Dependencies

- Parent: none
- Depends on: Referee review of `docs/architecture/manager-split-plan.md`
- Blocks: LISS-0024
- Related: `docs/work-plans/sakana-ollama-interchangeability.md`, LISS-0017,
  LISS-0021

## Referee Decision Points

- Accept `provider: "sakana"` with model `fugu` as the public configuration.
- Confirm provider-managed caching: cache-eligible input is always sent, and
  callers may configure stable/dynamic data but cannot disable provider cache.
- Confirm retry count is configurable from 0 through 3, defaults to 3, with no
  runtime fallback to another provider or mock provider; set delay/backoff and
  jitter.
- Resolved: no runtime fallback is allowed globally. The existing
  fallback-routing proposal and its dependent issues are withdrawn.
- Confirm whether Sakana belongs in the model-routing catalog as a paid tier.

## Context

- Included: `AGENTS.md`, quickstart, readiness checklist, manager split plan,
  testing strategy, IO contracts, fallback spec, existing manager/tests, and
  official Sakana API documentation.
- Omitted: secrets, real prompts, provider raw responses, and unrelated product
  changes.
- Assumptions: standard-library HTTP remains the runtime boundary; no SDK or
  persistent cache is introduced.

## References

- https://console.sakana.ai/get-started (fetch-verified 2026-07-16)
- https://console.sakana.ai/models (fetch-verified 2026-07-16)
- https://github.com/openai/openai-python/blob/main/src/openai/_base_client.py
  (fetch-verified 2026-07-16)
- https://docs.litellm.ai/ (fetch-verified 2026-07-16)

## Verification

- Design artifact consistency and issue dependency review.
- No implementation verification in this issue.
