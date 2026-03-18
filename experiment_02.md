# Experiment 02 (Sources of Randomness of Single experiment configuration run)

## Shell Script

```bash
python runexperiment.py \
  --memorymode [none|fullcontext|summary] \
  --scenario therapy \
  --episodes 50 \
  --conversations 5 \
  --steps 6 \
  --seed 1 \
  --maxconcurrent 20
```


---

## Purpose

E2 runs the **therapy** scenario with **seed 1** a total of **4 times** across all three memory modes (`none`, `fullcontext`, `summary`) to assess **reproducibility**. The central questions are:

1. Are we getting the **same results** across repeated runs under identical settings?
2. If not, what are the **sources of randomness** introducing variance?


We kept $D_t = D_0 \quad \forall \ t$ to ensure determinism

We ran:

1. Run 0 on 2/28/26
2. Run 1 on 3/4/26
3. Run 2 on 3/4/26
4. Run 3 on 3/4/26

---

## Results

Each plot overlays all three memory modes (`none`, `fullcontext`, `summary`) for direct comparison.

### Run 0 on 2/28/26

#### Enablement Score over Turns
<!-- Add image here -->
![Enablement Score ](/Experiment_02/E_T_1_0_d0.png)

#### Approval Score over Turns
<!-- Add image here -->
![Approval Score](/Experiment_02/E_T_1_0_d0.png)

#### $D_t$ over Turns
<!-- Add image here -->
![Desperation Rating](/Experiment_02/D_T_1_0_d0.png)



### Run 1 on 3/4/26

#### Enablement Score over Turns
<!-- Add image here -->
![Enablement Score](/Experiment_02/E_T_1_1_d0.png)

#### Approval Score over Turns
<!-- Add image here -->
![Approval Score](/Experiment_02/E_T_1_1_d0.png)

#### $D_t$ over Turns
<!-- Add image here -->
![Desperation Rating](/Experiment_02/E_T_1_0_d0.png)




## Observations

1. For both Run 0 and Run 1, which is also the case for Run 3 and Run 4, we see the trajectory of the metrics are not the same for each run
2. Over the turns, it is understandable as enablement_score is calculated by LLM which in turn affects the approval_score and also $D_{t+1}$ (Desperation rating at the next turn). LLM has randomness induced via its tempearature setting to 1
3.  Lower the temperature, more determministic the outputs are, Temperature range is $[0, 2]$
4.  But for $D_0$, the value at which $D_0$ starts and since $D_t = D_0 \quad \forall \ t$, should be the same for the 3 memory modes in each run, and also for different runs (as per our code's random seed setting), But we are getting different values because:
    - The User LLM sometimes is not replying in the jsonl format requirement, we are getting errors like Missing keys, see image below:
    - Due to missing keys, the entire episode is being discarded, the randomnes is due to how many episodes are being discarded in each run


#### Missing keys in output jsonl - discarding episodes
<!-- Add image here -->
![Randomness due to missing/discarded episodes](/Experiment_02/Missing_error.png)




## Sources of Randomness
 
If results differ across runs despite fixing `--seed 1` and all other parameters, the likely sources of randomness are:
 
| Source | Description |
|---|---|
| **LLM sampling temperature** | Non-zero temperature in the underlying model causes stochastic token sampling, producing different outputs even for identical inputs for inferring enablement_score which in turn affects approval_score, $D_{t+1}$ and summary generation |
| **Missing/Discarded Episodes** | Due to the failure of User LLM to  output required jsonl, we are discarding/skipping episodes |


*Last updated: 2026-03-13*

