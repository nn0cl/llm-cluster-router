# Feature: Ollama-Compatible Sakana Fugu Provider

## Goal

Allow callers to switch between Ollama and Sakana Fugu through provider
configuration while preserving the existing task-package, output, metadata,
and error contracts. Runtime fallback between providers or to mocks is
prohibited globally.

## EARS

When a configured host has `provider: "sakana"` and `model: "fugu"`, the
manager shall send the same normalized generation request used by Ollama to
the Sakana Responses API at `/v1/responses`.

When the provider changes from `ollama` to `sakana` without changing the task
package, the manager shall preserve output-path validation, output writing,
result metadata shape, and routing-profile evidence.

The manager shall always send cache-eligible input in the provider-neutral
generation request. The provider shall decide whether input-token caching is
available and effective; the caller shall not disable provider caching.

When a provider does not report prompt-cache usage, the manager shall report
the value as unavailable rather than as zero cached tokens.

When a provider does not support input-token cache usage reporting, the
manager shall still execute the request and mark cache application as
unknown/unavailable.

When Sakana returns an authentication, authorization, invalid-request, rate
limit, timeout, connection, or server error, the manager shall classify it
without exposing credentials or full prompt content.

When an error is retryable, the manager shall apply bounded retry/backoff
according to a configured retry count from 0 through 3, defaulting to 3, and
shall not retry non-retryable authentication or invalid-request errors.

When the selected provider remains unavailable after its retry budget is
exhausted, the manager shall fail with that provider's classified error and
shall not call another provider, a mock provider, or an implicit fallback.

When a task package is routed to Ollama, existing Ollama request behavior and
metadata shall remain unchanged.

## Proposed Data Contract

```json
{
  "prompt_cache": {
    "policy": "provider_managed",
    "data": {
      "stable_prefix": [],
      "dynamic_suffix": []
    }
  }
}
```

`policy: "provider_managed"` is the only supported policy in the first
release. The data object lets callers identify stable and dynamic input parts;
it does not promise a provider-specific cache key, TTL, or cache disable
operation.

The output metadata uses explicit availability rather than conflating
unsupported caching with a cache miss:

```json
{
  "prompt_cache": {
    "policy": "provider_managed",
    "provider_supported": true,
    "applied": true,
    "cached_tokens": 1200,
    "orchestration_cached_tokens": 800
  }
}
```

For Ollama or another provider without usage fields, `cached_tokens` and
`orchestration_cached_tokens` are `null`.

Structured output is requested through a provider-neutral task-package field:

```json
{
  "response_schema": {
    "name": "result",
    "schema": {"type": "object", "properties": {"answer": {"type": "string"}}},
    "strict": true
  }
}
```

Ollama maps this JSON Schema to `format`; Responses-compatible providers map it
to `text.format`. Providers without a native structured-output contract must
advertise that limitation rather than silently claim schema enforcement.

## Provider Contract

Sakana configuration:

```json
{
  "provider": "sakana",
  "url": "https://api.sakana.ai",
  "models": ["fugu"],
  "api_key_env": "SAKANA_API_KEY"
}
```

The provider adapter uses the standard-library HTTP port and does not add a
Sakana SDK dependency.

## Gherkin

```gherkin
Scenario: Route the unchanged task package from Ollama to Fugu
  Given a Sakana host is configured with model "fugu"
  And SAKANA_API_KEY is available
  When execute_task receives the same task package used by an Ollama host
  Then the request is sent to the Sakana Responses API
  And the output is written under the allowed root
  And the result identifies provider "sakana" and model "fugu"

Scenario: Use provider-managed Sakana input-token cache
  Given prompt_cache.policy is "provider_managed"
  And Sakana returns cached input-token usage
  When execute_task completes
  Then cached_tokens and orchestration_cached_tokens are preserved in metadata

Scenario: Provider-managed cache usage is unavailable
  Given prompt_cache.policy is "provider_managed"
  And the selected provider does not report cache usage
  When execute_task starts
  Then the provider request is still made
  And cache usage is reported as unavailable

Scenario: Sakana authentication failure does not retry
  Given Sakana returns HTTP 401
  When execute_task is called
  Then the error is classified as authentication failure
  And no retry request is made
  And the API key is absent from the error

Scenario: Sakana transient failure retries and then fails without fallback
  Given Sakana returns a timeout or HTTP 429/5xx
  And the configured retry count is 3
  When execute_task is called
  Then at most 3 retry requests are made
  And no other provider or mock provider is attempted
  And the classified Sakana error is returned after retry exhaustion

Scenario: Ollama behavior remains compatible
  Given an Ollama host is configured
  When execute_task is called with an existing Ollama task package
  Then the Ollama endpoint and existing metadata remain unchanged
```

## Out of Scope

- Local response caching or semantic caching in this feature.
- Streaming generation.
- Sakana built-in web-search tools.
- Provider-specific SDK dependencies.
- Claiming that the provider-managed policy guarantees a cache hit.
- Any runtime fallback to another provider or mock provider.

## Ambiguities

- Resolved by current design: Fugu is exposed as a named `sakana` provider,
  while the caller-facing generation contract remains provider-neutral.
- Resolved: retry delay/backoff uses bounded exponential backoff, with a
  provider Retry-After value capped by the configured maximum. Retry count is
  capped at 3 and fallback is prohibited globally.
