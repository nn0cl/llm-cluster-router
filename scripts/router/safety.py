"""Output-path and generated-text safety helpers."""

import re
from pathlib import Path

from .models import PathValidationError


CODE_FENCE_PATTERN = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)


def validate_output_path(output_path, allowed_root):
    candidate = Path(output_path)
    if not candidate.is_absolute():
        candidate = allowed_root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(allowed_root)
    except ValueError as error:
        raise PathValidationError(
            f"output_path must resolve inside allowed root: {allowed_root}"
        ) from error
    return resolved


def strip_code_fence(text):
    match = CODE_FENCE_PATTERN.search(text)
    if not match:
        return text
    return match.group(1)
