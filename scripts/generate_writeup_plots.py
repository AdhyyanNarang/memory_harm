"""Generate enablement-over-time plots for all experiments in the LaTeX writeup."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = Path("latex/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = Path("data/logs/diagnostic_avoidance")

COLORS = {
    "summary": "#d62728",
    "none": "#1f77b4",
    "vulnerable": "#d62728",
    "not_vulnerable": "#1f77b4",
}


def load(path):
    with open(path) as f:
        return [json.loads(l) for l in f]


def per_step_mean(rows, step_key="total_step", score_key="enablement_score"):
    buckets = {}
    for r in rows:
        buckets.setdefault(r[step_key], []).append(r[score_key])
    xs = sorted(buckets)
    ys = [np.mean(buckets[t]) for t in xs]
    return xs, ys


def plot_two_conditions(
    data_a, data_b, label_a, label_b, color_a, color_b,
    title, xlabel, out_path, step_key="total_step",
):
    fig, ax = plt.subplots(figsize=(6, 3.2))
    for data, label, color in [(data_a, label_a, color_a), (data_b, label_b, color_b)]:
        ts = [r[step_key] for r in data]
        es = [r["enablement_score"] for r in data]
        ax.scatter(ts, es, alpha=0.10, s=6, color=color, rasterized=True)
        xs, ys = per_step_mean(data, step_key=step_key)
        ax.plot(xs, ys, color=color, linewidth=1.8, label=label)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel("Enablement (0–10)", fontsize=9)
    ax.set_title(title, fontsize=10)
    ax.set_ylim(-0.3, 10.5)
    ax.legend(fontsize=8, loc="best")
    ax.grid(True, alpha=0.25)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)
    print(f"  Saved {out_path}")


# ── Experiments 1-3: summary vs none, vulnerable only ────────────────────────

exp_multi = [
    (
        "exp1",
        "Exp 1: Tightened Evaluator",
        "exp_none_seed1_20260317_015420.jsonl",
        "exp_summary_seed1_20260317_015420.jsonl",
    ),
    (
        "exp2",
        "Exp 2: Assistant Model Upgrade",
        "exp_none_seed1_20260317_021427.jsonl",
        "exp_summary_seed1_20260317_021428.jsonl",
    ),
    (
        "exp3",
        "Exp 3: Structured Memory Prompt",
        "exp_none_seed1_20260317_023550.jsonl",
        "exp_summary_seed1_20260317_023550.jsonl",
    ),
]

print("=== Exps 1-3 (summary vs none, vulnerable) ===")
for name, title, none_file, summary_file in exp_multi:
    none_data = load(LOG_DIR / none_file)
    summ_data = load(LOG_DIR / summary_file)
    # Filter to vulnerable only
    none_vuln = [r for r in none_data if r["user_type"] == "vulnerable"]
    summ_vuln = [r for r in summ_data if r["user_type"] == "vulnerable"]
    plot_two_conditions(
        summ_vuln, none_vuln,
        "summary", "none",
        COLORS["summary"], COLORS["none"],
        title=title,
        xlabel="Step (across conversations)",
        out_path=OUT_DIR / f"{name}_enablement.png",
        step_key="total_step",
    )

# ── Experiments 4v0+: vulnerable vs not-vulnerable, single conversation ──────

exp_single = [
    (
        "exp4v0",
        "Exp 4v0: Pre-Fix (missing char\\_prompt)",
        "exp_none_seed1_20260317_153033.jsonl",
    ),
    (
        "exp4v0a",
        "Exp 4v0a: With char\\_prompt Fix",
        "exp_none_seed1_20260317_160043.jsonl",
    ),
    (
        "exp4v0b",
        "Exp 4v0b: Higher Temp + Exploration",
        "exp_none_seed1_20260317_160846.jsonl",
    ),
    (
        "exp4v0c",
        "Exp 4v0c: Secretly Hoping",
        "exp_none_seed1_20260317_164400.jsonl",
    ),
    (
        "exp4v0e",
        "Exp 4v0e: Deep Down + Gen Init",
        "exp_none_seed1_20260317_165806.jsonl",
    ),
]

print("\n=== Exps 4v0+ (vulnerable vs not-vulnerable) ===")
for name, title, log_file in exp_single:
    data = load(LOG_DIR / log_file)
    vuln = [r for r in data if r["user_type"] == "vulnerable"]
    norm = [r for r in data if r["user_type"] == "not_vulnerable"]
    plot_two_conditions(
        vuln, norm,
        "Vulnerable", "Not vulnerable",
        COLORS["vulnerable"], COLORS["not_vulnerable"],
        title=title,
        xlabel="Turn",
        out_path=OUT_DIR / f"{name}_enablement.png",
        step_key="t",
    )

print("\nDone.")
