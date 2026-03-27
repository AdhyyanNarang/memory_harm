"""Assistant LLM interface."""

from typing import Any
from .prompts import get_prompts
from .utils import call_llm, call_llm_async
from .memory import MemoryManager


def assistant_reply(
    cfg: Any,
    memory: MemoryManager,
    history: list[tuple[str, str]],
    approval_last: float | None,
    current_user_msg: str,
    approval_reason: str = "",
    approval_history: list[float | None] | None = None,
) -> str:
    """
    Generate assistant's reply based on memory and current context.

    Args:
        cfg: Configuration object
        memory: MemoryManager instance
        history: Conversation history
        approval_last: Last approval score (None if first turn)
        current_user_msg: Current user message
        approval_history: List of past approval scores to embed in history

    Returns:
        Assistant's reply text
    """
    # Get prompts for the scenario
    prompts = get_prompts(cfg.scenario)

    # Get prompt from memory manager
    user_prompt = memory.render_for_assistant(
        history, approval_last, current_user_msg, approval_reason,
        approval_history=approval_history,
    )

    # Select system prompt: use no-approval variant if approval is hidden
    no_approval = (approval_last is None and approval_history is None
                   and "ASSISTANT_SYSTEM_NO_APPROVAL" in prompts)
    sys_prompt = prompts["ASSISTANT_SYSTEM_NO_APPROVAL"] if no_approval else prompts["ASSISTANT_SYSTEM"]

    # Call assistant LLM
    reply = call_llm(
        system_prompt=sys_prompt,
        user_prompt=user_prompt,
        model=cfg.assistant_model,
        temperature=cfg.assistant_temperature,
    )

    return reply


async def assistant_reply_async(
    cfg: Any,
    memory: MemoryManager,
    history: list[tuple[str, str]],
    approval_last: float | None,
    current_user_msg: str,
    approval_reason: str = "",
    approval_history: list[float | None] | None = None,
) -> str:
    """
    Generate assistant's reply asynchronously based on memory and current context.

    Args:
        cfg: Configuration object
        memory: MemoryManager instance
        history: Conversation history
        approval_last: Last approval score (None if first turn)
        current_user_msg: Current user message
        approval_history: List of past approval scores to embed in history

    Returns:
        Assistant's reply text
    """
    # Get prompts for the scenario
    prompts = get_prompts(cfg.scenario)

    # Get prompt from memory manager
    user_prompt = memory.render_for_assistant(
        history, approval_last, current_user_msg, approval_reason,
        approval_history=approval_history,
    )

    # Select system prompt: use no-approval variant if approval is hidden
    no_approval = (approval_last is None and approval_history is None
                   and "ASSISTANT_SYSTEM_NO_APPROVAL" in prompts)
    sys_prompt = prompts["ASSISTANT_SYSTEM_NO_APPROVAL"] if no_approval else prompts["ASSISTANT_SYSTEM"]

    # Call assistant LLM asynchronously
    reply = await call_llm_async(
        system_prompt=sys_prompt,
        user_prompt=user_prompt,
        model=cfg.assistant_model,
        temperature=cfg.assistant_temperature,
    )

    return reply
