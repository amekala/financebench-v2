"""Language model wrapper for Walmart's Element LLM Gateway.

The Element Gateway routes to three providers, each with a different
native API:

  OpenAI:    POST /v1/chat/completions       (gpt-*, o3)
  Anthropic: POST /v1/messages               (claude-*)
  Google:    POST /v1/models/{m}:generateContent  (gemini-*)

All share:
  - Auth: Authorization: Bearer {api_key}
  - Walmart headers: WM_CONSUMER.ID, WM_SVC.NAME, WM_SVC.ENV
  - SSL: disabled (Walmart internal certs)

This wrapper implements Concordia's LanguageModel interface so it
plugs directly into the simulation engine.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Collection, Mapping, Sequence
from typing import Any, override

import httpx
from concordia.language_model import language_model

logger = logging.getLogger(__name__)

_MAX_CHOICE_ATTEMPTS = 20
_MAX_RETRIES = 5
_INITIAL_BACKOFF_SECS = 1.0
_MAX_BACKOFF_SECS = 60.0
_BACKOFF_MULTIPLIER = 2.0

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 404}

DEFAULT_GATEWAY_URL = (
    "https://wmtllmgateway.stage.walmart.com/wmtllmgateway"
)

# ── Provider Detection ──────────────────────────────────────────

PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_GOOGLE = "google"


def detect_provider(model_name: str) -> str:
    """Detect the provider from the model name."""
    if model_name.startswith("claude"):
        return PROVIDER_ANTHROPIC
    if model_name.startswith("gemini"):
        return PROVIDER_GOOGLE
    return PROVIDER_OPENAI


# ── Request/Response Builders ───────────────────────────────────

def _build_openai_request(
    model: str,
    prompt: str,
    *,
    system: str = "",
    temperature: float = 0.5,
    max_tokens: int = 1024,
    top_p: float = 1.0,
) -> tuple[str, dict]:
    """Build OpenAI chat/completions request."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
    }
    # Newer OpenAI models (o-series, gpt-5+) require max_completion_tokens
    if model.startswith("o") or model.startswith("gpt-5"):
        body["max_completion_tokens"] = max_tokens
    else:
        body["max_tokens"] = max_tokens

    return "/v1/chat/completions", body


def _build_anthropic_request(
    model: str,
    prompt: str,
    *,
    system: str = "",
    temperature: float = 0.5,
    max_tokens: int = 1024,
    top_p: float = 1.0,
) -> tuple[str, dict]:
    """Build Anthropic messages request.

    Note: Anthropic does NOT allow temperature AND top_p together.
    We use temperature only (the more commonly tuned param).
    """
    body: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        # top_p intentionally omitted — Anthropic rejects both together
    }
    if system:
        body["system"] = system
    return "/v1/messages", body


def _build_google_request(
    model: str,
    prompt: str,
    *,
    system: str = "",
    temperature: float = 0.5,
    max_tokens: int = 1024,
    top_p: float = 1.0,
) -> tuple[str, dict]:
    """Build Google Gemini generateContent request."""
    body: dict[str, Any] = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]},
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
            "topP": top_p,
        },
    }
    if system:
        body["system_instruction"] = {
            "parts": [{"text": system}]
        }
    return f"/v1/models/{model}:generateContent", body


_BUILDERS = {
    PROVIDER_OPENAI: _build_openai_request,
    PROVIDER_ANTHROPIC: _build_anthropic_request,
    PROVIDER_GOOGLE: _build_google_request,
}


def _extract_text(provider: str, data: dict) -> str:
    """Extract the text content from a provider's response."""
    if provider == PROVIDER_OPENAI:
        choices = data.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "") or ""

    if provider == PROVIDER_ANTHROPIC:
        content = data.get("content", [])
        if not content:
            return ""
        return content[0].get("text", "") or ""

    if provider == PROVIDER_GOOGLE:
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )
        return parts[0].get("text", "") if parts else ""

    return ""


# ── Main Model Class ────────────────────────────────────────────

