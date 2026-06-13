"""HTML parsing and link discovery."""

from __future__ import annotations

import logging
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup, Tag
from tenacity import retry, stop_after_attempt, wait_exponential

from core.fetcher import FetchResult

logger = logging.getLogger(__name__)

MAX_LLM_PAGINATION_CHECKS_PER_RUN = int(os.getenv("MAX_LLM_PAGINATION_CHECKS_PER_RUN", "50"))
DENYLIST_CLASS_SUBSTRINGS = ("cookie", "banner", "advert", "ad-", "promo", "modal", "subscribe")
CATEGORY_LINK_PATTERNS = {
    "courses": r"/course[s]?/|/catalog|/module[s]?/",
    "course_listings": r"/course[s]?/|/catalog|/module[s]?/",
    "scholarships": r"/scholarship|/financial-aid|/funding",
    "intakes": r"/deadline|/admission|/apply|/intake",
    "intake_deadlines": r"/deadline|/admission|/apply|/intake",
}
LISTING_CATEGORIES = {"tuition", "scholarships", "salaries", "intakes", "courses", "course_listings"}
_FALLBACK_NEXT_WORDS = (
    "next",
    "more",
    "load more",
    "show more",
    "older",
    "suivant",
    "siguiente",
    "weiter",
    "proximo",
    "próximo",
    "volgende",
    "następna",
    "dalsi",
    "下一页",
    "次へ",
    "التالي",
)


@dataclass(slots=True)
class ParsedPage:
    """Cleaned page content and crawl hints."""

    url: str
    category: str
    clean_text: str
    next_page_url: str | None = None
    load_more_action: str | None = None
    discovered_links: list[str] = field(default_factory=list)


def parse(
    fetch_result: FetchResult,
    category: str,
    link_pattern: str | None = None,
    extractor: Any | None = None,
    page_type: str | None = None,
) -> ParsedPage:
    """Parse a fetched page into clean text, pagination URL, and relevant detail links.

    Args:
        fetch_result: Raw fetched HTML.
        category: Extraction category for the page.
        link_pattern: Optional regex overriding the category link pattern.
        extractor: Existing extractor used only for optional LLM pagination fallback.
        page_type: ``listing`` enables LLM pagination fallback when rules find nothing.

    Returns:
        ``ParsedPage`` containing cleaned text and discovered links.
    """

    soup = BeautifulSoup(fetch_result.html, "html.parser")
    raw_soup = BeautifulSoup(fetch_result.html, "html.parser")
    _remove_noise(soup)
    clean_text = _collapse_ws(soup.get_text("\n", strip=True))
    next_url = _find_next_url(raw_soup, fetch_result.url)
    load_more_action = None
    resolved_page_type = page_type or ("listing" if category in LISTING_CATEGORIES else "detail")
    if next_url is None and extractor is not None and resolved_page_type == "listing":
        target = llm_detect_pagination(_pagination_snippet(raw_soup), fetch_result.url, extractor)
        if target:
            if _looks_like_url_or_path(target):
                next_url = urljoin(fetch_result.url, target)
            else:
                load_more_action = target
    discovered = _find_discovered_links(soup, fetch_result.url, category, link_pattern)
    logger.info("Parsed %s (%s chars, %d discovered links)", fetch_result.url, len(clean_text), len(discovered))
    return ParsedPage(fetch_result.url, category, clean_text, next_url, load_more_action, discovered)


def _remove_noise(soup: BeautifulSoup) -> None:
    """Remove low-value page chrome and common overlays from a soup."""

    for tag in soup.select("script, style, nav, footer, header, noscript"):
        tag.decompose()
    for tag in list(soup.find_all(True)):
        if not isinstance(tag, Tag):  # skip NavigableString, Comment, etc.
            continue
        if tag.attrs is None:  # guard against BS4 nodes with null attrs (e.g. ProcessingInstruction)
            continue
        class_text = " ".join(tag.get("class", [])).lower()
        if any(term in class_text for term in DENYLIST_CLASS_SUBSTRINGS):
            tag.decompose()


def _find_next_url(soup: BeautifulSoup, base_url: str) -> str | None:
    """Detect a pagination next link."""

    numbered = _find_numbered_sequence_next(soup, base_url)
    if numbered:
        return numbered

    incremented = _find_incremented_url_pattern(soup, base_url)
    if incremented:
        return incremented

    rel_next = soup.find("a", rel=lambda rel: rel and "next" in rel)
    if rel_next and rel_next.get("href"):
        return urljoin(base_url, rel_next["href"])

    for selector in ("a", "button", ".pagination a"):
        for element in soup.select(selector):
            text = element.get_text(" ", strip=True).lower()
            if re.search(r"^(»|→|›|>|&gt;)$", text) and element.get("href"):
                return urljoin(base_url, element["href"])
    for element in soup.select("a[href]"):
        text = element.get_text(" ", strip=True).lower()
        aria = str(element.get("aria-label", "")).lower()
        title = str(element.get("title", "")).lower()
        haystack = f"{text} {aria} {title}"
        if any(word in haystack for word in _FALLBACK_NEXT_WORDS):
            return urljoin(base_url, element["href"])
    return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _call_llm_pagination(html_snippet: str, current_url: str, extractor: Any) -> str:
    """Call the LLM for pagination detection with retry/backoff."""

    system = (
        "You inspect HTML snippets for listing pagination. Return JSON only. "
        "If a link or button navigates to the next page of this listing, return "
        '{"target": "<href-or-css-selector>"}; otherwise return {"target": null}. '
        "Do not infer a next page unless the snippet explicitly contains one."
    )
    user = json.dumps({"current_url": current_url, "html_snippet": html_snippet[:2_000]}, ensure_ascii=True)
    cache_key = f"pagination:{hash(user)}"
    if hasattr(extractor, "call_cached"):
        return extractor.call_cached(cache_key, system, user)
    if hasattr(extractor, "_call"):
        return extractor._call(system, user)
    raise RuntimeError("Extractor does not expose an LLM call method")


