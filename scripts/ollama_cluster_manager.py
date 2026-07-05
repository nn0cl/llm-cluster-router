#!/usr/bin/env python3
import argparse
import importlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin


class ClusterConfigError(Exception):
    pass


class PathValidationError(Exception):
    pass


class RoutingError(Exception):
    pass


class ProviderExecutionError(Exception):
    pass


class OllamaHttpClient:
    def get_json(self, url, timeout_seconds):
        request = urllib.request.Request(url, method="GET")
        return self._send(request, timeout_seconds)

    def post_json(self, url, payload, timeout_seconds, headers=None):
        body = json.dumps(payload).encode("utf-8")
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers=request_headers,
        )
        return self._send(request, timeout_seconds)

    def _send(self, request, timeout_seconds):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(str(error.reason)) from error


class OllamaClusterManager:
    def __init__(self, config, http_client=None, allowed_root=None):
        self.config = normalize_config(config)
        self.http_client = http_client or OllamaHttpClient()
        self.allowed_root = Path(allowed_root or os.getcwd()).resolve()

    @classmethod
    def from_sources(cls, config_path=None, http_client=None, allowed_root=None):
        config = load_config(config_path)
        default_root = config.get("defaults", {}).get("allowed_root")
        return cls(config, http_client=http_client, allowed_root=allowed_root or default_root)

    def status_check(self):
        hosts = []
        for host in self.config["hosts"]:
            started = time.monotonic()
            host_status = {
                "label": host.get("label", host["url"]),
                "url": host["url"],
                "provider": host["provider"],
                "priority": host["priority"],
                "loaded_models": [],
                "available_models": [],
                "loaded_model_details": [],
                "available_model_details": [],
                "ok": True,
                "errors": [],
            }
            if host["provider"] != "ollama":
                host_status["available_models"] = host.get("models", [])
                host_status["available_model_details"] = [
                    {"name": model} for model in host.get("models", [])
                ]
                credential_error = credential_status_error(host)
                if credential_error:
                    host_status["ok"] = False
                    host_status["errors"].append(credential_error)
                host_status["elapsed_ms"] = round((time.monotonic() - started) * 1000, 3)
                hosts.append(host_status)
                continue

            try:
                ps_data = self.http_client.get_json(
                    endpoint_url(host["url"], "/api/ps"), host["timeout_seconds"]
                )
                loaded_details = ps_data.get("models", [])
                host_status["loaded_model_details"] = loaded_details
                host_status["loaded_models"] = model_names(loaded_details)
            except Exception as error:
                host_status["ok"] = False
                host_status["errors"].append({"endpoint": "/api/ps", "message": str(error)})

            try:
                tags_data = self.http_client.get_json(
                    endpoint_url(host["url"], "/api/tags"), host["timeout_seconds"]
                )
                available_details = tags_data.get("models", [])
                host_status["available_model_details"] = available_details
                host_status["available_models"] = model_names(available_details)
            except Exception as error:
                host_status["ok"] = False
                host_status["errors"].append(
                    {"endpoint": "/api/tags", "message": str(error)}
                )

            host_status["elapsed_ms"] = round((time.monotonic() - started) * 1000, 3)
            hosts.append(host_status)
        return {"status": "ok", "hosts": hosts}

    def execute_task(self, task_package, output_path):
        resolved_output = self.validate_output_path(output_path)
        routed_task, routing_metadata = resolve_routing_profile(task_package, self.config)
        status = self.status_check()
        host = self.choose_host(routed_task["model"], status, routed_task.get("provider"))
        generated_text, response_metadata = self.generate_text(host, routed_task)
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        resolved_output.write_text(generated_text, encoding="utf-8")
        return build_execute_result(
            host,
            routed_task,
            resolved_output,
            routing_metadata,
            response_metadata,
        )

    def generate_text(self, host, task_package):
        provider = host["provider"]
        if provider == "ollama":
            request_payload = build_ollama_payload(task_package, self.config)
            response = self.http_client.post_json(
                endpoint_url(host["url"], "/api/generate"),
                request_payload,
                host.get("timeout_seconds", 30),
            )
            return response.get("response", ""), ollama_metadata(response)
        if provider == "openai":
            request_payload = build_openai_payload(task_package)
            response = self.http_client.post_json(
                endpoint_url(host["url"], "/v1/responses"),
                request_payload,
                host.get("timeout_seconds", 30),
                headers=openai_headers(host),
            )
            return extract_openai_text(response), openai_metadata(response)
        if provider == "anthropic":
            request_payload = build_anthropic_payload(task_package)
            response = self.http_client.post_json(
                endpoint_url(host["url"], "/v1/messages"),
                request_payload,
                host.get("timeout_seconds", 30),
                headers=anthropic_headers(host),
            )
            return extract_anthropic_text(response), anthropic_metadata(response)
        if provider == "codex":
            return run_codex_sdk(host, task_package)
        raise RoutingError(f"unsupported provider: {provider}")

    def validate_output_path(self, output_path):
        candidate = Path(output_path)
        if not candidate.is_absolute():
            candidate = self.allowed_root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.allowed_root)
        except ValueError as error:
            raise PathValidationError(
                f"output_path must resolve inside allowed root: {self.allowed_root}"
            ) from error
        return resolved

    def choose_host(self, requested_model, status, requested_provider=None):
        configured = {host["url"]: host for host in self.config["hosts"]}
        reachable = [host for host in status["hosts"] if host.get("ok")]
        if requested_provider:
            profile_host = choose_configured_profile_host(
                self.config["hosts"], requested_provider, requested_model
            )
            if profile_host:
                return profile_host
        loaded = [
            host for host in reachable if requested_model in host.get("loaded_models", [])
        ]
        if loaded:
            return configured[best_host(loaded)["url"]]

        available = [
            host for host in reachable if requested_model in host.get("available_models", [])
        ]
        if available:
            return configured[best_host(available)["url"]]

        raise RoutingError(f"model is not available on any reachable host: {requested_model}")


