import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER_PATH = REPO_ROOT / "scripts" / "mcp_server.py"

MCP_AVAILABLE = importlib.util.find_spec("mcp") is not None

if MCP_AVAILABLE:
    from mcp.server.fastmcp.exceptions import ToolError


def load_mcp_server_module():
    spec = importlib.util.spec_from_file_location("mcp_server", MCP_SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(MCP_AVAILABLE, "mcp package is not installed (see requirements-mcp.txt)")
class McpServerAdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_mcp_server_module()

    async def test_lists_status_check_and_execute_task_tools(self):
        tools = await self.module.mcp.list_tools()
        tool_names = {tool.name for tool in tools}
        self.assertEqual(tool_names, {"status_check", "execute_task"})

    async def test_status_check_tool_reaches_the_real_manager(self):
        config = {
            "hosts": [
                {
                    "provider": "codex",
                    "url": "local-codex-sdk",
                    "priority": 10,
                    "label": "codex",
                    "models": ["gpt-5.4"],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            result = await self.module.mcp.call_tool(
                "status_check", {"config_path": str(config_path), "allowed_root": temp_dir}
            )

        payload = json.loads(result[0].text)
        self.assertEqual(payload["hosts"][0]["provider"], "codex")
        self.assertFalse(payload["hosts"][0]["ok"])
        self.assertEqual(payload["hosts"][0]["errors"][0]["endpoint"], "codex-sdk")

    async def test_execute_task_tool_rejects_output_path_outside_allowed_root(self):
        config = {"hosts": [{"provider": "ollama", "url": "http://local:11434", "priority": 1}]}
        task_package = {
            "model": "qwen2.5-coder:7b",
            "system_prompt": "test",
            "context": [],
            "instruction": "write a marker",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with self.assertRaises(ToolError) as context:
                await self.module.mcp.call_tool(
                    "execute_task",
                    {
                        "task_package": task_package,
                        "output_path": "/etc/should-not-be-writable.txt",
                        "config_path": str(config_path),
                        "allowed_root": temp_dir,
                    },
                )

        self.assertIn("output_path must resolve inside allowed root", str(context.exception))


if __name__ == "__main__":
    unittest.main()
