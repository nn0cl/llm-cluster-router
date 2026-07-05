# LLM Cluster Router

Reusable agent tooling for routing local model tasks across multiple Ollama
hosts.

The current skill package name is `ollama-cluster-router` for compatibility
with existing Codex and Claude Code skill installations. The repository name is
broader so future local LLM routing providers can be added without coupling this
tool to a single application repository.

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
the requested output path before sending any request to Ollama.
