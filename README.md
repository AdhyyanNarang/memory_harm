# Fork details

This is the copy of the original 'memory_harm' repo. This copy has modifications made by Laxman to run Google Colab Pro (A100 GPU). I think the code can also run on Colab Free version (just a different GPU ig). Follow the instructions on Run_Experiment_Laxman.ipynb notebook to run the code.





# Memory-Driven Personalization Can Induce Harmful Drift

LLM-vs-LLM simulation demonstrating how memory-based personalization at inference time can create self-reinforcing harmful feedback loops.

## Setup

```bash
pip install -r requirements.txt
```

Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Project Structure

```
memory_harm/
├── configs/           # Experiment configurations
│   └── exp.yaml      # Main config file
├── src/              # Source code
│   ├── sim.py        # Main simulation loop
│   ├── assistant.py  # Assistant LLM interface
│   ├── user.py       # Simulated user LLM
│   ├── memory.py     # Memory management
│   ├── prompts.py    # Prompt templates
│   ├── metrics.py    # Analysis and metrics
│   └── utils.py      # Utility functions
├── data/logs/        # Experiment logs (JSONL)
├── reports/          # Analysis notebooks
├── tests/            # Unit tests
└── project_plan.md   # Detailed specification
```

## Running Experiments

```bash
# Run a single experiment
python src/sim.py --config configs/exp.yaml

# Run with different memory modes
python src/sim.py --config configs/exp.yaml --memory_mode full_context
python src/sim.py --config configs/exp.yaml --memory_mode summary
python src/sim.py --config configs/exp.yaml --memory_mode none
```

## Analysis

See `reports/analyze.ipynb` for analysis and visualization.

## Key Concepts

- **Desperation (D)**: Hidden user state in [0,1] affecting behavior
- **Enablement score**: How much assistant validates immediate indulgence (0-10)
- **Indulgence score**: User's tendency to indulge based on D (0-10)
- **Approval score**: Reward based on alignment between enablement and indulgence
- **Memory modes**: full_context, summary, or none

See `project_plan.md` for complete technical specification.
