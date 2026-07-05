# LISS-0005: MCP venv direct-launch script

## Metadata

- Local issue ID: LISS-0005
- GitHub issue: none
- Status: done
- Phase: docs-only
- Type: tooling
- Priority: medium
- Owner/agent: AI agent
- Related branch: feature/mcp-launch-options

## Summary

- Today, running `scripts/mcp_server.py` requires the caller to manually
  create a venv (or pollute a system/Homebrew Python) and
  `pip install -r requirements-mcp.txt` themselves. Add a small setup script
  that creates a dedicated local venv, installs `requirements-mcp.txt` into
  it, and gives a single stable command an MCP client config can point at.

## Acceptance Notes

- Add `scripts/setup_mcp_venv.sh`: creates (or reuses) a venv at a fixed
  path (e.g. `.venv/`), installs `requirements-mcp.txt`, is idempotent
  (safe to re-run), and fails loudly with a clear message if `python3` is not
  on `PATH` (that failure case is exactly what LISS-0006 exists for).
- Add `scripts/run_mcp_server.sh`: thin wrapper that ensures the venv exists
  (calls the setup script if not) and then execs
  `.venv/bin/python scripts/mcp_server.py`, so an MCP client can be
  configured with one stable command instead of a manual pip/venv dance.
- `.venv/` must be ignored by git.
- Update `README.md`'s "MCP Server (optional)" section to document the venv
  script as the recommended path when Python is already available locally.
- Existing `pip install -r requirements-mcp.txt` + `python3
  scripts/mcp_server.py` instructions stay as the "manual" alternative; do
  not remove them.
- No changes to `scripts/mcp_server.py`, `scripts/ollama_cluster_manager.py`,
  or any routing behavior.

## Dependencies

- Parent: none
- Depends on: none
- Blocks: none
- Related: LISS-0006 (Docker Compose launch, for hosts without Python at
  all)

## Referee Decision Points

- Resolved: use `.venv/` (the standard Python convention) rather than the
  originally proposed `.venv-mcp/`. All scripts, `.gitignore`, and docs were
  updated accordingly.

## Context

- Included: `docs/architecture/adr/0007-mcp-delivery-adapter.md`,
  `requirements-mcp.txt`, `scripts/mcp_server.py`, `README.md`'s MCP section.
- Omitted: Docker/container tooling (LISS-0006), CI changes (not required
  for a local dev convenience script).
- Assumptions: `python3` is available on the host for this issue's scripts;
  the no-Python case is explicitly LISS-0006's problem, not this one's.

## References

- Existing `scripts/setup_skill.sh` for this repo's shell-script style
  conventions (arg parsing, `--help`, POSIX `sh`/`bash` compatibility).

## Work Notes

- `scripts/run_mcp_server.sh` delegates venv creation to
  `scripts/setup_mcp_venv.sh` rather than duplicating the logic, so there is
  one place that knows how to build `.venv/`.
- `.venv/` added to `.gitignore`.

## Verification

- `bash -n scripts/setup_mcp_venv.sh` and `bash -n scripts/run_mcp_server.sh`
  passed.
- Ran `scripts/setup_mcp_venv.sh` from a clean state (`.venv/` removed
  first): created the venv and installed `requirements-mcp.txt`. Re-ran it
  immediately after: completed without recreating the venv (idempotent).
- Ran the full test suite with `.venv/bin/python -m unittest discover -s
  tests`: 16/16 passed (including `tests/test_mcp_server.py`, which only
  runs when `mcp` is installed), confirming the venv's `mcp_server.py` +
  installed `mcp` package work together.
- `scripts/run_mcp_server.sh </dev/null` exits immediately because stdin
  hits EOF right away; this is correct stdio-transport behavior for a
  server driven by a real client's stdin, not a bug in the script.
