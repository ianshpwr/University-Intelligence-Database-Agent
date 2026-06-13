"""Tests for parser cleanup and link detection."""

from datetime import datetime, timezone
from pathlib import Path

from core.fetcher import FetchResult
from core.parser import parse


def test_parser_cleans_noise_and_detects_course_links() -> None:
    """Parser removes chrome and finds next/detail links."""

    html = Path("tests/fixtures/courses.html").read_text(encoding="utf-8")
    result = FetchResult(
        url="https://example.edu/academics/courses",
        html=html,
        status_code=200,
        fetched_via="httpx",
        fetched_at=datetime.now(timezone.utc),
    )
    parsed = parse(result, "courses")
    assert "Global navigation" not in parsed.clean_text
    assert "Footer text" not in parsed.clean_text
    assert parsed.next_page_url == "https://example.edu/academics/courses?page=2"
    assert "https://example.edu/courses/cs101" in parsed.discovered_links
    assert "https://example.edu/academics/catalog/math201" in parsed.discovered_links


def test_parser_listing_without_pagination_stays_terminal(monkeypatch) -> None:
    """Rules and LLM fallback returning None should not invent a next page."""

    html = Path("tests/fixtures/no_pagination.html").read_text(encoding="utf-8")
    result = FetchResult(
        url="https://example.edu/academics/courses",
        html=html,
        status_code=200,
        fetched_via="httpx",
        fetched_at=datetime.now(timezone.utc),
    )
    monkeypatch.setattr("core.parser.llm_detect_pagination", lambda snippet, url, extractor: None)
    parsed = parse(result, "courses", extractor=object(), page_type="listing")
    assert parsed.next_page_url is None
    assert parsed.load_more_action is None


def test_parser_uses_llm_selector_when_rules_fail(monkeypatch) -> None:
    """LLM fallback can return a CSS selector for JS load-more controls."""

    html = Path("tests/fixtures/llm_pagination.html").read_text(encoding="utf-8")
    result = FetchResult(
        url="https://example.edu/academics/courses",
        html=html,
        status_code=200,
        fetched_via="httpx",
        fetched_at=datetime.now(timezone.utc),
    )
    monkeypatch.setattr("core.parser.llm_detect_pagination", lambda snippet, url, extractor: ".results-control")
    parsed = parse(result, "courses", extractor=object(), page_type="listing")
    assert parsed.next_page_url is None
    assert parsed.load_more_action == ".results-control"
