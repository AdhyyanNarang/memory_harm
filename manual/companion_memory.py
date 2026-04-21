"""
Memory + assistant call for manual companion experiments using prompt_template.json / Scenarios.

Uses manual llm_client (OpenAI API or vLLM); render_history from src.utils.
"""

from __future__ import annotations

import sys
from typing import Any, Dict

from src.utils import render_history

from .llm_backend import ManualLLMBackend
from .llm_client import call_llm_async_manual, call_llm_manual


def _last_assistant_from_history(history: list[tuple[str, str]]) -> str | None:
    for role, text in reversed(history):
        if role == "assistant":
            return text
    return None



class CompanionMemoryManager:
    """Memory modes: none / summary / full_context. Prompts from load_prompt_bundle()."""

    def __init__(self, cfg: Any, prompt_bundle: dict[str, str], llm_backend: ManualLLMBackend):
        self.cfg = cfg
        self.mode = cfg.memory_mode
        self._prompts = prompt_bundle
        self.llm_backend = llm_backend
        self.summary: str = self._prompts["INITIAL_SUMMARY"]

    def snapshot(self) -> str | None:
        if self.mode == "summary":
            return self.summary
        return None



    def update(
        self,
        cfg: Any,
        previous_turn_assistant_text: str,
        current_turn_user_msg: str,
    ) -> None:
        """
        Refresh bullet memory after a completed turn.

        ``previous_turn_assistant_text`` is the assistant reply from turn *t−1* (empty on
        turn 0). ``current_turn_user_msg`` is the user's line for turn *t*. This pairs
        the latest user message with the prior assistant reply, not the assistant reply
        just produced for turn *t*.
        """
        if self.mode != "summary":
            return

        p = self._prompts

        prompt_user = p["MEMORY_UPDATE_USER"].format(
            summary_text=self.summary,
            last_assistant_block=previous_turn_assistant_text,
            current_user_msg=current_turn_user_msg,
            bullets_max=cfg.summary_bullets_max,
        )
        self.summary = call_llm_manual(
            system_prompt=p["MEMORY_UPDATE_SYSTEM"],
            user_prompt=prompt_user,
            llm_backend=self.llm_backend,
            model=cfg.assistant_model,
            temperature=cfg.summary_update_temperature,
        )

    def render_for_assistant(
        self,
        history: list[tuple[str, str]],
        current_user_msg: str,
        turn_index: int = 0,
    ) -> str:
        """
        Build the assistant user prompt.

        ``history`` is completed dialogue *before* the current user message: ``(user,
        assistant)`` pairs through turn ``turn_index - 1``, same pattern as ``src/sim``.

        *none* / *summary*: for ``turn_index > 0``, include the previous assistant
        reply as an explicit bridge before the current user line. *full_context*:
        tail-bounded transcript via ``render_history(history)`` (already includes the
        last assistant when history is built correctly).
        """
        p = self._prompts

        if self.mode == "full_context":
            history_text = render_history(
                history,
                budget=self.cfg.token_budget,
                approval_scores=None,
            )
            return p["USER_TEMPLATE_FULL"].format(
                history_text=history_text,
                current_user_msg=current_user_msg,
            )
        if self.mode == "summary":
            last_assistant_block = ""
            if turn_index > 0:
                la = _last_assistant_from_history(history)
                if la:
                    last_assistant_block = la
            return p["USER_TEMPLATE_SUMMARY"].format(
                summary_text=self.summary,
                last_assistant_block=last_assistant_block,
                current_user_msg=current_user_msg,
            )
        # none
        history_text = ""
        if turn_index > 0:
            la = _last_assistant_from_history(history)
            if la:
                history_text = f"Assistant (previous reply):\n{la}\n"
        return p["USER_TEMPLATE_FULL"].format(
            history_text=history_text,
            current_user_msg=current_user_msg,
        )


def _maybe_print_assistant_prompts(
    system_prompt: str,
    user_prompt: str,
    *,
    enabled: bool,
    log_label: str = "",
) -> None:
    if not enabled:
        return
    suffix = f" [{log_label}]" if log_label else ""
    sep = "=" * 72
    print(
        f"\n{sep}\nASSISTANT LLM INPUT{suffix}\n{sep}\n"
        f"### SYSTEM\n{system_prompt}\n\n### USER\n{user_prompt}\n{sep}\n",
        file=sys.stderr,
        flush=True,
    )


def companion_assistant_reply(
    cfg: Any,
    memory: CompanionMemoryManager,
    history: list[tuple[str, str]],
    current_user_msg: str,
    turn_index: int = 0,
    *,
    print_assistant_prompts: bool = False,
    prompt_log_label: str = "",
) -> str:
    """Render assistant user prompt and run one sync chat completion (see ``src/assistant.assistant_reply``)."""
    user_prompt = memory.render_for_assistant(
        history, current_user_msg, turn_index
    )
    _maybe_print_assistant_prompts(
        memory._prompts["SYSTEM"],
        user_prompt,
        enabled=print_assistant_prompts,
        log_label=prompt_log_label,
    )
    return call_llm_manual(
        system_prompt=memory._prompts["SYSTEM"],
        user_prompt=user_prompt,
        llm_backend=memory.llm_backend,
        model=cfg.assistant_model,
        temperature=cfg.assistant_temperature,
    )


async def companion_assistant_reply_async(
    cfg: Any,
    memory: CompanionMemoryManager,
    history: list[tuple[str, str]],
    current_user_msg: str,
    turn_index: int = 0,
    *,
    print_assistant_prompts: bool = False,
    prompt_log_label: str = "",
) -> str:
    """Same as ``companion_assistant_reply`` but async HTTP (see ``src/assistant.assistant_reply_async``)."""
    user_prompt = memory.render_for_assistant(
        history, current_user_msg, turn_index
    )
    _maybe_print_assistant_prompts(
        memory._prompts["SYSTEM"],
        user_prompt,
        enabled=print_assistant_prompts,
        log_label=prompt_log_label,
    )
    return await call_llm_async_manual(
        system_prompt=memory._prompts["SYSTEM"],
        user_prompt=user_prompt,
        llm_backend=memory.llm_backend,
        model=cfg.assistant_model,
        temperature=cfg.assistant_temperature,
    )
