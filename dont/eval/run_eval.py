"""Evaluate extracted JSON against manually curated ground truth."""

from __future__ import annotations

import argparse
import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


def main() -> None:
    """Run field-by-field evaluation and write a Markdown report."""

    parser = argparse.ArgumentParser(description="Evaluate university extraction outputs")
    parser.add_argument("--university", action="append", help="University ID to evaluate; repeatable")
    parser.add_argument("--output-dir", default="storage/output")
    parser.add_argument("--ground-truth-dir", default="eval/ground_truth")
    parser.add_argument("--report", default="eval/eval_report.md")
    args = parser.parse_args()

    ids = args.university or [path.stem for path in Path(args.ground_truth_dir).glob("*.json")]
    sections: list[str] = ["# Evaluation Report\n"]
    overall = []
    for university_id in ids:
        extracted = _load_json(Path(args.output_dir) / f"{university_id}.json")
        truth = _load_json(Path(args.ground_truth_dir) / f"{university_id}.json")
        rows = []
        for field, truth_value in _flatten(truth).items():
            extracted_value = _flatten(extracted).get(field)
            confidence = _confidence_for_field(extracted, field)
            match_type = _match_type(extracted_value, truth_value)
            rows.append((field, extracted_value, truth_value, match_type, confidence))
        correct = sum(1 for row in rows if row[3] in {"exact", "fuzzy", "missing"})
        accuracy = correct / len(rows) if rows else 0
        overall.append(accuracy)
        sections.append(_table(university_id, rows, accuracy))
    avg = sum(overall) / len(overall) if overall else 0
    sections.append(f"\n## Overall\n\nAccuracy: {avg:.1%}\n\n")
    sections.append("## Validator Flag Accuracy\n\nReview low-confidence rows above; mismatches should be concentrated there.\n")
    Path(args.report).write_text("\n".join(sections), encoding="utf-8")
    print(args.report)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    output: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "meta":
                continue
            name = f"{prefix}.{key}" if prefix else key
            output.update(_flatten(child, name))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            output.update(_flatten(child, f"{prefix}[{index}]"))
    else:
        output[prefix] = value
    return output


def _match_type(extracted: Any, truth: Any) -> str:
    if extracted in (None, "") and truth in (None, ""):
        return "missing"
    if extracted not in (None, "") and truth in (None, ""):
        return "hallucinated"
    if extracted == truth:
        return "exact"
    if isinstance(extracted, str) and isinstance(truth, str):
        if SequenceMatcher(None, extracted.lower(), truth.lower()).ratio() > 0.85:
            return "fuzzy"
    return "wrong"


def _confidence_for_field(extracted: dict[str, Any], field: str) -> str:
    current: Any = extracted
    parts = field.replace("]", "").replace("[", ".").split(".")
    for part in parts[:-1]:
        if isinstance(current, list) and part.isdigit():
            current = current[int(part)] if int(part) < len(current) else {}
        elif isinstance(current, dict):
            current = current.get(part, {})
    if isinstance(current, dict):
        return str(current.get("meta", {}).get("confidence", ""))
    return ""


def _table(university_id: str, rows: list[tuple[str, Any, Any, str, str]], accuracy: float) -> str:
    lines = [
        f"## {university_id}",
        "",
        f"Accuracy: {accuracy:.1%}",
        "",
        "| field | extracted | ground_truth | match_type | assigned_confidence |",
        "|---|---|---|---|---|",
    ]
    for field, extracted, truth, match_type, confidence in rows:
        lines.append(f"| {field} | {_cell(extracted)} | {_cell(truth)} | {match_type} | {confidence} |")
    return "\n".join(lines) + "\n"


def _cell(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=True) if isinstance(value, (dict, list)) else str(value)
    return text.replace("|", "\\|").replace("\n", " ")[:160]


if __name__ == "__main__":
    main()

