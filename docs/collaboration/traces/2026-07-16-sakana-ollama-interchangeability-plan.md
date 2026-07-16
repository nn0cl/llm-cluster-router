# Sakana/Ollama Interchangeability Plan Trace

## Request

- Date: 2026-07-16
- User request: Make Sakana Fugu interchangeable with Ollama, analyze product-
  quality error handling and prompt-cache capability, and issue the detailed
  plan after understanding `AGENTS.md`.
- Current phase: phase-3-refactor / implementation and verification.

## Context Ledger

- Included: `AGENTS.md`, architecture quickstart/readiness, AT-TDD process,
  provider routing and IO contracts, manager split plan, fallback spec, local
  issue planning rules, current manager/tests, and official Sakana API docs.
- Omitted: secrets, real prompts, provider raw responses, real network calls,
  and unrelated product changes.
- Assumptions: Fugu uses model `fugu`; standard-library HTTP remains the core
  transport; no provider SDK or local response cache is introduced.
- Open decision: model-routing catalog cost-tier placement remains deferred.

## Routing

- Model/assistant/tool: deterministic repository inspection and web lookup for
  official provider documentation; stronger reasoning review for architecture
  boundaries and error policy.
- Privacy constraints: no credentials or private user data were included.

## Cost / Reasoning Control

- Operating path: Architecture Path followed by Feature Path planning.
- Files read: directly relevant architecture, contracts, manager, tests,
  templates, and issue/work-plan examples only.
- Context intentionally omitted: unrelated source, generated artifacts,
  private data, and provider secrets.
- Deterministic checks used: repository search, document inspection, issue-ID
  collision check, and planned verification commands.
- Escalation reason: new provider boundary, cache capability contract, and
  product-grade retry/error classification.
- Avoided LLM work: no code generation and no real-provider integration test.

## Referee Decisions

- User explicitly requested Ollama/Fugu interchangeability and detailed local
  issue planning.
- Resolved: user authorized implementation and issue-slice execution without
  real OpenAI or Anthropic connection tests.
- Resolved: input-token cache policy is always provider-managed; callers can
  describe stable/dynamic input data but cannot disable provider-side caching.
- Resolved: retry count is configurable from 0 through 3 with default 3;
  runtime fallback to another provider or mock provider is prohibited.
- Resolved: the existing fallback-routing proposal is withdrawn and its
  dependent local issues are marked `wont_do`.
- Resolved: the no-fallback rule is global; no provider or mock substitution is
  permitted at runtime.

## Verification

- Confirmed existing local issue IDs through LISS-0019 and the manager-split
  plan's reserved LISS-0020–0022 sequence.
- Confirmed implementation uses replaceable HTTP doubles; no real OpenAI or
  Anthropic connection test was added.
- Confirmed official Fugu documentation describes OpenAI-compatible Responses
  API and cached-token usage fields.

## Changed Files

- `docs/specs/sakana-ollama-interchangeability.md`
- `docs/architecture/adr/0008-provider-neutral-sakana-ollama-interchangeability.md`
- `docs/work-plans/sakana-ollama-interchangeability.md`
- `docs/issues/LISS-0023-sakana-ollama-interchangeability-design.md`
- `docs/issues/LISS-0024-provider-neutral-contract-red.md`
- `docs/issues/LISS-0025-sakana-fugu-green.md`
- `docs/issues/LISS-0026-provider-error-and-cache-hardening.md`
- `docs/issues/LISS-0027-sakana-interchangeability-refactor-docs.md`
- This trace file.

## Next Safe Action

Run the deterministic unit, compile, JSON, and diff checks; then update issue
statuses and the handoff summary.
