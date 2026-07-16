"""Provider wire-format adapters.

Adapters translate the provider-neutral task package into provider requests and
return common text/metadata. Retry, routing, and fallback policy stay outside
this module.
"""

import importlib
import json
import os

try:
    from router.models import (
        ClusterConfigError,
        ProviderExecutionError,
        ProviderRequestError,
        RoutingError,
    )
except ModuleNotFoundError:
    from scripts.router.models import (
        ClusterConfigError,
        ProviderExecutionError,
        ProviderRequestError,
        RoutingError,
    )


def endpoint_url(base_url, path):
    return base_url.rstrip("/") + "/" + path.lstrip("/")


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
    prompt_body = build_prompt_body(task_package)
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
    if task_package.get("response_schema"):
        payload["format"] = response_schema_for_ollama(task_package["response_schema"])
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
    if task_package.get("response_schema"):
        payload["text"] = response_schema_for_responses(task_package["response_schema"])
    return payload


def build_sakana_payload(task_package):
    cache_config = task_package.get("prompt_cache", {}) or {}
    if cache_config.get("policy", "provider_managed") != "provider_managed":
        raise RoutingError("sakana prompt_cache policy must be provider_managed")
    cache_data = cache_config.get("data", {}) or {}
    input_body = {
        "stable_prefix": cache_data.get("stable_prefix", []),
        "context": task_package.get("context", []),
        "dynamic_suffix": cache_data.get("dynamic_suffix", []),
        "instruction": task_package.get("instruction", ""),
    }
    payload = {
        "model": task_package["model"],
        "instructions": task_package.get("system_prompt", ""),
        "input": [{"role": "user", "content": json.dumps(input_body, ensure_ascii=False)}],
        "metadata": {"prompt_cache_policy": "provider_managed"},
    }
    if task_package.get("options"):
        payload.update(task_package["options"])
    if task_package.get("response_schema"):
        payload["text"] = response_schema_for_responses(task_package["response_schema"])
    return payload


def build_anthropic_payload(task_package):
    payload = {
        "model": task_package["model"],
        "max_tokens": int(task_package.get("max_tokens", 4096)),
        "messages": [{"role": "user", "content": json.dumps(build_prompt_body(task_package), ensure_ascii=False)}],
    }
    if task_package.get("system_prompt"):
        payload["system"] = task_package.get("system_prompt", "")
    if task_package.get("options"):
        payload.update(task_package["options"])
    return payload


def response_schema_for_ollama(value):
    return normalize_response_schema(value)["schema"]


def response_schema_for_responses(value):
    schema = normalize_response_schema(value)
    return {
        "format": {
            "type": "json_schema",
            "name": schema["name"],
            "schema": schema["schema"],
            "strict": schema["strict"],
        }
    }


def normalize_response_schema(value):
    if not isinstance(value, dict):
        raise RoutingError("response_schema must be an object")
    name = value.get("name", "llm_result")
    schema = value.get("schema")
    if not isinstance(name, str) or not name:
        raise RoutingError("response_schema.name must be a non-empty string")
    if not isinstance(schema, dict):
        raise RoutingError("response_schema.schema must be a JSON Schema object")
    return {"name": name, "schema": schema, "strict": bool(value.get("strict", True))}


def openai_headers(host):
    return {"Authorization": f"Bearer {read_api_key(host)}"}


def anthropic_headers(host):
    return {
        "x-api-key": read_api_key(host),
        "anthropic-version": host.get("anthropic_version", "2023-06-01"),
    }


def sakana_headers(host):
    return {"Authorization": f"Bearer {read_api_key(host)}"}


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
    return "".join(
        item["text"]
        for item in response.get("content", [])
        if item.get("type") == "text" and item.get("text")
    )


def validate_response_schema(text, schema_config):
    try:
        value = json.loads(text)
    except (TypeError, ValueError) as error:
        raise ProviderRequestError(
            "provider returned invalid structured output",
            category="protocol",
            retryable=False,
            detail=str(error)[:240],
        ) from error
    schema = normalize_response_schema(schema_config)["schema"]
    validate_json_value(value, schema)
    return value


def validate_json_value(value, schema, path="$" ):
    expected = schema.get("type")
    type_matches = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }
    if expected and not type_matches.get(expected, True):
        raise ProviderRequestError(
            f"structured output schema type mismatch at {path}",
            category="schema",
            retryable=False,
        )
    if "enum" in schema and value not in schema["enum"]:
        raise ProviderRequestError(
            f"structured output schema enum mismatch at {path}",
            category="schema",
            retryable=False,
        )
    if isinstance(value, dict):
        for required in schema.get("required", []):
            if required not in value:
                raise ProviderRequestError(
                    f"structured output missing required field at {path}.{required}",
                    category="schema",
                    retryable=False,
                )
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unexpected = set(value) - set(properties)
            if unexpected:
                field = sorted(unexpected)[0]
                raise ProviderRequestError(
                    f"structured output has unexpected field at {path}.{field}",
                    category="schema",
                    retryable=False,
                )
        for key, child_schema in properties.items():
            if key in value:
                validate_json_value(value[key], child_schema, f"{path}.{key}")
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            validate_json_value(item, schema["items"], f"{path}[{index}]")


