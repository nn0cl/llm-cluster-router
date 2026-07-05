# Work Plan: MCP Launch Options (venv and Docker Compose)

## Goal

- Give the MCP server (`scripts/mcp_server.py`, ADR 0007) two documented,
  supported ways to start it: a venv-based direct launch for hosts that
  already have Python, and a Docker Compose launch for hosts that do not.

## Scope

- In:
  - `scripts/setup_mcp_venv.sh` / `scripts/run_mcp_server.sh` (LISS-0005).
  - `Dockerfile` / `docker-compose.yml` for the MCP server (LISS-0006).
  - README updates documenting both launch commands.
- Out:
  - Changing `scripts/mcp_server.py` or `OllamaClusterManager` behavior.
  - Publishing a container image to a registry or adding CI image builds.
  - Removing or deprecating the existing manual
    `pip install -r requirements-mcp.txt` instructions.

## Issue Graph

| Issue | Status | Depends on | Blocks | Branch |
| --- | --- | --- | --- | --- |
| LISS-0005 | done | - | - | feature/mcp-launch-options |
| LISS-0006 | done | - | - | feature/mcp-launch-options |

## Recommended Order

1. LISS-0005 (venv scripts) and LISS-0006 (Docker Compose) are independent;
   implement in either order. This session implements both since the
   Referee asked for both together.
2. Update `README.md`'s "MCP Server (optional)" section once both launch
   paths are verified.

## Current Next Issue

- None. Both LISS-0005 and LISS-0006 are implemented and verified
  end to end (see each issue's Verification section).
- Resolved by Referee: venv path changed from `.venv-mcp/` to the standard
  `.venv/` convention.
- Still open for Referee review: the `python:3.12-slim` base image /
  repo-root `Dockerfile` placement, used without a prior ADR since it does
  not change routing behavior or Clean Architecture boundaries.

## Risks

- `docker compose run` must not allocate a TTY, or the MCP client will see
  garbled stdio instead of clean JSON-RPC.
- A venv script that silently no-ops on failure would hide the "Python not
  available" case LISS-0006 exists to solve; it must fail loudly instead.
- Two new launch paths are two more places that can drift from
  `scripts/mcp_server.py`'s actual argument/tool contract if not verified
  end to end rather than just reviewed as text.

## Verification Plan

- `bash -n scripts/setup_mcp_venv.sh scripts/run_mcp_server.sh`
- `docker compose config`
- `docker compose build mcp-server`
- A real `status_check` call through both the venv launch and the Docker
  Compose launch, using a `codex`-only host config (no live network
  dependency), before marking either issue done.
