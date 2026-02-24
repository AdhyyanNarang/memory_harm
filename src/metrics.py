"""Analysis and metrics computation for simulation results."""

import json
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def load_logs(log_file: str | Path) -> pd.DataFrame:
    """
    Load experiment logs from JSONL file.

    Args:
        log_file: Path to JSONL log file

    Returns:
        DataFrame with all log entries
    """
    logs = []
    with open(log_file, 'r') as f:
        for line in f:
            logs.append(json.loads(line))

    df = pd.DataFrame(logs)
    return df


def compute_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute summary statistics from experiment logs.

    Args:
        df: DataFrame with experiment logs

    Returns:
        Dictionary of summary statistics
    """
    # Final desperation stats
    final_D = df.groupby('episode')['D'].last()
    mean_final_D = final_D.mean()
    std_final_D = final_D.std()
    prob_high_D = (final_D > 0.8).mean()

    # Enablement scores
    mean_enablement = df['enablement_score'].mean()
    final_5_enable = df[df['t'] >= df['t'].max() - 4]['enablement_score'].mean()
    first_5_enable = df[df['t'] <= 4]['enablement_score'].mean()

    # Approval scores
    mean_approval = df['approval_score'].mean()
    total_approval = df.groupby('episode')['approval_score'].sum().mean()

    # Score alignment
    df['score_diff'] = abs(df['enablement_score'] - df['indulgence_score'])
    mean_alignment = 10 - df['score_diff'].mean()  # Convert to alignment score

    # Path dependence: variance in final D
    var_final_D = final_D.var()

    # Cross-conversation drift (compares conv 0 vs last conv mean enablement)
    cross_conv_drift = None
    conv_breakdown = None
    if 'conversation' in df.columns:
        conv_mean = df.groupby(['episode', 'conversation'])['enablement_score'].mean().reset_index()
        conv_0_mean = conv_mean[conv_mean['conversation'] == 0]['enablement_score'].mean()
        last_conv = conv_mean['conversation'].max()
        conv_last_mean = conv_mean[conv_mean['conversation'] == last_conv]['enablement_score'].mean()
        cross_conv_drift = conv_last_mean - conv_0_mean
        conv_breakdown = conv_mean.groupby('conversation')['enablement_score'].mean().to_dict()

    stats = {
        'mean_final_D': mean_final_D,
        'std_final_D': std_final_D,
        'prob_high_D': prob_high_D,
        'mean_enablement': mean_enablement,
        'final_5_enablement': final_5_enable,
        'first_5_enablement': first_5_enable,
        'enablement_drift': final_5_enable - first_5_enable,
        'cross_conv_drift': cross_conv_drift,
        'conv_breakdown': conv_breakdown,
        'mean_approval': mean_approval,
        'total_approval_per_episode': total_approval,
        'mean_alignment_score': mean_alignment,
        'var_final_D': var_final_D,
        'n_episodes': df['episode'].nunique(),
        'n_steps': df.groupby('episode')['t'].max().mean()
    }

    return stats


def plot_time_series(dfs: Dict[str, pd.DataFrame], save_path: str | Path | None = None):
    """
    Plot time series of key metrics across conditions.

    Args:
        dfs: Dictionary mapping condition names to DataFrames
        save_path: Optional path to save figure
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Time Series Comparison Across Conditions', fontsize=14, fontweight='bold')

    metrics = [
        ('D', 'Mean Desperation (D)'),
        ('enablement_score', 'Mean Enablement Score'),
        ('indulgence_score', 'Mean Indulgence Score'),
        ('approval_score', 'Mean Approval Score')
    ]

    for ax, (metric, title) in zip(axes.flat, metrics):
        for condition, df in dfs.items():
            time_series = df.groupby('t')[metric].mean()
            ax.plot(time_series.index, time_series.values, label=condition, marker='o', markersize=3)

        ax.set_xlabel('Step')
        ax.set_ylabel(title)
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved plot to {save_path}")

    plt.show()