def unavailable_prompt_cache_metadata():
    return {
        "policy": "provider_managed",
        "provider_supported": False,
        "applied": False,
        "cached_tokens": None,
        "orchestration_cached_tokens": None,
    }


def ollama_metadata(response):
    return {
        "prompt_eval_count": response.get("prompt_eval_count"),
        "eval_count": response.get("eval_count"),
        "total_duration": response.get("total_duration"),
        "load_duration": response.get("load_duration"),
        "prompt_cache": unavailable_prompt_cache_metadata(),
    }


def openai_metadata(response):
    usage = response.get("usage", {})
    return {"response_id": response.get("id"), "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"), "prompt_cache": unavailable_prompt_cache_metadata()}


def anthropic_metadata(response):
    usage = response.get("usage", {})
    return {"response_id": response.get("id"), "stop_reason": response.get("stop_reason"), "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"), "prompt_cache": unavailable_prompt_cache_metadata()}


def sakana_metadata(response):
    usage = response.get("usage", {}) or {}
    details = usage.get("input_tokens_details", {}) or {}
    cached_tokens = details.get("cached_tokens")
    return {
        "response_id": response.get("id"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "prompt_cache": {
            "policy": "provider_managed",
            "provider_supported": "input_tokens_details" in usage,
            "applied": cached_tokens is not None and cached_tokens > 0,
            "cached_tokens": cached_tokens,
            "orchestration_cached_tokens": details.get("orchestration_input_cached_tokens"),
        },
    }


def _raise_model_not_found(error, model):
    if error.status_code == 404 and error.detail and "not found" in error.detail.lower():
        raise ProviderRequestError(
            f"ollama model is not installed: {model}",
            category="model_not_found",
            retryable=False,
            status_code=error.status_code,
            request_id=error.request_id,
            detail=error.detail,
            operation="generate",
            model=model,
        ) from error
    raise error


def run_codex_sdk(host, task_package):
    try:
        codex_module = importlib.import_module("openai_codex")
    except ImportError as error:
        raise ProviderExecutionError("install optional dependency first: pip install openai-codex") from error
    prompt = json.dumps(build_prompt_body(task_package), ensure_ascii=False, indent=2)
    sandbox_name = host.get("sandbox", "workspace_write")
    try:
        sandbox = getattr(codex_module.Sandbox, sandbox_name)
    except AttributeError:
        sandbox = None
    with codex_module.Codex() as codex:
        thread = codex.thread_start(model=task_package["model"], **({"sandbox": sandbox} if sandbox else {}))
        result = thread.run(prompt)
    return result.final_response, {"thread_id": getattr(result, "thread_id", None)}


def generate_provider_text(provider, host, task_package, http_client, config, codex_runner=None):
    if provider == "ollama":
        model = task_package["model"]
        try:
            response = http_client.post_json(
                endpoint_url(host["url"], "/api/generate"),
                build_ollama_payload(task_package, config),
                host.get("timeout_seconds", 30),
            )
        except ProviderRequestError as error:
            _raise_model_not_found(error, model)
        text = response.get("response", "")
        if not text:
            raise ProviderRequestError(
                "ollama returned empty response",
                category="protocol",
                retryable=False,
                operation="generate",
                model=model,
            )
        if task_package.get("response_schema"):
            validate_response_schema(text, task_package["response_schema"])
        return text, ollama_metadata(response)
    if provider == "openai":
        response = http_client.post_json(
            endpoint_url(host["url"], "/v1/responses"),
            build_openai_payload(task_package),
            host.get("timeout_seconds", 30),
            headers=openai_headers(host),
        )
        text = extract_openai_text(response)
        if task_package.get("response_schema"):
            validate_response_schema(text, task_package["response_schema"])
        return text, openai_metadata(response)
    if provider == "anthropic":
        response = http_client.post_json(
            endpoint_url(host["url"], "/v1/messages"),
            build_anthropic_payload(task_package),
            host.get("timeout_seconds", 30),
            headers=anthropic_headers(host),
        )
        return extract_anthropic_text(response), anthropic_metadata(response)
    if provider == "sakana":
        response = http_client.post_json(
            endpoint_url(host["url"], "/v1/responses"),
            build_sakana_payload(task_package),
            host.get("timeout_seconds", 30),
            headers=sakana_headers(host),
        )
        text = extract_openai_text(response)
        if task_package.get("response_schema"):
            validate_response_schema(text, task_package["response_schema"])
        return text, sakana_metadata(response)
    if provider == "codex":
        return (codex_runner or run_codex_sdk)(host, task_package)
    raise RoutingError(f"unsupported provider: {provider}")
