"""Safe debug logging and usage-cost observability helpers."""

import json
import logging
import logging.handlers
import os
import re
import sys
from urllib.parse import urlsplit, urlunsplit


LOGGER_NAME = "llm_cluster_router"


def configure_logging(debug=False, log_file=None, max_bytes=10_000_000, backup_count=5):
    logger = logging.getLogger(LOGGER_NAME)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    logger.setLevel(logging.DEBUG if debug else logging.WARNING)
    logger.propagate = False
    if debug:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        if log_file:
            try:
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
                try:
                    os.chmod(log_file, 0o600)
                except OSError:
                    pass
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except (OSError, TypeError, ValueError):
                logger.warning("debug log file is unavailable; continuing with stderr only")
    return logger


def safe_json_event(event):
    """Serialize only already-sanitized metadata; never include payload bodies."""
    allowed = {
        "event", "state", "provider", "host", "model", "operation", "request_id",
        "correlation_id", "trace_id", "span_id", "duration_ms",
        "category", "status_code", "retryable", "attempt", "max_attempts",
        "retry_after_seconds", "input_tokens", "output_tokens", "prompt_cache",
        "cost_estimate", "error_type", "message",
    }
    safe_event = {key: value for key, value in event.items() if key in allowed}
    if "host" in safe_event:
        safe_event["host"] = safe_host(safe_event["host"])
    if "message" in safe_event:
        safe_event["message"] = "provider request failed"
    return json.dumps(safe_event, ensure_ascii=False, default=str, separators=(",", ":"))


def safe_host(value):
    """Keep scheme/authority/path while dropping query and fragment secrets."""
    try:
        parsed = urlsplit(str(value))
        hostname = parsed.hostname or ""
        authority = hostname
        if parsed.port:
            authority = f"{hostname}:{parsed.port}"
        return urlunsplit((parsed.scheme, authority, "", "", ""))
    except (TypeError, ValueError):
        return "redacted"


def estimate_cost(metadata, host):
    pricing = host.get("pricing") or {}
    input_tokens = metadata.get("input_tokens")
    output_tokens = metadata.get("output_tokens")
    if not pricing or input_tokens is None or output_tokens is None:
        return {
            "available": False,
            "basis": "configured_rates",
            "currency": pricing.get("currency", "USD") if pricing else "USD",
        }
    cached_tokens = (metadata.get("prompt_cache") or {}).get("cached_tokens") or 0
    input_rate = pricing.get("input_per_1m")
    cached_rate = pricing.get("cached_input_per_1m", input_rate)
    output_rate = pricing.get("output_per_1m")
    rates = (input_rate, cached_rate, output_rate)
    if any(rate is None or not isinstance(rate, (int, float)) or rate < 0 for rate in rates):
        return {"available": False, "basis": "configured_rates", "currency": pricing.get("currency", "USD")}
    uncached_tokens = max(0, input_tokens - cached_tokens)
    amount = (uncached_tokens * input_rate + cached_tokens * cached_rate + output_tokens * output_rate) / 1_000_000
    return {
        "available": True,
        "basis": "configured_rates",
        "confidence": "estimate_only",
        "currency": pricing.get("currency", "USD"),
        "estimated_amount": round(amount, 8),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
    }
