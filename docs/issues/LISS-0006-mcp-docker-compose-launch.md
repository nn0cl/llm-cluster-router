# LISS-0006: MCP Docker Compose launch (no local Python required)

## Metadata

- Local issue ID: LISS-0006
- GitHub issue: none
- Status: done
- Phase: docs-only
- Type: tooling
- Priority: medium
- Owner/agent: AI agent
- Related branch: feature/mcp-launch-options

## Summary

- Some hosts running an MCP client (for example a locked-down machine, or a
  host where the Referee does not want to manage a Python install) have no
  Python at all. Add a container image and a `docker compose` command that
  an MCP client can invoke as its server "command," so the only local
  requirement is Docker.

## Acceptance Notes

- Add a `Dockerfile` (repo root) that installs `requirements-mcp.txt` into a
  slim Python base image and runs `scripts/mcp_server.py` as its entrypoint.
- Add `docker-compose.yml` (repo root) defining an `mcp-server` service built
  from that `Dockerfile`.
  - Must NOT allocate a TTY (`tty: false` / no `-t`) so stdio stays clean
    JSON-RPC for the MCP client. `stdin_open: true` is required so stdin
    stays open for a one-shot `docker compose run`.
  - Mount whatever config/allowed-root directories the caller needs as
    volumes, documented with a concrete example (do not hardcode the
    Referee's own local paths from this session).
- Document the exact launch command in `README.md`'s "MCP Server (optional)"
  section, in the form an MCP client config's `command`/`args` would use,
  e.g. `docker compose run --rm -T mcp-server` (`-T` disables pseudo-tty
  allocation on the client side of `run`, matching the service's own
  `tty: false`).
- Verify locally (Docker is available and running in this session's
  environment): build the image, run the compose command, and confirm the
  MCP tool list / a `status_check` call actually completes through the
  container before calling this done.
- Keep the existing skill/CLI and the LISS-0005 venv path unchanged; this is
  a third, additive way to run the same `scripts/mcp_server.py`.

## Dependencies

- Parent: none
- Depends on: none (implementable independently of LISS-0005)
- Blocks: none
- Related: LISS-0005 (venv launch, for hosts that do have Python)

## Referee Decision Points

- Confirm image base (a slim official Python image) and that adding a
  `Dockerfile`/`docker-compose.yml` to the repo root (rather than a
  subdirectory) is acceptable, since this project currently has no other
  container tooling and no ADR yet governs container packaging.

## Context

- Included: `docs/architecture/adr/0007-mcp-delivery-adapter.md`,
  `requirements-mcp.txt`, `scripts/mcp_server.py`, `references/*`, README's
  MCP section.
- Omitted: CI image publishing/registry (out of scope; local build only
  unless the Referee asks for a published image later).
- Assumptions: local `docker compose build` + `run` is sufficient; no image
  registry or CI publishing step is being added by this issue.

## References

- Docker Compose `run` vs `up` semantics for one-shot, stdio-attached
  processes (verified locally in this session, not just from memory).

## Work Notes

- Base image: `python:3.12-slim`. The image only copies `scripts/` and
  `references/`; it does not include `docs/` or `tests/`.
- `docker-compose.yml` ships with `volumes`/`environment` left as commented
  examples rather than a hardcoded path, since the right mount depends on
  where the caller keeps their own config/output directories.

## Verification

- `docker compose config`: valid.
- `docker compose build mcp-server`: succeeded (Docker was available and the
  daemon running in this session's environment).
- Full real end-to-end check: wrote a small MCP client script (using the
  `mcp` SDK's `stdio_client` + `ClientSession`, the same package the server
  uses) that ran
  `docker compose run --rm -T -v <tmp-config-dir>:/config:ro mcp-server` as
  its subprocess, then called `initialize`, `list_tools`, and
  `call_tool("status_check", {"config_path": "/config/config.json", ...})`
  against a `codex`-only host config (no live network dependency). Got back
  `tools: ['status_check', 'execute_task']` and the expected `ok: false` /
  `codex-sdk` result — the same shape `tests/test_mcp_server.py` asserts for
  the in-process adapter, now confirmed working through Docker Compose's
  actual stdio wire protocol.
- Cleaned up the built image, the compose-created network, and the scratch
  test files after verification; nothing left running.
