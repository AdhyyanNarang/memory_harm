"""Utility functions for the simulation."""

import json
import time
import asyncio
from typing import Any, Dict, Optional
import numpy as np
from openai import OpenAI, AsyncOpenAI


def clip(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clip value to [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def setup_rng(seed: int) -> np.random.Generator:
    """Create a seeded random number generator."""
    return np.random.default_rng(seed)


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    json_mode: bool = False,
) -> str:
    """
    Call OpenAI LLM with retry logic.

    Args:
        system_prompt: System message
        user_prompt: User message
        model: Model name
        temperature: Sampling temperature
        max_retries: Maximum number of retries on failure
        retry_delay: Delay between retries (seconds)
        json_mode: If True, force JSON output via response_format (requires "json" in prompt)

    Returns:
        LLM response text
    """
    client = OpenAI(                             # Changed from OpenAI()
        api_key="EMPTY",                         # Placeholders for local serving
        base_url="http://localhost:8000/v1"
    )
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                **kwargs,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)
            else:
                raise RuntimeError(f"LLM call failed after {max_retries} attempts: {e}")


async def call_llm_async(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    json_mode: bool = False,
) -> str:
    """
    Call OpenAI LLM asynchronously with retry logic.

    Args:
        system_prompt: System message
        user_prompt: User message
        model: Model name
        temperature: Sampling temperature
        max_retries: Maximum number of retries on failure
        retry_delay: Delay between retries (seconds)
        json_mode: If True, force JSON output via response_format (requires "json" in prompt)

    Returns:
        LLM response text
    """
    client = AsyncOpenAI(                       #Changed from OpenAI()
        api_key="EMPTY",                        #Placeholders for local serving 
        base_url="http://localhost:8000/v1"
    )
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                **kwargs,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(retry_delay)
            else:
                raise RuntimeError(f"LLM call failed after {max_retries} attempts: {e}")


def parse_json_response(response: str, required_keys: list[str]) -> Dict[str, Any]:
    """
    Parse JSON response from LLM and validate required keys.

    Args:
        response: LLM response string
        required_keys: List of required keys in the JSON

    Returns:
        Parsed JSON dict

    Raises:
        ValueError: If parsing fails or required keys are missing
    """
    try:
        # Try to extract JSON if wrapped in markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()

        data = json.loads(response)

        # Validate required keys
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")

        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}\nResponse: {response}")


def validate_score(score: float, name: str, min_val: float = 0.0, max_val: float = 10.0) -> float:
    """Validate and clip a score to the expected range."""
    if not isinstance(score, (int, float)):
        raise ValueError(f"{name} must be numeric, got {type(score)}")
    return clip(score, min_val, max_val)


def render_history(history: list[tuple[str, str]], budget: int = 6000) -> str:
    """
    Render conversation history as text, truncating if needed.

    Args:
        history: List of (role, text) tuples
        budget: Approximate token budget (rough estimate: 4 chars ≈ 1 token)

    Returns:
        Formatted history string
    """
    if not history:
        return "(No previous conversation)"

    # Render newest first, then reverse
    lines = []
    char_count = 0
    char_budget = budget * 4  # Rough approximation

    for role, text in reversed(history):
        line = f"{role.capitalize()}: {text}"
        char_count += len(line) + 1  # +1 for newline

        if char_count > char_budget:
            break

        lines.append(line)

    # Reverse to show oldest-to-newest
    lines.reverse()
    return "\n".join(lines)


def fmt_approval(approval: Optional[float]) -> str:
    """Format approval score for display."""
    if approval is None:
        return "None (first turn)"
    return f"{approval:.1f}/10"
