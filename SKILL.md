---
name: ollama-cluster-router
description: Route AI coding tasks across multiple Ollama hosts. Use when Codex should inspect Ollama cluster status, prefer hosts with the requested model already loaded in VRAM, send a compact JSON task package to local Ollama, and write generated output directly to an allowed project path without returning full generated content through the cloud-side agent.
---

# Ollama Cluster Router

Use this skill when a task should run through local Ollama machines instead of
cloud-side generation, especially for code generation that can be written
directly to the workspace.

## Workflow

1. Select the smallest useful task context: system prompt, relevant snippets,
   and a precise instruction.
2. Run `scripts/ollama_cluster_manager.py status_check` to inspect configured
   hosts before routing.
3. Prefer a host where the requested model is already loaded. If none are
   loaded, use a reachable host that has the model locally, ordered by priority.
4. Run `scripts/ollama_cluster_manager.py execute_task` with an allowed root and
   output path.
5. Report only metadata: status, host, model, output path, byte count, and any
   routing or write error. Do not paste the generated file content unless the
   user explicitly asks to inspect it.

## Resources

- `scripts/ollama_cluster_manager.py`: standard-library manager and CLI.
- `references/ollama_cluster_config.sample.json`: portable multi-host config.
- `references/agent_tool_schema.json`: JSON Schema for agent tool calls.
- `references/agent_system_prompt.md`: prompt text to add to agent systems.

## Safety

Always pass `--allowed-root` for the target project. The manager rejects
absolute or relative paths that resolve outside that root before making an
Ollama request.