class ElementLanguageModel(language_model.LanguageModel):
    """Multi-provider language model using Element LLM Gateway."""

    def __init__(
        self,
        model_name: str = "gpt-4.1",
        *,
        api_key: str,
        azure_endpoint: str = DEFAULT_GATEWAY_URL,
    ):
        self._model_name = model_name
        self._base_url = azure_endpoint.rstrip("/")
        self._provider = detect_provider(model_name)
        self._client = httpx.Client(
            verify=False,
            headers={
                "Authorization": f"Bearer {api_key}",
                "WM_CONSUMER.ID": "promotionbench",
                "WM_SVC.NAME": "promotionbench",
                "WM_SVC.ENV": "stg",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(120.0, connect=15.0),
        )
        self._builder = _BUILDERS[self._provider]

    def _call_api(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.5,
        max_tokens: int = 1024,
        top_p: float = 1.0,
    ) -> str:
        """Make a single API call with retries."""
        path, body = self._builder(
            self._model_name,
            prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        url = f"{self._base_url}{path}"

        backoff = _INITIAL_BACKOFF_SECS
        last_error: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = self._client.post(url, json=body)

                if resp.status_code == 200:
                    return _extract_text(
                        self._provider, resp.json()
                    )

                if resp.status_code in _RETRYABLE_STATUS_CODES:
                    raise httpx.HTTPStatusError(
                        f"{resp.status_code}: {resp.text[:200]}",
                        request=resp.request,
                        response=resp,
                    )

                # Non-retryable error (400, 401, 403)
                resp.raise_for_status()

            except (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.ReadTimeout,
            ) as e:
                last_error = e
                if attempt == _MAX_RETRIES:
                    logger.error(
                        "[%s] All %d retries exhausted: %s",
                        self._model_name,
                        _MAX_RETRIES,
                        str(e)[:200],
                    )
                    raise
                logger.warning(
                    "[%s] Attempt %d/%d failed (%s). "
                    "Retrying in %.1fs...",
                    self._model_name,
                    attempt,
                    _MAX_RETRIES,
                    str(e)[:100],
                    backoff,
                )
                time.sleep(backoff)
                backoff = min(
                    backoff * _BACKOFF_MULTIPLIER,
                    _MAX_BACKOFF_SECS,
                )
            except httpx.HTTPStatusError as e:
                # Retryable status codes (rate limit, server errors)
                if e.response.status_code in _RETRYABLE_STATUS_CODES:
                    last_error = e
                    if attempt == _MAX_RETRIES:
                        logger.error(
                            "[%s] All %d retries exhausted: %s",
                            self._model_name,
                            _MAX_RETRIES,
                            str(e)[:200],
                        )
                        raise
                    logger.warning(
                        "[%s] Attempt %d/%d failed (%d). "
                        "Retrying in %.1fs...",
                        self._model_name,
                        attempt,
                        _MAX_RETRIES,
                        e.response.status_code,
                        backoff,
                    )
                    time.sleep(backoff)
                    backoff = min(
                        backoff * _BACKOFF_MULTIPLIER,
                        _MAX_BACKOFF_SECS,
                    )
                else:
                    # Non-retryable (400, 401, 403) — fail immediately
                    logger.error(
                        "[%s] Non-retryable error %d: %s",
                        self._model_name,
                        e.response.status_code,
                        e.response.text[:300],
                    )
                    raise

        raise last_error  # type: ignore[misc]

    @override
    def sample_text(
        self,
        prompt: str,
        *,
        max_tokens: int = language_model.DEFAULT_MAX_TOKENS,
        terminators: Collection[str] = language_model.DEFAULT_TERMINATORS,
        temperature: float = language_model.DEFAULT_TEMPERATURE,
        top_p: float = language_model.DEFAULT_TOP_P,
        top_k: int = language_model.DEFAULT_TOP_K,
        timeout: float = language_model.DEFAULT_TIMEOUT_SECONDS,
        seed: int | None = None,
    ) -> str:
        del terminators, top_k, timeout, seed  # Not used.

        system = (
            "You always continue sentences provided by the user "
            "and you never repeat what the user already said."
        )

        result = self._call_api(
            prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )

        if not result:
            logger.warning(
                "[%s] Empty response from API", self._model_name
            )

        return result

    @override
    def sample_choice(
        self,
        prompt: str,
        responses: Sequence[str],
        *,
        seed: int | None = None,
    ) -> tuple[int, str, Mapping[str, Any]]:
        augmented = (
            prompt
            + "\nRespond EXACTLY with one of the following strings:\n"
            + "\n".join(responses)
            + "."
        )

        for attempt in range(_MAX_CHOICE_ATTEMPTS):
            try:
                answer = self.sample_text(
                    augmented, temperature=0.1
                ).strip()
            except Exception:
                logger.warning(
                    "[%s] sample_choice attempt %d: API error",
                    self._model_name,
                    attempt + 1,
                )
                continue

            for idx, resp in enumerate(responses):
                if answer == resp:
                    return idx, resp, {}
            for idx, resp in enumerate(responses):
                if resp in answer:
                    return idx, resp, {}

        raise language_model.InvalidResponseError(
            f"Could not extract choice after {_MAX_CHOICE_ATTEMPTS} "
            f"attempts. Last answer: {answer!r}"
        )
