"""HTTP and Playwright fetching with robots.txt, retries, and rate limiting."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

MIN_CONTENT_LENGTH = 500
DEFAULT_CRAWL_DELAY_SECONDS = 2.0
USER_AGENT = "UniversityIntelligenceAgent/0.1"


@dataclass(slots=True)
class FetchResult:
    """Fetched HTML and related metadata."""

    url: str
    html: str
    status_code: int
    fetched_via: Literal["httpx", "playwright"]
    fetched_at: datetime


class Fetcher:
    """Fetch pages respectfully using robots.txt, rate limits, httpx, and Playwright fallback."""

    def __init__(self, min_content_length: int = MIN_CONTENT_LENGTH) -> None:
        """Initialize robot and rate-limit caches.

        Args:
            min_content_length: Minimum visible text length before Playwright fallback.
        """

        self.min_content_length = min_content_length
        self._robots_cache: dict[str, RobotFileParser] = {}
        self._last_request_time: dict[str, float] = {}
        self.stats = {"visited": 0, "failed": 0, "playwright_fallbacks": 0}

    def fetch(self, url: str) -> FetchResult | None:
        """Fetch one URL and return HTML metadata, logging and returning ``None`` on failure."""

        domain = self._domain_key(url)
        if not self._allowed_by_robots(url):
            logger.warning("Blocked by robots.txt: %s", url)
            self.stats["failed"] += 1
            return None

        self._rate_limit(domain, url)
        try:
            response = self._get_httpx(url)
            html = response.text
            visible_text = self._visible_text(html, url=url)
            if len(visible_text) < self.min_content_length:
                logger.info("Thin content from httpx; using Playwright fallback for %s", url)
                html = self._fetch_playwright(url)
                self.stats["playwright_fallbacks"] += 1
                via: Literal["httpx", "playwright"] = "playwright"
            else:
                via = "httpx"
            self.stats["visited"] += 1
            return FetchResult(
                url=str(response.url),
                html=html,
                status_code=response.status_code,
                fetched_via=via,
                fetched_at=datetime.now(timezone.utc),
            )
        except (httpx.HTTPError, RuntimeError) as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
            self.stats["failed"] += 1
            return None

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    def _get_httpx(self, url: str) -> httpx.Response:
        """Fetch a URL with httpx and retry transient failures."""

        response = httpx.get(url, timeout=20, headers={"User-Agent": USER_AGENT}, follow_redirects=True)
        if response.status_code >= 500:
            response.raise_for_status()
        return response

    def _fetch_playwright(self, url: str) -> str:
        """Fetch fully rendered HTML using Playwright."""

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is required for JS-rendered pages") from exc

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(url, wait_until="networkidle", timeout=30_000)
            html = page.content()
            browser.close()
            return html

    def _allowed_by_robots(self, url: str) -> bool:
        """Return whether robots.txt permits fetching the URL.

        Fetches robots.txt via httpx (not urllib) so we have full control over
        the HTTP status code.  Any non-200 response (403, 404, 5xx) **and** any
        network/SSL error is treated as default-allow — this matches the standard
        crawler convention that an unreadable robots.txt imposes no restrictions.
        Only an HTTP 200 with valid content is used to restrict crawling.
        """

        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robots_cache:
            robot_url = urljoin(base, "/robots.txt")
            try:
                resp = httpx.get(
                    robot_url,
                    timeout=10,
                    headers={"User-Agent": USER_AGENT},
                    follow_redirects=True,
                )
                if resp.status_code == 200:
                    parser = RobotFileParser()
                    parser.set_url(robot_url)
                    parser.parse(resp.text.splitlines())
                    self._robots_cache[base] = parser
                else:
                    logger.warning(
                        "robots.txt for %s returned HTTP %d; proceeding without restrictions",
                        base,
                        resp.status_code,
                    )
                    self._robots_cache[base] = None  # sentinel: default-allow
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Could not read robots.txt for %s (%s); proceeding without restrictions",
                    base,
                    exc,
                )
                self._robots_cache[base] = None  # sentinel: default-allow
        cached = self._robots_cache[base]
        if cached is None:
            return True  # unreadable / non-200 robots.txt → allow
        return cached.can_fetch(USER_AGENT, url)

    def _rate_limit(self, domain: str, url: str) -> None:
        """Sleep as needed according to robots crawl-delay or the default delay."""

        delay = self._crawl_delay(url)
        elapsed = time.monotonic() - self._last_request_time.get(domain, 0)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_request_time[domain] = time.monotonic()

    def _crawl_delay(self, url: str) -> float:
        """Return robots crawl-delay for a URL or a conservative default."""

        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._robots_cache.get(base)
        # parser may be None (failed robots fetch) — fall back to default.
        delay = parser.crawl_delay(USER_AGENT) if parser else None
        return float(delay if delay is not None else DEFAULT_CRAWL_DELAY_SECONDS)

    @staticmethod
    def _domain_key(url: str) -> str:
        """Return normalized scheme and host for rate-limit tracking."""

        parsed = urlparse(url)
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"

    @staticmethod
    def _visible_text(html: str, url: str = "") -> str:
        """Return text content with tags and whitespace stripped.

        Uses the ``lxml-xml`` parser for ``.xml`` URLs to avoid
        ``XMLParsedAsHTMLWarning`` and to correctly walk XML node text.
        """

        parser = "lxml-xml" if url.lower().split("?")[0].endswith(".xml") else "html.parser"
        try:
            soup = BeautifulSoup(html, parser)
        except Exception:  # lxml not installed or parse error – fall back gracefully
            soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)
        return re.sub(r"\s+", " ", text)

