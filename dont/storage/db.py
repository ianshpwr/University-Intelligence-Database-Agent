"""SQLite persistence and JSON/CSV exports for university records."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from core.schema import (
    About,
    AcceptanceRate,
    AverageSalary,
    CourseListing,
    FieldMeta,
    GraduateEmployment,
    IntakeDeadline,
    LivingCosts,
    MoneyRange,
    Ranking,
    Scholarship,
    TuitionFee,
    UniversityRecord,
    VisaPolicy,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


class MetaColumns:
    """Mixin for flattened metadata columns."""

    confidence: Mapped[str] = mapped_column(String(20), default="missing")
    source_url: Mapped[str] = mapped_column(Text, default="")
    cross_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    extracted_at: Mapped[datetime] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class UniversityRow(Base, MetaColumns):
    """About/profile row, one per university."""

    __tablename__ = "universities"

    university_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Text)
    founding_year: Mapped[Optional[int]] = mapped_column(Integer)
    ranking_value: Mapped[Optional[str]] = mapped_column(Text)
    ranking_source: Mapped[Optional[str]] = mapped_column(Text)
    ranking_year: Mapped[Optional[int]] = mapped_column(Integer)
    city: Mapped[Optional[str]] = mapped_column(Text)
    country: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[Optional[str]] = mapped_column(String(20))
    website_url: Mapped[Optional[str]] = mapped_column(Text)


class TuitionFeeRow(Base, MetaColumns):
    """Tuition fee row."""

    __tablename__ = "tuition_fees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    university_id: Mapped[str] = mapped_column(ForeignKey("universities.university_id"))
    program_level: Mapped[Optional[str]] = mapped_column(String(40))
    domestic_fee: Mapped[Optional[float]] = mapped_column(Float)
    international_fee: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    fee_period: Mapped[Optional[str]] = mapped_column(Text)
    academic_year: Mapped[Optional[str]] = mapped_column(Text)


class LivingCostRow(Base, MetaColumns):
    """Living cost row, one per university."""

    __tablename__ = "living_costs"

    university_id: Mapped[str] = mapped_column(ForeignKey("universities.university_id"), primary_key=True)
    city: Mapped[Optional[str]] = mapped_column(Text)
    monthly_rent_min: Mapped[Optional[float]] = mapped_column(Float)
    monthly_rent_max: Mapped[Optional[float]] = mapped_column(Float)
    food_cost: Mapped[Optional[float]] = mapped_column(Float)
    transport_cost: Mapped[Optional[float]] = mapped_column(Float)
    total_estimate: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    source_year: Mapped[Optional[int]] = mapped_column(Integer)


class ScholarshipRow(Base, MetaColumns):
    """Scholarship row."""

    __tablename__ = "scholarships"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    university_id: Mapped[str] = mapped_column(ForeignKey("universities.university_id"))
    name: Mapped[Optional[str]] = mapped_column(Text)
    value: Mapped[Optional[str]] = mapped_column(Text)
    eligibility_criteria: Mapped[Optional[str]] = mapped_column(Text)
    application_deadline: Mapped[Optional[str]] = mapped_column(Text)
    renewable: Mapped[Optional[bool]] = mapped_column(Boolean)


class AcceptanceRateRow(Base, MetaColumns):
    """Acceptance-rate row, one per university."""

    __tablename__ = "acceptance_rates"

    university_id: Mapped[str] = mapped_column(ForeignKey("universities.university_id"), primary_key=True)
    overall_pct: Mapped[Optional[float]] = mapped_column(Float)
    undergrad_pct: Mapped[Optional[float]] = mapped_column(Float)
    postgrad_pct: Mapped[Optional[float]] = mapped_column(Float)
    year: Mapped[Optional[int]] = mapped_column(Integer)


class GraduateEmploymentRow(Base, MetaColumns):
    """Graduate employment row, one per university."""

    __tablename__ = "graduate_employment"

    university_id: Mapped[str] = mapped_column(ForeignKey("universities.university_id"), primary_key=True)
    employed_pct_6months: Mapped[Optional[float]] = mapped_column(Float)
    source_name: Mapped[Optional[str]] = mapped_column(Text)
    source_year: Mapped[Optional[int]] = mapped_column(Integer)


class AverageSalaryRow(Base, MetaColumns):
    """Average salary row."""

    __tablename__ = "average_salaries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    university_id: Mapped[str] = mapped_column(ForeignKey("universities.university_id"))
    field_of_study: Mapped[Optional[str]] = mapped_column(Text)
    median_salary: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    source_year: Mapped[Optional[int]] = mapped_column(Integer)


class VisaPolicyRow(Base, MetaColumns):
    """Visa policy row, one per university."""

    __tablename__ = "visa_policies"

    university_id: Mapped[str] = mapped_column(ForeignKey("universities.university_id"), primary_key=True)
    visa_type: Mapped[Optional[str]] = mapped_column(Text)
    processing_time: Mapped[Optional[str]] = mapped_column(Text)
    key_requirements: Mapped[str] = mapped_column(Text, default="[]")
    country: Mapped[Optional[str]] = mapped_column(Text)


class IntakeDeadlineRow(Base, MetaColumns):
    """Intake deadline row."""

    __tablename__ = "intake_deadlines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    university_id: Mapped[str] = mapped_column(ForeignKey("universities.university_id"))
    intake_name: Mapped[Optional[str]] = mapped_column(Text)
    application_open: Mapped[Optional[str]] = mapped_column(Text)
    application_close: Mapped[Optional[str]] = mapped_column(Text)
    program_level: Mapped[Optional[str]] = mapped_column(String(40))


class CourseRow(Base, MetaColumns):
    """Course listing row."""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    university_id: Mapped[str] = mapped_column(ForeignKey("universities.university_id"))
    code: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(Text)
    credits: Mapped[Optional[float]] = mapped_column(Float)
    description: Mapped[Optional[str]] = mapped_column(Text)
    prerequisites: Mapped[str] = mapped_column(Text, default="[]")
    mode: Mapped[Optional[str]] = mapped_column(Text)
    department: Mapped[Optional[str]] = mapped_column(Text)


LIST_TABLES = [TuitionFeeRow, ScholarshipRow, AverageSalaryRow, IntakeDeadlineRow, CourseRow]


class Database:
    """High-level database API for saving, reading, and exporting records."""

    def __init__(self, db_path: str | Path = "storage/university_intelligence.sqlite3") -> None:
        """Create a database connection factory."""

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.Session = sessionmaker(bind=self.engine)

    def init_db(self) -> None:
        """Create all database tables."""

        Base.metadata.create_all(self.engine)

    def save(self, record: UniversityRecord) -> None:
        """Replace and save a complete university record."""

        self.init_db()
        with self.Session() as session:
            self._delete_existing(session, record.university_id)
            session.add(_about_row(record))
            session.add(_living_row(record))
            session.add(_acceptance_row(record))
            session.add(_employment_row(record))
            session.add(_visa_row(record))
            session.add_all(_tuition_rows(record))
            session.add_all(_scholarship_rows(record))
            session.add_all(_salary_rows(record))
            session.add_all(_intake_rows(record))
            session.add_all(_course_rows(record))
            session.commit()

    def get(self, university_id: str) -> UniversityRecord:
        """Read a complete university record by ID."""

        self.init_db()
        with self.Session() as session:
            uni = session.get(UniversityRow, university_id)
            if uni is None:
                raise KeyError(f"University not found: {university_id}")
            return UniversityRecord(
                university_id=university_id,
                about=_about_model(uni),
                tuition_fees=[_tuition_model(row) for row in session.scalars(select(TuitionFeeRow).where(TuitionFeeRow.university_id == university_id))],
                living_costs=_living_model(session.get(LivingCostRow, university_id)),
                scholarships=[_scholarship_model(row) for row in session.scalars(select(ScholarshipRow).where(ScholarshipRow.university_id == university_id))],
                acceptance_rate=_acceptance_model(session.get(AcceptanceRateRow, university_id)),
                graduate_employment=_employment_model(session.get(GraduateEmploymentRow, university_id)),
                average_salaries=[_salary_model(row) for row in session.scalars(select(AverageSalaryRow).where(AverageSalaryRow.university_id == university_id))],
                visa_policy=_visa_model(session.get(VisaPolicyRow, university_id)),
                intake_deadlines=[_intake_model(row) for row in session.scalars(select(IntakeDeadlineRow).where(IntakeDeadlineRow.university_id == university_id))],
                course_listings=[_course_model(row) for row in session.scalars(select(CourseRow).where(CourseRow.university_id == university_id))],
            )

    def list_universities(self) -> list[dict[str, str | None]]:
        """Return saved university IDs and names."""

        self.init_db()
        with self.Session() as session:
            return [
                {"id": row.university_id, "name": row.name}
                for row in session.scalars(select(UniversityRow).order_by(UniversityRow.university_id))
            ]

    def export_json(self, university_id: str, out_dir: str | Path = "storage/output") -> Path:
        """Export a nested JSON record."""

        record = self.get(university_id)
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{university_id}.json"
        path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return path

    def export_csv(self, university_id: str, out_dir: str | Path = "storage/output") -> list[Path]:
        """Export summary and list-category CSV files."""

        record = self.get(university_id)
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        written = [_write_csv(out / f"{university_id}_summary.csv", [_summary_row(record)])]
        list_categories = {
            "tuition_fees": record.tuition_fees,
            "scholarships": record.scholarships,
            "average_salaries": record.average_salaries,
            "intake_deadlines": record.intake_deadlines,
            "courses": record.course_listings,
        }
        for category, items in list_categories.items():
            rows = [_flatten(item.model_dump(mode="json")) for item in items]
            written.append(_write_csv(out / f"{university_id}_{category}.csv", rows))
        return written

    def _delete_existing(self, session: Session, university_id: str) -> None:
        """Delete existing rows for a university before replacing them."""

        for table in LIST_TABLES:
            session.execute(delete(table).where(table.university_id == university_id))
        for table in (LivingCostRow, AcceptanceRateRow, GraduateEmploymentRow, VisaPolicyRow):
            session.execute(delete(table).where(table.university_id == university_id))
        session.execute(delete(UniversityRow).where(UniversityRow.university_id == university_id))


def init_db(db_path: str | Path = "storage/university_intelligence.sqlite3") -> Database:
    """Initialize database tables and return a ``Database`` instance."""

    db = Database(db_path)
    db.init_db()
    return db


def _meta_kwargs(meta: FieldMeta) -> dict[str, Any]:
    return {
        "confidence": meta.confidence,
        "source_url": meta.source_url,
        "cross_validated": meta.cross_validated,
        "extracted_at": meta.extracted_at.replace(tzinfo=None),
        "notes": meta.notes,
    }


def _meta_model(row: Any | None) -> FieldMeta:
    if row is None:
        return FieldMeta()
    extracted_at = row.extracted_at or datetime.utcnow()
    return FieldMeta(
        confidence=row.confidence,
        source_url=row.source_url or "",
        cross_validated=bool(row.cross_validated),
        extracted_at=extracted_at,
        notes=row.notes,
    )


def _about_row(record: UniversityRecord) -> UniversityRow:
    about = record.about
    ranking = about.ranking or Ranking()
    return UniversityRow(
        university_id=record.university_id,
        name=about.name,
        founding_year=about.founding_year,
        ranking_value=ranking.value,
        ranking_source=ranking.source,
        ranking_year=ranking.year,
        city=about.city,
        country=about.country,
        type=about.type,
        website_url=about.website_url,
        **_meta_kwargs(about.meta),
    )


def _about_model(row: UniversityRow) -> About:
    return About(
        name=row.name,
        founding_year=row.founding_year,
        ranking=Ranking(value=row.ranking_value, source=row.ranking_source, year=row.ranking_year),
        city=row.city,
        country=row.country,
        type=row.type,  # type: ignore[arg-type]
        website_url=row.website_url,
        meta=_meta_model(row),
    )


def _tuition_rows(record: UniversityRecord) -> list[TuitionFeeRow]:
    return [
        TuitionFeeRow(university_id=record.university_id, **fee.model_dump(exclude={"meta"}), **_meta_kwargs(fee.meta))
        for fee in record.tuition_fees
    ]


def _tuition_model(row: TuitionFeeRow) -> TuitionFee:
    return TuitionFee(
        program_level=row.program_level,  # type: ignore[arg-type]
        domestic_fee=row.domestic_fee,
        international_fee=row.international_fee,
        currency=row.currency,
        fee_period=row.fee_period,
        academic_year=row.academic_year,
        meta=_meta_model(row),
    )


def _living_row(record: UniversityRecord) -> LivingCostRow:
    costs = record.living_costs
    rent = costs.monthly_rent_range or MoneyRange()
    return LivingCostRow(
        university_id=record.university_id,
        city=costs.city,
        monthly_rent_min=rent.min,
        monthly_rent_max=rent.max,
        food_cost=costs.food_cost,
        transport_cost=costs.transport_cost,
        total_estimate=costs.total_estimate,
        currency=costs.currency,
        source_year=costs.source_year,
        **_meta_kwargs(costs.meta),
    )


def _living_model(row: LivingCostRow | None) -> LivingCosts:
    if row is None:
        return LivingCosts()
    return LivingCosts(
        city=row.city,
        monthly_rent_range=MoneyRange(min=row.monthly_rent_min, max=row.monthly_rent_max),
        food_cost=row.food_cost,
        transport_cost=row.transport_cost,
        total_estimate=row.total_estimate,
        currency=row.currency,
        source_year=row.source_year,
        meta=_meta_model(row),
    )


def _scholarship_rows(record: UniversityRecord) -> list[ScholarshipRow]:
    return [
        ScholarshipRow(university_id=record.university_id, **item.model_dump(exclude={"meta"}), **_meta_kwargs(item.meta))
        for item in record.scholarships
    ]


def _scholarship_model(row: ScholarshipRow) -> Scholarship:
    return Scholarship(
        name=row.name,
        value=row.value,
        eligibility_criteria=row.eligibility_criteria,
        application_deadline=row.application_deadline,
        renewable=row.renewable,
        meta=_meta_model(row),
    )


def _acceptance_row(record: UniversityRecord) -> AcceptanceRateRow:
    rate = record.acceptance_rate
    return AcceptanceRateRow(university_id=record.university_id, **rate.model_dump(exclude={"meta"}), **_meta_kwargs(rate.meta))


def _acceptance_model(row: AcceptanceRateRow | None) -> AcceptanceRate:
    if row is None:
        return AcceptanceRate()
    return AcceptanceRate(
        overall_pct=row.overall_pct,
        undergrad_pct=row.undergrad_pct,
        postgrad_pct=row.postgrad_pct,
        year=row.year,
        meta=_meta_model(row),
    )


def _employment_row(record: UniversityRecord) -> GraduateEmploymentRow:
    employment = record.graduate_employment
    return GraduateEmploymentRow(
        university_id=record.university_id,
        **employment.model_dump(exclude={"meta"}),
        **_meta_kwargs(employment.meta),
    )


def _employment_model(row: GraduateEmploymentRow | None) -> GraduateEmployment:
    if row is None:
        return GraduateEmployment()
    return GraduateEmployment(
        employed_pct_6months=row.employed_pct_6months,
        source_name=row.source_name,
        source_year=row.source_year,
        meta=_meta_model(row),
    )


def _salary_rows(record: UniversityRecord) -> list[AverageSalaryRow]:
    return [
        AverageSalaryRow(university_id=record.university_id, **item.model_dump(exclude={"meta"}), **_meta_kwargs(item.meta))
        for item in record.average_salaries
    ]


def _salary_model(row: AverageSalaryRow) -> AverageSalary:
    return AverageSalary(
        field_of_study=row.field_of_study,
        median_salary=row.median_salary,
        currency=row.currency,
        source_year=row.source_year,
        meta=_meta_model(row),
    )


def _visa_row(record: UniversityRecord) -> VisaPolicyRow:
    visa = record.visa_policy
    return VisaPolicyRow(
        university_id=record.university_id,
        visa_type=visa.visa_type,
        processing_time=visa.processing_time,
        key_requirements=json.dumps(visa.key_requirements),
        country=visa.country,
        **_meta_kwargs(visa.meta),
    )


def _visa_model(row: VisaPolicyRow | None) -> VisaPolicy:
    if row is None:
        return VisaPolicy()
    return VisaPolicy(
        visa_type=row.visa_type,
        processing_time=row.processing_time,
        key_requirements=json.loads(row.key_requirements or "[]"),
        country=row.country,
        meta=_meta_model(row),
    )


def _intake_rows(record: UniversityRecord) -> list[IntakeDeadlineRow]:
    return [
        IntakeDeadlineRow(university_id=record.university_id, **item.model_dump(exclude={"meta"}), **_meta_kwargs(item.meta))
        for item in record.intake_deadlines
    ]


def _intake_model(row: IntakeDeadlineRow) -> IntakeDeadline:
    return IntakeDeadline(
        intake_name=row.intake_name,
        application_open=row.application_open,
        application_close=row.application_close,
        program_level=row.program_level,  # type: ignore[arg-type]
        meta=_meta_model(row),
    )


def _course_rows(record: UniversityRecord) -> list[CourseRow]:
    rows = []
    for course in record.course_listings:
        data = course.model_dump(exclude={"meta", "prerequisites"})
        rows.append(
            CourseRow(
                university_id=record.university_id,
                prerequisites=json.dumps(course.prerequisites),
                **data,
                **_meta_kwargs(course.meta),
            )
        )
    return rows


def _course_model(row: CourseRow) -> CourseListing:
    return CourseListing(
        code=row.code,
        title=row.title,
        credits=row.credits,
        description=row.description,
        prerequisites=json.loads(row.prerequisites or "[]"),
        mode=row.mode,
        department=row.department,
        meta=_meta_model(row),
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    fieldnames = sorted({key for row in rows for key in row.keys()}) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def _summary_row(record: UniversityRecord) -> dict[str, Any]:
    data = record.model_dump(mode="json")
    row = {"university_id": record.university_id}
    for category in ("about", "living_costs", "acceptance_rate", "graduate_employment", "visa_policy"):
        row.update({f"{category}.{key}": value for key, value in _flatten(data[category]).items()})
    return row


def _flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in data.items():
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            output.update(_flatten(value, name))
        elif isinstance(value, list):
            output[name] = json.dumps(value)
        else:
            output[name] = value
    return output