def load_config(config_path=None):
    if config_path:
        with Path(config_path).open(encoding="utf-8") as handle:
            return json.load(handle)
    env_hosts = os.environ.get("OLLAMA_CLUSTER_HOSTS", "").strip()
    if env_hosts:
        hosts = []
        for index, raw_url in enumerate(env_hosts.split(",")):
            url = raw_url.strip()
            if url:
                hosts.append(
                    {
                        "provider": "ollama",
                        "url": url,
                        "priority": len(hosts),
                        "label": f"env-{index + 1}",
                    }
                )
        return {"hosts": hosts}
    raise ClusterConfigError("provide --config or OLLAMA_CLUSTER_HOSTS")


def normalize_config(config):
    hosts = config.get("hosts", [])
    if not hosts:
        raise ClusterConfigError("config must include at least one host")
    normalized_hosts = []
    for index, host in enumerate(hosts):
        provider = host.get("provider", "ollama")
        if provider not in {"ollama", "openai", "anthropic", "codex"}:
            raise ClusterConfigError(f"unsupported provider: {provider}")
        url = host.get("url") or default_provider_url(provider)
        if not url:
            raise ClusterConfigError("each host must include url")
        normalized_hosts.append(
            {
                "provider": provider,
                "url": url.rstrip("/"),
                "label": host.get("label", url),
                "priority": int(host.get("priority", 0)),
                "timeout_seconds": float(host.get("timeout_seconds", 30)),
                "api_key_env": host.get("api_key_env") or default_api_key_env(provider),
                "anthropic_version": host.get("anthropic_version", "2023-06-01"),
                "models": host.get("models", []),
            }
        )
    normalized = dict(config)
    normalized["hosts"] = normalized_hosts
    return normalized


def build_execute_result(
    host,
    routed_task,
    resolved_output,
    routing_metadata,
    response_metadata,
):
    result = {
        "status": "success",
        "provider": host["provider"],
        "host": host["url"],
        "host_label": host.get("label", host["url"]),
        "model": routed_task["model"],
        "output_path": str(resolved_output),
        "bytes_written": resolved_output.stat().st_size,
    }
    result.update(routing_metadata)
    result.update(response_metadata)
    return result


def choose_configured_profile_host(hosts, requested_provider, requested_model):
    configured_hosts = [
        host
        for host in hosts
        if host["provider"] == requested_provider and host_supports_model(host, requested_model)
    ]
    if configured_hosts:
        return best_host(configured_hosts)
    return None


def host_supports_model(host, requested_model):
    return requested_model in host.get("models", [])


def resolve_routing_profile(task_package, config):
    if task_package.get("routing_profile"):
        profile_name = task_package["routing_profile"]
        metadata = {"routing_profile": profile_name}
    elif task_package.get("task_complexity"):
        profile_name = task_package["task_complexity"]
        metadata = {"task_complexity": profile_name}
    else:
        return dict(task_package), {}

    profiles = config.get("routing", {}).get("profiles", {})
    profile = profiles.get(profile_name)
    if not profile:
        raise RoutingError(f"routing profile is not configured: {profile_name}")

    provider = profile.get("provider")
    model = profile.get("model")
    if not provider or not model:
        raise RoutingError(f"routing profile must include provider and model: {profile_name}")

    routed_task = dict(task_package)
    routed_task["provider"] = provider
    routed_task["model"] = model
    return routed_task, metadata


def endpoint_url(base_url, path):
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def model_names(model_details):
    names = []
    for item in model_details:
        name = item.get("name") or item.get("model")
        if name:
            names.append(name)
    return names


def best_host(host_statuses):
    return sorted(
        host_statuses,
        key=lambda host: (-int(host.get("priority", 0)), float(host.get("elapsed_ms", 0))),
    )[0]


def default_provider_url(provider):
    return {
        "openai": "https://api.openai.com",
        "anthropic": "https://api.anthropic.com",
        "codex": "local-codex-sdk",
    }.get(provider)


def default_api_key_env(provider):
    return {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }.get(provider)


