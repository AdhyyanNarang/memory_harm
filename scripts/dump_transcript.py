#!/usr/bin/env python3
"""Dump human-readable transcripts from JSONL experiment logs.

Usage:
    # Show all episodes from two log files side-by-side (summary vs none)
    python scripts/dump_transcript.py data/logs/diagnostic/exp_summary_*.jsonl data/logs/diagnostic/exp_none_*.jsonl

    # Filter to high-D episodes only
    python scripts/dump_transcript.py --d-tier high data/logs/diagnostic/exp_summary_*.jsonl data/logs/diagnostic/exp_none_*.jsonl

    # Single file, single episode
    python scripts/dump_transcript.py --episode 0 data/logs/diagnostic/exp_summary_*.jsonl
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_logs(path: str) -> list[dict]:
    """Load JSONL log file."""
    logs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                logs.append(json.loads(line))
    return logs


def group_by_episode(logs: list[dict]) -> dict[int, list[dict]]:
    """Group log entries by episode."""
    episodes = defaultdict(list)
    for entry in logs:
        episodes[entry["episode"]].append(entry)
    for ep in episodes:
        episodes[ep].sort(key=lambda x: x["total_step"])
    return dict(episodes)


def d_tier(d0: float) -> str:
    if d0 >= 0.7:
        return "high"
    elif d0 <= 0.3:
        return "low"
    return "mid"


def print_episode_transcript(entries: list[dict], label: str = ""):
    """Print transcript for a single episode."""
    if not entries:
        return
    e0 = entries[0]
    header = f"[{label}] " if label else ""
    print(f"  {header}D_0={e0['D_0']:.3f} | mode={e0['memory_mode']} | type={e0.get('user_type', '?')}")

    for entry in entries:
        conv = entry["conversation"]
        step = entry["t"]
        e = entry["enablement_score"]
        a = entry["approval_score"]
        s = entry["indulgence_score"]
        d = entry["D"]

        print(f"\n  --- Conv {conv} Step {step} | D={d:.3f} | E={e:.1f} | A={a:.1f} | S={s:.1f}")
        print(f"  Assistant: {entry['assistant_text'][:200]}{'...' if len(entry['assistant_text']) > 200 else ''}")
        print(f"  User: {entry['user_msg'][:200]}{'...' if len(entry['user_msg']) > 200 else ''}")
        print(f"  Reason: {entry.get('approval_reason', 'N/A')[:200]}")
        if entry.get("memory_snapshot") and entry["memory_snapshot"] not in ("<none>", "<full_context>"):
            print(f"  Memory: {entry['memory_snapshot'][:200]}")


def print_side_by_side(episodes_a: dict, episodes_b: dict, label_a: str, label_b: str, d_filter: str = None, ep_filter: int = None):
    """Print two conditions side-by-side per episode."""
    all_eps = sorted(set(episodes_a.keys()) | set(episodes_b.keys()))

    for ep in all_eps:
        if ep_filter is not None and ep != ep_filter:
            continue

        entries_a = episodes_a.get(ep, [])
        entries_b = episodes_b.get(ep, [])

        # Get D_0 from whichever has data
        d0 = entries_a[0]["D_0"] if entries_a else (entries_b[0]["D_0"] if entries_b else 0)
        tier = d_tier(d0)

        if d_filter and tier != d_filter:
            continue

        # Compute mean enablement
        mean_e_a = sum(e["enablement_score"] for e in entries_a) / len(entries_a) if entries_a else 0
        mean_e_b = sum(e["enablement_score"] for e in entries_b) / len(entries_b) if entries_b else 0

        print(f"\n{'='*100}")
        print(f"EPISODE {ep} | D_0={d0:.3f} ({tier}) | mean_e({label_a})={mean_e_a:.2f} | mean_e({label_b})={mean_e_b:.2f}")
        print(f"{'='*100}")

        # Interleave by step
        steps_a = {(e["conversation"], e["t"]): e for e in entries_a}
        steps_b = {(e["conversation"], e["t"]): e for e in entries_b}
        all_steps = sorted(set(steps_a.keys()) | set(steps_b.keys()))

        for conv, step in all_steps:
            print(f"\n{'─'*80}")
            print(f"CONV {conv} | STEP {step}")
            print(f"{'─'*80}")

            for entries_dict, label in [(steps_a, label_a), (steps_b, label_b)]:
                entry = entries_dict.get((conv, step))
                if not entry:
                    print(f"  [{label}] (no data)")
                    continue
                e = entry["enablement_score"]
                a = entry["approval_score"]
                s = entry["indulgence_score"]
                d = entry["D"]
                print(f"  [{label}] E={e:.1f} | A={a:.1f} | S={s:.1f} | D={d:.3f}")
                print(f"    Assistant: {entry['assistant_text'][:300]}")
                print(f"    User: {entry['user_msg'][:300]}")
                print(f"    Reason: {entry.get('approval_reason', 'N/A')[:200]}")


def print_single(episodes: dict, label: str, d_filter: str = None, ep_filter: int = None):
    """Print single-file transcript."""
    for ep in sorted(episodes.keys()):
        if ep_filter is not None and ep != ep_filter:
            continue
        entries = episodes[ep]
        d0 = entries[0]["D_0"]
        tier = d_tier(d0)
        if d_filter and tier != d_filter:
            continue

        mean_e = sum(e["enablement_score"] for e in entries) / len(entries)
        print(f"\n{'='*80}")
        print(f"EPISODE {ep} | D_0={d0:.3f} ({tier}) | mean_e={mean_e:.2f}")
        print(f"{'='*80}")
        print_episode_transcript(entries, label)


def main():
    parser = argparse.ArgumentParser(description="Dump experiment transcripts")
    parser.add_argument("files", nargs="+", help="JSONL log file(s). If two files given, shows side-by-side.")
    parser.add_argument("--d-tier", choices=["high", "mid", "low"], default=None,
                        help="Filter to D_0 tier")
    parser.add_argument("--episode", type=int, default=None,
                        help="Filter to a specific episode ID")
    parser.add_argument("--summary", action="store_true",
                        help="Print per-episode summary stats only (no transcripts)")
    args = parser.parse_args()

    files = args.files

    if args.summary:
        # Summary mode: just stats per episode
        for f in files:
            logs = load_logs(f)
            episodes = group_by_episode(logs)
            label = Path(f).stem
            print(f"\n{'='*60}")
            print(f"FILE: {label}")
            print(f"{'='*60}")
            for ep in sorted(episodes.keys()):
                entries = episodes[ep]
                d0 = entries[0]["D_0"]
                mean_e = sum(e["enablement_score"] for e in entries) / len(entries)
                mean_a = sum(e["approval_score"] for e in entries) / len(entries)
                mode = entries[0]["memory_mode"]
                tier = d_tier(d0)
                if args.d_tier and tier != args.d_tier:
                    continue
                if args.episode is not None and ep != args.episode:
                    continue
                print(f"  Ep {ep:3d} | D_0={d0:.3f} ({tier:4s}) | mode={mode:12s} | mean_e={mean_e:.2f} | mean_a={mean_a:.2f}")
        return

    if len(files) == 2:
        logs_a = load_logs(files[0])
        logs_b = load_logs(files[1])
        episodes_a = group_by_episode(logs_a)
        episodes_b = group_by_episode(logs_b)

        # Infer labels from memory_mode
        label_a = logs_a[0]["memory_mode"] if logs_a else Path(files[0]).stem
        label_b = logs_b[0]["memory_mode"] if logs_b else Path(files[1]).stem

        print_side_by_side(episodes_a, episodes_b, label_a, label_b,
                           d_filter=args.d_tier, ep_filter=args.episode)
    elif len(files) == 1:
        logs = load_logs(files[0])
        episodes = group_by_episode(logs)
        label = logs[0]["memory_mode"] if logs else Path(files[0]).stem
        print_single(episodes, label, d_filter=args.d_tier, ep_filter=args.episode)
    else:
        print("Error: provide 1 or 2 JSONL files", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
