"""Command-line interface for the university intelligence agent."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from core.config_loader import load_config, load_configs
from core.extractor import Extractor
from core.fetcher import Fetcher
from core.pipeline import run_university
from core.schema import UniversityRecord
from storage.db import Database

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Parse CLI args and dispatch scrape/export commands."""

    load_dotenv()
    parser = argparse.ArgumentParser(description="University Intelligence Database Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scrape = subparsers.add_parser("scrape", help="Scrape and save university data")
    scrape.add_argument(
        "--university",
        default=None,
        help="University ID to scrape (omit to scrape all configured universities)",
    )
    scrape.add_argument(
        "--mode",
        choices=["manual", "auto"],
        default="auto",
        help="manual uses configured seed URLs; auto also runs homepage/sitemap category discovery (default: auto)",
    )

    export = subparsers.add_parser("export", help="Export saved university data")
    export.add_argument(
        "--university",
        default=None,
        help="University ID to export (omit to export all configured universities)",
    )
    export.add_argument(
        "--format",
        choices=["json", "csv", "both"],
        default="both",
        help="Output format (default: both)",
    )

    args = parser.parse_args()
    db = Database()
    db.init_db()

    if args.command == "scrape":
        _handle_scrape(args, db)
    elif args.command == "export":
        _handle_export(args, db)


# ---------------------------------------------------------------------------
# Scrape
# ---------------------------------------------------------------------------

def _handle_scrape(args: argparse.Namespace, db: Database) -> None:
    """Run scrape for one or all universities, catching per-university errors."""

    configs = load_configs()
    if args.university:
        selected = [load_config(args.university)]
    else:
        selected = list(configs.values())

    if not selected:
        print("No university configs found in config/universities/. Nothing to scrape.")
        return

    extractor = _make_extractor_for_cli()
    succeeded: list[str] = []
    failed: list[tuple[str, str]] = []

    for config in selected:
        print(f"\n{'='*60}")
        print(f"  Scraping: {config.name} ({config.id})  [mode={args.mode}]")
        print(f"{'='*60}")
        try:
            fetcher = Fetcher()
            record = run_university(config, extractor, fetcher, db, mode=args.mode)
            summary = summarize_record(record)
            msg = (
                f"  Done. pages visited={fetcher.stats['visited']} "
                f"failed={fetcher.stats['failed']}  "
                f"fields extracted={summary['extracted']} "
                f"missing={summary['missing']} "
                f"low_confidence={summary['low']}"
            )
            print(msg)
            succeeded.append(config.id)
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"
            print(f"  ERROR: {err}")
            logger.exception("Scrape failed for %s", config.id)
            failed.append((config.id, err))

    _print_summary("Scrape", succeeded, failed)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def _handle_export(args: argparse.Namespace, db: Database) -> None:
    """Run export for one or all universities, catching per-university errors."""

    configs = load_configs()
    if args.university:
        selected_ids = [args.university]
    else:
        selected_ids = list(configs.keys())

    if not selected_ids:
        print("No university configs found in config/universities/. Nothing to export.")
        return

    succeeded: list[str] = []
    failed: list[tuple[str, str]] = []

    for uid in selected_ids:
        print(f"\n{'='*60}")
        print(f"  Exporting: {uid}  [format={args.format}]")
        print(f"{'='*60}")
        try:
            output_paths: list[Path] = []
            if args.format in ("json", "both"):
                output_paths.append(db.export_json(uid))
            if args.format in ("csv", "both"):
                output_paths.extend(db.export_csv(uid))
            for path in output_paths:
                print(f"  {path}")
            succeeded.append(uid)
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"
            print(f"  ERROR: {err}")
            logger.exception("Export failed for %s", uid)
            failed.append((uid, err))

    _print_summary("Export", succeeded, failed)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_summary(action: str, succeeded: list[str], failed: list[tuple[str, str]]) -> None:
    """Print a final success/failure summary."""

    print(f"\n{'='*60}")
    print(f"  {action} summary")
    print(f"{'='*60}")
    if succeeded:
        print(f"  Succeeded ({len(succeeded)}): {', '.join(succeeded)}")
    if failed:
        print(f"  Failed    ({len(failed)}):")
        for uid, reason in failed:
            print(f"    - {uid}: {reason}")
    if not succeeded and not failed:
        print("  Nothing processed.")


def summarize_record(record: UniversityRecord) -> dict[str, int]:
    """Count extracted, missing, and low-confidence leaf records."""

    data = record.model_dump()
    extracted = 0
    missing = 0
    low = 0

    def walk(value: object) -> None:
        nonlocal extracted, missing, low
        if isinstance(value, dict):
            meta = value.get("meta")
            if isinstance(meta, dict):
                confidence = meta.get("confidence")
                if confidence == "missing":
                    missing += 1
                else:
                    extracted += 1
                if confidence == "low":
                    low += 1
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)
    return {"extracted": extracted, "missing": missing, "low": low}


class NoopExtractor:
    """Extractor stand-in for offline/manual smoke runs with no API key."""

    llm_pagination_checks = 0
    llm_cache: dict[str, str] = {}

    def extract(self, parsed: object) -> None:
        """Return no extraction result without raising."""

        logger.warning("Skipping extraction because GROQ_API_KEY is not configured")
        return None

    def call_cached(self, cache_key: str, system: str, user: str) -> str:
        """Raise so callers use their deterministic fallback."""

        raise RuntimeError("GROQ_API_KEY is not configured")

    def _call(self, system: str, user: str) -> str:
        """Raise for optional LLM fallback callers so they can use deterministic fallback."""

        raise RuntimeError("GROQ_API_KEY is not configured")


def _make_extractor_for_cli() -> Extractor | NoopExtractor:
    """Create a real extractor, or a no-op extractor for runnable smoke checks."""

    try:
        return Extractor(api_key=os.getenv("GROQ_API_KEY"), model=os.getenv("GROQ_MODEL"))
    except ValueError as exc:
        logger.warning("%s; scrape will save a mostly empty record", exc)
        return NoopExtractor()


if __name__ == "__main__":
    main()
