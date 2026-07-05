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
- `scripts/mcp_server.py`: optional MCP delivery adapter for MCP-only clients
  (see `docs/architecture/adr/0007-mcp-delivery-adapter.md`). Calls the same
  `OllamaClusterManager` as the CLI; adds no routing logic of its own.
- `scripts/setup_mcp_venv.sh` / `scripts/run_mcp_server.sh`: venv-based MCP
  launch for hosts that already have Python (LISS-0005).
- `Dockerfile` / `docker-compose.yml`: Docker Compose MCP launch for hosts
  without Python (LISS-0006).
- `scripts/install_skill.py`: copies the skill into a Codex skills directory.
- `scripts/setup_skill.sh`: wires the skill into Codex, Claude Code, or a custom
  skills directory.
- `references/`: sample config, tool schema, and system prompt text.
- `tests/`: unit tests with fake Ollama clients and temporary directories.

## Test

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
python3 -m py_compile scripts/ollama_cluster_manager.py scripts/install_skill.py scripts/mcp_server.py
python3 -m json.tool references/ollama_cluster_config.sample.json >/dev/null
python3 -m json.tool references/agent_tool_schema.json >/dev/null
```

`tests/test_mcp_server.py` skips itself when the optional `mcp` package (see
below) is not installed.

## Install

Install for Codex:

```sh
python3 scripts/install_skill.py
```

Set up for Claude Code or a custom skill directory:

```sh
scripts/setup_skill.sh --help
```

## MCP Server (optional)

For MCP-only clients (for example Claude Desktop, or any MCP host that does
not read agent skill packages), run the router as an MCP server instead of
installing the skill. This is additive: it does not replace the skill/CLI
path, and both read the same config file and call the same
`OllamaClusterManager`.

The server exposes two tools over stdio, `status_check` and `execute_task`,
with the same arguments and result shape as the CLI actions of the same name
and `references/agent_tool_schema.json`. See
`docs/architecture/adr/0007-mcp-delivery-adapter.md` for the design decision
and its tradeoffs.

### Option A: venv launch (Python already installed)

Point an MCP client's server "command" at `scripts/run_mcp_server.sh`. It
creates a dedicated venv at `.venv/` on first run (delegating to
`scripts/setup_mcp_venv.sh`), installs `requirements-mcp.txt` into it, and
execs `scripts/mcp_server.py`. Safe to re-run.

```sh
scripts/run_mcp_server.sh
```

Manual/no-script alternative:

```sh
pip install -r requirements-mcp.txt
python3 scripts/mcp_server.py
```

### Option B: Docker Compose launch (no local Python required)

If the host running the MCP client has no Python at all, build and run the
server in a container instead. Point the MCP client's server "command" at:

```sh
docker compose run --rm -T mcp-server
```

`-T` disables pseudo-tty allocation so stdio stays clean JSON-RPC for the
client, matching `tty: false` on the `mcp-server` service in
`docker-compose.yml`. Mount your own config/output directories as volumes;
see the comments in `docker-compose.yml` for the pattern.

## Release Archives

`.gitattributes` marks AI-agent operating files (`AGENTS.md`, `CLAUDE.md`,
`.github/copilot-instructions.md`, and the internal AI-TDD process
directories under `docs/`: `at-tdd`, `collaboration`, `templates`, `issues`,
`work-plans`, `evaluation`) as `export-ignore`. `docs/architecture` and
`docs/specs` are kept since they document the router itself. Two ways this
applies:

- GitHub Release source archives (the automatic `.zip`/`.tar.gz` GitHub
  builds from a tag) already exclude these paths — no extra step needed.
- For distributing an archive outside GitHub Releases (or vendoring into
  another project instead of adding this repo as a git submodule, which
  would NOT respect `.gitattributes`), run:

  ```sh
  scripts/build_release_archive.sh [ref]
  ```

  This wraps `git archive` (defaulting to `HEAD`) and writes
  `dist/llm-cluster-router-<short-sha>.tar.gz` and `.zip`. It reuses
  `.gitattributes` as the single source of truth for exclusions rather than
  keeping a separate list.

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
