"""Config discovery and validation for target universities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class UniversityConfig(BaseModel):
    """Validated scraper configuration for a single university."""

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    base_url: HttpUrl
    city: str
    country: str
    expected_currency: str
    discovery_mode: Literal["manual", "auto"] = "manual"
    seed_pages: Optional[dict[str, list[str]]] = None
    secondary_sources: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def id_must_be_nonempty(cls, value: str) -> str:
        """Validate that the university ID is present."""

        if not value.strip():
            raise ValueError("id must not be empty")
        return value

    @model_validator(mode="after")
    def _check_seed_pages_for_mode(self) -> "UniversityConfig":
        """Enforce seed_pages rules based on discovery_mode.

        - ``manual``: ``seed_pages`` must be present and non-empty.
        - ``auto``: ``seed_pages`` may be omitted or empty (None / {}).
        """

        # Treat None and empty-dict as equivalent to "absent".
        has_seeds = bool(self.seed_pages)  # False for None or {}
        if self.discovery_mode == "manual" and not has_seeds:
            raise ValueError(
                "seed_pages must be present and non-empty when discovery_mode is 'manual'"
            )
        return self


def load_configs(config_dir: str | Path = "config/universities") -> dict[str, UniversityConfig]:
    """Load all university JSON configs from a directory.

    Args:
        config_dir: Directory containing ``*.json`` config files.

    Returns:
        Mapping of university ID to validated ``UniversityConfig``.
    """

    directory = Path(config_dir)
    configs: dict[str, UniversityConfig] = {}
    for path in sorted(directory.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        config = UniversityConfig.model_validate(payload)
        configs[config.id] = config
    return configs


def load_config(university_id: str, config_dir: str | Path = "config/universities") -> UniversityConfig:
    """Load one university config by ID.

    Args:
        university_id: ID from the config file.
        config_dir: Directory containing config JSON files.

    Returns:
        Matching ``UniversityConfig``.

    Raises:
        KeyError: If no config exists for the requested ID.
    """

    configs = load_configs(config_dir)
    if university_id not in configs:
        raise KeyError(f"Unknown university ID: {university_id}")
    return configs[university_id]

