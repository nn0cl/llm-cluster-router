---
name: ollama-cluster-router
description: Route AI coding tasks across Ollama hosts, OpenAI API, Anthropic Claude API, or local Codex SDK. Use when Codex should select a configured model provider, send a compact JSON task package, and write generated output directly to an allowed project path without returning full generated content through the cloud-side agent.
---

# Ollama Cluster Router

Use this skill when a task should run through a configured LLM provider,
especially for code generation that can be written directly to the workspace.

## Workflow

1. Select the smallest useful task context: system prompt, relevant snippets,
   and a precise instruction.
2. Run `scripts/ollama_cluster_manager.py status_check` to inspect configured
   providers before routing.
3. Prefer an Ollama host where the requested model is already loaded. If none
   are loaded, use a reachable configured provider that has the requested model,
   ordered by priority.
4. Run `scripts/ollama_cluster_manager.py execute_task` with an allowed root and
   output path.
5. Report only metadata: status, host, model, output path, byte count, and any
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
