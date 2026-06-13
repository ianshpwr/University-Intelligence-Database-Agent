"""Validation and confidence adjustment for extracted records."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from dateutil import parser as date_parser

from core.config_loader import UniversityConfig
from core.schema import (
    AcceptanceRate,
    CourseListing,
    FieldMeta,
    IntakeDeadline,
    TuitionFee,
    UniversityRecord,
)

logger = logging.getLogger(__name__)

COUNTRY_CURRENCY_MAP = {
    "United States": "USD",
    "United Kingdom": "GBP",
    "Canada": "CAD",
    "Australia": "AUD",
    "New Zealand": "NZD",
    "Ireland": "EUR",
    "Germany": "EUR",
    "France": "EUR",
    "Netherlands": "EUR",
    "India": "INR",
    "Singapore": "SGD",
}


def validate(record: UniversityRecord, config: UniversityConfig) -> UniversityRecord:
    """Validate a university record and adjust values, notes, and confidence.

    Args:
        record: Aggregated university record.
        config: Source configuration used for expectations.

    Returns:
        The same record with validation adjustments applied.
    """

    _validate_about(record)
    _validate_acceptance_rate(record.acceptance_rate)
    for tuition in record.tuition_fees:
        _validate_tuition(tuition, config)
    _validate_living_currency(record, config)
    for course in record.course_listings:
        _validate_course(course)
    for deadline in record.intake_deadlines:
        _validate_deadline(deadline)
    _mark_missing(record)
    return record


def _validate_about(record: UniversityRecord) -> None:
    """Validate top-level about fields."""

    current_year = datetime.now(timezone.utc).year
    year = record.about.founding_year
    if year is not None and not 1000 <= year <= current_year:
        record.about.founding_year = None
        _low(record.about.meta, f"founding_year {year} outside [1000, {current_year}]")


def _validate_acceptance_rate(rate: AcceptanceRate) -> None:
    """Validate acceptance-rate percentages."""

    for field_name in ("overall_pct", "undergrad_pct", "postgrad_pct"):
        value = getattr(rate, field_name)
        if value is not None and not 0 <= value <= 100:
            setattr(rate, field_name, None)
            _low(rate.meta, f"{field_name} {value} outside [0, 100]")


def _validate_tuition(tuition: TuitionFee, config: UniversityConfig) -> None:
    """Validate tuition ranges and expected currency."""

    for field_name in ("domestic_fee", "international_fee"):
        value = getattr(tuition, field_name)
        if value is not None and not 0 < value <= 200_000:
            setattr(tuition, field_name, None)
            _low(tuition.meta, f"{field_name} {value} outside (0, 200000]")
    expected = COUNTRY_CURRENCY_MAP.get(config.country, config.expected_currency)
    if tuition.currency and expected and tuition.currency != expected and tuition.currency != "USD":
        _low(tuition.meta, f"Currency {tuition.currency} does not match expected {expected}")


def _validate_living_currency(record: UniversityRecord, config: UniversityConfig) -> None:
    """Validate living-cost currency."""

    costs = record.living_costs
    expected = COUNTRY_CURRENCY_MAP.get(config.country, config.expected_currency)
    if costs.currency and expected and costs.currency != expected:
        _low(costs.meta, f"Currency {costs.currency} does not match expected {expected}")


def _validate_course(course: CourseListing) -> None:
    """Validate course credits."""

    if course.credits is not None and course.credits <= 0:
        course.credits = None
        _low(course.meta, "credits must be greater than 0")


def _validate_deadline(deadline: IntakeDeadline) -> None:
    """Flag stale intake deadlines."""

    extracted_at = deadline.meta.extracted_at
    for field_name in ("application_open", "application_close"):
        raw = getattr(deadline, field_name)
        if not raw:
            continue
        try:
            parsed = date_parser.parse(raw)
        except (ValueError, TypeError, OverflowError):
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        if (extracted_at - parsed).days > 730:
            _low(deadline.meta, f"{field_name} appears stale")


def _mark_missing(record: UniversityRecord) -> None:
    """Set confidence to missing on objects with no substantive extracted values."""

    for value in _iter_schema_objects(record):
        meta = getattr(value, "meta", None)
        if isinstance(meta, FieldMeta) and meta.confidence != "low" and _all_leaf_values_missing(value):
            meta.confidence = "missing"


def _iter_schema_objects(value: Any) -> list[Any]:
    """Return model objects nested under a record that carry metadata."""

    found: list[Any] = []
    if isinstance(value, list):
        for item in value:
            found.extend(_iter_schema_objects(item))
        return found
    if hasattr(value, "model_fields"):
        if hasattr(value, "meta"):
            found.append(value)
        for name in value.model_fields:
            if name == "meta":
                continue
            found.extend(_iter_schema_objects(getattr(value, name)))
    return found


def _all_leaf_values_missing(model: Any) -> bool:
    """Return whether all non-meta values on a model are missing."""

    for name in model.model_fields:
        if name == "meta":
            continue
        value = getattr(model, name)
        if value not in (None, "", []):
            return False
    return True


def _low(meta: FieldMeta, note: str) -> None:
    """Set confidence low and append a validation note."""

    meta.confidence = "low"
    meta.notes = f"{meta.notes}; {note}" if meta.notes else note
    logger.info("Validation flag: %s", note)
