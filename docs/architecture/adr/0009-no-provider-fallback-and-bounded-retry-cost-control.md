# ADR 0009: No Provider Fallback and Bounded Retry Cost Control

## Status

Accepted

## Context

The router sends prompts to AI providers that may charge for input/output
tokens or consume substantial local compute. A communication failure does not
prove that the provider did not receive or begin processing the request. A
timeout, connection reset, or dropped response can therefore leave the server
side request outcome ambiguous. Re-sending the prompt can create a second
generation, duplicate token usage, duplicate side effects in provider tools,
or additional local Ollama load.

The router also has multiple configured providers. Selecting another provider
after a failed request would silently change model behavior, cost tier, privacy
boundary, and potentially submit the same prompt to a second service. This is
not an acceptable implicit recovery mechanism.

## Evidence Reviewed

- OpenAI recommends exponential backoff with a maximum retry count for 429
  responses and explicitly notes that unsuccessful requests contribute to the
  per-minute limit:
  <https://help.openai.com/en/articles/5955604>
- The official OpenAI Python client retries connection errors, 408, 409, 429,
  and 5xx errors twice by default and exposes `max_retries`; it also reports
  request IDs for failed status errors:
  <https://github.com/openai/openai-python>
- Anthropic documents retryable transient failures, `Retry-After`, 429 rate
  limits, 500/504/529 service failures, and SDK retries twice by default:
  <https://platform.claude.com/docs/en/api/errors>
- Anthropic error responses provide a request ID for support and diagnosis:
  <https://platform.claude.com/docs/en/api/errors>
- Ollama's generation endpoint is a long-running local generation operation;
  its response includes generation and load duration fields. A timeout or
  disconnected client cannot be treated as proof that generation did not run:
  <https://docs.ollama.com/api/generate>
- Sakana's official setup documentation exposes request retry settings and
  recommends increased client-side timeouts for complex Fugu tasks. The
  router's stricter cap is intentional:
  <https://console.sakana.ai/get-started>

## Decision

1. The router retries only the currently selected provider. It never falls
   back to another configured provider, a mock provider, or an implicit model.
2. Retry is limited to explicitly classified transient failures:
   connection failure, timeout, 408, 425, 429, 5xx, and provider-specific
   overload/unavailable responses such as Anthropic 529. Authentication,
   permission, invalid request, billing, not-found, and schema/protocol
   failures do not retry by default.
3. `max_retries` is configurable from 0 through 3 and defaults to 3. This is a
   maximum number of retries, not a guarantee of a maximum number of billable
   requests. The total attempt count is therefore at most four.
4. `Retry-After` is honored when present but capped by the configured retry
   backoff maximum. Otherwise the router uses bounded exponential backoff.
5. Provider SDKs with their own hidden retry loops are not added to the core
   transport. Adapter implementations must expose one router-controlled retry
   boundary so retry counts are observable and cannot multiply accidentally.
6. Every failed attempt is classified with provider, category, HTTP status
   when available, request ID when safe, attempt count, and retry budget. Error
   messages must not include credentials or full request/response bodies.
7. Because a timeout can be an ambiguous outcome, the router does not claim
   exactly-once delivery. A future idempotency-key feature requires a separate
   provider-capability ADR; until then, bounded retry plus no fallback is the
   accepted risk boundary.

## Consequences

### Positive

- A failed provider cannot silently spend tokens with a second provider.
- Provider, model, privacy boundary, and cost tier remain stable for one task.
- Retry behavior is bounded, visible, and testable with transport doubles.
- Local Ollama overload is handled without multiplying work across the cluster.

### Negative

- A task fails even when another configured provider is healthy.
- Transient retries can still consume provider tokens or local compute when the
  original request was accepted but its response was lost.
- Exactly-once generation is unavailable without provider-supported
  idempotency semantics.
- Users must choose retry budgets consciously for expensive or side-effecting
  tasks.

## Enforcement

- Routing code must not contain fallback chains.
- Adapters must not select a replacement provider after an error.
- Tests must assert retry exhaustion invokes only the selected provider.
- Tests must cover non-retryable authentication and invalid-request failures.
- Logs and errors must omit API keys, authorization headers, and full prompts.
- Any future fallback or idempotency behavior requires a new ADR and explicit
  acceptance criteria.

## Related Decisions

- ADR 0008: Provider-Neutral Ollama and Sakana Generation Contract.
- LISS-0026: Provider error and cache-usage hardening.
- LISS-0028: Response schema and provider error hardening.
- LISS-0022: Manager orchestration and CLI thinning.
