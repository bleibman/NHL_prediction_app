"""Simple in-memory TTL cache for API responses."""

import time
from typing import Any

_cache: dict[str, tuple[float, Any]] = {}

DEFAULT_TTL = 1800  # 30 minutes


def get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    expires, value = entry
    if time.time() > expires:
        del _cache[key]
        return None
    return value


def set(key: str, value: Any, ttl: int = DEFAULT_TTL):
    _cache[key] = (time.time() + ttl, value)


def invalidate():
    _cache.clear()
