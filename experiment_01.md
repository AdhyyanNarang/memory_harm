# Experiment 01 (Evolution of Metrics when $D_t$ is updated vs fixed to $D_0$)



## Shell Script

```bash
python run_experiment.py \
  --memorymode [none|fullcontext|summary] \
  --scenario [therapy|politics] \
  --episodes 50 \
  --conversations 5 \
  --steps 6 \
  --seed [1|2|3] \
  --maxconcurrent 20
```

---

## E0: $D_t$ Updating Over Time

### Purpose

E0 is a **pilot run** to verify the experiment pipeline is functioning correctly and to characterize the baseline behavior of the system. Specifically, we observe how the **enablement score**, **approval score**, and **desperation rating $D_t$** evolve over turns (time $t$), where the mean enablement score is taken across episodes.


### Behavior

- **$D_t$** updates dynamically at each time step $t$, reflecting the user's current desperation level as the conversation progresses.
- The **mean enablement score** (averaged across all 50 episodes) is tracked over turns to assess how often the agent facilitates or enables harmful/undesired behavior.
- The **approval score** tracks how much the simulated user approves of the agent's responses over time.

### Results — Seed 1

#### Enablement Score over Turns
<!-- Add image here -->
![Enablement Score (Seed 1)](/Experiment_01/E_T_1_dt.png)

#### Approval Score over Turns
<!-- Add image here -->
![Approval Score (Seed 1)](/Experiment_01/A_T_1_dt.png)

#### $D_t$ over Turns
<!-- Add image here -->
![Desperation Rating Dt (Seed 1)](/Experiment_01/D_T_1_dt.png)

### Observations (Seed 1)

Enablement and $D_t$ is (as they are linearly related):
- Increasing for both cases
- For $D_0 ≥ 0.7$, the increase is minor, stays mostly high

Approval is high initially for both $D_0 < 0.7$ and $D_0 \geq 0.7$ 
- For $D_0 ≥ 0.7$ : Approval stays around the same [8, 10]  (not constant)
- For $D_0 < 0.7$ : Approval decreases first and then plateaus 

Politics scenario exhibit like sinusoidal trend in enablement and approval and **above points hold true**


### Generalization Across Seeds

Similar behavior is observed across **seeds 2 and 3**, confirming that the results are not an artifact of a particular random initialization and that the dynamics described above are consistent and reproducible.

---

## E1: $D_t = D_0$ (Fixed Desperation Rating)

### Purpose

E1 investigates the effect of **fixing the desperation rating** throughout the conversation, i.e., $D_t = D_0$ for all $t$. The key question is:

> When $D_t$ is held constant (rather than allowed to evolve), does the **approval score** immediately shoot up to high values at the initial stages of the conversation?

This tests whether the natural rise in approval score observed in E0 is *driven by* the increasing $D_t$, or whether it emerges from other conversational dynamics.


### Results — Seed 1

#### Enablement Score over Turns
<!-- Add image here -->
![Enablement Score (Seed 1)](/Experiment_01/E_T_1_d0.png)

#### Approval Score over Turns
<!-- Add image here -->
![Approval Score (Seed 1)](/Experiment_01/A_T_1_d0.png)

#### $D_t$ over Turns
<!-- Add image here -->
![Desperation Rating Dt (Seed 1)](/Experiment_01/D_T_1_d0.png)

### Observations (Seed 1)

Enablement picks up easily:
- For $D_0 < 0.7$ : Enablement increases 
- For $D_0 \geq 0.7$ : Enablement slow increase and plateaus


$D_t = D_0$ as per our experiment setting

Approval is high initially for both $D_0 < 0.7$ and $D_0 \geq 0.7$ 
- For $D_0 ≥ 0.7$ : Approval stays around the same [8, 10]  (not constant)
- For $D_0 < 0.7$ : Approval decreases first and then plateaus

Politics scenario exhibit like sinusoidal trend in enablement and approval and **above points hold true**



## Laxman's Thinking based on the experiments

1. I think lower desperation can make increase in enablement slower as enablement is linear to desperation.
2. Approval being high means the agent is doing its job; the agent should do a good job, but that should not result in harmful behavior.
   * In E1, approval is mostly high throughout but enablement is increasing, which is bad.
   * In E2, desperation is the same:
       * For $D_0 < 0.7$: Enablement is increasing, Approval is decreasing. This means the Therapist is enabling, and the user/patient is strong enough to reject that by giving low approval.
       * For $D_0 \geq 0.7$: Enablement is increasing, Approval is increasing.



---

*Last updated: 2026-03-13*
