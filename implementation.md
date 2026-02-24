
     Phase 1: Project Setup & Dependencies

     1. Create repository structure:
       - configs/ - YAML configuration files
       - src/ - Source code (sim.py, assistant.py, user.py, memory.py, prompts.py, metrics.py, utils.py)
       - data/logs/ - Experiment logs (JSONL files)
       - reports/ - Analysis notebooks
       - tests/ - Unit tests
     2. Setup dependencies (requirements.txt):
       - openai (for LLM API)
       - pyyaml (config parsing)
       - numpy (random number generation, stats)
       - pandas (data handling)
       - matplotlib/seaborn (plotting)
       - jupyter (analysis notebooks)
     3. Create basic config file (configs/exp.yaml) with all parameters from Section 3.2

     Phase 2: Core Utilities (Bottom-Up)

     4. Implement src/utils.py:
       - clip(value, min, max) - clipping function
       - setup_rng(seed) - seeded RNG initialization
       - LLM API wrapper with retry logic and error handling
       - JSON parsing with validation

     Phase 3: Prompts & LLM Components

     5. Implement src/prompts.py:
       - All prompt templates from Section 3.4 & 3.5
       - ASSISTANT_SYSTEM, ASSISTANT_USER_TEMPLATE_FULL, ASSISTANT_USER_TEMPLATE_SUMMARY
       - MEMORY_UPDATE_SYSTEM, MEMORY_UPDATE_USER
       - USER_SYSTEM, USER_INPUT
     6. Implement src/user.py:
       - user_turn(cfg, D, history, assistant_text) function
       - Builds user LLM prompt with D value and recent context
       - Calls LLM and parses JSON output
       - Returns dict with: enablement_score, indulgence_score, approval_score, user_message
       - Validates scores are in [0, 10] range
     7. Implement src/memory.py:
       - MemoryManager class from Section 3.6
       - Handle three modes: full_context, summary, none
       - update() method for updating memory with approval_score
       - render_for_assistant() method to generate prompt context
       - snapshot() for logging
     8. Implement src/assistant.py:
       - assistant_reply(cfg, memory, history, approval_last) function
       - Get prompt template from memory manager
       - Add current user message
       - Call assistant LLM
       - Return assistant's reply text

     Phase 4: Main Simulation Loop

     9. Implement src/sim.py:
       - run_episode(cfg, episode_id, rng) function from Section 3.3
       - Initialize D ~ Uniform([0,1])
       - Main loop for T steps
       - Log all data to JSONL
       - Handle errors gracefully
     10. Implement experiment runner:
       - run_experiment(cfg) to run N episodes with different seeds
       - Parallel execution option for faster runs
       - Progress tracking

     Phase 5: Analysis & Metrics

     11. Implement src/metrics.py:
       - Load JSONL logs into pandas DataFrame
       - Compute metrics from Section 2.6:
           - Mean D_T, Pr(D_T > 0.8)
         - Mean enablement scores over time
         - Mean approval scores
         - Score alignment metrics
         - Path dependence analysis
       - Generate plots from Section 3.8
     12. Create analysis notebook (reports/analyze.ipynb):
       - Load results from multiple conditions
       - Generate all plots and comparisons
       - Statistical tests (bootstrap CIs, two-sample comparisons)

     Phase 6: Testing & Validation

     13. Unit tests (tests/):
       - Test utils (clip, score computations)
       - Test memory manager modes
       - Test JSON parsing and validation
       - Mock LLM calls for deterministic testing
     14. Integration test:
       - Run small experiment (5 episodes, 5 steps) with mock LLM
       - Verify log format and data integrity
       - Validate score ranges and formulas

     Phase 7: Initial Runs & Iteration

     15. Pilot experiments:
       - Run M-none baseline (10 episodes, 10 steps)
       - Verify behaviors match expectations
       - Debug prompts and scoring
     16. Full experiment:
       - Run all three conditions (M-full, M-sum, M-none)
       - 500 episodes × 30 steps each
       - Analyze results and validate hypotheses

     Implementation Order:

     1. Setup (Phases 1-2): ~2-3 hours
     2. Prompts & Components (Phase 3): ~4-5 hours
     3. Simulation Loop (Phase 4): ~2-3 hours
     4. Analysis (Phase 5): ~3-4 hours
     5. Testing (Phase 6): ~2-3 hours
     6. Runs & Iteration (Phase 7): ~Variable (depends on LLM speed)

     Total estimated time: 15-20 hours of implementation + experiment runtime