"""Tests for database save and export."""

from pathlib import Path

from core.schema import About, FieldMeta, Scholarship, UniversityRecord
from storage.db import Database


def test_database_roundtrip_and_exports(tmp_path: Path) -> None:
    """Database can save, reload, and export a record."""

    db = Database(tmp_path / "test.sqlite3")
    record = UniversityRecord(
        university_id="uni_a",
        about=About(name="Test University", meta=FieldMeta(confidence="high", source_url="https://example.edu")),
        scholarships=[Scholarship(name="Merit", value="$1000", meta=FieldMeta(confidence="high"))],
    )
    db.save(record)
    loaded = db.get("uni_a")
    assert loaded.about.name == "Test University"
    assert loaded.scholarships[0].name == "Merit"
    assert db.export_json("uni_a", tmp_path).exists()
    csv_paths = db.export_csv("uni_a", tmp_path)
    assert any(path.name.endswith("_summary.csv") for path in csv_paths)

