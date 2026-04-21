"""
LLM endpoint configuration for manual scripts (OpenAI API vs vLLM / OpenAI-compatible servers).

Both backends use the OpenAI Python SDK with ``base_url`` + ``api_key``; vLLM typically uses a
placeholder API key (e.g. ``EMPTY``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

BackendName = Literal["openai", "vllm"]

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_VLLM_BASE_URL = "http://localhost:8000/v1"


@dataclass(frozen=True)
class ManualLLMBackend:
    """Resolved endpoint for chat completions."""

    name: BackendName
    base_url: str
    api_key: str

    def describe_safe(self) -> str:
        """Human-readable line without exposing the full API key."""
        masked = "(set)" if (self.api_key and self.api_key != "EMPTY") else "(empty/placeholder)"
        return f"{self.name}  base_url={self.base_url}  api_key={masked}"


def build_manual_llm_backend(
    backend: BackendName,
    base_url: str | None = None,
    api_key: str | None = None,
) -> ManualLLMBackend:
    """
    Resolve ``base_url`` and ``api_key`` from flags and environment.

    Environment (optional overrides):
    - OpenAI: ``OPENAI_BASE_URL``, ``OPENAI_API_KEY``
    - vLLM: ``VLLM_BASE_URL``, ``VLLM_API_KEY`` (often ``EMPTY`` for local)
    """
    if backend == "openai":
        url = (base_url or os.environ.get("OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE_URL).rstrip("/")
        key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
        if not key.strip():
            raise ValueError(
                "OpenAI backend requires an API key: set OPENAI_API_KEY or pass --api-key"
            )
        return ManualLLMBackend(name="openai", base_url=url, api_key=key.strip())

    # vLLM / local OpenAI-compatible
    url = (base_url or os.environ.get("VLLM_BASE_URL") or DEFAULT_VLLM_BASE_URL).rstrip("/")
    if api_key is not None:
        key = api_key
    else:
        key = os.environ.get("VLLM_API_KEY", "EMPTY")
    return ManualLLMBackend(name="vllm", base_url=url, api_key=key)
