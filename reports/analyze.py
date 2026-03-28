"""Analysis script for experiment results."""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metrics import (
    load_logs,
    compute_summary_stats,
    plot_time_series,
    plot_final_distribution,
    plot_scatter,
    print_summary_report
)


def _resolve_log_dir(log_dir: str) -> Path:
    """Resolve log directory with Colab+Drive fallback."""
    requested = Path(log_dir)
    if requested.exists():
        return requested

    drive_candidate = Path("/content/drive/MyDrive/memory_harm_Shinu/data/logs")
    if drive_candidate.exists():
        print(f"Using Drive logs: {drive_candidate}")
        return drive_candidate

    return requested


def analyze_experiments(log_dir: str = "data/logs"):
    """
    Analyze experiment results.

    Args:
        log_dir: Directory containing log files
    """
    log_path = _resolve_log_dir(log_dir)

    # Find log files for different conditions
    conditions = {}
    for mode in ["full_context", "summary", "none"]:
        log_files = list(log_path.glob(f"exp_{mode}_*.jsonl"))
        if log_files:
            print(f"Found {len(log_files)} log file(s) for {mode} mode")
            # Use the first one (or merge if multiple)
            conditions[mode] = load_logs(log_files[0])

    if not conditions:
        print(f"No log files found in {log_dir}")
        print("Run experiments first using: python run_experiment.py")
        return

    # Compute stats
    stats_by_condition = {}
    for condition, df in conditions.items():
        print(f"\nComputing stats for {condition}...")
        stats = compute_summary_stats(df)
        stats_by_condition[condition] = stats

    # Print summary report
    print_summary_report(stats_by_condition)

    # Generate plots
    print("Generating plots...")

    # Time series
    plot_time_series(conditions, save_path="reports/time_series.png")

    # Final distribution
    plot_final_distribution(conditions, save_path="reports/final_distribution.png")

    # Scatter plots for each condition
    for condition, df in conditions.items():
        plot_scatter(df, condition, save_path=f"reports/scatter_{condition}.png")

    print("\nAnalysis complete!")
    print("Plots saved to reports/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze experiment result logs")
    parser.add_argument("--log_dir", type=str, default="data/logs",
                        help="Directory containing experiment jsonl logs")
    args = parser.parse_args()
    analyze_experiments(args.log_dir)