def credential_status_error(host):
    api_key_env = host.get("api_key_env")
    if api_key_env and not os.environ.get(api_key_env):
        return {
            "endpoint": "credential",
            "message": f"missing required environment variable: {api_key_env}",
        }
    if host["provider"] == "codex" and importlib.util.find_spec("openai_codex") is None:
        return {
            "endpoint": "codex-sdk",
            "message": "missing optional Python package: openai-codex",
        }
    return None


def read_api_key(host):
    api_key_env = host.get("api_key_env")
    if not api_key_env:
        return None
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise ClusterConfigError(f"missing required environment variable: {api_key_env}")
    return api_key


def build_prompt_body(task_package):
    return {
        "context": task_package.get("context", []),
        "instruction": task_package.get("instruction", ""),
    }


def build_ollama_payload(task_package, config):
    prompt_body = {
        "context": task_package.get("context", []),
        "instruction": task_package.get("instruction", ""),
    }
    payload = {
        "model": task_package["model"],
        "system": task_package.get("system_prompt", ""),
        "prompt": json.dumps(prompt_body, ensure_ascii=False, indent=2),
        "stream": False,
    }
    if task_package.get("options"):
        payload["options"] = task_package["options"]
    keep_alive = task_package.get("keep_alive") or config.get("defaults", {}).get("keep_alive")
    if keep_alive:
        payload["keep_alive"] = keep_alive
    return payload


def build_openai_payload(task_package):
    input_items = []
    if task_package.get("system_prompt"):
        input_items.append(
            {"role": "developer", "content": task_package.get("system_prompt", "")}
        )
    input_items.append(
        {
            "role": "user",
            "content": json.dumps(build_prompt_body(task_package), ensure_ascii=False),
        }
    )
    payload = {"model": task_package["model"], "input": input_items}
    if task_package.get("options"):
        payload.update(task_package["options"])
    return payload


def build_anthropic_payload(task_package):
    payload = {
        "model": task_package["model"],
        "max_tokens": int(task_package.get("max_tokens", 4096)),
        "messages": [
            {
                "role": "user",
                "content": json.dumps(build_prompt_body(task_package), ensure_ascii=False),
            }
        ],
    }
    if task_package.get("system_prompt"):
        payload["system"] = task_package.get("system_prompt", "")
    if task_package.get("options"):
        payload.update(task_package["options"])
    return payload


def openai_headers(host):
    return {"Authorization": f"Bearer {read_api_key(host)}"}


def anthropic_headers(host):
    return {
        "x-api-key": read_api_key(host),
        "anthropic-version": host.get("anthropic_version", "2023-06-01"),
    }


def extract_openai_text(response):
    if response.get("output_text"):
        return response["output_text"]
    chunks = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    return "".join(chunks)


def extract_anthropic_text(response):
    chunks = []
    for item in response.get("content", []):
        if item.get("type") == "text" and item.get("text"):
            chunks.append(item["text"])
    return "".join(chunks)


def ollama_metadata(response):
    return {
        "prompt_eval_count": response.get("prompt_eval_count"),
        "eval_count": response.get("eval_count"),
        "total_duration": response.get("total_duration"),
        "load_duration": response.get("load_duration"),
    }


def openai_metadata(response):
    usage = response.get("usage", {})
    return {
        "response_id": response.get("id"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
    }


def anthropic_metadata(response):
    usage = response.get("usage", {})
    return {
        "response_id": response.get("id"),
        "stop_reason": response.get("stop_reason"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
    }


def run_codex_sdk(host, task_package):
    try:
        codex_module = importlib.import_module("openai_codex")
    except ImportError as error:
        raise ProviderExecutionError(
            "install optional dependency first: pip install openai-codex"
        ) from error

    prompt = json.dumps(build_prompt_body(task_package), ensure_ascii=False, indent=2)
    model = task_package["model"]
    sandbox_name = host.get("sandbox", "workspace_write")
    try:
        sandbox = getattr(codex_module.Sandbox, sandbox_name)
    except AttributeError:
        sandbox = None

    with codex_module.Codex() as codex:
        if sandbox is None:
            thread = codex.thread_start(model=model)
        else:
            thread = codex.thread_start(model=model, sandbox=sandbox)
        result = thread.run(prompt)
    return result.final_response, {"thread_id": getattr(result, "thread_id", None)}


def build_parser():
    parser = argparse.ArgumentParser(description="Route tasks across local and API LLM providers.")
    parser.add_argument("action", choices=["status_check", "execute_task"])
    parser.add_argument("--config", help="Path to ollama cluster config JSON.")
    parser.add_argument("--allowed-root", help="Directory that output_path must stay inside.")
    parser.add_argument("--task-package", help="Path to task package JSON for execute_task.")
    parser.add_argument("--output-path", help="Output path for execute_task.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        manager = OllamaClusterManager.from_sources(
            config_path=args.config, allowed_root=args.allowed_root
        )
        if args.action == "status_check":
            result = manager.status_check()
        else:
            if not args.task_package or not args.output_path:
                raise ClusterConfigError("execute_task requires --task-package and --output-path")
            with Path(args.task_package).open(encoding="utf-8") as handle:
                task_package = json.load(handle)
            result = manager.execute_task(task_package, args.output_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error_type": error.__class__.__name__,
                    "message": str(error),
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
