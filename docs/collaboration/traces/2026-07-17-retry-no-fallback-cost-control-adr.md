# Retry and No-Fallback Cost-Control ADR Trace

## Request

- Date: 2026-07-17
- Request: Research the cost risk of resubmitting prompts after AI-provider
  communication failures and record the retry/no-fallback policy as an ADR.

## Context Ledger

- Included: AGENTS.md, existing provider error policy, ADR 0008, LISS-0026,
  LISS-0028, and official OpenAI, Anthropic, Ollama, and Sakana documentation.
- Omitted: credentials, provider calls, real prompts, and billing-account data.
- Constraint: no OpenAI or Anthropic connection test.

## Evidence Summary

- OpenAI documents exponential backoff with a maximum retry count and notes
  that unsuccessful requests contribute to rate-limit usage.
- OpenAI and Anthropic SDKs retry transient failures by default, so adopting
  SDKs without an explicit boundary could multiply attempts invisibly.
- Anthropic documents 429/500/504/529 retry conditions, `Retry-After`, and
  request IDs.
- Ollama generation is long-running and exposes load/generation durations;
  a lost response is not proof that local generation did not run.
- Sakana documents request retry settings and long-running Fugu timeout needs.

## Decision

ADR 0009 accepts selected-provider-only retries, a 0–3 retry cap (default 3),
bounded backoff, no provider/mock fallback, safe error metadata, and an
explicit exactly-once limitation for ambiguous timeouts.

## Verification

- No provider connection was made.
- ADR links and implementation assumptions were checked against official docs
  fetched on 2026-07-17.
