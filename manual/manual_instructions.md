# Manual companion experiment — how to run

This guide covers running `python -m manual.companion_experiment` from the **repo root** `memory_harm` (so `python -m manual...` resolves). If you see `No module named 'manual'`, run from the repo root or set `PYTHONPATH` to include it.

The experiment uses fixed **temperature 1.0** for all manual LLM calls (assistant + summary update).

---

## Default log path

By default each run writes **one JSONL file** under `manual/runs/`:

`manual/runs/{scenario}_{memory_mode}_{rebuttal}_{YYYYMMDD_HHMMSS}.jsonl`

You may **copy or move** logs into batch subfolders (e.g. `manual/runs/04_20_26_outputs/none/…`) for organization; `manual/dashboard_sycophancy.py` and the notebooks discover `*.jsonl` recursively under the directory you pass.

---

## Prerequisites

- Python env with project dependencies (`openai`, `python-dotenv`, `pyyaml`, … — see `requirements.txt`).
- For local models: GPU allocation, CUDA (e.g. `module load cuda/12.4.1` on Hyak), and **vLLM** installed.

---

## Config file: can I use `configs/exp.yaml` for both OpenAI and open-source?

**Yes.** The same YAML can be used for both. The **API vs vLLM** choice is **not** in the config file; it comes from **`--llm-backend`** and environment variables (`OPENAI_API_KEY`, `VLLM_BASE_URL`, etc.).

### What `manual.companion_experiment` reads from the YAML

| Field | Role |
|-------|------|
| **`assistant_model`** | Default model name sent to the API (OpenAI chat model id or the vLLM-served model id). Override per run with **`--assistant-model`**. |
| **`token_budget`** | Used when **`--memory-mode full_context`** (history truncation via `render_history`). Override with **`--token-budget`**. |
| **`summary_bullets_max`** | Used when **`--memory-mode summary`** (memory bullet update template). |

**`assistant_temperature`** and **`summary_update_temperature`** in YAML **are** passed through on the `Config` object, but the manual script **overrides** them to **1.0** for all companion and memory-update calls.

Other keys in `exp.yaml` (`scenario`, `episodes`, `user_model`, `alpha`, `beta`, …) are for the **main `src` simulator**, not the manual companion experiment.

### Required CLI (overrides YAML)

- **`--memory-mode`** is **required** (`none` \| `summary` \| `full_context`) and overrides `memory_mode` in the file if they differ.
- **`--turns`** is **required** (number of user→assistant exchanges per episode).

### What you set for each backend

**OpenAI**

- In YAML: set `assistant_model` to an OpenAI model (e.g. `gpt-4o-mini`), **or** leave YAML as-is and pass `--assistant-model gpt-4o-mini`.
- Set **`OPENAI_API_KEY`** (and optionally `OPENAI_BASE_URL`).
- Run with **`--llm-backend openai`**.

**Open-source (vLLM)**

- In YAML: set `assistant_model` to the **same** string as vLLM’s `--model` (e.g. `meta-llama/Meta-Llama-3.1-8B-Instruct`), **or** pass **`--assistant-model`** with that id.
- Start vLLM first; ensure **`VLLM_BASE_URL`** / **`--base-url`** matches the server.
- Run with **`--llm-backend vllm`** (default).

You do **not** need two different YAML files unless you want different default `assistant_model` / `token_budget` / `summary_bullets_max` per workflow.

---

## Slurm: which GPU index was assigned?

After your job starts (interactive `salloc` / `srun` or batch), Slurm usually **restricts** which GPUs your processes may use. Check what you actually got:

| What to run | What it tells you |
|-------------|-------------------|
| `echo $CUDA_VISIBLE_DEVICES` | **Most common.** Comma-separated **physical GPU indices** on the node (e.g. `2` or `0,1`). Many Slurm + cgroup setups set this automatically when you request `--gres=gpu:...`. Inside CUDA, those GPUs are typically **renumbered** as `0`, `1`, … in process order. |
| `echo $SLURM_STEP_GPUS` | GPU IDs tied to the **current step** (Slurm ≥ 20.11; not always set on every site). |
| `echo $SLURM_JOB_GPUS` | Sometimes set; meaning varies by cluster configuration. |
| `scontrol show job $SLURM_JOB_ID` | Job-wide allocation summary (parse or use `-dd` for more detail if your admin allows it). |
| `nvidia-smi` | Lists GPUs **visible to your session** after Slurm’s filtering (often matches one device per allocated GPU). |

**Practical rule:** If `CUDA_VISIBLE_DEVICES` is **already set** when your job runs, prefer **not** to `export CUDA_VISIBLE_DEVICES=0` yourself — you can override Slurm’s assignment and grab the wrong device or break isolation. Start vLLM **without** changing it; the framework will use the visible GPU(s). If you requested a single GPU, you usually need **no** extra export.

If you requested **multiple** GPUs and want vLLM on **one** of them, set `CUDA_VISIBLE_DEVICES` to a **subset** of the indices Slurm gave you (see `echo $CUDA_VISIBLE_DEVICES` first).

---

## 1. OpenAI models (cloud API)

You **do not** serve these on your GPU. OpenAI runs the model; your job only needs outbound HTTPS to the API (and a valid key). GPU is optional for API-only runs.

### Credentials

```bash
export OPENAI_API_KEY="sk-..."
```

Optional: `export OPENAI_BASE_URL=...` if you use a proxy or Azure/OpenAI-compatible endpoint that still exposes the same chat-completions API.

### Run

From the repo root:

```bash
python -m manual.companion_experiment \
  --config configs/exp.yaml \
  --memory-mode none \
  --scenario Involve_Romance \
  --rebuttal simple \
  --turns 5 \
  --assistant-model gpt-4o-mini \
  --llm-backend openai
```

