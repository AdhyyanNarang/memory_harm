"""Helpers for running and saving manual transcript experiments."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .memory import MemoryManager
from .prompts import get_prompts
from .utils import call_llm


@dataclass
class ManualTranscriptConfig:
    """Minimal config surface needed for assistant-only manual runs."""

    scenario: str
    memory_mode: str = "none"
    assistant_model: str = "gpt-4o-mini"
    assistant_temperature: float = 0.7
    token_budget: int = 6000
    show_approval_reason: bool = False
    summary_bullets_max: int = 5
    summary_update_temperature: float = 0.2
    prompt_version: str = "base"
    assistant_system_prompt_override: str | None = None


def load_candidates(path: str | Path) -> list[dict[str, Any]]:
    """Load manual transcript candidates from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_candidate(path: str | Path, candidate_id: str) -> dict[str, Any]:
    """Return a single candidate by id."""
    candidates = load_candidates(path)
    for candidate in candidates:
        if candidate["id"] == candidate_id:
            return candidate
    available = ", ".join(sorted(c["id"] for c in candidates))
    raise KeyError(f"Unknown candidate_id={candidate_id!r}. Available: {available}")


def run_manual_transcript(
    candidate: dict[str, Any],
    cfg: ManualTranscriptConfig,
) -> dict[str, Any]:
    """Run one manual transcript candidate against the assistant."""
    prompts = get_prompts(cfg.scenario)
    assistant_system_prompt = (
        cfg.assistant_system_prompt_override
        if cfg.assistant_system_prompt_override is not None
        else prompts["ASSISTANT_SYSTEM"]
    )
    memory = MemoryManager(cfg)
    history: list[tuple[str, str]] = []
    approval_history: list[float | None] = []
    turns: list[dict[str, Any]] = []

    for turn_idx, user_msg in enumerate(candidate["user_turns"]):
        memory_before = memory.snapshot()
        assistant_user_prompt = memory.render_for_assistant(
            history=history,
            approval_last=None,
            current_user_msg=user_msg,
            approval_reason="",
            approval_history=approval_history,
        )
        assistant_text = call_llm(
            system_prompt=assistant_system_prompt,
            user_prompt=assistant_user_prompt,
            model=cfg.assistant_model,
            temperature=cfg.assistant_temperature,
        )

        turn_record = {
            "turn": turn_idx,
            "user_msg": user_msg,
            "assistant_text": assistant_text,
            "assistant_system_prompt": assistant_system_prompt,
            "assistant_user_prompt": assistant_user_prompt,
            "memory_snapshot_before": memory_before,
            "memory_snapshot_after": memory_before,
        }
        turns.append(turn_record)

        history.append(("user", user_msg))
        history.append(("assistant", assistant_text))
        approval_history.append(None)

    return {
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "candidate": candidate,
        "config": asdict(cfg),
        "turns": turns,
        "judgment": {
            "lead_to_safety_problem": None,
            "first_unsafe_turn": None,
            "failure_mode": "",
            "notes": "",
        },
    }


def run_variant_suite(
    candidate: dict[str, Any],
    variant_cfgs: list[ManualTranscriptConfig],
) -> list[dict[str, Any]]:
    """Run the same candidate across multiple prompt variants."""
    return [run_manual_transcript(candidate, cfg) for cfg in variant_cfgs]


def render_transcript(bundle: dict[str, Any]) -> str:
    """Render a human-readable transcript for notebook display."""
    lines = []
    candidate = bundle["candidate"]
    lines.append(f"Candidate: {candidate['id']} ({candidate['scenario']})")
    lines.append(f"Title: {candidate['title']}")
    lines.append("")
    for turn in bundle["turns"]:
        lines.append(f"Turn {turn['turn']}")
        lines.append(f"User: {turn['user_msg']}")
        lines.append(f"Assistant: {turn['assistant_text']}")
        lines.append("")
    return "\n".join(lines)


def save_bundle(bundle: dict[str, Any], output_dir: str | Path) -> Path:
    """Save a manual transcript bundle to disk."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    candidate_id = bundle["candidate"]["id"]
    prompt_version = bundle["config"].get("prompt_version", "base")
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"{candidate_id}_{prompt_version}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=True)
        f.write("\n")
    return path


def load_saved_bundles(output_dir: str | Path) -> list[dict[str, Any]]:
    """Load saved manual transcript bundles from disk."""
    out_dir = Path(output_dir)
    if not out_dir.exists():
        return []

    bundles = []
    for path in sorted(out_dir.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            bundle = json.load(f)
        bundle["_path"] = str(path)
        bundles.append(bundle)
    return bundles


def summarize_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """Extract a compact summary row for notebook comparison."""
    judgment = bundle.get("judgment", {})
    config = bundle.get("config", {})
    candidate = bundle.get("candidate", {})
    return {
        "candidate_id": candidate.get("id", ""),
        "scenario": candidate.get("scenario", ""),
        "prompt_version": config.get("prompt_version", "base"),
        "model": config.get("assistant_model", ""),
        "temperature": config.get("assistant_temperature", None),
        "lead_to_safety_problem": judgment.get("lead_to_safety_problem", None),
        "first_unsafe_turn": judgment.get("first_unsafe_turn", None),
        "failure_mode": judgment.get("failure_mode", ""),
        "notes": judgment.get("notes", ""),
        "path": bundle.get("_path", ""),
    }
