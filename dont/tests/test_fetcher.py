"""Mocked tests for fetcher behavior."""

from __future__ import annotations

from typing import Any

import httpx

from core.fetcher import Fetcher


class _Response:
    """Small stand-in for an httpx response."""

    def __init__(self, text: str, status_code: int = 200, url: str = "https://example.edu/page") -> None:
        self.text = text
        self.status_code = status_code
        self.url = url

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("bad", request=httpx.Request("GET", str(self.url)), response=httpx.Response(self.status_code))


def test_fetcher_returns_httpx_content(monkeypatch: Any) -> None:
    """Fetcher returns rich static content without Playwright fallback."""

    fetcher = Fetcher(min_content_length=20)
    monkeypatch.setattr(fetcher, "_allowed_by_robots", lambda url: True)
    monkeypatch.setattr(fetcher, "_rate_limit", lambda domain, url: None)
    monkeypatch.setattr(fetcher, "_get_httpx", lambda url: _Response("<main>" + ("content " * 10) + "</main>"))
    result = fetcher.fetch("https://example.edu/page")
    assert result is not None
    assert result.fetched_via == "httpx"


def test_fetcher_uses_playwright_for_thin_content(monkeypatch: Any) -> None:
    """Fetcher falls back to Playwright when visible content is thin."""

    fetcher = Fetcher(min_content_length=50)
    monkeypatch.setattr(fetcher, "_allowed_by_robots", lambda url: True)
    monkeypatch.setattr(fetcher, "_rate_limit", lambda domain, url: None)
    monkeypatch.setattr(fetcher, "_get_httpx", lambda url: _Response("<main>thin</main>"))
    monkeypatch.setattr(fetcher, "_fetch_playwright", lambda url: "<main>" + ("rendered " * 20) + "</main>")
    result = fetcher.fetch("https://example.edu/page")
    assert result is not None
    assert result.fetched_via == "playwright"


def test_fetcher_blocks_robots(monkeypatch: Any) -> None:
    """Robots denial returns None instead of raising."""

    fetcher = Fetcher()
    monkeypatch.setattr(fetcher, "_allowed_by_robots", lambda url: False)
    assert fetcher.fetch("https://example.edu/private") is None

