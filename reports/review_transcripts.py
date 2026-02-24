#!/usr/bin/env python3
"""CLI transcript reviewer for enablement drift analysis.

Prints conversation exchanges with their enablement scores for manual verification.

Usage:
    # Review all episodes
    python reports/review_transcripts.py data/logs/exp_full_context_seed1_XXXX.jsonl

    # Review a specific episode
    python reports/review_transcripts.py data/logs/exp_full_context_seed1_XXXX.jsonl --episode 3

    # Review the top 5 episodes by enablement drift
    python reports/review_transcripts.py data/logs/exp_full_context_seed1_XXXX.jsonl --high-drift 5

    # Include memory snapshots
    python reports/review_transcripts.py data/logs/exp_full_context_seed1_XXXX.jsonl --show-memory
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

DIVIDER = "─" * 60


def load_logs(log_file: str) -> list[dict]:
    """Load JSONL log file into a list of dicts."""
    entries = []
    with open(log_file, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def group_by_episode(entries: list[dict]) -> dict[int, list[dict]]:
    """Group log entries by episode id, preserving step order."""
    grouped = defaultdict(list)
    for entry in entries:
        grouped[entry["episode"]].append(entry)
    # Sort each episode's entries by total_step
    for ep in grouped:
        grouped[ep].sort(key=lambda x: x.get("total_step", x.get("t", 0)))
    return dict(grouped)


def compute_drift_per_episode(grouped: dict[int, list[dict]]) -> dict[int, float]:
    """
    Compute enablement drift for each episode.
    Drift = mean enablement score in the last half of steps minus the first half.
    """
    drifts = {}
    for ep, steps in grouped.items():
        scores = [s["enablement_score"] for s in steps]
        if len(scores) < 2:
            drifts[ep] = 0.0
            continue
        mid = len(scores) // 2
        early = sum(scores[:mid]) / mid
        late = sum(scores[mid:]) / (len(scores) - mid)
        drifts[ep] = late - early
    return drifts


def wrap_text(text: str, width: int = 80, indent: str = "  ") -> str:
    """Simple word-wrap for long text."""
    words = text.split()
    lines = []
    current = indent
    for word in words:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = indent + word
        else:
            current += ("" if current == indent else " ") + word
    if current.strip():
        lines.append(current)
    return "\n".join(lines)


def print_step(entry: dict, show_memory: bool) -> None:
    """Print a single step in the review format."""
    ep = entry["episode"]
    conv = entry["conversation"]
    step = entry["t"]
    D = entry["D"]
    enablement = entry["enablement_score"]
    indulgence = entry["indulgence_score"]
    approval = entry["approval_score"]
    assistant_text = entry.get("assistant_text", "")
    user_msg = entry.get("user_msg", "")
    approval_reason = entry.get("approval_reason", "")
    memory_snapshot = entry.get("memory_snapshot", "")

    print(f"\n[Episode {ep} | Conv {conv} | Step {step} | D={D:.2f}]")
    print(f"ASSISTANT: {wrap_text(assistant_text, indent='  ').lstrip()}")
    print(f"USER: {wrap_text(user_msg, indent='  ').lstrip()}")
    print(f"Enablement={enablement:.1f} | Indulgence={indulgence:.1f} | Approval={approval:.1f}")
    if approval_reason:
        print(f'Reason: "{approval_reason}"')

    if show_memory and memory_snapshot:
        print(f"Memory:")
        for line in memory_snapshot.strip().splitlines():
            print(f"  {line}")

    print(DIVIDER)


def print_episode(ep_id: int, steps: list[dict], show_memory: bool) -> None:
    """Print all steps for a single episode."""
    backstory = steps[0].get("backstory", "") if steps else ""
    scenario = steps[0].get("scenario", "unknown") if steps else "unknown"
    memory_mode = steps[0].get("memory_mode", "unknown") if steps else "unknown"

    scores = [s["enablement_score"] for s in steps]
    total = len(scores)
    mid = total // 2
    early_mean = sum(scores[:mid]) / mid if mid > 0 else float("nan")
    late_mean = sum(scores[mid:]) / (total - mid) if (total - mid) > 0 else float("nan")
    drift = late_mean - early_mean

    print(f"\n{'='*60}")
    print(f"EPISODE {ep_id}  |  scenario={scenario}  |  memory={memory_mode}")
    if backstory:
        print(f"Backstory: {backstory.strip()}")
    print(f"Enablement drift: {drift:+.2f}  (early={early_mean:.2f}, late={late_mean:.2f})")
    print(f"{'='*60}")

    for entry in steps:
        print_step(entry, show_memory)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review conversation transcripts with enablement scores"
    )
    parser.add_argument("log_file", help="Path to JSONL log file")
    parser.add_argument(
        "--episode", type=int, default=None,
        help="Filter to a specific episode number"
    )
    parser.add_argument(
        "--high-drift", type=int, default=None, metavar="N",
        help="Show top N episodes by enablement drift (late - early)"
    )
    parser.add_argument(
        "--show-memory", action="store_true",
        help="Include memory snapshots in output"
    )
    args = parser.parse_args()

    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"Error: log file not found: {log_path}", file=sys.stderr)
        sys.exit(1)

    entries = load_logs(str(log_path))
    if not entries:
        print("No log entries found.", file=sys.stderr)
        sys.exit(1)

    grouped = group_by_episode(entries)

    # Determine which episodes to show
    if args.episode is not None:
        if args.episode not in grouped:
            available = sorted(grouped.keys())
            print(
                f"Error: episode {args.episode} not found. "
                f"Available episodes: {available}",
                file=sys.stderr,
            )
            sys.exit(1)
        episodes_to_show = [args.episode]

    elif args.high_drift is not None:
        drifts = compute_drift_per_episode(grouped)
        sorted_eps = sorted(drifts.items(), key=lambda x: x[1], reverse=True)
        n = min(args.high_drift, len(sorted_eps))
        episodes_to_show = [ep for ep, _ in sorted_eps[:n]]
        print(f"Top {n} episodes by enablement drift:")
        for ep, drift in sorted_eps[:n]:
            print(f"  Episode {ep}: drift={drift:+.2f}")

    else:
        episodes_to_show = sorted(grouped.keys())

    # Print selected episodes
    for ep_id in episodes_to_show:
        print_episode(ep_id, grouped[ep_id], show_memory=args.show_memory)

    print(f"\nReviewed {len(episodes_to_show)} episode(s) from {log_path.name}")


if __name__ == "__main__":
    main()
