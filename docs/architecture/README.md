# Architecture Overview

This project uses Clean Architecture as a direction for future changes while
preserving the existing lightweight Python CLI and agent skill package.

The runtime assumption is local-first agent tooling with optional external
provider calls. The router runs locally, reads provider configuration from a
file or environment, checks configured providers, sends compact task packages
to the selected provider, and writes generated output only inside the
caller-provided allowed root.

The selected stack today is Python 3 standard-library CLI code plus portable
agent skill metadata and shell setup scripts. There is no front-end framework,
application datastore, secondary datastore, or migration tool currently.

## Layers

### Domain

Pure router behavior, such as task package routing decisions, provider
selection policy, output-path safety, and metadata reporting.

Must not depend on:

- any UI framework.
- SQL schemas, ORM structs, vector DB SDKs, or file-system APIs.
- LLM SDKs, cloud AI SDKs, or third-party provider APIs.

### UseCase

Coordinates domain behavior through ports.

Current use-case candidates reflected by the existing CLI:

- Check configured provider status.
- Execute a task package through a selected provider.
- Install or set up the skill package for an agent runtime.

### Ports

Interfaces owned by the application core.

Ports isolate every external resource named in `CLAUDE.md` / `AGENTS.md`
under "External Resources Must Be Ports".

Current port candidates:

- Provider configuration input.
- Secret and environment access.
- Provider status and generation.
- Output file writing under an allowed root.
- Optional SDK availability checks.

### Adapters

Framework and infrastructure implementations.

Adapters may use framework APIs, infrastructure libraries, DB or vector DB
SDKs, external file layouts, API clients, and provider SDKs.

Adapters must not define business policy.

Current adapter candidates:

- Ollama HTTP adapter for `/api/ps`, `/api/tags`, and `/api/generate`.
- OpenAI-compatible Responses API adapter.
- Anthropic Messages API adapter.
- Local Codex SDK adapter.
- Filesystem output adapter.
- Skill installation adapters for Codex, Claude Code, and custom skill
  directories.

### Front-End / Delivery

The delivery layer is CLI plus agent skill metadata, plus an optional MCP
server adapter (`scripts/mcp_server.py`, see
`docs/architecture/adr/0007-mcp-delivery-adapter.md`) for MCP-only clients.
All three parse their own transport's arguments, invoke the same
`OllamaClusterManager` router behavior, and return metadata results.

It must not own:

- confidence, trust, or merge policy for AI-derived data.
- validation or secret-storage policy.
- any policy that belongs in a use case.

## Runtime Direction

- Runs on a local developer or agent machine.
- Local or LAN Ollama hosts are optional and replaceable runtime services.
- OpenAI-compatible and Anthropic-compatible HTTP APIs are optional and
  replaceable external providers.
- The local Codex SDK adapter is optional and replaceable.
- Provider credentials are secret inputs and must not be committed, logged, or
  copied into AI payloads.
- Generated model output is untrusted text until reviewed by the caller.
- Output writes must remain inside the caller-provided allowed root.

## Selected Technology

- Runtime/shell: local CLI plus POSIX shell setup script.
- Application language: Python 3.
- UI framework: none currently.
- Package manager: none required for the current standard-library manager.
- Optional dependency: `openai-codex` for the local Codex SDK adapter.
- Optional dependency: `mcp` (`requirements-mcp.txt`) for the MCP delivery
  adapter.
- Distribution goal: portable skill package installable into Codex, Claude
  Code, or custom skill directories.

## Detailed Rules

- `project-structure.md`: where files belong.
- `testing-strategy.md`: AT-TDD test placement.
- `implementation-readiness.md`: checklist before coding.
- `dependency-policy.md`: package dependency checking policy.
- `ai-request-routing.md`: AI payload selection and task routing.
- `io-reasoning-contracts.md`: AI input/output/reasoning contracts.
- Provider-specific architecture documents should be added only when a
  specification, ADR, or Referee decision requires them.

## Remaining Technology Evaluation

These choices are intentionally open and must not be assumed by agents:

- Whether to keep the current single-file manager or split it into explicit
  domain, use-case, port, adapter, and delivery modules.
- Whether OpenAI, Anthropic, Codex SDK, and Ollama are all long-term supported
  providers or some are experimental compatibility adapters.
- Which concrete model names are recommended for production use.
- Whether to adopt a Python dependency manager, packaging metadata, or
  distribution format.
- Whether to add import-boundary tooling for Python.
- Whether the project should ever introduce persistence. Until an ADR says
  otherwise, assume no application datastore.
- Whether to create provider-specific architecture documents beyond this
  overview.
