import importlib.util
import json
import os
import subprocess
import sys
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

    def post_json(self, url, payload, timeout_seconds, headers=None):
        self.post_calls.append((url, payload, timeout_seconds, headers or {}))
        response = self.post_responses[url]
        if isinstance(response, Exception):
            raise response
        return response


class LlmClusterRouterSkillTests(unittest.TestCase):
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

    def test_strip_code_fence_extracts_first_fenced_block(self):
        module = load_manager_module()

        self.assertEqual(
            module.strip_code_fence("```python\ndef add(a, b):\n    return a + b\n```"),
            "def add(a, b):\n    return a + b\n",
        )

    def test_strip_code_fence_extracts_first_block_ignoring_surrounding_prose(self):
        module = load_manager_module()

        text = "Here you go:\n```\nline one\nline two\n```\nHope that helps!"
        self.assertEqual(module.strip_code_fence(text), "line one\nline two\n")

    def test_strip_code_fence_returns_original_text_when_unfenced(self):
        module = load_manager_module()

        self.assertEqual(module.strip_code_fence("plain output\n"), "plain output\n")

    def test_execute_task_strips_code_fence_from_generated_text_before_writing(self):
        module = load_manager_module()
        config = {
            "hosts": [
                {"url": "http://warm:11434", "priority": 99, "label": "warm"},
            ]
        }
        http_client = FakeOllamaHttpClient(
            {
                "http://warm:11434/api/ps": {
                    "models": [{"name": "qwen2.5-coder:7b"}]
                },
                "http://warm:11434/api/tags": {
                    "models": [{"name": "qwen2.5-coder:7b"}]
                },
            },
            {
                "http://warm:11434/api/generate": {
                    "response": "```python\ndef add(a, b):\n    return a + b\n```"
                }
            },
        )
        task_package = {
            "model": "qwen2.5-coder:7b",
            "system_prompt": "Write concise code.",
            "context": [],
            "instruction": "Write a function.",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = module.OllamaClusterManager(
                config, http_client=http_client, allowed_root=temp_dir
            )
            manager.execute_task(task_package, output_path="result.py")
            output_path = Path(temp_dir) / "result.py"

            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "def add(a, b):\n    return a + b\n",
            )

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

    def test_execute_task_can_route_to_openai_responses_api(self):
        module = load_manager_module()
        config = {
            "hosts": [
                {
                    "provider": "openai",
                    "url": "https://api.openai.com",
                    "priority": 10,
                    "label": "openai",
                    "models": ["gpt-5.4"],
                }
            ]
        }
        http_client = FakeOllamaHttpClient(
            {},
            {
                "https://api.openai.com/v1/responses": {
                    "id": "resp_test",
                    "output_text": "openai generated\n",
                    "usage": {"input_tokens": 11, "output_tokens": 3},
                }
            },
        )
        task_package = {
            "model": "gpt-5.4",
            "system_prompt": "Write concise code.",
            "context": [{"path": "example.py", "content": "pass"}],
            "instruction": "Write a result.",
            "options": {"temperature": 0},
        }

        old_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "test-key"
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                manager = module.OllamaClusterManager(
                    config, http_client=http_client, allowed_root=temp_dir
                )
                result = manager.execute_task(task_package, output_path="openai.txt")
                output_path = Path(temp_dir) / "openai.txt"
                output_text = output_path.read_text(encoding="utf-8")
        finally:
            if old_key is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = old_key

        self.assertEqual(output_text, "openai generated\n")
        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["response_id"], "resp_test")
        self.assertEqual(http_client.post_calls[0][0], "https://api.openai.com/v1/responses")
        self.assertEqual(
            http_client.post_calls[0][3]["Authorization"], "Bearer test-key"
        )
        self.assertEqual(http_client.post_calls[0][1]["model"], "gpt-5.4")
        self.assertEqual(http_client.post_calls[0][1]["input"][0]["role"], "developer")

    def test_execute_task_can_route_to_anthropic_messages_api(self):
        module = load_manager_module()
        config = {
            "hosts": [
                {
                    "provider": "anthropic",
                    "url": "https://api.anthropic.com",
                    "priority": 10,
                    "label": "claude",
                    "models": ["claude-sonnet-4-5"],
                }
            ]
        }
        http_client = FakeOllamaHttpClient(
            {},
            {
                "https://api.anthropic.com/v1/messages": {
                    "id": "msg_test",
                    "content": [{"type": "text", "text": "claude generated\n"}],
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 13, "output_tokens": 4},
                }
            },
        )
        task_package = {
            "model": "claude-sonnet-4-5",
            "system_prompt": "Write concise code.",
            "context": [{"path": "example.py", "content": "pass"}],
            "instruction": "Write a result.",
            "max_tokens": 1024,
        }

        old_key = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                manager = module.OllamaClusterManager(
                    config, http_client=http_client, allowed_root=temp_dir
                )
                result = manager.execute_task(task_package, output_path="claude.txt")
                output_path = Path(temp_dir) / "claude.txt"
                output_text = output_path.read_text(encoding="utf-8")
        finally:
            if old_key is None:
                os.environ.pop("ANTHROPIC_API_KEY", None)
            else:
                os.environ["ANTHROPIC_API_KEY"] = old_key

        self.assertEqual(output_text, "claude generated\n")
        self.assertEqual(result["provider"], "anthropic")
        self.assertEqual(result["response_id"], "msg_test")
        self.assertEqual(
            http_client.post_calls[0][0], "https://api.anthropic.com/v1/messages"
        )
        self.assertEqual(http_client.post_calls[0][3]["x-api-key"], "test-key")
        self.assertEqual(
            http_client.post_calls[0][3]["anthropic-version"], "2023-06-01"
        )
        self.assertEqual(http_client.post_calls[0][1]["model"], "claude-sonnet-4-5")
        self.assertEqual(http_client.post_calls[0][1]["system"], "Write concise code.")

    def test_execute_task_routing_profile_selects_configured_claude_model(self):
        module = load_manager_module()
        config = {
            "hosts": [
                {
                    "provider": "ollama",
                    "url": "http://local:11434",
                    "priority": 100,
                    "label": "local",
                },
                {
                    "provider": "anthropic",
                    "url": "https://api.anthropic.com",
                    "priority": 10,
                    "label": "claude",
                    "models": ["claude-sonnet-4-5"],
                },
            ],
            "routing": {
                "profiles": {
                    "hard": {
                        "provider": "anthropic",
                        "model": "claude-sonnet-4-5",
                    }
                }
            },
        }
        http_client = FakeOllamaHttpClient(
            {
                "http://local:11434/api/ps": {
                    "models": [{"name": "qwen2.5-coder:7b"}]
                },
                "http://local:11434/api/tags": {
                    "models": [{"name": "qwen2.5-coder:7b"}]
                },
            },
            {
                "http://local:11434/api/generate": {"response": "ollama generated\n"},
                "https://api.anthropic.com/v1/messages": {
                    "id": "msg_profile",
                    "content": [{"type": "text", "text": "claude generated\n"}],
                    "usage": {"input_tokens": 13, "output_tokens": 4},
                },
            },
        )
        task_package = {
            "model": "qwen2.5-coder:7b",
            "routing_profile": "hard",
            "system_prompt": "Use the configured hard profile.",
            "context": [],
            "instruction": "Write a result.",
        }

        old_key = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                manager = module.OllamaClusterManager(
                    config, http_client=http_client, allowed_root=temp_dir
                )
                result = manager.execute_task(task_package, output_path="profile.txt")
                output_path = Path(temp_dir) / "profile.txt"
                output_text = output_path.read_text(encoding="utf-8")
        finally:
            if old_key is None:
                os.environ.pop("ANTHROPIC_API_KEY", None)
            else:
                os.environ["ANTHROPIC_API_KEY"] = old_key

        self.assertEqual(output_text, "claude generated\n")
        self.assertEqual(result["provider"], "anthropic")
        self.assertEqual(result["model"], "claude-sonnet-4-5")
        self.assertEqual(result["routing_profile"], "hard")
        self.assertEqual(
            http_client.post_calls[0][0], "https://api.anthropic.com/v1/messages"
        )
        self.assertEqual(http_client.post_calls[0][1]["model"], "claude-sonnet-4-5")

    def test_execute_task_task_complexity_selects_configured_codex_model(self):
        module = load_manager_module()
        config = {
            "hosts": [
                {
                    "provider": "ollama",
                    "url": "http://local:11434",
                    "priority": 100,
                    "label": "local",
                },
                {
                    "provider": "codex",
                    "url": "local-codex-sdk",
                    "priority": 10,
                    "label": "codex",
                    "models": ["gpt-5.4"],
                },
            ],
            "routing": {
                "profiles": {
                    "agentic": {
                        "provider": "codex",
                        "model": "gpt-5.4",
                    }
                }
            },
        }
        http_client = FakeOllamaHttpClient(
            {
                "http://local:11434/api/ps": {
                    "models": [{"name": "qwen2.5-coder:7b"}]
                },
                "http://local:11434/api/tags": {
                    "models": [{"name": "qwen2.5-coder:7b"}]
                },
            },
            {"http://local:11434/api/generate": {"response": "ollama generated\n"}},
        )
        codex_calls = []

        def fake_codex_sdk(host, task_package):
            codex_calls.append((host, task_package))
            return "codex generated\n", {"thread_id": "thread_test"}

        original_codex_sdk = module.run_codex_sdk
        module.run_codex_sdk = fake_codex_sdk
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                manager = module.OllamaClusterManager(
                    config, http_client=http_client, allowed_root=temp_dir
                )
                task_package = {
                    "model": "qwen2.5-coder:7b",
                    "task_complexity": "agentic",
                    "system_prompt": "Use the configured agentic profile.",
                    "context": [],
                    "instruction": "Write a result.",
                }
                result = manager.execute_task(task_package, output_path="codex.txt")
                output_path = Path(temp_dir) / "codex.txt"
                output_text = output_path.read_text(encoding="utf-8")
        finally:
            module.run_codex_sdk = original_codex_sdk

        self.assertEqual(output_text, "codex generated\n")
        self.assertEqual(result["provider"], "codex")
        self.assertEqual(result["model"], "gpt-5.4")
        self.assertEqual(result["task_complexity"], "agentic")
        self.assertEqual(codex_calls[0][0]["provider"], "codex")
        self.assertEqual(codex_calls[0][1]["model"], "gpt-5.4")

    def test_execute_task_without_routing_hint_preserves_current_model_routing(self):
        module = load_manager_module()
        config = {
            "hosts": [
                {"url": "http://cold:11434", "priority": 1, "label": "cold"},
                {"url": "http://warm:11434", "priority": 99, "label": "warm"},
            ],
            "routing": {
                "profiles": {
                    "hard": {
                        "provider": "anthropic",
                        "model": "claude-sonnet-4-5",
                    }
                }
            },
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
            {"http://warm:11434/api/generate": {"response": "selected = True\n"}},
        )
        task_package = {
            "model": "qwen2.5-coder:7b",
            "system_prompt": "No routing hint.",
            "context": [],
            "instruction": "write a marker",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = module.OllamaClusterManager(
                config, http_client=http_client, allowed_root=temp_dir
            )
            result = manager.execute_task(task_package, output_path="marker.py")

        self.assertEqual(result["provider"], "ollama")
        self.assertEqual(result["host"], "http://warm:11434")
        self.assertEqual(result["model"], "qwen2.5-coder:7b")
        self.assertNotIn("routing_profile", result)
        self.assertNotIn("task_complexity", result)
        self.assertEqual(http_client.post_calls[0][0], "http://warm:11434/api/generate")

    def test_execute_task_unknown_routing_profile_fails_before_provider_generation(self):
        module = load_manager_module()
        config = {
            "hosts": [
                {
                    "provider": "ollama",
                    "url": "http://local:11434",
                    "priority": 100,
                    "label": "local",
                }
            ],
            "routing": {"profiles": {}},
        }
        http_client = FakeOllamaHttpClient(
            {
                "http://local:11434/api/ps": {
                    "models": [{"name": "qwen2.5-coder:7b"}]
                },
                "http://local:11434/api/tags": {
                    "models": [{"name": "qwen2.5-coder:7b"}]
                },
            },
            {"http://local:11434/api/generate": {"response": "should not run\n"}},
        )
        task_package = {
            "model": "qwen2.5-coder:7b",
            "routing_profile": "expensive",
            "system_prompt": "Unknown profile.",
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

    def test_cli_status_check_runs_as_a_real_subprocess_with_codex_host(self):
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

            process = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "status_check", "--config", str(config_path)],
                capture_output=True,
                text=True,
            )

        self.assertEqual(process.returncode, 0, msg=process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["hosts"][0]["provider"], "codex")
        self.assertFalse(result["hosts"][0]["ok"])
        self.assertEqual(result["hosts"][0]["errors"][0]["endpoint"], "codex-sdk")


if __name__ == "__main__":
    unittest.main()
