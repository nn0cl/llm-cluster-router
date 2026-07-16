# Feature: Fallback-Based LLM Routing

## Status

Wont do. Runtime provider fallback is prohibited: a failed provider is
retried according to its own retry policy and then returned as an error.

This document is retained as historical context for the withdrawn proposal;
it is not an accepted implementation specification.

## Goal

Allow the manager to fall back from a failing routing target to a configured
secondary target, without silently escalating to a more expensive or less
trusted provider, and with explicit metadata describing the fallback.

## EARS

When a routing profile points to a provider or model that is temporarily
unavailable and a configured fallback profile exists, the system shall route
the task to the fallback profile instead of failing immediately.

When a routing profile points to a provider that is configured but missing
required credentials (for example an API key environment variable), and a
configured fallback profile exists, the system shall treat that as a
fallback-eligible failure and route to the fallback profile.

When a routing profile points to a provider or model that is misconfigured
(missing from config) and no acceptable fallback profile is configured, the
system shall fail with a routing error before making any provider request.

When a fallback occurs, the system shall include metadata that records:

- the originally requested profile, provider, and model, and
- the effective profile, provider, and model that were actually used.

Fallback routing shall never escalate to a higher cost tier than the original
profile without an explicit `fallback_profiles` entry that names the
higher-cost profile.

When all configured fallback profiles are exhausted, the system shall fail
with a routing error that lists the profiles attempted.

## Proposed Config Contract

Extension to the `routing.profiles` entries in the cluster config:

```json
{
  "routing": {
    "default_profile": "easy",
    "profiles": {
      "easy": {
        "provider": "ollama",
        "model": "qwen2.5-coder:7b",
        "fallback_profiles": ["standard"]
      },
      "standard": {
        "provider": "openai",
        "model": "gpt-5.4",
        "fallback_profiles": ["hard"]
      },
      "hard": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-5",
        "fallback_profiles": []
      }
    }
  }
}
```

- `fallback_profiles` is an ordered list of profile names.
- The manager tries each fallback profile in order until one succeeds or all
  are exhausted.
- If `fallback_profiles` is omitted or empty, no fallback is attempted.
- Cost tier ordering follows `docs/architecture/model-routing-catalog.md`.

## Gherkin

```gherkin
Scenario: Fallback from OpenAI to Anthropic when primary is unreachable
  Given the config has a routing profile named "standard"
  And the "standard" profile points to provider "openai" and model "gpt-5.4"
  And the config has a routing profile named "hard"
  And the "hard" profile points to provider "anthropic" and model "claude-sonnet-4-5"
  And the "standard" profile lists "hard" in fallback_profiles
  And the OpenAI provider is configured but currently unreachable
  And the Anthropic provider is configured and reachable
  When execute_task receives a task package with routing_profile "standard"
  Then the task is sent to the Anthropic Messages API using model "claude-sonnet-4-5"
  And the result metadata includes requested_routing_profile "standard"
  And the result metadata includes effective_routing_profile "hard"
  And the result metadata includes fallback_used true

Scenario: Fallback when primary provider credentials are missing
  Given the config has a routing profile named "standard"
  And the "standard" profile points to provider "openai" and model "gpt-5.4"
  And the config has a routing profile named "hard"
  And the "hard" profile points to provider "anthropic" and model "claude-sonnet-4-5"
  And the "standard" profile lists "hard" in fallback_profiles
  And the OpenAI API key environment variable is missing
  And the Anthropic provider is configured, credentialed, and reachable
  When execute_task receives a task package with routing_profile "standard"
  Then the task is sent to the Anthropic Messages API using model "claude-sonnet-4-5"
  And the result metadata includes requested_routing_profile "standard"
  And the result metadata includes effective_routing_profile "hard"
  And the result metadata includes fallback_used true

Scenario: Missing profile target and no fallback yields routing error
  Given the config has a routing profile named "standard"
  And the "standard" profile points to a provider/model that is not configured
  And the "standard" profile has no fallback_profiles
  When execute_task receives a task package with routing_profile "standard"
  Then the task fails before any provider request is made
  And the error describes the missing provider or model and the lack of fallback

Scenario: Fallback cannot escalate cost tiers without explicit config
  Given the config defines cost tiers for profiles in the model routing catalog
  And the "easy" profile has no fallback_profiles entry naming a higher cost tier
  When execute_task receives a task package with routing_profile "easy"
  And the "easy" profile target is unreachable
  Then the manager does not silently escalate to a higher cost tier
  And the task fails with a routing error

Scenario: Exhausted fallback chain fails with evidence
  Given the config has routing profiles "standard" and "hard"
  And the "standard" profile lists only "hard" in fallback_profiles
  And both profile targets are unreachable
  When execute_task receives a task package with routing_profile "standard"
  Then the task fails with a routing error
  And the error lists the profiles attempted in order
```

## Out of Scope

- Automatic discovery of cheaper or more expensive models at runtime.
- Dynamic reordering of `fallback_profiles` based on observed latency or cost.
- Cross-provider retries beyond what is explicitly listed in the config.
- Changing the existing model-name and priority routing when no
  `routing_profile` or `task_complexity` is present.

## Ambiguities

- Resolved by Referee (2026-07-09): credential-missing errors and temporary
  unreachability both trigger fallback when `fallback_profiles` names a
  secondary profile. Misconfigured providers (absent from config) remain
  immediate errors unless a fallback is named.
- Whether `fallback_profiles` may reference the same profile name more than
  once. Default: ignore duplicates while preserving first-seen order.
