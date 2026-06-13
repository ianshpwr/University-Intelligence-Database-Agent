"""Pydantic schemas for university intelligence records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


Confidence = Literal["high", "medium", "low", "missing"]


class FieldMeta(BaseModel):
    """Metadata describing provenance and extraction confidence for a record."""

    confidence: Confidence = "missing"
    source_url: str = ""
    cross_validated: bool = False
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None


class Ranking(BaseModel):
    """University ranking value from a named source and year."""

    value: Optional[str] = None
    source: Optional[str] = None
    year: Optional[int] = None


class About(BaseModel):
    """General university profile data."""

    name: Optional[str] = None
    founding_year: Optional[int] = None
    ranking: Optional[Ranking] = None
    city: Optional[str] = None
    country: Optional[str] = None
    type: Optional[Literal["public", "private"]] = None
    website_url: Optional[str] = None
    meta: FieldMeta = Field(default_factory=FieldMeta)


class TuitionFee(BaseModel):
    """Tuition fee information for one program level."""

    program_level: Optional[Literal["undergrad", "postgrad", "phd"]] = None
    domestic_fee: Optional[float] = None
    international_fee: Optional[float] = None
    currency: Optional[str] = None
    fee_period: Optional[str] = None
    academic_year: Optional[str] = None
    meta: FieldMeta = Field(default_factory=FieldMeta)


class MoneyRange(BaseModel):
    """Minimum and maximum monetary range."""

    min: Optional[float] = None
    max: Optional[float] = None


class LivingCosts(BaseModel):
    """Estimated cost of living for the university city."""

    city: Optional[str] = None
    monthly_rent_range: Optional[MoneyRange] = None
    food_cost: Optional[float] = None
    transport_cost: Optional[float] = None
    total_estimate: Optional[float] = None
    currency: Optional[str] = None
    source_year: Optional[int] = None
    meta: FieldMeta = Field(default_factory=FieldMeta)


class Scholarship(BaseModel):
    """Scholarship or award available to students."""

    name: Optional[str] = None
    value: Optional[str] = None
    eligibility_criteria: Optional[str] = None
    application_deadline: Optional[str] = None
    renewable: Optional[bool] = None
    meta: FieldMeta = Field(default_factory=FieldMeta)


class AcceptanceRate(BaseModel):
    """Acceptance-rate metrics."""

    overall_pct: Optional[float] = None
    undergrad_pct: Optional[float] = None
    postgrad_pct: Optional[float] = None
    year: Optional[int] = None
    meta: FieldMeta = Field(default_factory=FieldMeta)


class GraduateEmployment(BaseModel):
    """Graduate employment outcome metrics."""

    employed_pct_6months: Optional[float] = None
    source_name: Optional[str] = None
    source_year: Optional[int] = None
    meta: FieldMeta = Field(default_factory=FieldMeta)


class AverageSalary(BaseModel):
    """Salary outcome for one field of study."""

    field_of_study: Optional[str] = None
    median_salary: Optional[float] = None
    currency: Optional[str] = None
    source_year: Optional[int] = None
    meta: FieldMeta = Field(default_factory=FieldMeta)


class VisaPolicy(BaseModel):
    """Student visa policy summary for the university country."""

    visa_type: Optional[str] = None
    processing_time: Optional[str] = None
    key_requirements: list[str] = Field(default_factory=list)
    country: Optional[str] = None
    meta: FieldMeta = Field(default_factory=FieldMeta)


class IntakeDeadline(BaseModel):
    """Application opening and closing dates for one intake."""

    intake_name: Optional[str] = None
    application_open: Optional[str] = None
    application_close: Optional[str] = None
    program_level: Optional[Literal["undergrad", "postgrad", "phd"]] = None
    meta: FieldMeta = Field(default_factory=FieldMeta)


class CourseListing(BaseModel):
    """Course catalog entry."""

    code: Optional[str] = None
    title: Optional[str] = None
    credits: Optional[float] = None
    description: Optional[str] = None
    prerequisites: list[str] = Field(default_factory=list)
    mode: Optional[str] = None
    department: Optional[str] = None
    meta: FieldMeta = Field(default_factory=FieldMeta)


class UniversityRecord(BaseModel):
    """Complete intelligence record for one university."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    university_id: str
    about: About = Field(default_factory=About)
    tuition_fees: list[TuitionFee] = Field(default_factory=list)
    living_costs: LivingCosts = Field(default_factory=LivingCosts)
    scholarships: list[Scholarship] = Field(default_factory=list)
    acceptance_rate: AcceptanceRate = Field(default_factory=AcceptanceRate)
    graduate_employment: GraduateEmployment = Field(default_factory=GraduateEmployment)
    average_salaries: list[AverageSalary] = Field(default_factory=list)
    visa_policy: VisaPolicy = Field(default_factory=VisaPolicy)
    intake_deadlines: list[IntakeDeadline] = Field(default_factory=list)
    course_listings: list[CourseListing] = Field(default_factory=list)


class CategoryList(BaseModel):
    """Wrapper used when an extraction category returns a list."""

    items: list[dict] = Field(default_factory=list)


CATEGORY_MODEL_MAP = {
    "about": About,
    "tuition": TuitionFee,
    "tuition_fees": TuitionFee,
    "living_costs": LivingCosts,
    "scholarships": Scholarship,
    "acceptance_rate": AcceptanceRate,
    "employment": GraduateEmployment,
    "graduate_employment": GraduateEmployment,
    "salaries": AverageSalary,
    "average_salaries": AverageSalary,
    "visa": VisaPolicy,
    "visa_policy": VisaPolicy,
    "intakes": IntakeDeadline,
    "intake_deadlines": IntakeDeadline,
    "courses": CourseListing,
    "course_listings": CourseListing,
}

LIST_CATEGORIES = {
    "tuition",
    "tuition_fees",
    "scholarships",
    "salaries",
    "average_salaries",
    "intakes",
    "intake_deadlines",
    "courses",
    "course_listings",
}

