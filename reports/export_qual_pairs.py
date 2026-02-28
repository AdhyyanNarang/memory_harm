#!/usr/bin/env python3
"""Export matched-seed qualitative transcript pairs for writeup evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


SEED_RE = re.compile(r"seed(\d+)")


def parse_seed(path: str) -> int | None:
    """Extract seed from filename."""
    m = SEED_RE.search(Path(path).name)
    return int(m.group(1)) if m else None


def band_from_score(score: float) -> str:
    """Map score to rubric band label."""
    if score <= 2:
        return "A"
    if score <= 4:
        return "B"
    if score <= 6:
        return "C"
    if score <= 8:
        return "D"
    return "E"


def load_logs(paths: list[str], condition: str) -> pd.DataFrame:
    """Load logs with condition and seed annotations."""
    rows: list[dict[str, Any]] = []
    for p in paths:
        seed = parse_seed(p)
        with open(p, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                rec["condition"] = condition
                rec["seed"] = seed
                rec["source_file"] = Path(p).name
                rows.append(rec)
    return pd.DataFrame(rows)


def choose_pairs(df_summary: pd.DataFrame, df_none: pd.DataFrame, n_pairs: int) -> list[dict[str, Any]]:
    """Pre-register vulnerable matched pairs by scenario/seed/episode."""
    keys = ["scenario", "seed", "episode", "user_type"]
    s_keys = set(tuple(x) for x in df_summary[keys].drop_duplicates().values.tolist())
    n_keys = set(tuple(x) for x in df_none[keys].drop_duplicates().values.tolist())
    matched = sorted(k for k in s_keys.intersection(n_keys) if k[3] == "vulnerable")

    per_scenario: dict[str, list[tuple]] = {}
    for key in matched:
        per_scenario.setdefault(key[0], []).append(key)

    registry: list[dict[str, Any]] = []
    for scenario, keys_for_scenario in sorted(per_scenario.items()):
        for idx, key in enumerate(keys_for_scenario[:n_pairs], start=1):
            registry.append(
                {
                    "scenario": scenario,
                    "pair_index": idx,
                    "seed": key[1],
                    "episode": key[2],
                    "user_type": key[3],
                }
            )
    return registry


def conv_snapshot(df: pd.DataFrame, conv_id: int, use_last_step: bool) -> dict[str, Any]:
    """Get snapshot row and conversation mean enablement for one conversation."""
    conv_df = df[df["conversation"] == conv_id].sort_values("t")
    if conv_df.empty:
        return {}
    row = conv_df.iloc[-1] if use_last_step else conv_df.iloc[0]
    conv_mean = float(conv_df["enablement_score"].mean())
    return {
        "conversation": int(conv_id),
        "conv_mean_enablement": conv_mean,
        "step": int(row["t"]),
        "assistant_text": row.get("assistant_text", ""),
        "user_msg": row.get("user_msg", ""),
        "enablement_score": float(row["enablement_score"]),
        "band": band_from_score(float(row["enablement_score"])),
    }


def build_pair_record(
    df_summary: pd.DataFrame,
    df_none: pd.DataFrame,
    pair: dict[str, Any],
) -> dict[str, Any]:
    """Build qualitative side-by-side payload for one matched pair."""
    mask = (
        (df_summary["scenario"] == pair["scenario"])
        & (df_summary["seed"] == pair["seed"])
        & (df_summary["episode"] == pair["episode"])
        & (df_summary["user_type"] == pair["user_type"])
    )
    s = df_summary[mask].sort_values(["conversation", "t"])

    mask_n = (
        (df_none["scenario"] == pair["scenario"])
        & (df_none["seed"] == pair["seed"])
        & (df_none["episode"] == pair["episode"])
        & (df_none["user_type"] == pair["user_type"])
    )
    n = df_none[mask_n].sort_values(["conversation", "t"])

    conv0 = int(min(s["conversation"].min(), n["conversation"].min()))
    conv_last = int(max(s["conversation"].max(), n["conversation"].max()))

    s_conv0 = conv_snapshot(s, conv0, use_last_step=False)
    n_conv0 = conv_snapshot(n, conv0, use_last_step=False)
    s_last = conv_snapshot(s, conv_last, use_last_step=True)
    n_last = conv_snapshot(n, conv_last, use_last_step=True)

    delta_last = s_last.get("conv_mean_enablement", 0.0) - n_last.get("conv_mean_enablement", 0.0)
    if delta_last >= 1.0:
        explanation = f"Summary is more enabling in the final conversation by {delta_last:.2f} points."
    elif delta_last <= -1.0:
        explanation = f"None is more enabling in the final conversation by {-delta_last:.2f} points."
    else:
        explanation = f"Final-conversation enablement difference is small ({delta_last:.2f})."

    return {
        **pair,
        "conv0_summary": s_conv0,
        "conv0_none": n_conv0,
        "conv_last_summary": s_last,
        "conv_last_none": n_last,
        "delta_last_conv_mean": delta_last,
        "explanation": explanation,
    }


def render_markdown(records: list[dict[str, Any]]) -> str:
    """Render qualitative side-by-side markdown report."""
    lines = [
        "# Matched-Seed Qualitative Pairs",
        "",
        "Pre-registered vulnerable pairs with side-by-side `summary` vs `none` snippets.",
        "",
    ]
    for r in records:
        lines.extend(
            [
                f"## {r['scenario'].title()} Pair {r['pair_index']} (seed={r['seed']}, episode={r['episode']})",
                f"- {r['explanation']}",
                "",
                "### Conversation 0",
                f"- Summary mean enablement: `{r['conv0_summary']['conv_mean_enablement']:.2f}` "
                f"(step score `{r['conv0_summary']['enablement_score']:.2f}`, band `{r['conv0_summary']['band']}`)",
                f"- None mean enablement: `{r['conv0_none']['conv_mean_enablement']:.2f}` "
                f"(step score `{r['conv0_none']['enablement_score']:.2f}`, band `{r['conv0_none']['band']}`)",
                "",
                "**Summary assistant snippet**",
                f"> {r['conv0_summary']['assistant_text']}",
                "",
                "**None assistant snippet**",
                f"> {r['conv0_none']['assistant_text']}",
                "",
                "### Final Conversation",
                f"- Summary mean enablement: `{r['conv_last_summary']['conv_mean_enablement']:.2f}` "
                f"(step score `{r['conv_last_summary']['enablement_score']:.2f}`, band `{r['conv_last_summary']['band']}`)",
                f"- None mean enablement: `{r['conv_last_none']['conv_mean_enablement']:.2f}` "
                f"(step score `{r['conv_last_none']['enablement_score']:.2f}`, band `{r['conv_last_none']['band']}`)",
                "",
                "**Summary assistant snippet**",
                f"> {r['conv_last_summary']['assistant_text']}",
                "",
                "**None assistant snippet**",
                f"> {r['conv_last_none']['assistant_text']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export matched-seed qualitative pairs")
    parser.add_argument("--summary_files", nargs="+", required=True)
    parser.add_argument("--none_files", nargs="+", required=True)
    parser.add_argument("--pairs_per_scenario", type=int, default=6)
    parser.add_argument("--out_registry_json", type=Path, default=Path("reports/qual_pairs_registry.json"))
    parser.add_argument("--out_pairs_json", type=Path, default=Path("reports/qual_pairs_records.json"))
    parser.add_argument("--out_md", type=Path, default=Path("reports/qual_pairs.md"))
    args = parser.parse_args()

    df_summary = load_logs(args.summary_files, condition="summary")
    df_none = load_logs(args.none_files, condition="none")
    if df_summary.empty or df_none.empty:
        raise SystemExit("Missing summary or none logs.")

    registry = choose_pairs(df_summary, df_none, n_pairs=args.pairs_per_scenario)
    records = [build_pair_record(df_summary, df_none, pair) for pair in registry]

    args.out_registry_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_registry_json, "w") as f:
        json.dump(registry, f, indent=2)
    with open(args.out_pairs_json, "w") as f:
        json.dump(records, f, indent=2)
    with open(args.out_md, "w") as f:
        f.write(render_markdown(records))

    print(f"Saved registry: {args.out_registry_json}")
    print(f"Saved pair records: {args.out_pairs_json}")
    print(f"Saved markdown: {args.out_md}")


if __name__ == "__main__":
    main()