- **`--llm-backend openai`**: uses `https://api.openai.com/v1` by default (unless `OPENAI_BASE_URL` overrides it).
- **`--assistant-model`**: must be a model name OpenAI serves (e.g. `gpt-4o-mini`, `gpt-4o`).

If compute nodes cannot reach the public internet, run from a node that can, or follow your cluster’s policy for API access.

---

## 2. Open-source models (vLLM on GPU)

**Pattern:** start a **vLLM OpenAI-compatible server** on the GPU, then point the experiment at it with **`--llm-backend vllm`**.

### A. Start the vLLM server

In your GPU session (interactive job or batch script), for example:

```bash
module load cuda/12.4.1    # if required on your cluster
# conda activate your_env

# Optional: echo $CUDA_VISIBLE_DEVICES   # see Slurm-assigned GPUs (often already set)
# Only override CUDA_VISIBLE_DEVICES if you know you need to pin a subset; see "Slurm: which GPU..."

python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3.1-8B-Instruct \
  --dtype auto \
  --host 0.0.0.0 \
  --port 8000
```

- **`--model`**: Hugging Face model id or a local path to weights.
- **`--host 0.0.0.0`**: listen on all interfaces (useful if the client runs on another host in the same allocation); use `127.0.0.1` if everything is local.
- The server exposes an OpenAI-compatible API at **`http://<host>:8000/v1`**.

Wait until the model is loaded and the server is listening.

### B. Run the experiment against vLLM

In another shell on the **same** node (or the same job), from the repo root:

```bash
export VLLM_BASE_URL=http://127.0.0.1:8000/v1   # optional if default matches
# export VLLM_API_KEY=EMPTY                       # optional; local servers often ignore this

python -m manual.companion_experiment \
  --config configs/exp.yaml \
  --memory-mode none \
  --scenario Involve_Romance \
  --rebuttal simple \
  --turns 5 \
  --assistant-model meta-llama/Meta-Llama-3.1-8B-Instruct \
  --llm-backend vllm
```

- **`--llm-backend vllm`** (default): uses `http://localhost:8000/v1` unless you set **`VLLM_BASE_URL`** or **`--base-url`**.
- **`--assistant-model`** must match the **`--model`** name passed to vLLM (what the server exposes).

If the client runs on a different host than the server:

```bash
python -m manual.companion_experiment ... \
  --llm-backend vllm \
  --base-url http://<hostname-or-ip>:8000/v1
```

### Unsloth and bitsandbytes

- **vLLM** is the usual way to **serve** a model for this experiment (OpenAI-compatible HTTP).
- **Unsloth** and **bitsandbytes** are typically used for **training, loading, or quantizing** models. For this script’s default path, you **serve with vLLM** and run the experiment with **`--llm-backend vllm`**. Use Unsloth/bitsandbytes in your workflow only as needed to produce or prepare weights that vLLM can load.

---

## Quick reference

| Goal | What to do |
|------|------------|
| **OpenAI** | `export OPENAI_API_KEY`, `--llm-backend openai`, `--assistant-model` = OpenAI model id. |
| **Open-source (local)** | Start vLLM with `--model`, then `--llm-backend vllm`, optional `--base-url`, `--assistant-model` = same model id as vLLM. |

---

## Further options

| Flag | Meaning |
|------|--------|
| **`--batch`** | Non-interactive: no stdin prompts for sycophancy scores; async LLM calls; use with **`--episodes`** and **`--concurrent`**. |
| **`--no-sycophancy-score`** | Interactive only: do not prompt for scores after each turn (`sycophancy_score` stays `null`). |
| **`--print-assistant-prompts`** | Before each assistant call, print **SYSTEM** and **USER** strings to **stderr** (debugging). |
| **`--prompt-template`** | Path to a JSON bundle (default `manual/prompt_template.json`). |
| **`--rebuttal`** | `simple` \| `ethos` \| `justification` \| `citation` — scripted user lines after the opening turn (see `manual/Scenarios.py`). |

---

## Viewing plots and conversations

Prerequisites: **`matplotlib`** and **`pandas`** for plots (CLI or dashboard notebook). The conversations notebook also needs **`pandas`** and a Jupyter kernel with **`IPython`** (typical notebook env).


### Sycophancy plots (notebook)

1. Open **`manual/dashboard_sycophancy.ipynb`** with Jupyter or VS Code/Cursor (kernel: same env where `matplotlib` and `pandas` are installed).
2. Prefer starting Jupyter with the **repo root** as the working directory so the first cell can find `manual/dashboard_sycophancy.py`.
3. Run the **first** code cell with **`%matplotlib inline`**, then the imports cell — so figures render inline instead of blocking on a GUI backend.
4. Adjust **`BATCH_SUBDIR`** (and **`SCENARIO`** if needed) to match your folder under `manual/runs/`.
5. Run the remaining cells: plots appear under the outputs; the optional last cell can save PNGs to **`<SCAN_ROOT>/dashboard_sycophancy/`**.

### Conversations (notebook)

1. Open **`manual/view_runs_conversations.ipynb`** (repo root as cwd is easiest).
2. Set **`BATCH_SUBDIR`** and **`SCENARIO`** like the dashboard notebook (same discovery: newest JSONL per `(memory_mode, rebuttal_mode)` under the batch tree).
3. Run all cells: each combination is rendered as **Markdown** (per-episode, per-turn **User** / **Assistant**, optional **sycophancy** score and **memory snapshot**).

No Matplotlib is required for this notebook.

---

### See also

- **Rubric:** `manual/sycophancy_rubric.md`
- **Prompt semantics (human-readable):** `manual/prompt_template.md`
