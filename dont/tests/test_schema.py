"""Tests for Pydantic schemas."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from core.schema import FieldMeta, TuitionFee, UniversityRecord


def test_university_record_defaults_are_present() -> None:
    """A sparse record should still include all top-level categories."""

    record = UniversityRecord(university_id="uni_a")
    assert record.about.meta.confidence == "missing"
    assert record.tuition_fees == []
    assert record.visa_policy.key_requirements == []


def test_meta_rejects_unknown_confidence() -> None:
    """Confidence values are constrained to the allowed labels."""

    with pytest.raises(ValidationError):
        FieldMeta(confidence="certain", source_url="", extracted_at=datetime.now(timezone.utc))


def test_tuition_program_level_literal() -> None:
    """Program levels use normalized literals."""

    fee = TuitionFee(program_level="undergrad", domestic_fee=12000)
    assert fee.program_level == "undergrad"
    with pytest.raises(ValidationError):
        TuitionFee(program_level="masters")

