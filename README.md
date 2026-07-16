# LLM Cluster Router

Route compact LLM task packages across local Ollama, OpenAI-compatible APIs,
Anthropic Claude, and the local Codex SDK — then write output only inside an
allowed project root.

[日本語 README](README.ja.md)

**In one line:** a thin routing layer for agents that picks the right model
provider per task, keeps costs down, and enforces safe output paths.

## Why use this

- **Cost control:** route small tasks to free local models; escalate to paid APIs
  only when the task needs deeper reasoning.
- **Provider portability:** one task package shape and config file across
  Ollama, OpenAI, Anthropic, and Codex SDK.
- **Agent-ready delivery:** use as a CLI, agent skill, or optional MCP server
  without duplicating routing logic.

## 30-second demo

Check configured providers:

```sh
python3 scripts/ollama_cluster_manager.py status_check \
  --config references/ollama_cluster_config.sample.json
```

Run a task (set API keys only when your config uses paid providers):

```sh
python3 scripts/ollama_cluster_manager.py execute_task \
  --config references/ollama_cluster_config.sample.json \
  --allowed-root "$PWD" \
  --task-package references/example-task-package.json \
  --output-path generated/demo-output.txt
```

For development diagnostics, add `--debug`. Safe structured events are written
to stderr; `--log-file path` also writes them to a file. Logs include token
usage, provider-reported prompt-cache fields, retries, request IDs, and stack
traces on errors, but never prompt/response bodies or credentials. Optional
per-host `pricing` settings (`input_per_1m`, `cached_input_per_1m`, and
`output_per_1m`) enable an estimate; without them cost remains unavailable.
Log retention can be bounded with `--log-max-bytes` (default 10 MB) and
`--log-backup-count` (default 5 generations).

## What it does

- Accepts a compact JSON **task package** (system prompt, context snippets,
  instruction, optional routing profile).
- Selects a provider and model from config, including **profile-based
  routing** (`easy`, `standard`, `hard`, `agentic`).
- Validates the output path against `--allowed-root` **before** any model call.
- Strips a single wrapping Markdown code fence from generated text before
  writing.
- Returns metadata (provider, model, profile evidence, byte count) without
  requiring the caller to paste full generated content.

## What it does not do

- Full agent orchestration, tool planning, or multi-step workflows.
- Automatic model pricing, quota tracking, or SaaS-style governance.
- Persistence, audit databases, or team admin UI.
- Silent escalation to more expensive models without config evidence.

Routing design details: `docs/architecture/README.md`. Profile catalog:
`docs/architecture/model-routing-catalog.md`.

## Quick start

1. Clone this repository.
2. Copy `references/ollama_cluster_config.sample.json` and adjust hosts/models.
3. Set provider credentials in the environment (`OPENAI_API_KEY`,
   `ANTHROPIC_API_KEY`, etc.) when needed.
4. Run `status_check`, then `execute_task` with `--allowed-root`.

Install as an agent skill:

```sh
python3 scripts/install_skill.py
# or
scripts/setup_skill.sh --help
```

## Contents

- `SKILL.md`: agent-facing skill instructions.
- `agents/openai.yaml`: OpenAI/Codex agent metadata.
- `scripts/ollama_cluster_manager.py`: standard-library CLI and routing logic.
- `scripts/mcp_server.py`: optional MCP delivery adapter for MCP-only clients
  (see `docs/architecture/adr/0007-mcp-delivery-adapter.md`). Calls the same
  `OllamaClusterManager` as the CLI; adds no routing logic of its own.
- `scripts/setup_mcp_venv.sh` / `scripts/run_mcp_server.sh`: venv-based MCP
  launch for hosts that already have Python.
- `Dockerfile` / `docker-compose.yml`: Docker Compose MCP launch for hosts
  without Python.
- `scripts/install_skill.py`: copies the skill into a Codex skills directory.
- `scripts/setup_skill.sh`: wires the skill into Codex, Claude Code, or a custom
  skills directory.
