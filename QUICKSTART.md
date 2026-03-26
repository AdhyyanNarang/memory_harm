# Quickstart Guide

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set OpenAI API key**:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Running a Pilot Experiment

Start with a small pilot to test the setup:

```bash
# Run 5 users, each having 2 conversations with 5 steps per conversation
python run_experiment.py --episodes 5 --conversations 2 --steps 5 --memory_mode summary
```

This will:
- Simulate 5 users, each with hidden desperation state D
- Each user has 2 separate conversations (returning user)
- Each conversation has 5 interaction steps (total: 10 steps per user)
- Memory and D persist across conversations for each user
- Runs with 10 concurrent users by default (async execution)
- Save logs to `data/logs/exp_summary_seed123.jsonl`

### Saving Logs to Colab + Drive

```bash
python run_experiment.py --episodes 5 --conversations 2 --steps 5 --memory_mode summary --use_colab_drive
```

Using this option mounts Google Drive in Colab and saves logs to:
`/content/drive/MyDrive/memory_harm_Shinu/data/logs/`

### Colab One-Cell Run Management

Use this cell in Colab after your experiment to save run metadata and checkpoint the notebook:

```python
from src.colab_workflow import (
    mount_drive_if_needed,
    DriveLayout,
    save_run_manifest,
    save_notebook_checkpoint,
)

mount_drive_if_needed()
layout = DriveLayout.from_drive(project_name="memory_harm_Shinu")
layout.ensure_dirs()

manifest_path = save_run_manifest(
    layout,
    note="therapy scenario run in Colab",
    extra={"memory_mode": "summary", "episodes": 50, "conversations": 5, "steps": 6},
)
print(f"Saved run manifest: {manifest_path}")

save_notebook_checkpoint()
print("Notebook checkpoint requested.")
```

This keeps outputs in Drive and avoids committing large runtime artifacts to GitHub.

## Understanding the Multi-Conversation Structure

**New structure**:
- **Episode** = One user's entire journey
- **Conversation** = One session (user returns multiple times)
- **Step** = One turn within a conversation

**Key feature**: Desperation (D) and memory **persist across conversations** for each user, making the simulation more realistic.

## Running Full Experiments

To run all three conditions for the full experiment:

```bash
# M-full: Full conversation context
python run_experiment.py --memory_mode full_context

# M-sum: Summary memory
python run_experiment.py --memory_mode summary

# M-none: No memory baseline
python run_experiment.py --memory_mode none
```

**Default settings** (in `configs/exp.yaml`):
- 500 users (episodes)
- 5 conversations per user
- 6 steps per conversation
- Total: 30 steps per user (same as before, but split into sessions)
- 10 concurrent users (async execution for ~5-10x speedup)

**Note**: Each condition makes ~45,000 LLM calls (500 × 5 × 6 × 3 calls/step). With async execution and `max_concurrent=10`, this takes 2-4 hours instead of 10-20 hours.

## Analyzing Results

### Option 1: Interactive Dashboard (Recommended)

Launch the Jupyter notebook dashboard for interactive exploration:

```bash
jupyter notebook reports/dashboard.ipynb
```

The dashboard provides:
- 📊 Aggregate time series plots (desperation, approval, enablement over time)
- 🔍 Interactive episode browser with full conversation transcripts
- 📈 Distribution plots and statistics
- 💬 Search for interesting episodes (high/low D, big changes)
- 🔀 Compare multiple experiments side-by-side

### Option 2: Command-line Analysis

For quick statistics and plots:

```bash
python reports/analyze.py
```

To explicitly analyze logs saved in Colab + Drive:

```bash
python reports/analyze.py --log_dir /content/drive/MyDrive/memory_harm_Shinu/data/logs
```

This will:
- Load all experiment logs
- Compute summary statistics
- Generate comparison plots
- Save visualizations to `reports/`

## Understanding the Output

### Log Files

Each line in the JSONL log file contains:
- `episode`: Episode number
- `t`: Step number within episode
- `D`: Current desperation state
- `approval_score`: User's approval (0-10)
- `enablement_score`: How much assistant enables indulgence (0-10)
- `indulgence_score`: User's tendency to indulge (0-10)
- `user_msg`: User's message
- `assistant_text`: Assistant's response
- `memory_snapshot`: Current memory state

### Key Metrics

- **Mean Final D**: Average desperation at end of episodes
- **Pr(D_T > 0.8)**: Proportion of episodes ending in high desperation
- **Enablement Drift**: Change in enablement scores from early to late steps
- **Mean Approval**: Average approval score across all interactions
- **Mean Alignment**: How well enablement matches indulgence

## Adjusting Configuration

Edit `configs/exp.yaml` to modify:
- `steps`: Number of steps per episode (default: 30)
- `episodes`: Number of episodes to run (default: 500)
- `alpha`, `beta`: Parameters controlling desperation dynamics
- `assistant_model`, `user_model`: LLM models to use

## Troubleshooting

**API Key Error**:
- Make sure OPENAI_API_KEY is set in your environment
- Verify your API key has sufficient credits

**Import Errors**:
- Make sure you're running from the project root directory
- Try: `export PYTHONPATH=$PYTHONPATH:$(pwd)`

**Memory Errors**:
- Reduce `episodes` or `steps` for smaller experiments
- Results are saved incrementally, so you can stop and analyze partial results

## Running Tests

```bash
pytest tests/
```

## Next Steps

- Review `project_plan.md` for complete technical specification
- Examine log files to understand the feedback loop dynamics
- Try different memory modes and compare results
- Modify prompts in `src/prompts.py` to test variations
