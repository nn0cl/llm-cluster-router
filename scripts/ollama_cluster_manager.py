#!/usr/bin/env python3
import argparse
import importlib
import importlib.util
import json
import os
import socket
import sys
import threading
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

try:
    from router.models import (
        ClusterConfigError,
        PathValidationError,
        ProviderExecutionError,
        ProviderRequestError,
        RoutingError,
    )
    from router.safety import strip_code_fence, validate_output_path
    from router.routing import (
        best_host,
        choose_configured_profile_host,
        host_supports_model,
        model_name_matches,
        resolve_routing_profile,
    )
    from router.observability import configure_logging, estimate_cost, safe_json_event
    from adapters import providers
    from adapters import http as provider_http
except ModuleNotFoundError:
    from scripts.router.models import (
        ClusterConfigError,
        PathValidationError,
        ProviderExecutionError,
        ProviderRequestError,
        RoutingError,
    )
    from scripts.router.safety import strip_code_fence, validate_output_path
    from scripts.router.routing import (
        best_host,
        choose_configured_profile_host,
        host_supports_model,
        model_name_matches,
        resolve_routing_profile,
    )
    from scripts.router.observability import configure_logging, estimate_cost, safe_json_event
    from scripts.adapters import providers
    from scripts.adapters import http as provider_http

OllamaHttpClient = provider_http.OllamaHttpClient