- `references/`: sample config, tool schema, system prompt, and example task
  package.
- `tests/`: unit tests with fake Ollama clients and temporary directories.

## Test

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
python3 -m py_compile scripts/ollama_cluster_manager.py scripts/install_skill.py scripts/mcp_server.py
python3 -m json.tool references/ollama_cluster_config.sample.json >/dev/null
python3 -m json.tool references/agent_tool_schema.json >/dev/null
```

`tests/test_mcp_server.py` skips itself when the optional `mcp` package is not
installed.

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

`execute_task` always strips a single wrapping Markdown code fence
(` ```lang ... ``` `) from the generated text before writing it, since coding
models (local Ollama models especially) often wrap output that way even when
asked for raw code. Only the content of the first fenced block is kept; any
other formatting is written as-is.

## Providers

Configure providers in `references/ollama_cluster_config.sample.json` or your
own config file.

- `ollama`: local or LAN Ollama hosts. Uses `/api/ps`, `/api/tags`, and
  `/api/generate`.
- `openai`: OpenAI Responses API. Requires `OPENAI_API_KEY`.
- `anthropic`: Claude Messages API. Requires `ANTHROPIC_API_KEY` and sends the
  configured `anthropic_version`.
- `sakana`: Sakana Fugu Responses API. Uses model `fugu` by default and
  requires `SAKANA_API_KEY`. Input-token cache usage is provider-managed and
  reported when Fugu returns it.
- `codex`: local Codex Python SDK. Requires `pip install openai-codex` in the
  environment that runs the router.

Claude, Sakana, and Codex are first-class configuration targets. Add them as
`provider: "anthropic"`, `provider: "sakana"`, and `provider: "codex"` host entries with their
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
      "fugu": {"provider": "sakana", "model": "fugu"},
      "agentic": {"provider": "codex", "model": "gpt-5.4"}
    }
  }
}
```

When a task package sets `routing_profile` (or `task_complexity` as a
secondary routing hint) to a name defined under `routing.profiles`, the manager
routes the task to that profile's configured provider and model. Without a
matching profile, it routes by requested model, provider availability, and
priority. A failed selected provider is never substituted with another provider
or mock. `routing_guidance` stays descriptive-only: it helps the calling agent
pick a profile name, but the manager does not read it.

Pick a profile from the cheapest tier that can still do the task: `easy` (free
local model) first, then `standard`, `hard`, or `agentic` only when the task
needs that tier's reasoning depth. See
`docs/architecture/model-routing-catalog.md` for the known models, their
relative cost tier and reasoning depth, and which profile each one backs.

`max_retries` accepts `0` through `3` and defaults to `3`. Retryable 408/425/429
and 5xx responses, timeouts, and connection failures use bounded backoff. The
selected provider is never replaced with another provider or mock. Structured
output can be requested with a JSON Schema in `response_schema`; Ollama maps it
to `format`, while Responses-compatible providers map it to `text.format`.

Example:

```sh
OPENAI_API_KEY=... python3 scripts/ollama_cluster_manager.py \
  execute_task \
  --config references/ollama_cluster_config.sample.json \
  --allowed-root "$PWD" \
  --task-package references/example-task-package.json \
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

## Development process

This repository applies the
[llm-project-template](https://github.com/nn0cl/llm-project-template) collaboration
strategy:

- `AGENTS.md` – agent operating contract for all coding agents.
- `docs/collaboration/README.md` – collaboration template overview (English).
- `docs/collaboration/README.ja.md` – collaboration template overview
  (Japanese).
- `docs/collaboration/adoption-guide.md` – how the template is adopted here.

Feature work follows AT-TDD: accepted specs under `docs/specs/`, local issues
under `docs/issues/`, and work plans under `docs/work-plans/`.

## License

MIT License, Copyright (c) 2026 dstechnology co., ltd. See
[LICENSE](LICENSE).
