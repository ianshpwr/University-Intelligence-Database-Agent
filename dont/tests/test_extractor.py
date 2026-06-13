"""Mocked tests for the Groq-backed Extractor."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from core.extractor import Extractor
from core.parser import ParsedPage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_parsed(category: str = "about", text: str = "Some university text.") -> ParsedPage:
    return ParsedPage(
        url="https://example.edu/about",
        category=category,
        clean_text=text,
        discovered_links=[],
    )


def _mock_groq_response(content: str) -> MagicMock:
    """Build a minimal stand-in for an OpenAI ChatCompletion response."""
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def _make_extractor() -> Extractor:
    """Create an Extractor with a dummy key (no real network calls)."""
    with patch("core.extractor.OpenAI"):
        extractor = Extractor(api_key="test-key", model="llama-3.3-70b-versatile")
    return extractor


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_extractor_raises_without_api_key(monkeypatch: Any) -> None:
    """Constructor raises ValueError when no GROQ_API_KEY is available."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        Extractor()


def test_extractor_uses_env_key(monkeypatch: Any) -> None:
    """Constructor picks up GROQ_API_KEY from environment."""
    monkeypatch.setenv("GROQ_API_KEY", "env-key")
    with patch("core.extractor.OpenAI") as mock_openai:
        extractor = Extractor()
    mock_openai.assert_called_once_with(
        api_key="env-key",
        base_url="https://api.groq.com/openai/v1",
    )
    assert extractor.model == "llama-3.3-70b-versatile"


def test_extractor_uses_env_model(monkeypatch: Any) -> None:
    """GROQ_MODEL env var overrides the default model."""
    monkeypatch.setenv("GROQ_API_KEY", "env-key")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.1-8b-instant")
    with patch("core.extractor.OpenAI"):
        extractor = Extractor()
    assert extractor.model == "llama-3.1-8b-instant"


# ---------------------------------------------------------------------------
# Successful extraction
# ---------------------------------------------------------------------------

def test_extract_returns_validated_dict(monkeypatch: Any) -> None:
    """Extractor returns a model_dump dict for a valid Groq JSON response."""
    extractor = _make_extractor()
    payload = json.dumps(
        {
            "name": "Example University",
            "founding_year": None,
            "ranking": None,
            "city": None,
            "country": None,
            "type": None,
            "website_url": None,
            "meta": {"confidence": "high", "source_url": "https://example.edu/about", "notes": None},
        }
    )
    extractor.client.chat.completions.create = MagicMock(
        return_value=_mock_groq_response(payload)
    )
    result = extractor.extract(_make_parsed("about"))
    assert result is not None
    assert result["name"] == "Example University"
    assert result["meta"]["confidence"] == "high"


def test_extract_unknown_category_returns_none() -> None:
    """Unknown categories return None without calling the API."""
    extractor = _make_extractor()
    extractor.client.chat.completions.create = MagicMock()
    result = extractor.extract(_make_parsed("nonexistent_category"))
    assert result is None
    extractor.client.chat.completions.create.assert_not_called()


# ---------------------------------------------------------------------------
# Text truncation
# ---------------------------------------------------------------------------

def test_extract_truncates_long_text(monkeypatch: Any) -> None:
    """Input text longer than MAX_PROMPT_CHARS is truncated before sending."""
    from core.extractor import MAX_PROMPT_CHARS

    extractor = _make_extractor()
    long_text = "x" * (MAX_PROMPT_CHARS + 500)
    captured: list[Any] = []

    def fake_call(system: str, user: str) -> str:
        captured.append(user)
        return json.dumps(
            {
                "name": None,
                "founding_year": None,
                "ranking": None,
                "city": None,
                "country": None,
                "type": None,
                "website_url": None,
                "meta": {"confidence": "missing", "source_url": "", "notes": None},
            }
        )

    monkeypatch.setattr(extractor, "_call", fake_call)
    extractor.extract(_make_parsed("about", long_text))
    assert len(captured) == 1
    # The page text portion should not exceed the cap
    assert len(captured[0]) < MAX_PROMPT_CHARS + 500


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------

def test_extract_retries_on_bad_json(monkeypatch: Any) -> None:
    """Extractor retries exactly once when the first response is invalid JSON."""
    extractor = _make_extractor()
    call_count = 0

    good_payload = json.dumps(
        {
            "name": "Retry University",
            "founding_year": None,
            "ranking": None,
            "city": None,
            "country": None,
            "type": None,
            "website_url": None,
            "meta": {"confidence": "low", "source_url": "", "notes": None},
        }
    )

    def fake_call(system: str, user: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return "not valid json {{{"
        return good_payload

    monkeypatch.setattr(extractor, "_call", fake_call)
    result = extractor.extract(_make_parsed("about"))
    assert call_count == 2
    assert result is not None
    assert result["name"] == "Retry University"


def test_extract_returns_none_after_two_failures(monkeypatch: Any) -> None:
    """Extractor gives up and returns None after two consecutive failures."""
    extractor = _make_extractor()

    monkeypatch.setattr(extractor, "_call", lambda s, u: "{{bad}}")
    result = extractor.extract(_make_parsed("about"))
    assert result is None


# ---------------------------------------------------------------------------
# _call wiring
# ---------------------------------------------------------------------------

def test_call_passes_json_object_response_format() -> None:
    """_call requests json_object response_format from the Groq API."""
    extractor = _make_extractor()
    extractor.client.chat.completions.create = MagicMock(
        return_value=_mock_groq_response('{"key": "value"}')
    )
    extractor._call("system prompt", "user prompt")
    call_kwargs = extractor.client.chat.completions.create.call_args.kwargs
    assert call_kwargs["response_format"] == {"type": "json_object"}
    assert call_kwargs["temperature"] == 0
    assert call_kwargs["max_tokens"] == 2_000


def test_call_sends_system_and_user_messages() -> None:
    """_call sends system and user messages in the correct order."""
    extractor = _make_extractor()
    extractor.client.chat.completions.create = MagicMock(
        return_value=_mock_groq_response("{}")
    )
    extractor._call("sys", "usr")
    messages = extractor.client.chat.completions.create.call_args.kwargs["messages"]
    assert messages[0] == {"role": "system", "content": "sys"}
    assert messages[1] == {"role": "user", "content": "usr"}
