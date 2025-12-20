from __future__ import annotations

from typing import Any, Mapping, Optional


def get_user_subject(meta: Optional[Mapping[str, Any]]) -> str:
    """
    Extract the host-provided anonymized user id from request `_meta`.

    Apps SDK reference: `_meta["openai/subject"]` is an anonymized user id hint.
    """
    if not meta:
        return "unknown"
    val = meta.get("openai/subject")
    if isinstance(val, str) and val.strip():
        return val.strip()
    return "unknown"


