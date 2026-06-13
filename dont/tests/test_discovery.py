"""Tests for hybrid category discovery."""

from __future__ import annotations

import json
import logging
from typing import Any

from core.discovery import _FALLBACK_CATEGORY_KEYWORDS, classify_links_by_category


class FakeExtractor:
    """Minimal extractor test double for cached LLM calls."""

    def __init__(self, response: str | Exception) -> None:
        self.response = response
        self.calls = 0

    def call_cached(self, cache_key: str, system: str, user: str) -> str:
        self.calls += 1
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_classify_links_by_category_uses_llm_mapping() -> None:
    """Successful LLM classification returns normalized category mappings."""

    links = [
        ("https://example.edu/about", "About us"),
        ("https://example.edu/fees", "Tuition and fees"),
        ("https://example.edu/courses", "Course catalog"),
    ]
    payload: dict[str, Any] = {
        "about": ["https://example.edu/about"],
        "tuition": ["https://example.edu/fees"],
        "courses": ["https://example.edu/courses"],
    }
    extractor = FakeExtractor(json.dumps(payload))

    result = classify_links_by_category(links, extractor)

    assert result["about"] == ["https://example.edu/about"]
    assert result["tuition"] == ["https://example.edu/fees"]
    assert result["courses"] == ["https://example.edu/courses"]
    assert extractor.calls == 1


def test_classify_links_by_category_falls_back_on_llm_failure(caplog: Any) -> None:
    """LLM errors trigger keyword fallback and log a warning."""

    links = [
        ("https://example.edu/admissions/tuition", "Tuition and fees"),
        ("https://example.edu/academics/catalog", "Course catalog"),
    ]
    extractor = FakeExtractor(RuntimeError("rate limited"))

    with caplog.at_level(logging.WARNING):
        result = classify_links_by_category(links, extractor)

    assert "tuition" in _FALLBACK_CATEGORY_KEYWORDS
    assert result["tuition"] == ["https://example.edu/admissions/tuition"]
    assert result["courses"] == ["https://example.edu/academics/catalog"]
    assert "keyword fallback" in caplog.text

