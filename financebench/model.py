"""Language model wrapper for Walmart's Element LLM Gateway.

Element Gateway uses Azure OpenAI format with these specifics:
  - azure_endpoint: https://wmtllmgateway.{env}.walmart.com/wmtllmgateway
  - api_version: 2024-10-21
  - Auth: API key header
  - SSL: Walmart uses self-signed certs, so we disable verification.

This wrapper implements Concordia's LanguageModel interface so it
plugs directly into the simulation engine.
"""

from collections.abc import Collection, Mapping, Sequence
from typing import Any, override

from concordia.language_model import language_model
import httpx
import openai

_MAX_CHOICE_ATTEMPTS = 20

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

        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            timeout=timeout,
            seed=seed,
        )
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

        for _ in range(_MAX_CHOICE_ATTEMPTS):
            answer = self.sample_text(
                augmented, temperature=0.1, seed=seed
            ).strip()
            for idx, resp in enumerate(responses):
                if answer == resp:
                    return idx, resp, {}
            for idx, resp in enumerate(responses):
                if resp in answer:
                    return idx, resp, {}

        raise language_model.InvalidResponseError(
            f"Could not extract choice after {_MAX_CHOICE_ATTEMPTS} attempts. "
            f"Last answer: {answer!r}"
        )
