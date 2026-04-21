#!/usr/bin/env python3
"""
Companion / assistant sycophancy experiment: scripted user turns from Scenarios.py,
assistant replies via ``manual.companion_memory``, optional interactive sycophancy score (0–10) per turn.

Uses manual/prompt_template.json and manual/Scenarios.py. Rubric: manual/sycophancy_rubric.md

LLM endpoints: ``--llm-backend vllm`` (default: localhost:8000, OpenAI-compatible / vLLM) or
``--llm-backend openai`` (requires OPENAI_API_KEY). Override with ``--base-url`` / ``--api-key``.

Examples (repo root):
  python -m manual.companion_experiment \\
    --config configs/exp.yaml --memory-mode none \\
    --scenario Involve_Romance --rebuttal simple --turns 5 --assistant-model gpt-4o-mini \\
    --llm-backend openai --episodes 1 --concurrent 1

Batch (no score prompts; parallel LLM work bounded by --concurrent). Logs always go to manual/runs/{scenario}_{memory_mode}_{rebuttal}_{YYYYMMDD_HHMMSS}.jsonl:
  python -m manual.companion_experiment --batch --episodes 4 --concurrent 2 ...

Use ``--print-assistant-prompts`` to dump the exact system + user strings sent to the chat API (stderr, per turn).
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
_MANUAL = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

from src.sim import Config, load_config  # noqa: E402

from .llm_backend import ManualLLMBackend, build_manual_llm_backend  # noqa: E402
from .Scenarios import (  # noqa: E402
    RebuttalMode,
    get_scenario,
    load_prompt_bundle,
    parse_rebuttal_mode,
    user_message_for_turn,
)
from .companion_memory import (  # noqa: E402
    CompanionMemoryManager,
    _last_assistant_from_history,
    companion_assistant_reply,
    companion_assistant_reply_async,
)

RUBRIC_PATH = _MANUAL / "sycophancy_rubric.md"
_RUNS_DIR = _MANUAL / "runs"

# Fixed sampling temperature for all manual companion LLM calls (overrides config YAML).
MANUAL_LLM_TEMPERATURE = 1.0


def default_jsonl_path(
    scenario_id: str, memory_mode: str, rebuttal_mode: str
) -> Path:
    """``manual/runs/{scenario}_{memory_mode}_{rebuttal}_{YYYYMMDD_HHMMSS}.jsonl``"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_scenario = scenario_id.replace("/", "_").replace("\\", "_")
    safe_rebuttal = rebuttal_mode.replace("/", "_").replace("\\", "_")
    return _RUNS_DIR / f"{safe_scenario}_{memory_mode}_{safe_rebuttal}_{ts}.jsonl"


def _llm_log_fields(llm_backend: ManualLLMBackend) -> dict[str, str]:
    return {"llm_backend": llm_backend.name, "llm_base_url": llm_backend.base_url}


def _parse_sycophancy(raw: str) -> float:
    s = raw.strip()
    if not s:
        raise ValueError("Empty score")
    v = float(s)
    if not 0.0 <= v <= 10.0:
        raise ValueError("Score must be between 0 and 10")
    return v


def _build_cfg(
    base: Config,
    memory_mode: str,
    token_budget: int | None,
    assistant_model: str | None,
) -> Config:
    cfg = copy.copy(base)
    cfg.memory_mode = memory_mode
    if token_budget is not None:
        cfg.token_budget = token_budget
    if assistant_model is not None:
        cfg.assistant_model = assistant_model
    cfg.assistant_temperature = MANUAL_LLM_TEMPERATURE
    cfg.summary_update_temperature = MANUAL_LLM_TEMPERATURE
    return cfg


async def run_episode_async(
    cfg: Config,
    scenario_id: str,
    turns: int,
    episode_id: int,
    rebuttal_mode: RebuttalMode,
    llm_backend: ManualLLMBackend,
    prompt_path: Path | None,
    semaphore: asyncio.Semaphore | None,
    print_assistant_prompts: bool = False,
) -> list[dict[str, Any]]:
    """One episode: scripted user lines; rows have sycophancy_score None until interactive fill."""
    spec = get_scenario(scenario_id)
    bundle = load_prompt_bundle(prompt_path)
    memory = CompanionMemoryManager(cfg, bundle, llm_backend)
    history: list[tuple[str, str]] = []
    logs: list[dict[str, Any]] = []

    for t in range(turns):
        user_msg = user_message_for_turn(spec, t, rebuttal_mode)
        # For summary memory refresh: pair user on turn t with assistant from turn t−1.
        prev_assistant_for_memory = _last_assistant_from_history(history) or ""
        plab = f"episode={episode_id} turn={t}"
        if semaphore:
            async with semaphore:
                a_text = await companion_assistant_reply_async(
                    cfg,
                    memory,
                    history,
                    user_msg,
                    t,
                    print_assistant_prompts=print_assistant_prompts,
                    prompt_log_label=plab,
                )
        else:
            a_text = await companion_assistant_reply_async(
                cfg,
                memory,
                history,
                user_msg,
                t,
                print_assistant_prompts=print_assistant_prompts,
                prompt_log_label=plab,
            )

        history.extend([("user", user_msg), ("assistant", a_text)])

        row: dict[str, Any] = {
            "episode_id": episode_id,
            "t": t,
            "scenario": scenario_id,
            "rebuttal_mode": rebuttal_mode,
            "user_msg": user_msg,
            "assistant_text": a_text,
            "sycophancy_score": None,
            "memory_mode": cfg.memory_mode,
            "memory_snapshot": memory.snapshot(),
            **_llm_log_fields(llm_backend),
        }
        logs.append(row)

        if cfg.memory_mode == "summary":
            memory.update(cfg, prev_assistant_for_memory, user_msg)

    return logs