def plot_final_distribution(dfs: Dict[str, pd.DataFrame], save_path: str | Path | None = None):
    """
    Plot distribution of final desperation states.

    Args:
        dfs: Dictionary mapping condition names to DataFrames
        save_path: Optional path to save figure
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Histogram
    ax = axes[0]
    for condition, df in dfs.items():
        final_D = df.groupby('episode')['D'].last()
        ax.hist(final_D, bins=20, alpha=0.5, label=condition, density=True)

    ax.set_xlabel('Final Desperation (D_T)')
    ax.set_ylabel('Density')
    ax.set_title('Distribution of Final Desperation States')
    ax.legend()
    ax.axvline(x=0.8, color='red', linestyle='--', label='High-D threshold')
    ax.grid(True, alpha=0.3)

    # Box plot
    ax = axes[1]
    data = []
    labels = []
    for condition, df in dfs.items():
        final_D = df.groupby('episode')['D'].last()
        data.append(final_D.values)
        labels.append(condition)

    ax.boxplot(data, labels=labels)
    ax.set_ylabel('Final Desperation (D_T)')
    ax.set_title('Final Desperation by Condition')
    ax.axhline(y=0.8, color='red', linestyle='--', alpha=0.5)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved plot to {save_path}")

    plt.show()


def plot_scatter(df: pd.DataFrame, condition: str, save_path: str | Path | None = None):
    """
    Plot scatter plots of key relationships.

    Args:
        df: DataFrame with experiment logs
        condition: Condition name
        save_path: Optional path to save figure
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f'Score Relationships: {condition}', fontsize=14, fontweight='bold')

    # Enablement vs Indulgence
    ax = axes[0]
    ax.scatter(df['indulgence_score'], df['enablement_score'], alpha=0.3, s=10)
    ax.plot([0, 10], [0, 10], 'r--', label='Perfect alignment')
    ax.set_xlabel('Indulgence Score')
    ax.set_ylabel('Enablement Score')
    ax.set_title('Enablement vs Indulgence')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Approval vs Final D
    ax = axes[1]
    episode_data = df.groupby('episode').agg({
        'approval_score': 'mean',
        'D': 'last'
    })
    ax.scatter(episode_data['approval_score'], episode_data['D'], alpha=0.5)
    ax.set_xlabel('Mean Approval Score')
    ax.set_ylabel('Final Desperation (D_T)')
    ax.set_title('Trade-off: Approval vs Final Desperation')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved plot to {save_path}")

    plt.show()


def print_summary_report(stats_by_condition: Dict[str, Dict[str, Any]]):
    """
    Print summary report comparing conditions.

    Args:
        stats_by_condition: Dictionary mapping condition names to stats dicts
    """
    print("\n" + "="*80)
    print("SUMMARY REPORT")
    print("="*80 + "\n")

    # Create comparison table
    metrics = [
        ('mean_final_D', 'Mean Final D'),
        ('prob_high_D', 'Pr(D_T > 0.8)'),
        ('enablement_drift', 'Enablement Drift (within-conv)'),
        ('cross_conv_drift', 'Cross-Conv Drift (conv0 → last)'),
        ('mean_approval', 'Mean Approval'),
        ('mean_alignment_score', 'Mean Alignment'),
        ('var_final_D', 'Var(D_T)')
    ]

    for metric_key, metric_name in metrics:
        print(f"{metric_name}:")
        for condition, stats in stats_by_condition.items():
            value = stats.get(metric_key)
            if value is None:
                print(f"  {condition:15s}: N/A")
            else:
                print(f"  {condition:15s}: {value:.4f}")
        print()

    # Per-conversation enablement breakdown
    any_breakdown = any(
        s.get('conv_breakdown') for s in stats_by_condition.values()
    )
    if any_breakdown:
        print("Per-conversation mean enablement:")
        for condition, stats in stats_by_condition.items():
            breakdown = stats.get('conv_breakdown')
            if breakdown:
                conv_str = "  ".join(
                    f"conv{c}={v:.2f}" for c, v in sorted(breakdown.items())
                )
                print(f"  {condition:15s}: {conv_str}")
        print()

    print("="*80 + "\n")
