"""Memory management for assistant personalization."""

from typing import Any, Tuple, Dict
from .prompts import get_prompts
from .utils import call_llm, call_llm_async, render_history, fmt_approval


class MemoryManager:
    """Manages memory for the assistant across different modes."""

    def __init__(self, cfg: Any):
        """
        Initialize memory manager.

        Args:
            cfg: Configuration object with memory_mode and scenario attributes
        """
        self.mode = cfg.memory_mode
        self.cfg = cfg

        # Initial summary for summary mode (scenario-specific)
        if cfg.scenario == "politics":
            self.summary = "- User appreciates engagement with their political views\n- Be conversational\n- Stay on topic\n"
        else:
            self.summary = "- User appreciates empathy\n- Be concise\n- Avoid specifics\n"

    def update(
        self,
        cfg: Any,
        history: list[tuple[str, str]],
        assistant_text: str,
        user_msg: str,
        approval_score: float,
        approval_reason: str = ""
    ) -> None:
        """
        Update memory based on latest interaction.

        Args:
            cfg: Configuration object
            history: Conversation history
            assistant_text: Assistant's last message
            user_msg: User's response
            approval_score: Approval score received
        """
        if self.mode == "summary":
            # Get prompts for the scenario
            prompts = get_prompts(cfg.scenario)

            # Update summary using LLM
            prompt_sys = prompts["MEMORY_UPDATE_SYSTEM"]
            prompt_user = prompts["MEMORY_UPDATE_USER"].format(
                summary_text=self.summary,
                user_msg=user_msg,
                assistant_text=assistant_text,
                approval_score=approval_score,
                approval_reason=approval_reason or "Not provided",
                bullets_max=cfg.summary_bullets_max
            )
            recent_block = self._build_recent_history_block(
                history=history,
                assistant_text=assistant_text,
                user_msg=user_msg
            )
            if recent_block:
                prompt_user += (
                    "\n\nAdditional trailing context from recent exchanges:\n"
                    f"{recent_block}\n"
                    "Use this only as supporting signal when refining memory."
                )

            self.summary = call_llm(
                system_prompt=prompt_sys,
                user_prompt=prompt_user,
                model=cfg.assistant_model,
                temperature=cfg.summary_update_temperature,
            )

        # For full_context and none modes, no update needed

    async def update_async(
        self,
        cfg: Any,
        history: list[tuple[str, str]],
        assistant_text: str,
        user_msg: str,
        approval_score: float,
        approval_reason: str = ""
    ) -> None:
        """
        Update memory asynchronously based on latest interaction.

        Args:
            cfg: Configuration object
            history: Conversation history
            assistant_text: Assistant's last message
            user_msg: User's response
            approval_score: Approval score received
        """
        if self.mode == "summary":
            # Get prompts for the scenario
            prompts = get_prompts(cfg.scenario)

            # Update summary using LLM asynchronously
            prompt_sys = prompts["MEMORY_UPDATE_SYSTEM"]
            prompt_user = prompts["MEMORY_UPDATE_USER"].format(
                summary_text=self.summary,
                user_msg=user_msg,
                assistant_text=assistant_text,
                approval_score=approval_score,
                approval_reason=approval_reason or "Not provided",
                bullets_max=cfg.summary_bullets_max
            )
            recent_block = self._build_recent_history_block(
                history=history,
                assistant_text=assistant_text,
                user_msg=user_msg
            )
            if recent_block:
                prompt_user += (
                    "\n\nAdditional trailing context from recent exchanges:\n"
                    f"{recent_block}\n"
                    "Use this only as supporting signal when refining memory."
                )

            self.summary = await call_llm_async(
                system_prompt=prompt_sys,
                user_prompt=prompt_user,
                model=cfg.assistant_model,
                temperature=cfg.summary_update_temperature,
            )

        # For full_context and none modes, no update needed

    def _build_recent_history_block(
        self,
        history: list[tuple[str, str]],
        assistant_text: str,
        user_msg: str
    ) -> str:
        """
        Render trailing context for summary updater if configured.
        """
        k = getattr(self.cfg, "summary_update_history_k", 0)
        if k <= 0:
            return ""

        trailing = history[-(2 * k):] if history else []
        recent_with_current = trailing + [("assistant", assistant_text), ("user", user_msg)]
        if not recent_with_current:
            return ""

        budget = max(256, self.cfg.token_budget // 4)
        return render_history(recent_with_current, budget=budget)

    def snapshot(self) -> str:
        """
        Get current memory state for logging.

        Returns:
            Memory snapshot string
        """
        if self.mode == "summary":
            return self.summary
        elif self.mode == "full_context":
            return "<full_context>"
        else:
            return "<none>"

    def render_for_assistant(
        self,
        history: list[tuple[str, str]],
        approval_last: float | None,
        current_user_msg: str,
        approval_reason: str = ""
    ) -> str:
        """
        Render prompt template and context for assistant.

        Args:
            history: Conversation history
            approval_last: Last approval score (None if first turn)
            current_user_msg: Current user message

        Returns:
            Formatted prompt string
        """
        # Get prompts for the scenario
        prompts = get_prompts(self.cfg.scenario)

        last_approval_str = fmt_approval(approval_last)
        reason_str = approval_reason if approval_reason else "N/A (first turn)"

        if self.mode == "full_context":
            history_text = render_history(history, budget=self.cfg.token_budget)
            return prompts["ASSISTANT_USER_TEMPLATE_FULL"].format(
                history_text=history_text,
                last_approval=last_approval_str,
                approval_reason=reason_str,
                current_user_msg=current_user_msg
            )

        elif self.mode == "summary":
            return prompts["ASSISTANT_USER_TEMPLATE_SUMMARY"].format(
                summary_text=self.summary,
                last_approval=last_approval_str,
                approval_reason=reason_str,
                current_user_msg=current_user_msg
            )

        else:  # none mode
            return prompts["ASSISTANT_USER_TEMPLATE_FULL"].format(
                history_text="",
                last_approval=last_approval_str,
                approval_reason=reason_str,
                current_user_msg=current_user_msg
            )
