---
name: llm-cluster-router
description: Route AI coding tasks across Ollama hosts, OpenAI API, Anthropic Claude API, or local Codex SDK. Use when Codex should select a configured model provider, send a compact JSON task package, and write generated output directly to an allowed project path without returning full generated content through the cloud-side agent.
---

# LLM Cluster Router

Use this skill when a task should run through a configured LLM provider,
especially for code generation that can be written directly to the workspace.

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

The current manager routes by requested model, provider availability, and
provider priority. `task_complexity`, `routing_profile`, and
`routing_guidance` are guidance for the calling agent until profile-based
routing is implemented in the manager.

## Workflow

1. Select the smallest useful task context: system prompt, relevant snippets,
   and a precise instruction.
2. Classify the task before routing: use `easy` for small local tasks,
   `standard` for ordinary coding tasks, `hard` for ambiguous or
   architecture-sensitive tasks, and `agentic` for multi-step workspace coding
   tasks. Use the configured provider guidance to choose the requested model.
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
