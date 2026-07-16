# Work Plan: Sakana Fugu as an Ollama-Compatible Provider

## Goal

Add a production-quality Sakana Fugu provider while preserving the caller-facing
Ollama task contract and exposing provider capability differences explicitly.

## Scope

- In:
  - Provider-neutral generation DTO/port boundary.
  - `sakana` / `fugu` configuration.
  - Provider-managed prompt-cache data and usage DTOs.
  - Typed provider error classification and bounded retry.
  - Ollama regression compatibility.
  - Config, schema, README, and model catalog updates.
- Out:
  - Local or semantic response cache.
  - Streaming, tools, and Sakana SDK.
  - Unconfigured automatic provider escalation.

## Design Intake

- Requested phase: planning and issue creation only.
- Proposed next phase: Phase 1 Red after Referee approval of the ADR and spec.
- Include: existing manager/provider tests, manager split plan, testing and
  IO contracts, Fugu official API/model docs.
- Omit: secrets, real prompts, real provider calls, unrelated adapters.
- DTO candidates: `GenerationRequest`, `GenerationResponse`, `PromptCachePolicy`,
  `PromptCacheUsage`, `ProviderCapabilities`, `ProviderError`.
- Ports/adapters: generation transport port; Ollama and Sakana HTTP adapters;
  secret access and retry clock seams if required by tests.
- Routing: strong reasoning review for boundary/error policy; code assistant for
  Red tests; deterministic unittest, compile, and JSON validation.

## Issue Graph

| Issue | Status | Phase | Depends on | Blocks | Branch |
| --- | --- | --- | --- | --- | --- |
| LISS-0023 | done | phase-0-design | manager split plan review | LISS-0024 | feature/sakana-ollama-interchangeability |
| LISS-0024 | done | phase-1-red | LISS-0023, LISS-0017 | LISS-0025 | feature/sakana-ollama-interchangeability |
| LISS-0025 | done | phase-2-green | LISS-0024, provider adapter extraction | LISS-0026 | feature/sakana-ollama-interchangeability |
| LISS-0026 | done | phase-2-green | LISS-0025 | LISS-0027 | feature/sakana-ollama-interchangeability |
| LISS-0027 | review | phase-3-refactor | LISS-0026 | - | feature/sakana-ollama-interchangeability |
| LISS-0028 | in_progress | phase-2-green / phase-3-refactor | LISS-0027 review findings | - | feature/sakana-ollama-interchangeability |
| LISS-0029 | review | phase-3-refactor | LISS-0028, LISS-0022 | - | feature/sakana-ollama-interchangeability |
| LISS-0030 | done | phase-3-refactor | LISS-0029 | - | feature/sakana-ollama-interchangeability |
| LISS-0031 | done | phase-3-refactor | LISS-0030 | - | feature/sakana-ollama-interchangeability |
| LISS-0032 | done | phase-3-refactor | LISS-0030 | - | feature/sakana-ollama-interchangeability |
| LISS-0033 | done | phase-3-refactor | LISS-0030 | - | feature/sakana-ollama-interchangeability |
| LISS-0034 | done | phase-3-refactor | LISS-0031, LISS-0032, LISS-0033 | - | feature/sakana-ollama-interchangeability |

`LISS-0020`–`LISS-0022` remain reserved by
`docs/work-plans/manager-module-split.md` and are not reused here.

## Recommended Order

1. ADR and acceptance specification were approved by the user for execution.
2. Retry count is fixed to 0–3 with default 3 and no fallback. Cache policy is
   fixed to provider-managed input caching.
3. Feature branch and local issue slices are active.
4. Phase 1 Red tests cover common contracts, Fugu routing, cache usage, and
   error classification.
5. The Green implementation adds the Sakana adapter path and cache DTO.
6. Retry/backoff hardening uses deterministic injected clock and transport
   behavior; verify retry exhaustion never invokes another provider.
7. Documentation, schema, samples, and provider-neutral metadata are updated;
   full module extraction remains a follow-up under the manager-split plan.
8. LISS-0028 adds structured response-schema mapping and provider error
   hardening before LISS-0027 is closed.
9. LISS-0029 incorporates the reviewed Ollama communication patterns while
   excluding hidden retry multiplication and endpoint/provider fallback.

## Risks

- Fugu may apply or skip its internal cache independently of the requested
  stable/dynamic input structure.
- Retry can multiply cost if idempotency and retry classification are wrong;
  the hard cap is three retries.
- The existing monolithic manager and manager-split plan may create merge
  conflicts; provider work should use the adapter extraction boundary.
- Runtime fallback is prohibited globally. The historical fallback-routing
  proposal and dependent issues are withdrawn and must not be implemented.

## Verification Plan

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`
- `python3 -m py_compile scripts/ollama_cluster_manager.py scripts/mcp_server.py`
- `python3 -m json.tool references/ollama_cluster_config.sample.json`
- Assert no real network call in unit tests.
- Assert no secret or full prompt appears in errors or metadata.