def run_interactive_session(
    cfg: Config,
    scenario_id: str,
    turns: int,
    episodes: int,
    rebuttal_mode: RebuttalMode,
    llm_backend: ManualLLMBackend,
    prompt_path: Path | None,
    jsonl_out: Path,
    ask_sycophancy: bool,
    print_assistant_prompts: bool = False,
) -> None:
    """Sequential episodes; scripted user text; optional score after each assistant reply."""
    spec = get_scenario(scenario_id)
    bundle = load_prompt_bundle(prompt_path)
    all_rows: list[dict[str, Any]] = []

    print(
        f"\n{'=' * 60}\n"
        f"Scenario: {scenario_id}  |  Rebuttal mode: {rebuttal_mode}  |  Memory: {cfg.memory_mode}  |  Model: {cfg.assistant_model}\n"
        f"LLM: {llm_backend.describe_safe()}\n"
        f"Turns per episode: {turns}  |  Episodes: {episodes}\n"
        f"Sycophancy rubric: {RUBRIC_PATH}\n"
        f"{'=' * 60}\n"
    )

    for ep in range(episodes):
        memory = CompanionMemoryManager(cfg, bundle, llm_backend)
        history: list[tuple[str, str]] = []
        episode_rows: list[dict[str, Any]] = []

        if episodes > 1:
            print(f"\n--- Episode {ep + 1}/{episodes} ---\n")

        for t in range(turns):
            user_msg = user_message_for_turn(spec, t, rebuttal_mode)
            prev_assistant_for_memory = _last_assistant_from_history(history) or ""
            a_text = companion_assistant_reply(
                cfg,
                memory,
                history,
                user_msg,
                t,
                print_assistant_prompts=print_assistant_prompts,
                prompt_log_label=f"episode={ep} turn={t}",
            )

            print(f"\n--- Turn {t + 1}/{turns} (episode {ep}) ---")
            print(f"User (scripted):\n{user_msg}\n")
            print(f"Assistant:\n{a_text}\n")

            history.extend([("user", user_msg), ("assistant", a_text)])

            sycophancy_score: float | None = None
            if ask_sycophancy:
                while True:
                    try:
                        raw = input(
                            "Sycophancy score for this reply (0–10, see sycophancy_rubric.md): "
                        )
                        sycophancy_score = _parse_sycophancy(raw)
                        break
                    except ValueError as e:
                        print(f"Invalid: {e}")

            row: dict[str, Any] = {
                "episode_id": ep,
                "t": t,
                "scenario": scenario_id,
                "rebuttal_mode": rebuttal_mode,
                "user_msg": user_msg,
                "assistant_text": a_text,
                "sycophancy_score": sycophancy_score,
                "memory_mode": cfg.memory_mode,
                "memory_snapshot": memory.snapshot(),
                **_llm_log_fields(llm_backend),
            }
            all_rows.append(row)

            if cfg.memory_mode == "summary":
                memory.update(cfg, prev_assistant_for_memory, user_msg)

        if cfg.memory_mode == "summary":
            print("\n[Summary memory at end of episode]\n")
            print(memory.summary)

    jsonl_out.parent.mkdir(parents=True, exist_ok=True)
    with open(jsonl_out, "w", encoding="utf-8") as f:
        for row in all_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"\nWrote log to {jsonl_out}")


async def run_batch_episodes(
    cfg: Config,
    scenario_id: str,
    turns: int,
    episodes: int,
    concurrent: int,
    rebuttal_mode: RebuttalMode,
    llm_backend: ManualLLMBackend,
    prompt_path: Path | None,
    print_assistant_prompts: bool = False,
) -> list[dict[str, Any]]:
    """Run multiple episodes; at most `concurrent` assistant calls in flight (global semaphore)."""
    sem = asyncio.Semaphore(max(1, concurrent))

    async def one(ep_id: int) -> list[dict[str, Any]]:
        return await run_episode_async(
            cfg,
            scenario_id,
            turns,
            ep_id,
            rebuttal_mode,
            llm_backend,
            prompt_path,
            sem,
            print_assistant_prompts=print_assistant_prompts,
        )

    results = await asyncio.gather(*[one(ep) for ep in range(episodes)])
    rows: list[dict[str, Any]] = []
    for block in results:
        rows.extend(block)
    return rows


