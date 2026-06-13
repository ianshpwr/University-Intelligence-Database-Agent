"""Hybrid category discovery for university seed links."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from collections import defaultdict
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config_loader import UniversityConfig
from core.fetcher import Fetcher

logger = logging.getLogger(__name__)

CATEGORIES = [
    "about",
    "tuition",
    "living_costs",
    "scholarships",
    "acceptance_rate",
    "employment",
    "salaries",
    "visa",
    "intakes",
    "courses",
]
MAX_DISCOVERY_LINKS = 150
MIN_LINKS_BEFORE_EXPANSION = 5

# Common path patterns tried directly when discovery finds too few links.
# Ordered roughly by relevance to university intelligence categories.
COMMON_CATEGORY_PATHS: list[tuple[str, str]] = [
    ("/about", "about"),
    ("/about-us", "about"),
    ("/academics", "courses"),
    ("/academic-programmes", "courses"),
    ("/programmes", "courses"),
    ("/courses", "courses"),
    ("/admissions", "intakes"),
    ("/admissions/fees", "tuition"),
    ("/fees", "tuition"),
    ("/tuition", "tuition"),
    ("/scholarships", "scholarships"),
    ("/financial-aid", "scholarships"),
    ("/placements", "employment"),
    ("/placement", "employment"),
    ("/careers", "employment"),
    ("/international", "visa"),
    ("/international-students", "visa"),
    ("/student-life", "living_costs"),
    ("/living", "living_costs"),
    ("/research", "about"),
]

_FALLBACK_CATEGORY_KEYWORDS = {
    "about": ("about", "profile", "facts", "history", "mission"),
    "tuition": ("tuition", "fees", "cost", "finance"),
    "living_costs": ("living", "housing", "accommodation", "cost of living"),
    "scholarships": ("scholarship", "funding", "financial aid", "bursary"),
    "acceptance_rate": ("acceptance", "admission statistics", "facts", "selectivity"),
    "employment": ("employment", "outcomes", "career", "graduate outcomes"),
    "salaries": ("salary", "salaries", "earnings", "outcomes"),
    "visa": ("visa", "immigration", "international students"),
    "intakes": ("deadline", "intake", "apply", "application dates"),
    "courses": ("course", "catalog", "programme", "program", "module"),
}


def classify_links_by_category(links: list[tuple[str, str]], extractor: Any) -> dict[str, list[str]]:
    """Classify candidate links into university intelligence categories.

    Args:
        links: Tuples of ``(href, anchor_text)`` from homepage or sitemap pages.
        extractor: Existing extractor instance used for LLM calls and in-run cache.

    Returns:
        Mapping from each configured category to zero, one, or two URL strings.
    """

    candidates = _cap_links(links)
    if _llm_disabled():
        return _fallback_classify_links(candidates)
    try:
        return _llm_classify_links(candidates, extractor)
    except (json.JSONDecodeError, TypeError, KeyError, AttributeError, RuntimeError, ValueError) as exc:
        logger.warning("LLM category classification failed; using keyword fallback: %s", exc)
        return _fallback_classify_links(candidates)


def collect_candidate_links(html: str, base_url: str) -> list[tuple[str, str]]:
    """Collect deduplicated absolute links and anchor text from an HTML page."""

    _parser = "lxml-xml" if base_url.lower().split("?")[0].endswith(".xml") else "html.parser"
    try:
        soup = BeautifulSoup(html, _parser)
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
    links: list[tuple[str, str]] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor["href"])
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"}:
            continue
        normalized = href.split("#", 1)[0]
        if normalized in seen:
            continue
        seen.add(normalized)
        links.append((normalized, anchor.get_text(" ", strip=True)))
    return links


def discover_category_urls(
    config: UniversityConfig, fetcher: Fetcher, extractor: Any
) -> dict[str, list[str]]:
    """Fetch discovery entry points, expand if too few links found, then classify.

    Strategy:
    1. Fetch homepage + sitemap.xml + /sitemap and collect all links.
    2. If fewer than ``MIN_LINKS_BEFORE_EXPANSION`` unique internal links found,
       do a one-level-deep expansion: fetch any top-level same-domain nav links
       discovered on the homepage and add their links to the pool.
    3. Probe ``COMMON_CATEGORY_PATHS`` with httpx; confirmed 200 URLs are added
       directly to the pool with their path as anchor text.
    4. Cap at ``MAX_DISCOVERY_LINKS`` (preferring links with anchor text) and
       classify with the LLM (or keyword fallback).
    """

    base_url = str(config.base_url)
    base_netloc = urlparse(base_url).netloc
    links: list[tuple[str, str]] = []
    homepage_html: str | None = None

    for path in ("", "/sitemap.xml", "/sitemap"):
        result = fetcher.fetch(urljoin(base_url, path))
        if result is None:
            continue
        page_links = collect_candidate_links(result.html, result.url)
        links.extend(page_links)
        if path == "":  # save homepage HTML for nav expansion
            homepage_html = result.html

    # --- second pass: expand via top-level nav links when pool is small ---
    internal_count = sum(
        1 for href, _ in links if urlparse(href).netloc == base_netloc
    )
    if internal_count < MIN_LINKS_BEFORE_EXPANSION and homepage_html:
        logger.info(
            "Only %d internal links found for %s; fetching top-level nav links for expansion",
            internal_count,
            config.id,
        )
        nav_links = [
            href for href, _ in collect_candidate_links(homepage_html, base_url)
            if urlparse(href).netloc == base_netloc
        ][:10]  # limit nav expansion pages
        for nav_url in nav_links:
            nav_result = fetcher.fetch(nav_url)
            if nav_result:
                links.extend(collect_candidate_links(nav_result.html, nav_result.url))

    # --- probe common paths directly ---
    probed_urls: set[str] = {href for href, _ in links}
    for rel_path, category_hint in COMMON_CATEGORY_PATHS:
        probe_url = urljoin(base_url, rel_path)
        if probe_url in probed_urls:
            continue
        try:
            resp = fetcher._get_httpx(probe_url)
            if resp.status_code == 200:
                links.append((probe_url, rel_path.strip("/").replace("-", " ")))
                probed_urls.add(probe_url)
        except Exception:  # noqa: BLE001
            pass

    if not links:
        logger.warning("No discovery links found for %s", config.id)
        return {category: [] for category in CATEGORIES}

    logger.info(
        "Discovery pool for %s: %d candidate links before LLM classification",
        config.id,
        len(links),
    )
    return classify_links_by_category(links, extractor)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _llm_classify_links(links: list[tuple[str, str]], extractor: Any) -> dict[str, list[str]]:
    """Ask the LLM to choose the best category URLs from a capped link list."""

    payload = [{"href": href, "anchor_text": text} for href, text in links]
    system = (
        "You classify university website links into fixed data categories. "
        "Return JSON only. The output must be an object with exactly these keys: "
        f"{', '.join(CATEGORIES)}. Each value must be an array of the 1-2 best hrefs "
        "from the provided list, or an empty array when no link fits. Do not invent URLs."
    )
    user = json.dumps({"links": payload}, ensure_ascii=True)
    cache_key = "discovery:" + hashlib.sha256(user.encode("utf-8")).hexdigest()
    raw = _call_cached(extractor, cache_key, system, user)
    decoded = json.loads(raw)
    return _normalize_classification(decoded, {href for href, _ in links})


def _fallback_classify_links(links: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Keyword-score links when LLM classification is unavailable."""

    scored: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for href, text in links:
        haystack = f"{href} {text}".lower()
        for category, keywords in _FALLBACK_CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in haystack)
            if score:
                scored[category].append((score, href))
    result: dict[str, list[str]] = {}
    for category in CATEGORIES:
        ranked = sorted(scored.get(category, []), key=lambda item: (-item[0], item[1]))
        result[category] = list(dict.fromkeys(href for _, href in ranked[:2]))
    return result


