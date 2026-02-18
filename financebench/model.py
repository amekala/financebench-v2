"""Language model wrapper for Walmart's Element LLM Gateway.

Element Gateway uses Azure OpenAI format with these specifics:
  - azure_endpoint: https://wmtllmgateway.{env}.walmart.com/wmtllmgateway
  - api_version: 2024-10-21
  - Auth: API key header
  - SSL: Walmart uses self-signed certs, so we disable verification.

This wrapper implements Concordia's LanguageModel interface so it
plugs directly into the simulation engine.

Resilience (addressing review feedback):
  - Retry with exponential backoff on transient errors (429, 500, 503)
  - Null-check on response content
  - Timeout handling via httpx
  - Catches openai.APIError, openai.RateLimitError, httpx exceptions
"""

from __future__ import annotations

import logging
import time
from collections.abc import Collection, Mapping, Sequence
from typing import Any, override

from concordia.language_model import language_model
import httpx
import openai

logger = logging.getLogger(__name__)

_MAX_CHOICE_ATTEMPTS = 20
_MAX_RETRIES = 5
_INITIAL_BACKOFF_SECS = 1.0
_MAX_BACKOFF_SECS = 60.0
_BACKOFF_MULTIPLIER = 2.0

# Transient errors worth retrying
_RETRYABLE_EXCEPTIONS = (
    openai.APIConnectionError,
    openai.RateLimitError,
    openai.InternalServerError,
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.ReadTimeout,
)

DEFAULT_GATEWAY_URL = (
    "https://wmtllmgateway.prod.walmart.com/wmtllmgateway"
)
DEFAULT_API_VERSION = "2024-10-21"


def _make_insecure_httpx_client() -> httpx.Client:
    """Create an httpx client that skips SSL verification.

    Walmart's internal network uses self-signed certificates.
    This is safe because we're inside the corporate network (Eagle).
    """
    return httpx.Client(verify=False)


class ElementLanguageModel(language_model.LanguageModel):
    """Language model using Walmart's Element LLM Gateway (Azure OpenAI)."""

    def __init__(
        self,
        model_name: str = "gpt-4o",
        *,
        api_key: str,
        azure_endpoint: str = DEFAULT_GATEWAY_URL,
        api_version: str = DEFAULT_API_VERSION,
    ):
        self._model_name = model_name
        self._client = openai.AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            http_client=_make_insecure_httpx_client(),
        )

    def _retry_with_backoff(
        self,
        fn: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute fn with exponential backoff on transient errors.

        Retries up to _MAX_RETRIES times with exponential backoff.
        Only retries on transient errors (429, 500, 503, timeouts).
        Non-transient errors (400, 401, 403) are raised immediately.
        """
        backoff = _INITIAL_BACKOFF_SECS
        last_error: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                return fn(*args, **kwargs)
            except _RETRYABLE_EXCEPTIONS as e:
                last_error = e
                if attempt == _MAX_RETRIES:
                    logger.error(
                        "[%s] All %d retries exhausted: %s",
                        self._model_name,
                        _MAX_RETRIES,
                        e,
                    )
                    raise
                logger.warning(
                    "[%s] Attempt %d/%d failed (%s: %s). "
                    "Retrying in %.1fs...",
                    self._model_name,
                    attempt,
                    _MAX_RETRIES,
                    type(e).__name__,
                    str(e)[:100],
                    backoff,
                )
                time.sleep(backoff)
                backoff = min(
                    backoff * _BACKOFF_MULTIPLIER,
                    _MAX_BACKOFF_SECS,
                )

        # Unreachable, but satisfies type checker
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
        del terminators, top_k  # Not used by Azure OpenAI.

        messages = [
            {
                "role": "system",
                "content": (
                    "You always continue sentences provided by the user "
                    "and you never repeat what the user already said."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        response = self._retry_with_backoff(
            self._client.chat.completions.create,
            model=self._model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            timeout=timeout,
            seed=seed,
        )

        # Null-check: API can return empty choices or null content
        if (
            not response.choices
            or response.choices[0].message.content is None
        ):
            logger.warning(
                "[%s] Empty response from API", self._model_name
            )
            return ""

        return response.choices[0].message.content

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
                    augmented, temperature=0.1, seed=seed
                ).strip()
            except _RETRYABLE_EXCEPTIONS:
                # sample_text already retried; if it still fails,
                # continue to next attempt with fresh call
                logger.warning(
                    "[%s] sample_choice attempt %d: API error",
                    self._model_name,
                    attempt + 1,
                )
                continue

            # Exact match first
            for idx, resp in enumerate(responses):
                if answer == resp:
                    return idx, resp, {}
            # Substring match fallback
            for idx, resp in enumerate(responses):
                if resp in answer:
                    return idx, resp, {}

        raise language_model.InvalidResponseError(
            f"Could not extract choice after {_MAX_CHOICE_ATTEMPTS} "
            f"attempts. Last answer: {answer!r}"
        )
