"""Tests for validation rules."""

from datetime import datetime, timezone

from core.config_loader import UniversityConfig
from core.schema import About, AcceptanceRate, CourseListing, FieldMeta, IntakeDeadline, TuitionFee, UniversityRecord
from core.validator import validate


def _config() -> UniversityConfig:
    return UniversityConfig(
        id="uni_a",
        name="TODO",
        base_url="https://example.edu",
        city="Example City",
        country="United States",
        expected_currency="USD",
        discovery_mode="auto",
        secondary_sources={},
    )


def test_validator_nulls_out_of_range_values() -> None:
    """Validator removes impossible values and marks confidence low."""

    record = UniversityRecord(
        university_id="uni_a",
        about=About(founding_year=999, meta=FieldMeta(confidence="high")),
        acceptance_rate=AcceptanceRate(overall_pct=120, meta=FieldMeta(confidence="high")),
        course_listings=[CourseListing(code="BAD", credits=0, meta=FieldMeta(confidence="high"))],
    )
    validate(record, _config())
    assert record.about.founding_year is None
    assert record.about.meta.confidence == "low"
    assert record.acceptance_rate.overall_pct is None
    assert record.course_listings[0].credits is None


def test_validator_flags_currency_mismatch() -> None:
    """Currency mismatch should lower confidence without deleting the value."""

    record = UniversityRecord(
        university_id="uni_a",
        tuition_fees=[TuitionFee(program_level="undergrad", domestic_fee=1000, currency="GBP", meta=FieldMeta(confidence="high"))],
    )
    validate(record, _config())
    assert record.tuition_fees[0].currency == "GBP"
    assert record.tuition_fees[0].meta.confidence == "low"


def test_validator_flags_stale_deadlines() -> None:
    """Deadlines more than two years old should be flagged low confidence."""

    record = UniversityRecord(
        university_id="uni_a",
        intake_deadlines=[
            IntakeDeadline(
                intake_name="Fall",
                application_close="2020-01-01",
                meta=FieldMeta(confidence="high", extracted_at=datetime(2026, 1, 1, tzinfo=timezone.utc)),
            )
        ],
    )
    validate(record, _config())
    assert record.intake_deadlines[0].meta.confidence == "low"