class OllamaClusterManager:
    def __init__(
        self,
        config,
        http_client=None,
        allowed_root=None,
        sleep_fn=None,
        cancel_event=None,
        event_sink=None,
        debug=False,
        logger=None,
    ):
        self.config = normalize_config(config)
        self.http_client = http_client or OllamaHttpClient()
        self.allowed_root = Path(allowed_root or os.getcwd()).resolve()
        self.sleep_fn = sleep_fn or time.sleep
        self.cancel_event = cancel_event or threading.Event()
        self.event_sink = event_sink or (lambda _event: None)
        self.logger = logger or configure_logging(debug=debug)
        self.correlation_id = None

    @classmethod
    def from_sources(
        cls,
        config_path=None,
        http_client=None,
        allowed_root=None,
        debug=False,
        log_file=None,
        log_max_bytes=10_000_000,
        log_backup_count=5,
    ):
        config = load_config(config_path)
        default_root = config.get("defaults", {}).get("allowed_root")
        return cls(
            config,
            http_client=http_client,
            allowed_root=allowed_root or default_root,
            debug=debug,
            logger=configure_logging(
                debug=debug,
                log_file=log_file,
                max_bytes=log_max_bytes,
                backup_count=log_backup_count,
            ),
        )

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
                host_status["errors"].append(
                    {
                        "endpoint": "/api/ps",
                        "message": str(error),
                        "kind": "telemetry_unavailable",
                        **provider_error_metadata(error),
                    }
                )

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
                    {
                        "endpoint": "/api/tags",
                        "message": str(error),
                        "kind": "availability_check_failed",
                        **provider_error_metadata(error),
                    }
                )

            host_status["elapsed_ms"] = round((time.monotonic() - started) * 1000, 3)
            hosts.append(host_status)
        return {"status": "ok", "hosts": hosts}

    def execute_task(self, task_package, output_path):
        self.correlation_id = uuid.uuid4().hex
        self._emit_event("waiting", task_package)
        resolved_output = self.validate_output_path(output_path)
        routed_task, routing_metadata = resolve_routing_profile(task_package, self.config)
        status = self.status_check()
        host = self.choose_host(routed_task["model"], status, routed_task.get("provider"))
        generated_text, response_metadata = self.generate_text(host, routed_task)
        generated_text = strip_code_fence(generated_text)
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        resolved_output.write_text(generated_text, encoding="utf-8")
        self._emit_event("completed", routed_task, host=host)
        return build_execute_result(
            host,
            routed_task,
            resolved_output,
            routing_metadata,
            response_metadata,
        )

    def generate_text(self, host, task_package):
        if self.correlation_id is None:
            self.correlation_id = uuid.uuid4().hex
        retry_count = host.get("max_retries", 3)
        attempt = 0
        started = time.monotonic()
        while True:
            if self.cancel_event.is_set():
                self._emit_event("cancelled", task_package, host=host, attempt=attempt + 1)
                raise ProviderExecutionError("ollama request cancelled")
            try:
                text, metadata = self._generate_text_once(host, task_package)
                metadata = dict(metadata)
                metadata["attempts"] = attempt + 1
                metadata["retries"] = attempt
                metadata["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
                metadata["cost_estimate"] = estimate_cost(metadata, host)
                self._log_event("completed", metadata, host=host, task_package=task_package)
                return text, metadata
            except Exception as error:
                self._log_exception(error, host, task_package, attempt + 1)
                if isinstance(error, (ConnectionError, TimeoutError)):
                    error = ProviderRequestError(
                        "provider connection failed",
                        category="connection",
                        retryable=True,
                        operation="generate",
                        model=task_package.get("model"),
                    )
                current_attempt = attempt + 1
                if isinstance(error, ProviderRequestError):
                    error.attempt = current_attempt
                    error.max_attempts = retry_count + 1
                    error.operation = error.operation or "generate"
                    error.model = error.model or task_package.get("model")
                if not is_retryable_provider_error(error) or attempt >= retry_count:
                    if self.cancel_event.is_set():
                        self._emit_event("cancelled", task_package, host=host, attempt=current_attempt)
                    elif attempt >= retry_count:
                        self._emit_event("exhausted", task_package, host=host, attempt=current_attempt)
                    if isinstance(error, ProviderRequestError) and attempt >= retry_count:
                        raise ProviderRequestError(
                            f"{host['provider']} request failed after {attempt} retries "
                            f"({error.category})",
                            category=error.category,
                            retryable=False,
                            status_code=error.status_code,
                            request_id=error.request_id,
                            detail=error.detail,
                            operation=error.operation,
                            model=error.model,
                            attempt=current_attempt,
                            max_attempts=retry_count + 1,
                        ) from error
                    if isinstance(error, ProviderExecutionError):
                        raise
                    raise ProviderExecutionError(
                        f"{host['provider']} request failed after {attempt} retries: {error}"
                    ) from error
                delay = error.retry_after if isinstance(error, ProviderRequestError) else None
                if delay is None:
                    delay = min(
                        host.get("retry_delay_seconds", 1.0) * (2**attempt),
                        host.get("retry_backoff_max_seconds", 30.0),
                    )
                else:
                    delay = min(delay, host.get("retry_backoff_max_seconds", 30.0))
                self.sleep_fn(delay)
                self._emit_event(
                    "retrying",
                    task_package,
                    host=host,
                    attempt=current_attempt,
                    retry_after=delay,
                )
                attempt += 1

    def _emit_event(self, state, task_package, host=None, attempt=None, retry_after=None):
        event = {
            "state": state,
            "provider": host.get("provider") if host else None,
            "model": task_package.get("model") if isinstance(task_package, dict) else None,
            "correlation_id": self.correlation_id,
            "trace_id": self.correlation_id,
            "span_id": uuid.uuid4().hex[:16],
        }
        if attempt is not None:
            event["attempt"] = attempt
        if retry_after is not None:
            event["retry_after_seconds"] = retry_after
        self.event_sink(event)
        self._log_event(
            state,
            host=host,
            task_package=task_package,
            attempt=attempt,
            retry_after_seconds=retry_after,
        )

    def _log_event(self, event_name, metadata=None, host=None, task_package=None, **fields):
        event = {"event": event_name, **fields}
        event["correlation_id"] = self.correlation_id
        event["trace_id"] = self.correlation_id
        event["span_id"] = uuid.uuid4().hex[:16]
        if host:
            event.update({"provider": host.get("provider"), "host": host.get("url"), "model": host.get("model")})
        if task_package:
            event["model"] = task_package.get("model")
        if metadata:
            event.update(metadata)
        self.logger.debug(safe_json_event(event))

    def _log_exception(self, error, host, task_package, attempt):
        event = {
            "event": "error",
            "provider": host.get("provider"),
            "host": host.get("url"),
            "model": task_package.get("model"),
            "attempt": attempt,
            "error_type": type(error).__name__,
            "message": "provider request failed",
            "correlation_id": self.correlation_id,
            "trace_id": self.correlation_id,
            "span_id": uuid.uuid4().hex[:16],
        }
        if isinstance(error, ProviderRequestError):
            event.update(provider_error_metadata(error))
            event.update({"operation": error.operation, "max_attempts": error.max_attempts})
        self.logger.exception(safe_json_event(event))

    def cancel(self):
        self.cancel_event.set()

    def clear_cancel(self):
        self.cancel_event.clear()

    def _generate_text_once(self, host, task_package):
        return providers.generate_provider_text(
            host["provider"],
            host,
            task_package,
            self.http_client,
            self.config,
            codex_runner=run_codex_sdk,
        )

    def validate_output_path(self, output_path):
        return validate_output_path(output_path, self.allowed_root)

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
            host
            for host in reachable
            if any(
                model_name_matches(requested_model, candidate)
                for candidate in host.get("loaded_models", [])
            )
        ]
        if loaded:
            return configured[best_host(loaded)["url"]]

        available = [
            host
            for host in reachable
            if any(
                model_name_matches(requested_model, candidate)
                for candidate in host.get("available_models", [])
            )
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
        if provider not in {"ollama", "openai", "anthropic", "sakana", "codex"}:
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
                "max_retries": normalize_retry_count(host.get("max_retries", 3)),
                "retry_delay_seconds": float(host.get("retry_delay_seconds", 1.0)),
                "retry_backoff_max_seconds": float(
                    host.get("retry_backoff_max_seconds", 30.0)
                ),
                "api_key_env": host.get("api_key_env") or default_api_key_env(provider),
                "anthropic_version": host.get("anthropic_version", "2023-06-01"),
                "models": host.get("models", []),
            }
        )
    normalized = dict(config)
    normalized["hosts"] = normalized_hosts
    return normalized


