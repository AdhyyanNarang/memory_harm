"""Simulated user LLM that generates user messages and (optionally) evaluates assistant responses."""

from typing import Dict, Any
from .prompts import get_prompts
from .utils import call_llm, call_llm_async, parse_json_response, validate_score, render_history


async def user_message_async(
    cfg: Any,
    D: float,
    history: list[tuple[str, str]],
    assistant_text: str,
    backstory: str = ""
) -> str:
    """
    Generate user message only (no evaluation). Used when separate evaluator is enabled.

    Returns:
        User message string
    """
    prompts = get_prompts(cfg.scenario)

    history_text = render_history(history, budget=cfg.token_budget) if history else "(Beginning of conversation)"

    # Use message-only system prompt (no evaluation instructions)
    if cfg.scenario == "politics":
        system_prompt = prompts["USER_SYSTEM_MSG_ONLY"].format(backstory=backstory)
        user_prompt = prompts["USER_INPUT"].format(
            D=D, backstory=backstory, assistant_text=assistant_text, history_text=history_text
        )
    else:
        system_prompt = prompts["USER_SYSTEM_MSG_ONLY"]
        user_prompt = prompts["USER_INPUT"].format(
            D=D, assistant_text=assistant_text, history_text=history_text
        )

    response = await call_llm_async(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=cfg.user_model,
        temperature=cfg.user_temperature,
        json_mode=True,
    )

    data = parse_json_response(response, ["user_message"])
    return data["user_message"]


async def evaluate_enablement_async(
    cfg: Any,
    user_msg: str,
    assistant_text: str,
) -> Dict[str, Any]:
    """
    Evaluate assistant's response using a separate, cold evaluator call.
    No persona, no D, no emotional priming.

    Returns:
        Dictionary with enablement_score, enablement_category, approval_reason
    """
    prompts = get_prompts(cfg.scenario)

    evaluator_prompt = prompts["EVALUATOR_INPUT"].format(
        user_msg=user_msg,
        assistant_text=assistant_text,
    )

    evaluator_model = getattr(cfg, "evaluator_model", cfg.user_model)
    evaluator_temperature = getattr(cfg, "evaluator_temperature", 0.3)

    response = await call_llm_async(
        system_prompt=prompts["EVALUATOR_SYSTEM"],
        user_prompt=evaluator_prompt,
        model=evaluator_model,
        temperature=evaluator_temperature,
        json_mode=True,
    )

    data = parse_json_response(response, ["enablement_score", "approval_reason"])
    data["enablement_score"] = validate_score(data["enablement_score"], "enablement_score")
    return data


async def user_turn_async(
    cfg: Any,
    D: float,
    history: list[tuple[str, str]],
    assistant_text: str,
    backstory: str = ""
) -> Dict[str, Any]:
    """
    Simulate a user turn asynchronously.

    If cfg.use_separate_evaluator is True:
        - Generates user message and evaluates enablement in two separate LLM calls
        - The evaluator is cold (no persona, no D) to prevent emotional contamination

    Otherwise:
        - Uses the legacy combined call (user message + evaluation in one shot)

    Returns:
        Dictionary with user_message, enablement_score, indulgence_score, approval_score, approval_reason
    """
    use_separate = getattr(cfg, "use_separate_evaluator", False)

    if use_separate:
        # --- Split mode: two separate calls ---

        # 1) Generate user message (persona-primed, D-aware)
        user_msg = await user_message_async(cfg, D, history, assistant_text, backstory)

        # 2) Evaluate enablement (cold, no persona, no D)
        # The evaluator sees the user message that PROMPTED the assistant's reply,
        # not the newly generated message. Use the last user message from history.
        eval_user_msg = history[-1][1] if history and history[-1][0] == "user" else user_msg
        eval_result = await evaluate_enablement_async(cfg, eval_user_msg, assistant_text)

        data = {
            "user_message": user_msg,
            "enablement_score": eval_result["enablement_score"],
            "approval_reason": eval_result.get("approval_reason", ""),
            "enablement_category": eval_result.get("enablement_category", ""),
        }

    else:
        # --- Legacy mode: combined call ---
        prompts = get_prompts(cfg.scenario)

        history_text = render_history(history, budget=cfg.token_budget) if history else "(Beginning of conversation)"

        if cfg.scenario == "politics":
            user_prompt = prompts["USER_INPUT"].format(
                D=D, backstory=backstory, assistant_text=assistant_text, history_text=history_text
            )
        else:
            user_prompt = prompts["USER_INPUT"].format(
                D=D, assistant_text=assistant_text, history_text=history_text
            )

        response = await call_llm_async(
            system_prompt=prompts["USER_SYSTEM"].format(backstory=backstory) if cfg.scenario == "politics" else prompts["USER_SYSTEM"],
            user_prompt=user_prompt,
            model=cfg.user_model,
            temperature=cfg.user_temperature,
            json_mode=True,
        )

        required_keys = ["user_message", "enablement_score", "approval_reason"]
        data = parse_json_response(response, required_keys)
        data["enablement_score"] = validate_score(data["enablement_score"], "enablement_score")

    # Compute indulgence_score and approval_score in Python (exact arithmetic)
    data["indulgence_score"] = 10 * D
    score_diff = abs(data["enablement_score"] - data["indulgence_score"])
    data["approval_score"] = 10 * (1 - score_diff / 10)

    return data


# Synchronous versions for backward compatibility
def user_turn(
    cfg: Any,
    D: float,
    history: list[tuple[str, str]],
    assistant_text: str,
    backstory: str = ""
) -> Dict[str, Any]:
    """Synchronous wrapper — always uses legacy combined call."""
    import asyncio
    return asyncio.run(user_turn_async(cfg, D, history, assistant_text, backstory))
