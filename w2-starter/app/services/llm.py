"""The only place in the codebase that talks to OpenAI.

Design rules from slides 24-25 and the study guide (Week 2):
- Structured output: ask for a JSON object that matches
  ``MeetingAnalysis`` and validate it again with Pydantic on our side.
  A schema-valid shape is not enough on its own — the "no invention"
  rule (null owner / null relative date) is a business rule, so the
  server still checks the payload before returning it.
- Bounded retry: at most 3 attempts in total for transient failures
  (429 / timeout / upstream 5xx). Backoff is 1s, then 2s (each with a
  small jitter) between the attempts, and a ``Retry-After`` header is
  always respected.
- The OpenAI SDK already retries some transient errors on its own, so
  the client is created with ``max_retries=0``: our retry budget here
  is the *only* retry budget, otherwise retries nest and multiply.
- 400/422-style client errors are never retried.
- Errors are mapped to small exception types; ``app/main.py`` turns
  them into the HTTP codes of the study guide's error table:
  timeout -> 504, persistent 429 -> 503, upstream 5xx -> 502,
  unparsable model output -> 502 (invalid_upstream_response).
- The API key and model name come from ``.env`` only, never from
  code, logs or the repo.
"""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path

from app.schemas import MeetingAnalysis

MAX_ATTEMPTS = 3
LLM_TIMEOUT_SECONDS = 20.0
BACKOFF_BASE_SECONDS = 1.0


class UpstreamTimeout(Exception):
    """The LLM call timed out even after the bounded retries."""


class UpstreamRateLimited(Exception):
    """The LLM kept returning 429 after the bounded retries."""


class UpstreamError(Exception):
    """The LLM returned a 5xx (or another non-retryable upstream error)."""


class InvalidUpstreamResponse(Exception):
    """The model replied, but its output did not validate as MeetingAnalysis."""


def _load_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent.parent.parent / "prompts" / "w2_v1.md"
    return prompt_path.read_text(encoding="utf-8")


def _get_client():
    """Build the OpenAI client lazily so importing this module never
    needs an API key (tests that mock ``analyze_meeting`` import fine)."""
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise UpstreamError("OPENAI_API_KEY is not set in .env")
    return OpenAI(api_key=api_key, max_retries=0)


def _sleep_with_backoff(attempt: int, retry_after: float | None) -> None:
    if retry_after is not None:
        time.sleep(retry_after)
        return
    delay = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
    delay += random.uniform(0, 0.5)  # jitter, avoids synchronised retries
    time.sleep(delay)


def _retry_after_seconds(error: Exception) -> float | None:
    """Read Retry-After from a 429 error when the SDK exposes it."""
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None) or {}
    raw = headers.get("retry-after") or headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _is_rate_limit(error: Exception) -> bool:
    status = getattr(error, "status_code", None)
    return status == 429 or "429" in type(error).__name__ or "RateLimit" in type(error).__name__


def _is_timeout(error: Exception) -> bool:
    return "Timeout" in type(error).__name__ or "timeout" in str(error).lower()


def _is_server_error(error: Exception) -> bool:
    status = getattr(error, "status_code", None)
    return isinstance(status, int) and 500 <= status < 600


def analyze_meeting(notes: str) -> MeetingAnalysis:
    """Send one meeting's notes to the model and return validated output."""
    client = _get_client()
    model = os.environ.get("OPENAI_MODEL", "")
    if not model or model == "choose_approved_model":
        raise UpstreamError(
            "OPENAI_MODEL is not set to a real model in .env "
            "(still the placeholder 'choose_approved_model')"
        )

    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0,
                timeout=LLM_TIMEOUT_SECONDS,
                messages=[
                    {"role": "system", "content": _load_prompt()},
                    {"role": "user", "content": notes},
                ],
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or ""
            try:
                return MeetingAnalysis.model_validate_json(raw)
            except Exception as exc:
                raise InvalidUpstreamResponse(
                    f"Model output did not match MeetingAnalysis: {raw[:200]}"
                ) from exc
        except InvalidUpstreamResponse:
            raise
        except Exception as exc:  # transient upstream failure: maybe retry
            last_error = exc
            if attempt == MAX_ATTEMPTS:
                break
            if _is_rate_limit(exc) or _is_timeout(exc) or _is_server_error(exc):
                _sleep_with_backoff(attempt, _retry_after_seconds(exc))
                continue
            raise UpstreamError(str(exc)) from exc

    assert last_error is not None
    if _is_rate_limit(last_error):
        raise UpstreamRateLimited(str(last_error)) from last_error
    if _is_timeout(last_error):
        raise UpstreamTimeout(str(last_error)) from last_error
    raise UpstreamError(str(last_error)) from last_error
