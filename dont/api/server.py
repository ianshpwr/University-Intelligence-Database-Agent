"""Read-only FastAPI server for saved university intelligence records."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from storage.db import Database

app = FastAPI(title="University Intelligence API")
db = Database()

VALID_CATEGORIES = {
    "about",
    "tuition_fees",
    "living_costs",
    "scholarships",
    "acceptance_rate",
    "graduate_employment",
    "average_salaries",
    "visa_policy",
    "intake_deadlines",
    "course_listings",
}


@app.get("/universities")
def list_universities() -> list[dict[str, str | None]]:
    """Return saved university IDs and names."""

    return db.list_universities()


@app.get("/universities/{university_id}")
def get_university(university_id: str) -> dict:
    """Return a full university record."""

    try:
        return db.get(university_id).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/universities/{university_id}/{category}")
def get_category(university_id: str, category: str) -> object:
    """Return one category from a university record."""

    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=404, detail=f"Unknown category: {category}")
    try:
        record = db.get(university_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return getattr(record, category).model_dump(mode="json") if hasattr(getattr(record, category), "model_dump") else [
        item.model_dump(mode="json") for item in getattr(record, category)
    ]

