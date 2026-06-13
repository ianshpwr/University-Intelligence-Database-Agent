"""Crawl frontier planning for configured university sources."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Literal
from urllib.parse import urljoin, urlparse, urlunparse

from core.config_loader import UniversityConfig
from core.parser import ParsedPage

MAX_DEPTH = 5
MAX_PAGES_PER_CATEGORY = 15

SourceType = Literal["primary", "secondary"]


@dataclass(frozen=True, slots=True)
class FrontierItem:
    """A page planned for fetching."""

    url: str
    category: str
    depth: int = 0
    source_type: SourceType = "primary"


class Planner:
    """Build and maintain a deduplicated crawl frontier."""

    def __init__(
        self,
        max_depth: int = MAX_DEPTH,
        max_pages_per_category: int = MAX_PAGES_PER_CATEGORY,
    ) -> None:
        """Initialize planner state and crawl limits."""

        self.max_depth = max_depth
        self.max_pages_per_category = max_pages_per_category
        self.visited: set[str] = set()
        self.category_counts: dict[str, int] = defaultdict(int)

    def build_frontier(self, config: UniversityConfig) -> Deque[FrontierItem]:
        """Create the initial frontier from primary seed pages."""

        frontier: Deque[FrontierItem] = deque()
        base = str(config.base_url)
        for category, paths in (config.seed_pages or {}).items():
            for path in paths:
                self._enqueue(frontier, urljoin(base, path), category, 0, "primary")
        return frontier

    def add_secondary_sources(self, frontier: Deque[FrontierItem], config: UniversityConfig) -> None:
        """Append secondary source URLs to an existing frontier."""

        for category, urls in config.secondary_sources.items():
            for url in urls:
                self._enqueue(frontier, url, category, 0, "secondary")

    def add_discovered_sources(self, frontier: Deque[FrontierItem], category_urls: dict[str, list[str]]) -> None:
        """Append auto-discovered primary URLs to an existing frontier."""

        for category, urls in category_urls.items():
            for url in urls:
                self._enqueue(frontier, url, category, 0, "primary")

    def enqueue_from_parsed(
        self,
        frontier: Deque[FrontierItem],
        item: FrontierItem,
        parsed: ParsedPage,
    ) -> None:
        """Add pagination and detail links discovered from a parsed page."""

        if item.depth >= self.max_depth:
            return
        if parsed.next_page_url:
            self._enqueue(frontier, parsed.next_page_url, item.category, item.depth + 1, item.source_type)
        for link in parsed.discovered_links:
            self._enqueue(frontier, link, item.category, item.depth + 1, item.source_type)

    def mark_visited(self, item: FrontierItem) -> bool:
        """Mark an item as visited and return whether it should be processed."""

        key = normalize_url(item.url)
        if key in self.visited:
            return False
        if self.category_counts[item.category] >= self.max_pages_per_category:
            return False
        self.visited.add(key)
        self.category_counts[item.category] += 1
        return True

    def _enqueue(
        self,
        frontier: Deque[FrontierItem],
        url: str,
        category: str,
        depth: int,
        source_type: SourceType,
    ) -> None:
        """Add a URL if it has not been visited and category cap allows more pages."""

        if depth > self.max_depth:
            return
        if self.category_counts[category] >= self.max_pages_per_category:
            return
        if normalize_url(url) not in self.visited:
            frontier.append(FrontierItem(url=url, category=category, depth=depth, source_type=source_type))


def normalize_url(url: str) -> str:
    """Normalize URL for duplicate detection."""

    parsed = urlparse(url)
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        path=parsed.path.rstrip("/") or "/",
        fragment="",
    )
    return urlunparse(normalized)
