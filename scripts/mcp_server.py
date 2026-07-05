#!/usr/bin/env python3
"""MCP delivery adapter for the LLM cluster router.

Exposes the same status_check and execute_task actions as
ollama_cluster_manager.py's CLI, over the Model Context Protocol, for MCP
clients that do not read the agent skill package. See
docs/architecture/adr/0007-mcp-delivery-adapter.md.

This module adds no routing, provider-selection, or validation logic of its
own; it only marshals arguments into OllamaClusterManager calls.
"""
import importlib.util
from pathlib import Path
from typing import Any, Optional

SCRIPT_DIR = Path(__file__).resolve().parent

if importlib.util.find_spec("mcp") is None:
    raise SystemExit(
        "The 'mcp' package is required to run scripts/mcp_server.py. "
        "Install it with: pip install -r requirements-mcp.txt"
    )

from mcp.server.fastmcp import FastMCP  # noqa: E402


def _load_manager_module():
    manager_path = SCRIPT_DIR / "ollama_cluster_manager.py"
    spec = importlib.util.spec_from_file_location("ollama_cluster_manager", manager_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


manager_module = _load_manager_module()

mcp = FastMCP("llm-cluster-router")


def _build_manager(config_path, allowed_root):
    return manager_module.OllamaClusterManager.from_sources(
        config_path=config_path, allowed_root=allowed_root
    )


@mcp.tool()
def status_check(
    config_path: Optional[str] = None, allowed_root: Optional[str] = None
) -> dict:
    """Inspect configured Ollama, OpenAI, Anthropic, and Codex providers."""
    return _build_manager(config_path, allowed_root).status_check()


@mcp.tool()
def execute_task(
    task_package: dict[str, Any],
    output_path: str,
    config_path: Optional[str] = None,
    allowed_root: Optional[str] = None,
) -> dict:
    """Route a task package to a configured provider and write the result."""
    return _build_manager(config_path, allowed_root).execute_task(task_package, output_path)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
