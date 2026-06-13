"""LLM-based structured extraction using Groq (OpenAI-compatible API)."""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

from openai import OpenAI, APIError
from pydantic import ValidationError

from core.parser import ParsedPage
from core.schema import CATEGORY_MODEL_MAP, LIST_CATEGORIES

logger = logging.getLogger(__name__)

MAX_PROMPT_CHARS = 8_000
DEFAULT_MODEL = "llama-3.3-70b-versatile"
# Faster/cheaper fallback option: "llama-3.1-8b-instant"


class Extractor:
    """Extract category-specific structured JSON from clean page text."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        """Create a Groq client via the OpenAI-compatible SDK.

        Args:
            api_key: Groq API key. Falls back to ``GROQ_API_KEY``.
            model: Groq model name. Falls back to ``GROQ_MODEL`` then
                ``llama-3.3-70b-versatile``.
        """

        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required")
        self.model = model or os.getenv("GROQ_MODEL", DEFAULT_MODEL)
        # Groq exposes an OpenAI-compatible /chat/completions endpoint.
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.llm_cache: dict[str, str] = {}
        self.llm_pagination_checks = 0
        # Minimum seconds between consecutive LLM calls to stay under Groq's
        # free-tier 30 RPM limit (~2 s gap → ~24 RPM worst case).
        self._call_delay: float = float(
            os.getenv("LLM_CALL_DELAY_SECONDS", "2.5")
        )

    def extract(self, parsed: ParsedPage) -> dict[str, Any] | None:
        """Extract validated data from a parsed page, retrying one correction on bad JSON."""

        model_cls = CATEGORY_MODEL_MAP.get(parsed.category)
        if model_cls is None:
            logger.warning("No schema registered for category %s", parsed.category)
            return None

        text = parsed.clean_text
        if len(text) > MAX_PROMPT_CHARS:
            logger.info("Truncating %s from %d to %d chars", parsed.url, len(text), MAX_PROMPT_CHARS)
            text = text[:MAX_PROMPT_CHARS]

        schema = model_cls.model_json_schema()
        expects_list = parsed.category in LIST_CATEGORIES
        system = self._system_prompt(parsed.category, schema, expects_list)
        user = f"Source URL: {parsed.url}\n\nPage text:\n{text}"

        last_error: str | None = None
        for attempt in range(2):
            if last_error:
                user += f"\n\nYour previous response had this error: {last_error}. Return corrected JSON."
            try:
                payload = self._call(system, user)
                data = json.loads(payload)
                if expects_list:
                    if isinstance(data, list):
                        items = data
                    else:
                        items = data.get("items", [])
                    return {
                        "items": [
                            model_cls.model_validate(
                                self._inject_meta(item, parsed.url)
                            ).model_dump(mode="json")
                            for item in items
                        ]
                    }
                return model_cls.model_validate(
                    self._inject_meta(data, parsed.url)
                ).model_dump(mode="json")
            except (json.JSONDecodeError, ValidationError, TypeError, KeyError, APIError) as exc:
                last_error = str(exc)
                logger.warning("Extraction validation failed for %s attempt %d: %s", parsed.url, attempt + 1, exc)
        logger.error("Extraction failed after retry for %s", parsed.url)
        return None

    def _call(self, system: str, user: str) -> str:
        """Call Groq via the OpenAI-compatible endpoint and return text content.

        ``response_format={"type": "json_object"}`` is supported by
        ``llama-3.3-70b-versatile`` and ``llama-3.1-8b-instant`` on Groq.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2_000,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return (response.choices[0].message.content or "").strip()
        finally:
            # Always throttle, even after errors, to protect the rate limit
            # budget before the tenacity retry fires.
            if self._call_delay > 0:
                time.sleep(self._call_delay)

    def call_cached(self, cache_key: str, system: str, user: str) -> str:
        """Call the LLM once per cache key within this extractor instance."""

        if cache_key not in self.llm_cache:
            self.llm_cache[cache_key] = self._call(system, user)
        return self.llm_cache[cache_key]

    @staticmethod
    def _inject_meta(data: Any, source_url: str) -> Any:
        """Stamp system-generated meta fields onto an LLM response dict.

        ``extracted_at``, ``source_url``, and ``cross_validated`` must never
        come from the LLM — they are injected here, before Pydantic validation,
        so a null or missing value from the LLM cannot cause a ValidationError.
        This applies to the top-level ``meta`` object and to any nested model
        that also carries a ``meta`` sub-object.
        """

        if not isinstance(data, dict):
            return data
        now_iso = datetime.now(timezone.utc).isoformat()

        def _patch_meta(node: dict) -> None:
            meta = node.get("meta")
            if isinstance(meta, dict):
                meta["extracted_at"] = now_iso
                meta["source_url"] = meta.get("source_url") or source_url
                meta["cross_validated"] = False
            for value in node.values():
                if isinstance(value, dict):
                    _patch_meta(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            _patch_meta(item)

        _patch_meta(data)
        return data

    @staticmethod
    def _system_prompt(category: str, schema: dict[str, Any], expects_list: bool) -> str:
        """Build a JSON-only extraction instruction."""

        shape = "Return a JSON array of records." if expects_list else "Return one JSON object."
        return (
            "You extract structured university intelligence data. "
            "Extract only explicitly stated information. Use null for fields not present. "
            "Do not infer, estimate, guess, or hallucinate values. "
            "Include the meta object and confidence values: high, medium, low, or missing. "
            "Do not set extracted_at, source_url, or cross_validated — leave them null or omit them. "
            "Return valid JSON only, with no Markdown.\n\n"
            f"Category: {category}\n{shape}\nSchema:\n{json.dumps(schema, indent=2)}"
        )
