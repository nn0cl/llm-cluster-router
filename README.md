# LLM Cluster Router

Reusable agent tooling for routing model tasks across local Ollama hosts,
OpenAI-compatible API calls, Anthropic Claude API calls, and the local Codex
SDK.

The skill package name is `llm-cluster-router`, matching the broader
multi-provider scope of this repository.

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

Claude and Codex are first-class configuration targets. Add them as
`provider: "anthropic"` and `provider: "codex"` host entries with their
available `models`. The sample config also includes optional `task_profiles`
and `routing_guidance` fields so the calling skill can classify a task before
choosing the requested model.

The manager resolves profile-based routing from the config's `routing`
section:

```json
{
  "routing": {
    "default_profile": "easy",
    "profiles": {
      "easy": {"provider": "ollama", "model": "qwen2.5-coder:7b"},
      "standard": {"provider": "openai", "model": "gpt-5.4"},
      "hard": {"provider": "anthropic", "model": "claude-sonnet-4-5"},
      "agentic": {"provider": "codex", "model": "gpt-5.4"}
    }
  }
}
```

When a task package sets `routing_profile` (or `task_complexity` as a
fallback) to a name defined under `routing.profiles`, the manager routes the
task to that profile's configured provider and model. Without a matching
profile, the manager falls back to routing by requested model, provider
availability, and priority. `routing_guidance` stays descriptive-only: it
helps the calling agent pick a profile name, but the manager does not read it.

Pick a profile from the cheapest tier that can still do the task: `easy` (free
local model) first, then `standard`, `hard`, or `agentic` only when the task
needs that tier's reasoning depth. See
`docs/architecture/model-routing-catalog.md` for the known models, their
relative cost tier and reasoning depth, and which profile each one backs.

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
  "task_complexity": "agentic",
  "routing_profile": "agentic",
  "options": {}
}
```
