# Model Routing Catalog

This catalog lists the models this project's docs and sample config currently
know about, so a routing profile can pick the cheapest model that can still do
the task. It intentionally avoids exact prices or benchmark scores: those
change often and are not tracked here. It only records relative cost tier and
relative reasoning depth, both taken from how this repo already configures and
prioritizes each provider.

This is a router-config catalog, not the AI-collaboration model/tool routing
in `docs/collaboration/model-tool-capability-matrix.md`. That document routes
this project's own AI-TDD process tasks; this one routes end-user task
packages sent through `scripts/ollama_cluster_manager.py`.

## Known Models

| Provider | Model | Cost tier | Reasoning depth | Notes |
| --- | --- | --- | --- | --- |
| `ollama` | `qwen2.5-coder:7b` | Free (local/LAN compute only) | Shallow to moderate | Runs on hosts already in the cluster; no per-call cost. |
| `openai` | `gpt-5.4` | Paid, low-to-moderate | Moderate | OpenAI-compatible Responses API. |
| `anthropic` | `claude-sonnet-4-5` | Paid, higher | Deep | Claude Messages API; best for ambiguous or long-context work. |
| `codex` | `gpt-5.4` | Paid, higher | Deep, with tool use | Local Codex SDK; adds multi-step workspace/tool-use ability over the plain `openai` call. |

Add a row here whenever a new provider or model becomes a configuration
target. Remove a row once no sample config or doc references that model.

## Routing Profiles and Cost Minimization

`references/ollama_cluster_config.sample.json` maps each profile to the
cheapest model in the table that fits the profile's task class:

| Profile | Provider / model | When to use |
| --- | --- | --- |
| `easy` (`default_profile`) | `ollama` / `qwen2.5-coder:7b` | Small, local, low-risk tasks. Always the first tier tried. |
| `standard` | `openai` / `gpt-5.4` | Ordinary coding tasks a local model handles poorly, but that do not need deep reasoning. |
| `hard` | `anthropic` / `claude-sonnet-4-5` | Ambiguous, architecture-sensitive, or long-context reasoning. |
| `agentic` | `codex` / `gpt-5.4` | Multi-step workspace coding that needs tool use, when the SDK is available. |

Cost-minimization principle: escalate one tier at a time. Only request
`standard`, `hard`, or `agentic` when the task genuinely needs that tier's
reasoning depth; otherwise let a task package omit `routing_profile` and
`task_complexity` so the manager's default model/priority routing (which
prefers free local hosts) applies, or explicitly set `routing_profile` to
`easy`.

## Keeping This Honest

- Only list models that already appear in `references/agent_system_prompt.md`,
  `references/ollama_cluster_config.sample.json`, or an accepted spec. Do not
  add a model here on the assumption that it exists or is available.
- Cost tier and reasoning depth are relative judgments recorded by the
  Referee, not a pricing feed. Update them when the Referee's judgment
  changes, not from unverified outside claims.
- Real pricing, quota, and benchmark tracking remain out of scope until an ADR
  says otherwise (see CLAUDE.md "Current Non-Decisions").
