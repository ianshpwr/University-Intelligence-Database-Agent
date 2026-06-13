"""Small cache helpers reserved for future fetch-content hashing."""

from __future__ import annotations

import hashlib


def content_hash(content: str) -> str:
    """Return a stable SHA-256 hash for text content."""

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def get(_key: str) -> None:
    """Placeholder cache get hook for future integration."""

    return None


def set(_key: str, _value: str) -> None:
    """Placeholder cache set hook for future integration."""

    return None

