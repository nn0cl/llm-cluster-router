---
name: llm-cluster-router
description: Route AI coding tasks across Ollama hosts, OpenAI API, Anthropic Claude API, or local Codex SDK. Use when Codex should select a configured model provider, send a compact JSON task package, and write generated output directly to an allowed project path without returning full generated content through the cloud-side agent.
---

# LLM Cluster Router

Use this skill when a task should run through a configured LLM provider,
especially for code generation that can be written directly to the workspace.

For MCP-only clients that cannot read this skill package, run
`scripts/mcp_server.py` instead; it exposes the same `status_check` and
`execute_task` actions as MCP tools over the same underlying manager. See
`docs/architecture/adr/0007-mcp-delivery-adapter.md`.

## Configured Providers

Use only providers configured by the user in the cluster config.

- `ollama`: local or LAN Ollama hosts for small, local, low-risk tasks when a
  suitable model is available.
- `anthropic`: Claude Messages API for configured Claude models. Prefer this
  for hard, ambiguous, architecture-sensitive, or long-context tasks when the
  provider is configured and credentials are available.
- `codex`: local Codex SDK for configured Codex models. Prefer this for
  agentic, multi-step workspace coding tasks when the SDK is available.
- `openai`: OpenAI-compatible Responses API for configured OpenAI models.

The manager routes a task package by, in order: a matching `routing_profile`
or `task_complexity` name found under the config's `routing.profiles` (sends
the task straight to that profile's configured provider and model), then
requested model, provider availability, and provider priority when no
profile matches. `routing_guidance` remains descriptive-only: it helps the
calling agent pick a `task_complexity` or `routing_profile` value but is not
read by the manager itself.

## Workflow

1. Select the smallest useful task context: system prompt, relevant snippets,
   and a precise instruction.
2. Classify the task before routing: use `easy` for small local tasks,
   `standard` for ordinary coding tasks, `hard` for ambiguous or
   architecture-sensitive tasks, and `agentic` for multi-step workspace coding
   tasks. Use the configured provider guidance (`routing_guidance`) to pick a
   `routing_profile` or `task_complexity` value, and set the requested model
   to match if the config does not define that profile. Pick the cheapest tier
   that can still do the task; see
   `docs/architecture/model-routing-catalog.md` for known models, their
   relative cost tier and reasoning depth, and which profile each backs.
3. Run `scripts/ollama_cluster_manager.py status_check` to inspect configured
   providers before routing.
4. Prefer an Ollama host where the requested model is already loaded. If none
   are loaded, use a reachable configured provider that has the requested model,
   ordered by priority.
5. Run `scripts/ollama_cluster_manager.py execute_task` with an allowed root and
   output path.
6. Report only metadata: status, host, model, output path, byte count, and any
   routing or write error. Do not paste the generated file content unless the
   user explicitly asks to inspect it.

## Resources

- `scripts/ollama_cluster_manager.py`: standard-library manager and CLI.
- `references/ollama_cluster_config.sample.json`: portable multi-provider config.
- `references/agent_tool_schema.json`: JSON Schema for agent tool calls.
- `references/agent_system_prompt.md`: prompt text to add to agent systems.

## Safety

Always pass `--allowed-root` for the target project. The manager rejects
absolute or relative paths that resolve outside that root before making a model
request.