def _cap_links(links: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Deduplicate and cap candidate links, preferring anchors with useful text and unique paths."""

    deduped: dict[str, tuple[str, str]] = {}
    for href, text in links:
        normalized = href.split("#", 1)[0]
        deduped.setdefault(normalized, (normalized, text.strip()))

    def rank(item: tuple[str, str]) -> tuple[int, str]:
        href, text = item
        path = urlparse(href).path
        has_text = 0 if text else 1
        return (has_text, path)

    unique_paths: set[str] = set()
    prioritized: list[tuple[str, str]] = []
    for href, text in sorted(deduped.values(), key=rank):
        path = urlparse(href).path.rstrip("/") or "/"
        if path in unique_paths and len(prioritized) >= MAX_DISCOVERY_LINKS:
            continue
        unique_paths.add(path)
        prioritized.append((href, text))
        if len(prioritized) >= MAX_DISCOVERY_LINKS:
            break
    return prioritized


def _normalize_classification(decoded: Any, allowed_urls: set[str]) -> dict[str, list[str]]:
    """Normalize and validate the LLM category mapping."""

    if not isinstance(decoded, dict):
        raise TypeError("LLM classification response must be a JSON object")
    result: dict[str, list[str]] = {}
    for category in CATEGORIES:
        raw_value = decoded.get(category, [])
        if raw_value is None:
            result[category] = []
            continue
        if isinstance(raw_value, str):
            raw_items = [raw_value]
        elif isinstance(raw_value, list):
            raw_items = raw_value
        else:
            raw_items = []
        urls = [url for url in raw_items if isinstance(url, str) and url in allowed_urls]
        result[category] = list(dict.fromkeys(urls))[:2]
    return result


def _call_cached(extractor: Any, cache_key: str, system: str, user: str) -> str:
    """Use extractor cache if available, otherwise call its private LLM method."""

    if hasattr(extractor, "call_cached"):
        return extractor.call_cached(cache_key, system, user)
    if hasattr(extractor, "_call"):
        return extractor._call(system, user)
    raise RuntimeError("Extractor does not expose an LLM call method")


def _llm_disabled() -> bool:
    """Return whether LLM fallbacks are disabled by environment."""

    return os.getenv("DISABLE_LLM_FALLBACK", "").strip().lower() in {"1", "true", "yes", "on"}