def normalize_retry_count(value):
    try:
        retry_count = int(value)
    except (TypeError, ValueError) as error:
        raise ClusterConfigError("max_retries must be an integer from 0 through 3") from error
    if retry_count < 0 or retry_count > 3:
        raise ClusterConfigError("max_retries must be an integer from 0 through 3")
    return retry_count


def classify_http_status(status_code):
    if status_code in {401, 403}:
        return "authentication", False
    if status_code == 429:
        return "rate_limit", True
    if status_code in {408, 425}:
        return "transient_client", True
    if 400 <= status_code < 500:
        return "invalid_request", False
    if status_code >= 500:
        return "server", True
    return "http", False


def parse_retry_after(value):
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return None


def is_retryable_provider_error(error):
    if isinstance(error, ProviderRequestError):
        return error.retryable
    return isinstance(error, (ConnectionError, TimeoutError, urllib.error.URLError))


def provider_error_metadata(error):
    if isinstance(error, ProviderRequestError):
        return {
            "category": error.category,
            "status_code": error.status_code,
            "retryable": error.retryable,
            "request_id": error.request_id,
        }
    return {"category": "connection", "status_code": None, "retryable": True}


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


def endpoint_url(base_url, path):
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def model_names(model_details):
    names = []
    for item in model_details:
        name = item.get("name") or item.get("model")
        if name:
            names.append(name)
    return names


def default_provider_url(provider):
    return {
        "openai": "https://api.openai.com",
        "anthropic": "https://api.anthropic.com",
        "sakana": "https://api.sakana.ai",
        "codex": "local-codex-sdk",
    }.get(provider)


def default_api_key_env(provider):
    return {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "sakana": "SAKANA_API_KEY",
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
    return providers.build_prompt_body(task_package)


def build_ollama_payload(task_package, config):
    return providers.build_ollama_payload(task_package, config)


def build_openai_payload(task_package):
    return providers.build_openai_payload(task_package)


def build_sakana_payload(task_package):
    return providers.build_sakana_payload(task_package)


def normalize_response_schema(value):
    return providers.normalize_response_schema(value)


def response_schema_for_ollama(value):
    return providers.response_schema_for_ollama(value)


def response_schema_for_responses(value):
    return providers.response_schema_for_responses(value)


def build_anthropic_payload(task_package):
    return providers.build_anthropic_payload(task_package)


def openai_headers(host):
    return providers.openai_headers(host)


def anthropic_headers(host):
    return providers.anthropic_headers(host)


def sakana_headers(host):
    return providers.sakana_headers(host)


def provider_request_id(headers):
    return headers.get("x-request-id") or headers.get("request-id")


def extract_openai_text(response):
    return providers.extract_openai_text(response)


def extract_anthropic_text(response):
    return providers.extract_anthropic_text(response)


def ollama_metadata(response):
    return providers.ollama_metadata(response)


def openai_metadata(response):
    return providers.openai_metadata(response)


def anthropic_metadata(response):
    return providers.anthropic_metadata(response)


def unavailable_prompt_cache_metadata():
    return providers.unavailable_prompt_cache_metadata()


def sakana_metadata(response):
    return providers.sakana_metadata(response)


def run_codex_sdk(host, task_package):
    return providers.run_codex_sdk(host, task_package)


def build_parser():
    parser = argparse.ArgumentParser(description="Route tasks across local and API LLM providers.")
    parser.add_argument("action", choices=["status_check", "execute_task"])
    parser.add_argument("--config", help="Path to ollama cluster config JSON.")
    parser.add_argument("--allowed-root", help="Directory that output_path must stay inside.")
    parser.add_argument("--task-package", help="Path to task package JSON for execute_task.")
    parser.add_argument("--output-path", help="Output path for execute_task.")
    parser.add_argument("--debug", action="store_true", help="Emit safe provider debug logs.")
    parser.add_argument("--log-file", help="Write debug logs to this file as well as stderr.")
    parser.add_argument("--log-max-bytes", type=int, default=10_000_000)
    parser.add_argument("--log-backup-count", type=int, default=5)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        manager = OllamaClusterManager.from_sources(
            config_path=args.config,
            allowed_root=args.allowed_root,
            debug=args.debug,
            log_file=args.log_file,
            log_max_bytes=args.log_max_bytes,
            log_backup_count=args.log_backup_count,
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
