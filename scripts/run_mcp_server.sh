#!/usr/bin/env bash
# Stable single-command launcher for the optional MCP delivery adapter
# (scripts/mcp_server.py). Point an MCP client's server "command" at this
# script. Ensures the dedicated venv exists, then execs the server over
# stdio. Any arguments are passed through to mcp_server.py unchanged.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  "${SCRIPT_DIR}/setup_mcp_venv.sh"
fi

exec "${VENV_DIR}/bin/python" "${REPO_ROOT}/scripts/mcp_server.py" "$@"
