# Feature: Profile-Based LLM Routing

## Goal

Let the calling skill classify a task and request a routing profile so the
manager can choose a configured Ollama, Claude, Codex, or OpenAI-compatible
provider without relying on model-name guessing alone.

## EARS

When a task package includes `routing_profile`, the system shall resolve that
profile from the cluster config and route to the configured provider and model.

When a task package includes `task_complexity` but not `routing_profile`, the
system shall resolve the matching complexity profile from the cluster config.

If no routing profile or task complexity is provided, the system shall preserve
the current behavior of routing by `model`, provider availability, loaded
Ollama state, and priority.

If the selected profile points to a provider or model that is not configured or
reachable, the system shall fail with a routing error unless an accepted
fallback rule exists in the config.

While executing a routed task, the system shall return metadata that includes
the selected provider, selected model, and profile or complexity evidence when
profile routing was used.

## Proposed Config Contract

```json
{
  "routing": {
    "default_profile": "easy",
    "profiles": {
      "easy": {
        "provider": "ollama",
        "model": "qwen2.5-coder:7b"
      },
      "hard": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-5"
      },
      "agentic": {
        "provider": "codex",
        "model": "gpt-5.4"
      }
    }
  }
}
```

## Gherkin

```gherkin
Scenario: Explicit routing profile selects Claude
  Given the config has a routing profile named "hard"
  And the "hard" profile points to provider "anthropic" and model "claude-sonnet-4-5"
  And the Anthropic provider is configured, credential-ready, and lists "claude-sonnet-4-5"
  When execute_task receives a task package with routing_profile "hard"
  Then the task is sent to the Anthropic Messages API using model "claude-sonnet-4-5"
  And the result metadata includes routing_profile "hard"
  And the result metadata includes provider "anthropic"

Scenario: Task complexity selects Codex
  Given the config has a routing profile named "agentic"
  And the "agentic" profile points to provider "codex" and model "gpt-5.4"
  And the Codex provider is configured and SDK-ready
  When execute_task receives a task package with task_complexity "agentic"
  Then the task is sent through the Codex provider using model "gpt-5.4"
  And the result metadata includes task_complexity "agentic"
  And the result metadata includes provider "codex"

Scenario: Missing profile preserves current model routing
  Given the config has reachable Ollama providers
  And no routing_profile or task_complexity is present in the task package
  When execute_task receives a task package with model "qwen2.5-coder:7b"
  Then the current loaded-model and priority routing behavior is used

Scenario: Unknown routing profile fails before provider execution
  Given the config has no routing profile named "expensive"
  When execute_task receives a task package with routing_profile "expensive"
  Then execution fails with a routing error
  And no provider generation request is sent
```

## External Dependencies

- Provider configuration via config file.
- Secret and environment access for Anthropic and OpenAI-compatible providers.
- Optional Codex SDK availability.
- Ollama runtime status via `/api/ps` and `/api/tags`.
- Output file writes under the allowed root.

## Out of Scope

- Automatic model pricing discovery.
- Automatic SaaS model capability ranking.
- Configured fallback routing between profiles (see
  `docs/specs/fallback-routing.md`).
- Network calls to list OpenAI or Anthropic models.
- New third-party dependencies.
- Renaming existing Ollama-specific filenames or environment variables.
- Real provider integration tests.

## Ambiguities

- Whether fallback from one profile to another should be implemented now or
  deferred.
- Whether `default_profile` should apply when only `model` is missing, or
  whenever routing hints are missing.
- Whether `routing_guidance` should remain a calling-agent hint or be replaced
  by executable `routing.profiles`.
