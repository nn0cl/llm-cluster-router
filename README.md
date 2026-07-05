# LLM Cluster Router

Reusable agent tooling for routing model tasks across local Ollama hosts,
OpenAI-compatible API calls, Anthropic Claude API calls, and the local Codex
SDK.

The current skill package name is `ollama-cluster-router` for compatibility
with existing Codex and Claude Code skill installations. The repository name is
broader because the router can now target multiple LLM providers.

## Contents

- `SKILL.md`: agent-facing skill instructions.
- `agents/openai.yaml`: OpenAI/Codex agent metadata.
- `scripts/ollama_cluster_manager.py`: standard-library CLI and routing logic.
- `scripts/install_skill.py`: copies the skill into a Codex skills directory.
- `scripts/setup_skill.sh`: wires the skill into Codex, Claude Code, or a custom
  skills directory.
- `references/`: sample config, tool schema, and system prompt text.
- `tests/`: unit tests with fake Ollama clients and temporary directories.

## Test

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_ollama_cluster_router_skill.py
python3 -m py_compile scripts/ollama_cluster_manager.py scripts/install_skill.py
python3 -m json.tool references/ollama_cluster_config.sample.json >/dev/null
python3 -m json.tool references/agent_tool_schema.json >/dev/null
```

## Install

Install for Codex:

```sh
python3 scripts/install_skill.py
```

Set up for Claude Code or a custom skill directory:

```sh
scripts/setup_skill.sh --help
```

## Safety

Always pass `--allowed-root` when running `execute_task`. The manager validates
the requested output path before sending any model request.

## Providers

Configure providers in `references/ollama_cluster_config.sample.json` or your
own config file.

- `ollama`: local or LAN Ollama hosts. Uses `/api/ps`, `/api/tags`, and
  `/api/generate`.
- `openai`: OpenAI Responses API. Requires `OPENAI_API_KEY`.
- `anthropic`: Claude Messages API. Requires `ANTHROPIC_API_KEY` and sends the
  configured `anthropic_version`.
- `codex`: local Codex Python SDK. Requires `pip install openai-codex` in the
  environment that runs the router.

Example:

```sh
OPENAI_API_KEY=... python3 scripts/ollama_cluster_manager.py \
  execute_task \
  --config references/ollama_cluster_config.sample.json \
  --allowed-root "$PWD" \
  --task-package /path/to/task.json \
  --output-path generated/result.txt
```

Task package shape:

```json
{
  "model": "gpt-5.4",
  "system_prompt": "Write concise, reviewable code.",
  "context": [{"path": "example.py", "content": "def existing(): pass"}],
  "instruction": "Create the requested function.",
  "options": {}
}
```
