"""Chat completions for manual experiments (configurable base URL / API key)."""

from __future__ import annotations

import asyncio
import time
from openai import AsyncOpenAI, OpenAI

from .llm_backend import ManualLLMBackend


def call_llm_manual(
    system_prompt: str,
    user_prompt: str,
    *,
    llm_backend: ManualLLMBackend,
    model: str,
    temperature: float = 1.0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    json_mode: bool = False,
) -> str:
    client = OpenAI(api_key=llm_backend.api_key, base_url=llm_backend.base_url)
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                **kwargs,
            )
            content = response.choices[0].message.content
            return (content or "").strip()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)
            else:
                raise RuntimeError(f"LLM call failed after {max_retries} attempts: {e}") from e
    raise RuntimeError("unreachable")


async def call_llm_async_manual(
    system_prompt: str,
    user_prompt: str,
    *,
    llm_backend: ManualLLMBackend,
    model: str,
    temperature: float = 1.0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    json_mode: bool = False,
) -> str:
    client = AsyncOpenAI(api_key=llm_backend.api_key, base_url=llm_backend.base_url)
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                **kwargs,
            )
            content = response.choices[0].message.content
            return (content or "").strip()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(retry_delay)
            else:
                raise RuntimeError(f"LLM call failed after {max_retries} attempts: {e}") from e
    raise RuntimeError("unreachable")
