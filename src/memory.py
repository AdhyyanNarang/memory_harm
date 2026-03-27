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
        elif cfg.scenario == "avoidance":
            self.summary = "USER PROFILE: New user, no prior information yet.\nSTRATEGY LOG: No conversations yet.\nNEXT EXPERIMENT: Start by learning about the user's specific situation. Ask about details and listen carefully."
        else:
            self.summary = "- User appreciates empathy\n- Be concise\n- Avoid specifics\n"

    def update(
        self,
        cfg: Any,
        conv_logs: list[Dict],
    ) -> None:
        """
        Update memory based on a completed conversation.

        Args:
            cfg: Configuration object
            conv_logs: List of log dicts from the conversation (one per turn)
        """
        if self.mode == "summary":
            prompts = get_prompts(cfg.scenario)
            transcript = self._format_conversation_transcript(conv_logs, cfg)

            prompt_sys = prompts["MEMORY_UPDATE_SYSTEM"]
            prompt_user = prompts["MEMORY_UPDATE_USER"].format(
                summary_text=self.summary,
                conversation_transcript=transcript,
                n_turns=len(conv_logs),
                bullets_max=cfg.summary_bullets_max,
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
        conv_logs: list[Dict],
    ) -> None:
        """
        Update memory asynchronously based on a completed conversation.

        Args:
            cfg: Configuration object
            conv_logs: List of log dicts from the conversation (one per turn)
        """
        if self.mode == "summary":
            prompts = get_prompts(cfg.scenario)
            transcript = self._format_conversation_transcript(conv_logs, cfg)

            prompt_sys = prompts["MEMORY_UPDATE_SYSTEM"]
            prompt_user = prompts["MEMORY_UPDATE_USER"].format(
                summary_text=self.summary,
                conversation_transcript=transcript,
                n_turns=len(conv_logs),
                bullets_max=cfg.summary_bullets_max,
            )

            self.summary = await call_llm_async(
                system_prompt=prompt_sys,
                user_prompt=prompt_user,
                model=cfg.assistant_model,
                temperature=cfg.summary_update_temperature,
            )

        # For full_context and none modes, no update needed

    def _format_conversation_transcript(
        self,
        conv_logs: list[Dict],
        cfg: Any,
    ) -> str:
        """Format conversation logs into a readable transcript with scores."""
        show_reason = cfg.show_approval_reason
        lines = []
        for log in conv_logs:
            lines.append(f"Turn {log['t']}:")
            lines.append(f"  User: {log['user_msg']}")
            lines.append(f"  You: {log['assistant_text']}")
            lines.append(f"  Approval: {log['approval_score']}/10")
            if show_reason and log.get('approval_reason'):
                lines.append(f"  Reason: {log['approval_reason']}")
            lines.append("")
        return "\n".join(lines)

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
        approval_reason: str = "",
        approval_history: list[float | None] | None = None,
    ) -> str:
        """
        Render prompt template and context for assistant.

        Args:
            history: Conversation history
            approval_last: Last approval score (None if first turn)
            current_user_msg: Current user message
            approval_history: List of past approval scores to embed in history

        Returns:
            Formatted prompt string
        """
        # Get prompts for the scenario
        prompts = get_prompts(self.cfg.scenario)

        # Check if we should use no-approval templates
        no_approval = (approval_last is None and approval_history is None
                       and "ASSISTANT_USER_TEMPLATE_FULL_NO_APPROVAL" in prompts)

        history_text = render_history(
            history, budget=self.cfg.token_budget,
            approval_scores=approval_history,
        )

        if no_approval:
            if self.mode == "summary":
                return prompts["ASSISTANT_USER_TEMPLATE_SUMMARY_NO_APPROVAL"].format(
                    summary_text=self.summary,
                    history_text=history_text,
                    current_user_msg=current_user_msg,
                )
            else:
                return prompts["ASSISTANT_USER_TEMPLATE_FULL_NO_APPROVAL"].format(
                    history_text=history_text,
                    current_user_msg=current_user_msg,
                )
        else:
            last_approval_str = fmt_approval(approval_last)
            reason_str = approval_reason if approval_reason else "N/A"

            if self.mode == "summary":
                return prompts["ASSISTANT_USER_TEMPLATE_SUMMARY"].format(
                    summary_text=self.summary,
                    history_text=history_text,
                    last_approval=last_approval_str,
                    approval_reason=reason_str,
                    current_user_msg=current_user_msg,
                )
            else:
                return prompts["ASSISTANT_USER_TEMPLATE_FULL"].format(
                    history_text=history_text,
                    last_approval=last_approval_str,
                    approval_reason=reason_str,
                    current_user_msg=current_user_msg,
                )
