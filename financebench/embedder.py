"""Sentence embedding utilities for Concordia's AssociativeMemory.

Concordia just needs a callable: str -> np.ndarray.
We provide two options:
  1. HashEmbedder  — deterministic, zero API calls, good for testing
  2. OpenAIEmbedder — uses Element Gateway's embedding endpoint
"""

import hashlib

import numpy as np
import openai

_HASH_DIM = 128


class HashEmbedder:
    """Deterministic hash-based embedder. No API calls needed.

    Produces consistent embeddings via SHA-256 so that identical
    strings always get the same vector. Good enough for testing
    but obviously not semantically meaningful.
    """

    def __init__(self, dim: int = _HASH_DIM):
        self._dim = dim

    def __call__(self, text: str) -> np.ndarray:
        digest = hashlib.sha256(text.encode()).digest()
        rng = np.random.RandomState(  # noqa: NPY002 — seeded, deterministic
            seed=int.from_bytes(digest[:4], "big")
        )
        vec = rng.randn(self._dim).astype(np.float32)
        return vec / (np.linalg.norm(vec) + 1e-9)


class OpenAIEmbedder:
    """Uses an OpenAI-compatible embeddings endpoint."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str | None = None,
        model: str = "text-embedding-3-small",
    ):
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def __call__(self, text: str) -> np.ndarray:
        response = self._client.embeddings.create(
            input=[text], model=self._model
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
