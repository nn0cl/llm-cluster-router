import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT
SCRIPT_PATH = SKILL_ROOT / "scripts" / "ollama_cluster_manager.py"


def load_manager_module():
    if not SCRIPT_PATH.exists():
        raise AssertionError(f"missing manager script: {SCRIPT_PATH}")
    spec = importlib.util.spec_from_file_location("ollama_cluster_manager", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeOllamaHttpClient:
    def __init__(self, get_responses, post_responses=None):
        self.get_responses = get_responses
        self.post_responses = post_responses or {}
        self.get_calls = []
        self.post_calls = []

    def get_json(self, url, timeout_seconds):
        self.get_calls.append((url, timeout_seconds))
        response = self.get_responses[url]
        if isinstance(response, Exception):
            raise response
        return response

    def post_json(self, url, payload, timeout_seconds):
        self.post_calls.append((url, payload, timeout_seconds))
        response = self.post_responses[url]
        if isinstance(response, Exception):
            raise response
        return response


class OllamaClusterRouterSkillTests(unittest.TestCase):
    def test_skill_artifacts_are_present_and_json_resources_parse(self):
        expected_paths = [
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "agents" / "openai.yaml",
            SKILL_ROOT / "scripts" / "ollama_cluster_manager.py",
            SKILL_ROOT / "references" / "ollama_cluster_config.sample.json",
            SKILL_ROOT / "references" / "agent_tool_schema.json",
            SKILL_ROOT / "references" / "agent_system_prompt.md",
        ]

        for path in expected_paths:
            self.assertTrue(path.exists(), f"missing skill artifact: {path}")

        with (SKILL_ROOT / "references" / "ollama_cluster_config.sample.json").open(
            encoding="utf-8"
        ) as handle:
            sample_config = json.load(handle)

        with (SKILL_ROOT / "references" / "agent_tool_schema.json").open(
            encoding="utf-8"
        ) as handle:
            tool_schema = json.load(handle)

        self.assertGreaterEqual(len(sample_config["hosts"]), 2)
        self.assertEqual(tool_schema["type"], "object")
        self.assertIn("action", tool_schema["properties"])
        self.assertIn("status_check", tool_schema["properties"]["action"]["enum"])
        self.assertIn("execute_task", tool_schema["properties"]["action"]["enum"])

    def test_status_check_aggregates_loaded_and_available_models_per_host(self):
        module = load_manager_module()
        config = {
            "hosts": [
                {"url": "http://alpha:11434", "priority": 10, "label": "alpha"},
                {"url": "http://beta:11434", "priority": 20, "label": "beta"},
            ]
        }
        http_client = FakeOllamaHttpClient(
            {
                "http://alpha:11434/api/ps": {
                    "models": [{"name": "qwen2.5-coder:7b"}]
                },
                "http://alpha:11434/api/tags": {
                    "models": [{"name": "qwen2.5-coder:7b"}, {"name": "llama3.1:8b"}]
                },
                "http://beta:11434/api/ps": {"models": []},
                "http://beta:11434/api/tags": {
                    "models": [{"name": "llama3.1:8b"}]
                },
            }
        )

        manager = module.OllamaClusterManager(config, http_client=http_client)
        status = manager.status_check()

        self.assertEqual(status["hosts"][0]["label"], "alpha")
        self.assertEqual(status["hosts"][0]["loaded_models"], ["qwen2.5-coder:7b"])
        self.assertEqual(
            status["hosts"][0]["available_models"], ["qwen2.5-coder:7b", "llama3.1:8b"]
        )
        self.assertEqual(status["hosts"][1]["label"], "beta")
        self.assertEqual(status["hosts"][1]["loaded_models"], [])
        self.assertEqual(status["hosts"][1]["available_models"], ["llama3.1:8b"])

    def test_execute_task_prefers_loaded_model_and_writes_without_returning_content(self):
        module = load_manager_module()
        config = {
            "hosts": [
                {"url": "http://cold:11434", "priority": 1, "label": "cold"},
                {"url": "http://warm:11434", "priority": 99, "label": "warm"},
            ]
        }
        http_client = FakeOllamaHttpClient(
            {
                "http://cold:11434/api/ps": {"models": []},
                "http://cold:11434/api/tags": {
                    "models": [{"name": "qwen2.5-coder:7b"}]
                },
                "http://warm:11434/api/ps": {
                    "models": [{"name": "qwen2.5-coder:7b"}]
                },
                "http://warm:11434/api/tags": {
                    "models": [{"name": "qwen2.5-coder:7b"}]
                },
            },
            {
                "http://warm:11434/api/generate": {
                    "response": "def generated():\n    return 'ok'\n"
                }
            },
        )
        task_package = {
            "model": "qwen2.5-coder:7b",
            "system_prompt": "You write small Python functions.",
            "context": [{"path": "example.py", "content": "def existing(): pass"}],
            "instruction": "Create the requested function.",
            "options": {"temperature": 0},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = module.OllamaClusterManager(
                config, http_client=http_client, allowed_root=temp_dir
            )
            result = manager.execute_task(task_package, output_path="generated/result.py")
            output_path = Path(temp_dir) / "generated" / "result.py"

            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_text(encoding="utf-8"), "def generated():\n    return 'ok'\n")
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["host"], "http://warm:11434")
            self.assertEqual(result["model"], "qwen2.5-coder:7b")
            self.assertEqual(result["bytes_written"], output_path.stat().st_size)
            self.assertNotIn("response", result)
            self.assertNotIn("content", result)

        self.assertEqual(http_client.post_calls[0][0], "http://warm:11434/api/generate")

    def test_execute_task_rejects_path_traversal_before_any_network_call(self):
        module = load_manager_module()
        config = {"hosts": [{"url": "http://alpha:11434", "priority": 1}]}
        http_client = FakeOllamaHttpClient({})
        task_package = {
            "model": "qwen2.5-coder:7b",
            "system_prompt": "local only",
            "context": [],
            "instruction": "write a file",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = module.OllamaClusterManager(
                config, http_client=http_client, allowed_root=temp_dir
            )
            with self.assertRaises(module.PathValidationError):
                manager.execute_task(task_package, output_path="../escape.py")

        self.assertEqual(http_client.get_calls, [])
        self.assertEqual(http_client.post_calls, [])

    def test_execute_task_uses_priority_when_model_is_available_but_not_loaded(self):
        module = load_manager_module()
        config = {
            "hosts": [
                {"url": "http://low:11434", "priority": 1, "label": "low"},
                {"url": "http://high:11434", "priority": 50, "label": "high"},
            ]
        }
        http_client = FakeOllamaHttpClient(
            {
                "http://low:11434/api/ps": {"models": []},
                "http://low:11434/api/tags": {"models": [{"name": "llama3.1:8b"}]},
                "http://high:11434/api/ps": {"models": []},
                "http://high:11434/api/tags": {"models": [{"name": "llama3.1:8b"}]},
            },
            {"http://high:11434/api/generate": {"response": "selected = True\n"}},
        )
        task_package = {
            "model": "llama3.1:8b",
            "system_prompt": "local only",
            "context": [],
            "instruction": "write a marker",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = module.OllamaClusterManager(
                config, http_client=http_client, allowed_root=temp_dir
            )
            result = manager.execute_task(task_package, output_path="marker.py")

        self.assertEqual(result["host"], "http://high:11434")
        self.assertEqual(http_client.post_calls[0][0], "http://high:11434/api/generate")

    def test_execute_task_fails_when_requested_model_is_not_available_anywhere(self):
        module = load_manager_module()
        config = {"hosts": [{"url": "http://alpha:11434", "priority": 1}]}
        http_client = FakeOllamaHttpClient(
            {
                "http://alpha:11434/api/ps": {"models": []},
                "http://alpha:11434/api/tags": {"models": [{"name": "llama3.1:8b"}]},
            }
        )
        task_package = {
            "model": "missing-model:latest",
            "system_prompt": "local only",
            "context": [],
            "instruction": "write a marker",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = module.OllamaClusterManager(
                config, http_client=http_client, allowed_root=temp_dir
            )
            with self.assertRaises(module.RoutingError):
                manager.execute_task(task_package, output_path="marker.py")

        self.assertEqual(http_client.post_calls, [])


if __name__ == "__main__":
    unittest.main()
