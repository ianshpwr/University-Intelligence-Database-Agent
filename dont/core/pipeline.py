"""End-to-end scraping, extraction, aggregation, validation, and storage pipeline."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Any

from pydantic import ValidationError

from core.config_loader import UniversityConfig
from core.discovery import discover_category_urls
from core.extractor import Extractor
from core.fetcher import Fetcher
from core.parser import parse
from core.planner import Planner
from core.schema import (
    About,
    AcceptanceRate,
    AverageSalary,
    CourseListing,
    GraduateEmployment,
    IntakeDeadline,
    LivingCosts,
    Scholarship,
    TuitionFee,
    UniversityRecord,
    VisaPolicy,
)
from core.validator import validate

logger = logging.getLogger(__name__)

RawFragments = dict[str, dict[str, list[dict[str, Any]]]]
LISTING_CATEGORIES = {"tuition", "scholarships", "salaries", "intakes", "courses", "course_listings"}

# Minimum visible-text characters a page must have to be worth extracting.
MIN_EXTRACT_CHARS = 200

# URL path suffixes/patterns that reliably indicate an error or redirect page.
_ERROR_PATH_RE = re.compile(
    r"(/|\.)404\.?php$"
    r"|/404$"
    r"|/error/?$"
    r"|/not-found/?$"
    r"|/page-not-found/?$",
    re.IGNORECASE,
)


def run_university(
    config: UniversityConfig,
    extractor: Extractor,
    fetcher: Fetcher,
    db: Any,
    mode: str = "manual",
) -> UniversityRecord:
    """Run the full intelligence pipeline for one configured university.

    Args:
        config: University target configuration.
        extractor: LLM extraction component.
        fetcher: Web fetching component.
        db: Storage object exposing ``save(record)``.
        mode: ``auto`` enables homepage/sitemap category discovery before configured seeds.

    Returns:
        Validated and saved university record.
    """

    planner = Planner()
    frontier = planner.build_frontier(config)
    if mode == "auto":
        discovered = discover_category_urls(config, fetcher, extractor)
        planner.add_discovered_sources(frontier, discovered)
    planner.add_secondary_sources(frontier, config)
    raw_fragments: RawFragments = defaultdict(lambda: defaultdict(list))

    while frontier:
        item = frontier.popleft()
        if not planner.mark_visited(item):
            continue
        fetched = fetcher.fetch(item.url)
        if fetched is None:
            logger.warning("Skipping failed fetch: %s", item.url)
            continue
        page_type = "listing" if item.category in LISTING_CATEGORIES else "detail"
        parsed = parse(fetched, item.category, extractor=extractor, page_type=page_type)
        if _is_skippable_page(fetched, parsed):
            planner.enqueue_from_parsed(frontier, item, parsed)
            continue
        extraction = extractor.extract(parsed)
        if extraction:
            if "items" in extraction:
                raw_fragments[item.category][item.source_type].extend(extraction["items"])
            else:
                raw_fragments[item.category][item.source_type].append(extraction)
        planner.enqueue_from_parsed(frontier, item, parsed)

    record = aggregate_fragments(config, raw_fragments)
    validated = validate(record, config)
    db.save(validated)
    return validated


def aggregate_fragments(config: UniversityConfig, raw_fragments: RawFragments) -> UniversityRecord:
    """Merge extracted fragments into one record, preferring primary sources for singletons."""

    def values(category: str) -> list[dict[str, Any]]:
        primary = raw_fragments.get(category, {}).get("primary", [])
        secondary = raw_fragments.get(category, {}).get("secondary", [])
        return primary + secondary

    return UniversityRecord(
        university_id=config.id,
        about=_first_model(values("about"), About) or About(name=config.name, country=config.country),
        tuition_fees=_dedupe_with_cross_validation(
            raw_fragments,
            ["tuition", "tuition_fees"],
            TuitionFee,
            "program_level",
            _tuition_matches,
        ),
        living_costs=_first_model(values("living_costs"), LivingCosts) or LivingCosts(),
        scholarships=_dedupe_models(values("scholarships"), Scholarship, "name"),
        acceptance_rate=_first_model(values("acceptance_rate"), AcceptanceRate) or AcceptanceRate(),
        graduate_employment=(
            _first_model(values("employment") + values("graduate_employment"), GraduateEmployment)
            or GraduateEmployment()
        ),
        average_salaries=_dedupe_models(values("salaries") + values("average_salaries"), AverageSalary, "field_of_study"),
        visa_policy=_first_model(values("visa") + values("visa_policy"), VisaPolicy) or VisaPolicy(country=config.country),
        intake_deadlines=_dedupe_with_cross_validation(
            raw_fragments,
            ["intakes", "intake_deadlines"],
            IntakeDeadline,
            "intake_name",
            _intake_matches,
        ),
        course_listings=_dedupe_models(values("courses") + values("course_listings"), CourseListing, "code"),
    )


def _first_model(items: list[dict[str, Any]], model_cls: type[Any]) -> Any | None:
    """Return first valid model from primary-then-secondary fragments."""

    for item in items:
        try:
            return model_cls.model_validate(item)
        except ValidationError as exc:
            logger.warning("Dropping invalid %s fragment: %s", model_cls.__name__, exc)
    return None


def _dedupe_models(items: list[dict[str, Any]], model_cls: type[Any], key_field: str) -> list[Any]:
    """Validate and deduplicate list-category fragments by a natural key."""

    seen: set[str] = set()
    output: list[Any] = []
    for item in items:
        try:
            model = model_cls.model_validate(item)
        except ValidationError as exc:
            logger.warning("Dropping invalid %s fragment: %s", model_cls.__name__, exc)
            continue
        key = str(getattr(model, key_field, "") or "").strip().lower()
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        output.append(model)
    return output


def _dedupe_with_cross_validation(
    raw_fragments: RawFragments,
    categories: list[str],
    model_cls: type[Any],
    key_field: str,
    matcher: Any,
) -> list[Any]:
    """Deduplicate primary/secondary list fragments and mark matches or mismatches."""

    primary = []
    secondary = []
    for category in categories:
        primary.extend(raw_fragments.get(category, {}).get("primary", []))
        secondary.extend(raw_fragments.get(category, {}).get("secondary", []))
    primary_models = _dedupe_models(primary, model_cls, key_field)
    secondary_models = _dedupe_models(secondary, model_cls, key_field)
    secondary_by_key = {
        str(getattr(item, key_field, "") or "").strip().lower(): item
        for item in secondary_models
        if str(getattr(item, key_field, "") or "").strip()
    }

    output: list[Any] = []
    consumed_secondary: set[str] = set()
    for item in primary_models:
        key = str(getattr(item, key_field, "") or "").strip().lower()
        match = secondary_by_key.get(key)
        if match is None:
            output.append(item)
            continue
        consumed_secondary.add(key)
        if matcher(item, match):
            item.meta.cross_validated = True
            item.meta.confidence = "high"
            output.append(item)
        else:
            item.meta.confidence = "low"
            item.meta.notes = _append_note(item.meta.notes, f"Secondary source differs: {match.model_dump(mode='json')}")
            match.meta.confidence = "low"
            match.meta.notes = _append_note(match.meta.notes, "Primary source differs")
            output.extend([item, match])

    for item in secondary_models:
        key = str(getattr(item, key_field, "") or "").strip().lower()
        if key not in consumed_secondary:
            output.append(item)
    return output


def _tuition_matches(primary: TuitionFee, secondary: TuitionFee) -> bool:
    """Return whether tuition fragments agree within numeric tolerance and currency."""

    if primary.currency and secondary.currency and primary.currency != secondary.currency:
        return False
    return _within_tolerance(primary.domestic_fee, secondary.domestic_fee) and _within_tolerance(
        primary.international_fee, secondary.international_fee
    )


def _intake_matches(primary: IntakeDeadline, secondary: IntakeDeadline) -> bool:
    """Return whether intake deadline fragments agree exactly on present dates."""

    for field_name in ("application_open", "application_close"):
        left = getattr(primary, field_name)
        right = getattr(secondary, field_name)
        if left and right and left != right:
            return False
    return True


def _within_tolerance(left: float | None, right: float | None, tolerance: float = 0.05) -> bool:
    """Return whether two optional numbers match within a relative tolerance."""

    if left is None or right is None:
        return True
    if left == right:
        return True
    baseline = max(abs(left), 1.0)
    return abs(left - right) / baseline <= tolerance


def _append_note(existing: str | None, note: str) -> str:
    """Append a note to an optional notes string."""

    return f"{existing}; {note}" if existing else note


def _is_skippable_page(fetched: Any, parsed: Any) -> bool:
    """Return True when a fetched page should be skipped before extraction.

    Skips pages that are guaranteed to contain no useful content:
    - URL matches known error-page path patterns (e.g. ``/404.php``, ``/404``)
    - HTTP status code indicates an error (4xx / 5xx)
    - Visible clean text is shorter than ``MIN_EXTRACT_CHARS`` after stripping

    Pagination/navigation links are still enqueued even for skipped pages so
    the planner can follow discovered links normally.
    """

    url = getattr(fetched, "url", "") or ""
    status = getattr(fetched, "status_code", 200) or 200
    clean_text = getattr(parsed, "clean_text", "") or ""

    if _ERROR_PATH_RE.search(url):
        logger.info("Skipping error page: %s", url)
        return True

    if status >= 400:
        logger.info("Skipping %d response page: %s", status, url)
        return True

    if len(clean_text) < MIN_EXTRACT_CHARS:
        logger.info("Skipping thin page (%d chars): %s", len(clean_text), url)
        return True

    return False
