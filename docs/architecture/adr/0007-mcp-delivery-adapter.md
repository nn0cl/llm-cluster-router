# ADR 0007: Add an MCP Delivery Adapter Alongside the Existing Skill

## Status

Accepted

## Context

The router currently exposes `OllamaClusterManager` (`status_check`,
`execute_task`) through two things: a CLI entry point in
`scripts/ollama_cluster_manager.py`, and an agent skill package
(`SKILL.md` plus references) that a coding agent reads and then shells out to
that CLI. This works for agent runtimes that support the skill/markdown
convention (Claude Code, Codex-style skill directories) but not for MCP-only
hosts (for example, Claude Desktop or any other MCP client) that expect a
typed tool server rather than a shell-invoked script plus prose instructions.

The Referee asked whether the delivery approach could change from "skill" to
"MCP," and then asked to write an ADR and implement it.

`references/agent_tool_schema.json` already defines `status_check` and
`execute_task` as a JSON-Schema-shaped action/argument contract, which maps
directly onto MCP tool definitions without redesigning the contract.

## Dependency Adoption Evidence

This decision adds a new runtime dependency: the official `mcp` Python SDK
(Anthropic, PyPI package `mcp`, tested version `1.28.1`).

- Vulnerability/advisory check: no CVEs found in package metadata at
  installation time; this is the official first-party SDK for the protocol
  this project needs to speak, not a third-party reimplementation.
- Version-specific examples checked: used the `mcp.server.fastmcp.FastMCP`
  high-level API from the installed `1.28.1` package directly (imported and
  exercised in this session), not from possibly-stale prose examples.
- Troubleshooting depth: the package is actively maintained by Anthropic with
  a stable public spec (modelcontextprotocol.io); import and tool
  registration are straightforward stdlib-style Python with no exotic build
  step.
- Minimal real-file test: performed in an isolated virtualenv in this
  session — `pip install mcp` succeeded, `from mcp.server.fastmcp import
  FastMCP` succeeded. The in-repo adapter is covered by
  `tests/test_mcp_server.py`, added in this change, which registers the real
  tools and calls them in-process.
- POC feasibility/result: confirmed feasible. `FastMCP` lets a tool be
  registered with a plain Python function, so the adapter can call the
  existing `OllamaClusterManager` methods directly with no shape translation
  beyond argument/result marshaling already used by the CLI's
  `main()`.
- Clean Architecture boundary: this dependency is confined to a new delivery
  adapter file (`scripts/mcp_server.py`). It does not appear in
  `OllamaClusterManager`, `OllamaHttpClient`, or any routing/domain code.

Transitive dependencies pulled in by `mcp` (`anyio`, `httpx`, `pydantic`,
`starlette`, `uvicorn`, and others) are heavier than this project's current
stdlib-only footprint. This is a real cost of the decision, accepted because
it is the official SDK and the alternative (hand-rolling the MCP wire
protocol) is worse for correctness and maintenance.

## Decision

Add an MCP delivery adapter, `scripts/mcp_server.py`, that runs alongside
the existing CLI and skill package rather than replacing them:

- The adapter uses `mcp.server.fastmcp.FastMCP` and registers two tools,
  `status_check` and `execute_task`, with the same argument and result shape
  as the CLI actions of the same name and as
  `references/agent_tool_schema.json`.
- The adapter constructs `OllamaClusterManager` the same way the CLI does
  (`OllamaClusterManager.from_sources`) and calls the existing manager
  methods directly. It adds no new routing, provider-selection, or
  validation logic of its own.
- The adapter runs over the stdio transport by default, since the primary
  consumers are local MCP clients (Claude Desktop, Claude Code, other local
  agent runtimes), matching this project's "local-first agent tooling"
  framing. HTTP/SSE transport is not implemented by this ADR.
- `mcp` is an optional dependency, installed the same way `openai-codex`
  already is (documented `pip install` step, not a required dependency for
  the core CLI or the skill package).
- `SKILL.md` and the skill installation flow (`scripts/install_skill.py`,
  `scripts/setup_skill.sh`) are unchanged. Choosing between the skill and the
  MCP server is left to whichever agent runtime the user is configuring;
  this ADR does not deprecate either path.

## Consequences

Positive:

- MCP-only hosts can use this router without needing skill/markdown support.
- No duplicated routing logic: the MCP adapter is a thin wrapper over the
  same `OllamaClusterManager` the CLI already uses, so Clean Architecture
  boundaries (adapter -> use case, not the reverse) are preserved.
- The existing `agent_tool_schema.json` contract carries over almost as-is,
  so no new input/output contract had to be invented.

Negative:

- Adds a moderately heavy dependency tree (`anyio`, `httpx`, `pydantic`,
  `starlette`, `uvicorn`, etc.) to a project that previously required no
  third-party packages for its core CLI. This is accepted as the cost of
  speaking a real MCP server rather than reimplementing the protocol.
- Two delivery surfaces (skill+CLI, and MCP) now need to be kept in sync
  whenever `status_check` or `execute_task` behavior changes. Both call the
  same manager methods, so behavior drift risk is low, but wording/response
  shape in each surface's own docs can still drift.
- This project still has no dependency manager or lockfile (see
  CLAUDE.md "Current Non-Decisions"). The `mcp` dependency is declared in a
  new `requirements-mcp.txt` file rather than a full package-manager
  adoption, which is itself a scoped, reversible choice, not a resolution of
  that broader non-decision.

## Enforcement

Code review should reject:

- Routing, provider-selection, or output-path-validation logic written
  directly inside `scripts/mcp_server.py` instead of in
  `OllamaClusterManager`.
- MCP tool argument or result shapes that diverge from
  `references/agent_tool_schema.json` without updating that schema and this
  ADR together.
- Making `mcp` a required import for `scripts/ollama_cluster_manager.py` or
  any test that does not specifically test the MCP adapter.
- Removing or degrading the existing skill/CLI path as part of adding MCP
  support.
