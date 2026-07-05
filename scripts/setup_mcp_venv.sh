#!/usr/bin/env bash
# Create (or reuse) a dedicated virtualenv for the optional MCP delivery
# adapter (scripts/mcp_server.py, see docs/architecture/adr/0007) and install
# requirements-mcp.txt into it. Safe to re-run.
#
# If python3 is not available at all, use the Docker Compose launch instead
# (see LISS-0006 / README.md "MCP Server (optional)").
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 was not found on PATH." >&2
  echo "       Use the Docker Compose launch instead: see README.md 'MCP Server (optional)'." >&2
  exit 1
fi

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  echo "creating venv: ${VENV_DIR}"
  python3 -m venv "${VENV_DIR}"
fi

echo "installing requirements-mcp.txt into ${VENV_DIR}"
"${VENV_DIR}/bin/pip" install --quiet --upgrade pip
"${VENV_DIR}/bin/pip" install --quiet -r "${REPO_ROOT}/requirements-mcp.txt"

echo "ready: ${VENV_DIR}/bin/python ${REPO_ROOT}/scripts/mcp_server.py"
