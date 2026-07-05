# AI Work Trace

## Request

- Date: 2026-07-05
- User request: First asked, exploratorily, whether the skill implementation
  could change to MCP. After a short recommendation (add MCP alongside the
  skill, not replace it), the user asked to write an ADR and implement MCP.
- Current phase: Architecture Path (ADR) followed by Phase 1/2 implementation
  of a new delivery adapter.

## Context Ledger

- Included: `docs/architecture/README.md`, `docs/architecture/dependency-policy.md`,
  `docs/collaboration/ai-human-scheme.md`, `docs/architecture/ai-request-routing.md`,
  `docs/architecture/testing-strategy.md`, `references/agent_tool_schema.json`,
  `scripts/ollama_cluster_manager.py`, existing tests, and prior ADRs
  0001-0006 for numbering/style.
- Omitted: front-end docs (not applicable), private data, real provider
  network calls beyond the earlier session's OpenAI/Anthropic connectivity
  check (not repeated here).
- Assumptions: MCP is additive, not a replacement for the skill/CLI path
  (proposed earlier in conversation; the user did not object). Stdio
  transport is the default (matches "local-first agent tooling" framing);
  HTTP/SSE transport is out of scope for this ADR.
- Open decisions: none blocking; ADR 0007 documents the dependency-weight
  tradeoff of pulling in `mcp` and its transitive dependencies as a known,
  accepted cost.

## Routing

- Model/assistant/tool: Architecture Path (ADR) followed by Feature Path
  Phase 1/2 for the new adapter, done in one pass since the user directed
  both steps explicitly.
- Reason: New delivery mechanism and new external dependency both require an
  ADR per CLAUDE.md's Referee Interaction and Decision Gates rules.
- Privacy constraints: No secrets used. No real provider credentials touched
  in this task (unrelated to the earlier OpenAI/Anthropic key exposure
  incident in this session).

## Dependency Adoption (mcp package)

Performed a real POC, not just documentation review, before adopting the
dependency:

- Created an isolated virtualenv in the scratch directory (not the project).
- `pip install mcp` succeeded (network access confirmed available in this
  environment); resolved version `1.28.1`.
- Imported `mcp.server.fastmcp.FastMCP`, registered two toy tools, and
  confirmed: (a) the `@mcp.tool()` decorator returns the original callable
  unchanged, (b) `await mcp.list_tools()` and `await mcp.call_tool(...)` work
  end to end, (c) dict-returning tools serialize to JSON text content
  automatically, (d) exceptions raised inside a tool surface as
  `mcp.server.fastmcp.exceptions.ToolError`.
- Full evidence recorded in ADR 0007's "Dependency Adoption Evidence"
  section.
- Deleted the scratch virtualenv after the POC and after running the real
  in-repo tests against it once more for final confirmation.

## Cost / Reasoning Control

- Operating path: Architecture Path (ADR) then Feature Path Phase 1/2.
- Files read: see Context Ledger.
- Context intentionally omitted: unrelated docs, private data.
- Deterministic checks used: JSON validation, Python compile checks,
  `install_skill.validate_source`, and two full unittest runs (one without
  `mcp` installed to confirm graceful skip, one inside the scratch venv with
  `mcp` installed to confirm the adapter actually works end to end).
- Escalation reason: New delivery mechanism, new third-party dependency, and
  a Referee-directed architecture decision all require Architecture Path.
- Avoided LLM work: Did not call any configured LLM provider for this task.
- Rework caused by AI output: None.

## Referee Decisions

- Write ADR 0007 and implement the MCP delivery adapter, additive to the
  existing skill/CLI, per explicit Referee instruction.

## Verification

- Commands/checks:
  - `python3 -m py_compile scripts/ollama_cluster_manager.py scripts/install_skill.py scripts/mcp_server.py tests/test_mcp_server.py tests/test_ollama_cluster_router_skill.py`
  - `python3 -m json.tool references/ollama_cluster_config.sample.json`
  - `python3 -m json.tool references/agent_tool_schema.json`
  - `install_skill.validate_source(Path("."))` called directly.
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` — 16
    tests, 3 skipped (mcp not installed in the main environment), 0 failures.
  - Same command re-run inside the scratch venv with `mcp` installed — 16
    tests, 0 skipped, 0 failures.
- Result: All checks passed in both configurations.

## Changed Files

- `docs/architecture/adr/0007-mcp-delivery-adapter.md` (new)
- `scripts/mcp_server.py` (new)
- `tests/test_mcp_server.py` (new)
- `requirements-mcp.txt` (new)
- `docs/architecture/README.md`
- `README.md`
- `SKILL.md`
- `.github/workflows/ci.yml`
- `docs/collaboration/traces/2026-07-05-mcp-delivery-adapter.md` (this file)

## Next Safe Action

- Referee reviews ADR 0007's dependency-weight tradeoff and the additive
  (not replacing) decision, then decides whether to commit and push.
