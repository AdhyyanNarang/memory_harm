"""Experiment 4v0 analysis: single-conversation optimization check with character profiles.

Generates plots:
1. Approval score vs turn, by user_type (with smoothed trend)
2. Enablement score vs turn, by user_type (with smoothed trend)
3. Enablement category distribution: early vs late turns, by user_type
4. Approval vs enablement scatter, by user_type
5. Per-episode approval trajectories (faceted)
"""

import json
import sys
from pathlib import Path
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

LOG_FILE = "data/logs/diagnostic_avoidance/exp_none_seed1_20260317_153033.jsonl"
OUT_DIR = Path("reports/plots_4v0")


def load_data(path: str) -> list[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def smooth(x, y, window=5):
    """Simple rolling mean for trend lines."""
    arr = np.array(list(zip(x, y)), dtype=float)
    arr = arr[arr[:, 0].argsort()]
    xs, ys = arr[:, 0], arr[:, 1]
    smoothed_y = np.convolve(ys, np.ones(window) / window, mode="valid")
    smoothed_x = xs[window - 1:]  # align with 'valid' mode
    return smoothed_x, smoothed_y


def main():
    data = load_data(LOG_FILE)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    vuln = [r for r in data if r["user_type"] == "vulnerable"]
    norm = [r for r in data if r["user_type"] == "not_vulnerable"]

    print(f"Total rows: {len(data)}")
    print(f"Vulnerable: {len(vuln)} rows, {len(set(r['episode'] for r in vuln))} episodes")
    print(f"Not vulnerable: {len(norm)} rows, {len(set(r['episode'] for r in norm))} episodes")

    # Summary stats
    for label, subset in [("Vulnerable", vuln), ("Not vulnerable", norm)]:
        early = [r for r in subset if r["t"] < 10]
        late = [r for r in subset if r["t"] >= 40]
        print(f"\n{label}:")
        print(f"  Approval  early (t<10): {np.mean([r['approval_score'] for r in early]):.2f}")
        print(f"  Approval  late (t>=40): {np.mean([r['approval_score'] for r in late]):.2f}")
        print(f"  Enablement early (t<10): {np.mean([r['enablement_score'] for r in early]):.2f}")
        print(f"  Enablement late (t>=40): {np.mean([r['enablement_score'] for r in late]):.2f}")
        early_cats = Counter(r.get("enablement_category", "?") for r in early)
        late_cats = Counter(r.get("enablement_category", "?") for r in late)
        print(f"  Categories early: {dict(early_cats)}")
        print(f"  Categories late:  {dict(late_cats)}")

    colors = {"vulnerable": "#d62728", "not_vulnerable": "#1f77b4"}

    # --- Plot 1: Approval vs turn ---
    fig, ax = plt.subplots(figsize=(10, 5))
    for label, subset, color in [("Vulnerable", vuln, colors["vulnerable"]),
                                  ("Not vulnerable", norm, colors["not_vulnerable"])]:
        turns = [r["t"] for r in subset]
        scores = [r["approval_score"] for r in subset]
        ax.scatter(turns, scores, alpha=0.15, s=10, color=color)
        # Per-turn mean
        turn_means = {}
        for r in subset:
            turn_means.setdefault(r["t"], []).append(r["approval_score"])
        xs = sorted(turn_means.keys())
        ys = [np.mean(turn_means[t]) for t in xs]
        ax.plot(xs, ys, color=color, linewidth=2, label=f"{label} (mean)")
    ax.set_xlabel("Turn")
    ax.set_ylabel("Approval Score (1-10)")
    ax.set_title("Experiment 4v0: Approval Score vs Turn")
    ax.legend()
    ax.set_ylim(0, 10.5)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "approval_vs_turn.png", dpi=150)
    plt.close(fig)

    # --- Plot 2: Enablement vs turn ---
    fig, ax = plt.subplots(figsize=(10, 5))
    for label, subset, color in [("Vulnerable", vuln, colors["vulnerable"]),
                                  ("Not vulnerable", norm, colors["not_vulnerable"])]:
        turns = [r["t"] for r in subset]
        scores = [r["enablement_score"] for r in subset]
        ax.scatter(turns, scores, alpha=0.15, s=10, color=color)
        turn_means = {}
        for r in subset:
            turn_means.setdefault(r["t"], []).append(r["enablement_score"])
        xs = sorted(turn_means.keys())
        ys = [np.mean(turn_means[t]) for t in xs]
        ax.plot(xs, ys, color=color, linewidth=2, label=f"{label} (mean)")
    ax.set_xlabel("Turn")
    ax.set_ylabel("Enablement Score (0-10)")
    ax.set_title("Experiment 4v0: Enablement Score vs Turn")
    ax.legend()
    ax.set_ylim(-0.5, 10.5)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "enablement_vs_turn.png", dpi=150)
    plt.close(fig)

    # --- Plot 3: Category distribution early vs late ---
    categories = ["a", "b", "c", "d"]
    cat_labels = ["(a) explicit\nendorsement", "(b) implicit\nvalidation", "(c) neutral", "(d) encouraged\nengagement"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, (label, subset) in zip(axes, [("Vulnerable", vuln), ("Not vulnerable", norm)]):
        early = [r for r in subset if r["t"] < 10]
        late = [r for r in subset if r["t"] >= 40]
        early_counts = Counter(r.get("enablement_category", "?") for r in early)
        late_counts = Counter(r.get("enablement_category", "?") for r in late)
        n_early = len(early) or 1
        n_late = len(late) or 1
        x = np.arange(len(categories))
        w = 0.35
        early_pcts = [early_counts.get(c, 0) / n_early * 100 for c in categories]
        late_pcts = [late_counts.get(c, 0) / n_late * 100 for c in categories]
        ax.bar(x - w/2, early_pcts, w, label="Early (t<10)", alpha=0.8, color="#7fbf7f")
        ax.bar(x + w/2, late_pcts, w, label="Late (t>=40)", alpha=0.8, color="#ff7f7f")
        ax.set_xticks(x)
        ax.set_xticklabels(cat_labels, fontsize=9)
        ax.set_title(label)
        ax.set_ylabel("% of turns")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")
    fig.suptitle("Enablement Category Distribution: Early vs Late Turns", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "category_distribution.png", dpi=150)
    plt.close(fig)

    # --- Plot 4: Approval vs enablement scatter ---
    fig, ax = plt.subplots(figsize=(8, 6))
    for label, subset, color in [("Vulnerable", vuln, colors["vulnerable"]),
                                  ("Not vulnerable", norm, colors["not_vulnerable"])]:
        approval = [r["approval_score"] for r in subset]
        enablement = [r["enablement_score"] for r in subset]
        ax.scatter(enablement, approval, alpha=0.25, s=15, color=color, label=label)
        # Correlation
        if len(approval) > 2:
            corr = np.corrcoef(enablement, approval)[0, 1]
            ax.annotate(f"r={corr:.2f}", xy=(0.05 if label == "Vulnerable" else 0.55, 0.95 if label == "Vulnerable" else 0.90),
                       xycoords="axes fraction", color=color, fontsize=11, fontweight="bold")
    ax.set_xlabel("Enablement Score")
    ax.set_ylabel("Approval Score")
    ax.set_title("Approval vs Enablement (by user type)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "approval_vs_enablement.png", dpi=150)
    plt.close(fig)

    # --- Plot 5: Per-episode approval trajectories ---
    episodes_vuln = sorted(set(r["episode"] for r in vuln))
    episodes_norm = sorted(set(r["episode"] for r in norm))
    n_vuln = len(episodes_vuln)
    n_norm = len(episodes_norm)
    n_cols = max(n_vuln, n_norm)
    fig, axes = plt.subplots(2, n_cols, figsize=(3.5 * n_cols, 7), sharey=True, squeeze=False)
    for col, ep in enumerate(episodes_vuln):
        ep_data = [r for r in vuln if r["episode"] == ep]
        ts = [r["t"] for r in ep_data]
        axes[0][col].plot(ts, [r["approval_score"] for r in ep_data], color=colors["vulnerable"], alpha=0.7, linewidth=1)
        axes[0][col].plot(ts, [r["enablement_score"] for r in ep_data], color="gray", alpha=0.5, linewidth=1, linestyle="--")
        name = ep_data[0].get("profile_name", f"Ep {ep}")
        axes[0][col].set_title(f"V: {name[:15]}", fontsize=8)
        axes[0][col].set_ylim(0, 10.5)
        axes[0][col].grid(True, alpha=0.2)
    for col, ep in enumerate(episodes_norm):
        ep_data = [r for r in norm if r["episode"] == ep]
        ts = [r["t"] for r in ep_data]
        axes[1][col].plot(ts, [r["approval_score"] for r in ep_data], color=colors["not_vulnerable"], alpha=0.7, linewidth=1)
        axes[1][col].plot(ts, [r["enablement_score"] for r in ep_data], color="gray", alpha=0.5, linewidth=1, linestyle="--")
        name = ep_data[0].get("profile_name", f"Ep {ep}")
        axes[1][col].set_title(f"NV: {name[:15]}", fontsize=8)
        axes[1][col].set_ylim(0, 10.5)
        axes[1][col].grid(True, alpha=0.2)
    # Hide unused axes
    for row in range(2):
        for col in range(n_cols):
            if (row == 0 and col >= n_vuln) or (row == 1 and col >= n_norm):
                axes[row][col].set_visible(False)
    fig.suptitle("Per-Episode Trajectories (red/blue=approval, gray dashed=enablement)", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "per_episode_trajectories.png", dpi=150)
    plt.close(fig)

    print(f"\nPlots saved to {OUT_DIR}/")


if __name__ == "__main__":
    main()
