"""Standard-library HTTP transport for provider adapters."""

import json
import socket
import urllib.error
import urllib.request
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

try:
    from router.models import ProviderRequestError
except ModuleNotFoundError:
    from scripts.router.models import ProviderRequestError


def classify_http_status(status_code):
    if status_code in {401, 403}:
        return "authentication", False
    if status_code == 429:
        return "rate_limit", True
    if status_code == 529:
        return "overloaded", True
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
        try:
            retry_at = parsedate_to_datetime(str(value))
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


def provider_request_id(headers):
    return headers.get("x-request-id") or headers.get("request-id")


def safe_error_detail(raw_body):
    try:
        payload = json.loads(raw_body)
    except (TypeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    value = payload.get("error") or payload.get("message")
    if isinstance(value, dict):
        value = value.get("message") or value.get("type") or value.get("code")
    if not isinstance(value, str):
        return None
    return value[:240]


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
            category, retryable = classify_http_status(error.code)
            detail = safe_error_detail(error.read().decode("utf-8", errors="replace"))
            raise ProviderRequestError(
                f"provider request failed ({category}, HTTP {error.code})",
                category=category,
                retryable=retryable,
                status_code=error.code,
                retry_after=parse_retry_after(error.headers.get("Retry-After")),
                request_id=provider_request_id(error.headers),
                detail=detail,
            ) from error
        except (socket.timeout, TimeoutError) as error:
            raise ProviderRequestError(
                "provider request timed out",
                category="timeout",
                retryable=True,
            ) from error
        except ConnectionError as error:
            raise ProviderRequestError(
                "provider connection failed",
                category="connection",
                retryable=True,
            ) from error
        except urllib.error.URLError as error:
            raise ProviderRequestError(
                "provider connection failed",
                category="connection",
                retryable=True,
            ) from error
        except (TypeError, ValueError) as error:
            raise ProviderRequestError(
                f"provider returned invalid JSON: {error}",
                category="protocol",
                retryable=False,
            ) from error