def llm_detect_pagination(html_snippet: str, current_url: str, extractor: Any) -> Optional[str]:
    """Ask the LLM whether a listing page exposes next-page navigation.

    Returns:
        A URL/path or CSS selector string, or ``None`` when nothing is detected.
    """

    if _llm_disabled():
        return None
    checks = int(getattr(extractor, "llm_pagination_checks", 0))
    if checks >= MAX_LLM_PAGINATION_CHECKS_PER_RUN:
        logger.warning("Skipping LLM pagination check after reaching per-run limit %s", MAX_LLM_PAGINATION_CHECKS_PER_RUN)
        return None
    try:
        setattr(extractor, "llm_pagination_checks", checks + 1)
        raw = _call_llm_pagination(html_snippet, current_url, extractor)
        decoded = json.loads(raw)
        target = decoded.get("target") if isinstance(decoded, dict) else decoded
        return target.strip() if isinstance(target, str) and target.strip() else None
    except (json.JSONDecodeError, TypeError, AttributeError, RuntimeError, ValueError) as exc:
        logger.info("LLM pagination fallback did not produce a usable result for %s: %s", current_url, exc)
        return None


def _find_discovered_links(
    soup: BeautifulSoup, base_url: str, category: str, link_pattern: str | None
) -> list[str]:
    """Return deduped category-relevant detail links."""

    pattern = link_pattern or CATEGORY_LINK_PATTERNS.get(category)
    if not pattern:
        return []
    regex = re.compile(pattern, re.IGNORECASE)
    seen: set[str] = set()
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        text = anchor.get_text(" ", strip=True)
        if regex.search(href) or regex.search(text):
            absolute = urljoin(base_url, href)
            if absolute not in seen:
                seen.add(absolute)
                links.append(absolute)
    return links


def _collapse_ws(text: str) -> str:
    """Collapse noisy whitespace while preserving paragraph-like line breaks."""

    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _find_numbered_sequence_next(soup: BeautifulSoup, base_url: str) -> str | None:
    """Find the link after the current numbered pagination item."""

    current_number: int | None = None
    links: list[tuple[int, str]] = []
    for element in soup.select(".pagination a[href], nav a[href], a[href]"):
        text = element.get_text(" ", strip=True)
        if not text.isdigit():
            continue
        number = int(text)
        href = urljoin(base_url, element["href"])
        links.append((number, href))
        classes = " ".join(element.get("class", [])).lower()
        parent_classes = (
            " ".join(element.parent.get("class", [])).lower()
            if isinstance(element.parent, Tag)
            else ""
        )
        if "current" in classes or "active" in classes or "current" in parent_classes or "active" in parent_classes:
            current_number = number
    if current_number is None:
        return None
    next_candidates = [href for number, href in links if number == current_number + 1]
    return next_candidates[0] if next_candidates else None


def _find_incremented_url_pattern(soup: BeautifulSoup, base_url: str) -> str | None:
    """Find hrefs whose page query/path number is current page + 1."""

    current = urlparse(base_url)
    query = parse_qs(current.query)
    for key in ("page", "p"):
        if key in query and query[key] and query[key][0].isdigit():
            next_query = query.copy()
            next_query[key] = [str(int(query[key][0]) + 1)]
            next_url = urlunparse(current._replace(query=urlencode(next_query, doseq=True)))
            if soup.find("a", href=lambda href: href and urljoin(base_url, href) == next_url):
                return next_url
    path_match = re.search(r"(.*/page/)(\d+)(/?)$", current.path)
    if path_match:
        next_path = f"{path_match.group(1)}{int(path_match.group(2)) + 1}{path_match.group(3)}"
        next_url = urlunparse(current._replace(path=next_path))
        if soup.find("a", href=lambda href: href and urljoin(base_url, href) == next_url):
            return next_url
    return None


def _pagination_snippet(soup: BeautifulSoup) -> str:
    """Return a compact bottom-of-page snippet for LLM pagination fallback."""

    controls = soup.select("body > footer a, body > footer button, nav a, nav button, .pagination a, .pagination button")
    if controls:
        return "\n".join(str(control) for control in controls)[-2_000:]
    body = soup.body or soup
    return str(body)[-2_000:]


def _looks_like_url_or_path(target: str) -> bool:
    """Return whether an LLM target appears to be a URL/path rather than a CSS selector."""

    return target.startswith(("http://", "https://", "/", "./", "../", "?"))


def _llm_disabled() -> bool:
    """Return whether LLM fallbacks are disabled by environment."""

    return os.getenv("DISABLE_LLM_FALLBACK", "").strip().lower() in {"1", "true", "yes", "on"}
