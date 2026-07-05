#!/usr/bin/env python3
import argparse
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


class OllamaHttpClient:
    def get_json(self, url, timeout_seconds):
        request = urllib.request.Request(url, method="GET")
        return self._send(request, timeout_seconds)

    def post_json(self, url, payload, timeout_seconds):
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
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
                "priority": host["priority"],
                "loaded_models": [],
                "available_models": [],
                "loaded_model_details": [],
                "available_model_details": [],
                "ok": True,
                "errors": [],
            }
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
        status = self.status_check()
        host = self.choose_host(task_package["model"], status)
        request_payload = build_generate_payload(task_package, self.config)
        response = self.http_client.post_json(
            endpoint_url(host["url"], "/api/generate"),
            request_payload,
            host.get("timeout_seconds", 30),
        )
        generated_text = response.get("response", "")
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        resolved_output.write_text(generated_text, encoding="utf-8")
        return {
            "status": "success",
            "host": host["url"],
            "host_label": host.get("label", host["url"]),
            "model": task_package["model"],
            "output_path": str(resolved_output),
            "bytes_written": resolved_output.stat().st_size,
            "prompt_eval_count": response.get("prompt_eval_count"),
            "eval_count": response.get("eval_count"),
            "total_duration": response.get("total_duration"),
            "load_duration": response.get("load_duration"),
        }

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

    def choose_host(self, requested_model, status):
        configured = {host["url"]: host for host in self.config["hosts"]}
        reachable = [host for host in status["hosts"] if host.get("ok")]
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
                hosts.append({"url": url, "priority": len(hosts), "label": f"env-{index + 1}"})
        return {"hosts": hosts}
    raise ClusterConfigError("provide --config or OLLAMA_CLUSTER_HOSTS")


def normalize_config(config):
    hosts = config.get("hosts", [])
    if not hosts:
        raise ClusterConfigError("config must include at least one host")
    normalized_hosts = []
    for index, host in enumerate(hosts):
        url = host.get("url")
        if not url:
            raise ClusterConfigError("each host must include url")
        normalized_hosts.append(
            {
                "url": url.rstrip("/"),
                "label": host.get("label", url),
                "priority": int(host.get("priority", 0)),
                "timeout_seconds": float(host.get("timeout_seconds", 30)),
            }
        )
    normalized = dict(config)
    normalized["hosts"] = normalized_hosts
    return normalized


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


def build_generate_payload(task_package, config):
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


def build_parser():
    parser = argparse.ArgumentParser(description="Route tasks across Ollama hosts.")
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
