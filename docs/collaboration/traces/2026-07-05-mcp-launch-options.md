# AI Work Trace

## Request

- Date: 2026-07-05
- User request: Make the MCP server usable even on hosts without Python.
  Support a venv-based direct launch and a Docker Compose launch command.
  Necessary files and README updates are needed. Prepare local issues first,
  then implement.
- Current phase: Local issue planning (LISS-0005, LISS-0006, work plan),
  then Phase 1/2 implementation for both.

## Context Ledger

- Included: `docs/collaboration/local-issue-planning.md`,
  `docs/templates/local-issue.md`, `docs/templates/work-plan.md`,
  `docs/architecture/adr/0007-mcp-delivery-adapter.md`,
  `scripts/mcp_server.py`, `requirements-mcp.txt`, `scripts/setup_skill.sh`
  (style reference for the new shell scripts).
- Omitted: CI image publishing, container registries, and changes to
  `scripts/mcp_server.py` / `OllamaClusterManager` routing behavior (none of
  this issue's scope touches routing logic).
- Assumptions: `.venv-mcp/` is an acceptable fixed venv path (flagged as a
  Referee Decision Point in LISS-0005 rather than assumed silently).
  `python:3.12-slim` is an acceptable Docker base image (flagged similarly in
  LISS-0006).
- Open decisions: whether either launch path needs a dedicated ADR later if
  container packaging expands beyond this single-service case (not needed
  yet; this is additive tooling, not a routing/architecture change).

## Routing

- Model/assistant/tool: Local issue planning (docs-only) followed by Feature
  Path Phase 1/2 tooling work, done directly with deterministic verification
  since both issues are mechanical scripting/packaging tasks against an
  already-implemented adapter.
- Reason: The user explicitly asked for issues to be prepared before
  implementation, per this project's local-issue-planning process.
- Privacy constraints: No secrets used. No real provider credentials
  involved.

## Cost / Reasoning Control

- Operating path: docs-only planning, then Fast/Feature Path tooling.
- Files read: see Context Ledger.
- Context intentionally omitted: unrelated docs, CI publishing concerns.
- Deterministic checks used: `bash -n` on both new shell scripts,
  `docker compose config`, `docker compose build`, full unittest suite run
  through the new dedicated venv, and a real MCP client script (using the
  `mcp` SDK's `stdio_client`/`ClientSession`) driving the actual Docker
  Compose-launched server through `initialize`/`list_tools`/`call_tool`.
- Escalation reason: None beyond what ADR 0007 already established; this is
  packaging/tooling around an already-accepted adapter, not a new
  architecture decision.
- Avoided LLM work: Did not call any configured LLM provider.
- Rework caused by AI output: None.

## Referee Decisions

- Prepare LISS-0005 (venv launch) and LISS-0006 (Docker Compose launch) as
  local issues before implementing, per explicit instruction.
- Implement both in the same session once the issues existed.

## Verification

- Commands/checks:
  - `bash -n scripts/setup_mcp_venv.sh scripts/run_mcp_server.sh`
  - Ran `scripts/setup_mcp_venv.sh` from a clean state, then again
    immediately (idempotency check).
  - `PYTHONDONTWRITEBYTECODE=1 .venv-mcp/bin/python -m unittest discover -s tests`
    — 16/16 passed through the dedicated venv.
  - `docker compose config`, `docker compose build mcp-server` — both
    succeeded (Docker was available and running in this environment).
  - Wrote a throwaway MCP client script and ran a full real handshake
    (`initialize`, `list_tools`, `call_tool("status_check", ...)`) through
    `docker compose run --rm -T -v <tmp>:/config:ro mcp-server`, using a
    `codex`-only host config to avoid any live network dependency. Got the
    expected tool list and result shape.
  - Cleaned up the built image, the compose-created Docker network, and all
    scratch files after verification.
- Result: All checks passed. Both launch paths work end to end, not just by
  code review.

## Changed Files

- `docs/issues/LISS-0005-mcp-venv-launch-script.md` (new)
- `docs/issues/LISS-0006-mcp-docker-compose-launch.md` (new)
- `docs/work-plans/mcp-launch-options.md` (new)
- `scripts/setup_mcp_venv.sh` (new)
- `scripts/run_mcp_server.sh` (new)
- `Dockerfile` (new)
- `docker-compose.yml` (new)
- `.gitignore`
- `README.md`
- `docs/collaboration/traces/2026-07-05-mcp-launch-options.md` (this file)

## Next Safe Action

- Referee reviews the `.venv-mcp/` path convention and the
  `python:3.12-slim`/repo-root `Dockerfile` placement (the two flagged
  Referee Decision Points), then decides whether to commit and push.

## Follow-Up: Rename `.venv-mcp` to `.venv` (same day)

- User request: follow convention and use `.venv` instead of `.venv-mcp`;
  redo README/procedure docs; asked whether script maintenance was also
  needed.
- Answer given: yes — `scripts/setup_mcp_venv.sh` and
  `scripts/run_mcp_server.sh` both hardcode the venv path, so renaming
  required updating them, not just the docs.
- Changed: `VENV_DIR` in both scripts, `.gitignore`, `README.md`,
  `docs/issues/LISS-0005-mcp-venv-launch-script.md` (path references plus
  the Referee Decision Point marked resolved), and
  `docs/work-plans/mcp-launch-options.md`.
- Verification: removed the old real `.venv-mcp/` directory, ran
  `scripts/setup_mcp_venv.sh` from a clean state (created `.venv/`), ran it
  again immediately (idempotent, no error), and ran
  `.venv/bin/python -m unittest discover -s tests`: 16/16 passed. Confirmed
  no remaining `.venv-mcp` references outside historical trace/issue text
  describing what was originally done.
- Next safe action: Referee reviews the rename, then decides whether to
  commit and push.
