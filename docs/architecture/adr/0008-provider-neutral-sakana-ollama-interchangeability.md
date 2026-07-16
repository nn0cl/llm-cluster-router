# ADR 0008: Provider-Neutral Ollama and Sakana Generation Contract

## Status

Proposed

## Context

The router currently exposes one public task execution contract but keeps
provider-specific request, response, and error handling in a single manager
module. Sakana Fugu is OpenAI-compatible at the HTTP wire level, while Ollama
uses a different API. Treating Sakana as an Ollama special case would make
provider differences leak into routing policy and make error handling hard to
review.

The user requires Fugu to be interchangeable with Ollama from the caller's
perspective and requires product-quality error handling and prompt-cache
usage reporting.

## Dependency Adoption Evidence

- Vulnerability/advisory check: no new runtime dependency proposed.
- Version-specific examples checked: Sakana official Responses API and model
  usage documentation, fetched 2026-07-16.
- Troubleshooting and known-issue evidence: Sakana documents long-running
  requests and retry settings for Codex integration; retry policy remains a
  router contract and must be bounded.
- Minimal real-file test or fixture plan: mocked HTTP responses for Ollama and
  Sakana, plus JSON sample validation; no real provider call in core tests.
- POC feasibility/result: existing standard-library HTTP boundary can send
  JSON to both providers; implementation is pending Phase 1 review.
- Clean Architecture boundary: provider adapters own HTTP mapping; routing
  policy and cache DTOs remain provider-neutral.

## Decision

1. Introduce a provider-neutral generation contract behind a narrow port-like
   boundary while preserving `OllamaClusterManager` as the public entry point.
2. Implement separate Ollama and Sakana adapters. Adapters map wire formats
   and provider usage into common response metadata; they do not choose
   profiles, fallback chains, or cost policy.
3. Expose Fugu as `provider: "sakana"`, default model `fugu`, and default key
   environment `SAKANA_API_KEY`.
4. Always send provider-managed cache-eligible input. Expose a
   `provider_managed` cache policy and stable/dynamic input data object, but do
   not expose provider-specific TTL, cache key, or disable semantics. A
   provider that cannot report usage still executes the request and returns
   unavailable (`null`), not zero.
5. Classify transport and API errors into retryable and non-retryable typed
   categories. Retry count is provider-configurable from 0 through 3, defaults
   to 3, and has no runtime fallback to another provider or mock provider.
6. Do not add a provider SDK or local response cache.

## Consequences

Positive:

- Ollama and Fugu are interchangeable at the task-package and delivery
  boundaries.
- Provider-specific API changes stay in adapters.
- Cache capability differences are visible instead of silently ignored.
- Error classification can be tested without a real provider.

Negative:

- The current monolithic manager requires an incremental extraction.
- Fugu and Ollama cannot expose identical usage metrics because Ollama does
  not provide Fugu's orchestration cache fields.
- Retry behavior adds configuration and test cases.
- A provider outage fails the task even when another configured provider is
  healthy; availability does not silently substitute providers.

## Enforcement

Code review should reject:

- Sakana-specific fields added directly to routing policy.
- Provider adapters implementing fallback or cost-tier decisions.
- Runtime substitution of another provider or mock provider after retry
  exhaustion.
- Treating unavailable cache usage as zero.
- Logging API keys, authorization headers, or full prompt payloads.
- Retrying authentication or invalid-request errors by default.