def main() -> None:
    p = argparse.ArgumentParser(
        description=(
            "Scripted companion chat from Scenarios.py; rate sycophancy per turn (interactive) "
            "or batch-run episodes with concurrent LLM calls."
        )
    )
    p.add_argument(
        "--config",
        type=str,
        default=str(_ROOT / "configs" / "exp.yaml"),
        help="Base YAML (seed, temperatures, etc.)",
    )
    p.add_argument(
        "--memory-mode",
        type=str,
        required=True,
        choices=("none", "summary", "full_context"),
        help="Memory mode for the assistant",
    )
    p.add_argument(
        "--scenario",
        type=str,
        default="Involve_Romance",
        help="Scenario id from manual/Scenarios.py",
    )
    p.add_argument(
        "--rebuttal",
        type=str,
        default="simple",
        choices=("simple", "ethos", "justification", "citation"),
        help=(
            "After the opening turn, every user message repeats the same scripted line for this mode "
            "(simple / ethos / justification / citation)."
        ),
    )
    p.add_argument("--turns", type=int, required=True, help="User→assistant exchanges per episode")
    p.add_argument("--episodes", type=int, default=1, help="Number of episodes to run")
    p.add_argument(
        "--assistant-model",
        type=str,
        default=None,
        help="Override assistant model from config",
    )
    p.add_argument(
        "--concurrent",
        type=int,
        default=1,
        help="Max concurrent in-flight LLM calls (batch mode only; use 1 for interactive)",
    )
    p.add_argument("--token-budget", type=int, default=None)
    p.add_argument(
        "--prompt-template",
        type=str,
        default=None,
        help="Path to prompt_template.json (default: manual/prompt_template.json)",
    )
    p.add_argument(
        "--llm-backend",
        type=str,
        default="vllm",
        choices=("openai", "vllm"),
        help=(
            "openai: OpenAI API (needs OPENAI_API_KEY or --api-key; default base URL "
            "https://api.openai.com/v1). vllm: OpenAI-compatible server (default "
            "http://localhost:8000/v1, placeholder key EMPTY)."
        ),
    )
    p.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Override chat completions base URL (else OPENAI_BASE_URL / VLLM_BASE_URL / defaults)",
    )
    p.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Override API key (else OPENAI_API_KEY for openai, VLLM_API_KEY or EMPTY for vllm)",
    )
    p.add_argument(
        "--batch",
        action="store_true",
        help=(
            "Run without stdin: do not prompt for sycophancy scores; use async LLM calls. "
            "Use with --episodes and --concurrent to run many episodes in parallel (bounded by "
            "--concurrent). Interactive mode still runs one turn at a time and can ask for scores."
        ),
    )
    p.add_argument(
        "--no-sycophancy-score",
        action="store_true",
        help="Interactive mode only: do not ask for scores",
    )
    p.add_argument(
        "--print-assistant-prompts",
        action="store_true",
        help="Before each assistant LLM call, print SYSTEM and USER strings to stderr (for debugging).",
    )
    args = p.parse_args()

    if args.turns < 1:
        print("--turns must be >= 1", file=sys.stderr)
        sys.exit(1)
    if args.episodes < 1:
        print("--episodes must be >= 1", file=sys.stderr)
        sys.exit(1)
    if args.concurrent < 1:
        print("--concurrent must be >= 1", file=sys.stderr)
        sys.exit(1)

    try:
        get_scenario(args.scenario)
        rebuttal_mode = parse_rebuttal_mode(args.rebuttal)
        llm_backend = build_manual_llm_backend(
            args.llm_backend, base_url=args.base_url, api_key=args.api_key
        )
    except (KeyError, ValueError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    base = load_config(args.config)
    cfg = _build_cfg(
        base,
        memory_mode=args.memory_mode,
        token_budget=args.token_budget,
        assistant_model=args.assistant_model,
    )

    prompt_path = Path(args.prompt_template) if args.prompt_template else None
    out = default_jsonl_path(args.scenario, args.memory_mode, rebuttal_mode)

    if args.batch:
        print(f"LLM: {llm_backend.describe_safe()}\n")
        rows = asyncio.run(
            run_batch_episodes(
                cfg,
                args.scenario,
                args.turns,
                args.episodes,
                args.concurrent,
                rebuttal_mode,
                llm_backend,
                prompt_path,
                print_assistant_prompts=args.print_assistant_prompts,
            )
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Wrote {len(rows)} rows to {out}")
        print("\nDone.")
        return

    if args.concurrent != 1:
        print(
            "Note: --concurrent > 1 applies to --batch only; running interactive with concurrent=1.",
            file=sys.stderr,
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    run_interactive_session(
        cfg,
        scenario_id=args.scenario,
        turns=args.turns,
        episodes=args.episodes,
        rebuttal_mode=rebuttal_mode,
        llm_backend=llm_backend,
        prompt_path=prompt_path,
        jsonl_out=out,
        ask_sycophancy=not args.no_sycophancy_score,
        print_assistant_prompts=args.print_assistant_prompts,
    )
    print("\nDone.")


if __name__ == "__main__":
    main()
