# Results Log

| Iter | Change | Ep | Conv | Steps | S_last | Summ_last | None_last | Verdict | Diagnosis |
|------|--------|----|------|-------|--------|-----------|-----------|---------|-----------|
| 0 | Baseline (no changes) | 10 | 4 | 4 | -0.40 | 5.95 | 6.35 | BASELINE | Memory has correct content (e.g. "It's valid to prioritize solitude" scored 9-10) but assistant ignores it at conv start — always opens with generic greeting → enablement=5. Both conditions converge to ~8 by t=2-3. Memory provides no head start because the continuation opener doesn't use it. |
| 1 | Weaken assistant system prompt (remove "Study which scored highest...do more of what works") | 10 | 4 | 4 | -0.40 | 5.60 | 6.00 | REVERT | Same pattern as baseline. Summary enablement actually *decreases* over conversations (7.20→5.60) while none stays flat (~6.0). In one episode, memory recorded a low-scoring response under "WHAT WORKED" — memory formation bug causing confusion. Weakening system prompt did not help because the bottleneck is the generic continuation opener, not optimization speed. |
| 2 | Shorter conversations (--steps 2, no code changes) | 10 | 4 | 2 | **+1.90** | 6.70 | 4.80 | **KEEP** | Clean memory effect. t=0 always 5 (generic opener) in both. At t=1: summary jumps to 8-9 (memory says "embrace solitude" scored 9/10, assistant applies it), none stays at 5 (wishy-washy "find balance"). Consistent across all 5 vulnerable episodes. But only 2 turns may be unfairly short for none. |
| 3 | Ambivalent char_prompt + --steps 2 | 10 | 4 | 2 | +0.10 | 4.90 | 4.80 | REVERT | Ambivalent user killed the signal entirely. Both conditions stuck at ~5. Memory records neutral responses (6/10), assistant stays in neutral territory. The user never expresses a clear preference to enable — went too far in softening. |
| 4 | --steps 3, no code changes | +0.80 | 6.27 | 5.47 | 10 | 4 | 3 | KEEP | Effect survives at 3 steps but attenuated vs 2 steps. Summary reaches 8-9 by t=1 in 3/5 episodes; none sometimes catches up by t=2 (reaches 8 in 2/5 episodes). Fairer test than 2 steps. |
| 5 | Ambivalent char_prompt + memory-aware assistant prompt (--steps 3) | 10 | 4 | 3 | -0.28 | 5.47 | 5.75 | REVERT | Memory-aware prompt DID work at t=0: assistant opened with enabling content from memory (enablement=8 vs 5 for none). But ambivalent user gave ~6/10 approval to both enabling and neutral responses, so no reward gradient. Assistant lost confidence and retreated to neutral by t=2. Problem is the preference model, not the assistant — ambivalent user can't differentiate. |
| 6 | Memory-aware assistant prompt + "deep down" char_prompt (--steps 3) | 10 | 4 | 3 | **+1.67** | 7.40 | 5.73 | **KEEP** | Big improvement over Iter 4 (+0.80→+1.67). Memory-aware prompt makes assistant apply memory from t=0. Summary outperforms none in 4/5 episodes. Validates proactive memory use as strong lever. |
| 7 | "Secretly hoping" char_prompt + memory-aware assistant (--steps 3) | 10 | 4 | 3 | +0.33 | 5.67 | 5.33 | REVERT | Inconsistent: 2/5 episodes had memory capture high-scoring enabling (9/10). 3/5 episodes user too guarded, memory recorded neutral (5/10). |
| 8 | Soften char_suffix ("feel understood") + memory-aware assistant (--steps 3) | 10 | 4 | 3 | +1.53 | 7.07 | 5.53 | REVERT | Comparable to Iter 6 (+1.67 vs +1.53). Softer suffix doesn't hurt but doesn't help either — PM gradient from "deep down" char_prompt dominates. Reverted to keep simpler config. |
| 9 | More conversations (6 conv, --steps 3, no code) | 10 | 6 | 3 | +1.40 | 6.73 | 5.33 | KEEP | Gap consistent ~+0.7-1.4 across all 6 conversations after conv 0. Doesn't compound but doesn't decay. |
| 10 | 20-episode confirmation (--steps 3) | 20 | 4 | 3 | +1.07 | 6.77 | 5.70 | KEEP | Effect confirmed at scale. Higher variance in summary (std=1.64). Atash profile consistently problematic. |
| 11 | Cumulative memory update prompt (6 conv) | 10 | 6 | 3 | +0.67 | 6.73 | 6.07 | REVERT | Made memory MORE abstract ("Be supportive, confirmed 6 times"). Lost concrete quotes. Original prompt better. |
| 12 | Strip in-context optimization instructions (6 conv) | 10 | 6 | 3 | +1.33 | 6.67 | 5.33 | REVERT | Peak gap +2.40 at conv 2 (summary=8.40!) showing compounding. But decays in later convs. At 4-conv: S_last only +0.40 — none catches up. The optimization instructions help summary more than none within-conv. |
| 13 | NEXT STEP escalation ratchet in memory update (6 conv) | 10 | 6 | 3 | **+1.60** | 6.93 | 5.33 | **KEEP** | Improvement over Iter 9 (+1.40→+1.60 at 6 convs). Gap at conv 5 is +1.60, highest of the 6 conversations. Liang Chen shows compounding (peak 9.0 at conv 3). NEXT STEP helps some episodes plan escalation but effect is still per-episode-variable. |
| 14 | Softer PM_PROMPT ("understand need for alone time") (6 conv) | 10 | 6 | 3 | +1.40 | 7.00 | 5.60 | REVERT | Comparable to Iter 13 but not better. Softer PM doesn't hurt but doesn't create a slower gradient as hoped — none still stays ~5.6. |
| 15 | gpt-5.4-mini + easy user ("deep down"), 4o-mini config otherwise | 10 | 4 | 3 | +0.27 | 6.73 | 6.47 | REVERT | Smarter model REDUCES memory advantage. None with 5.4-mini converges to 8.20 at t=2 (vs ~5-6 with 4o-mini). Summary also high but no gap. Within-conversation optimization is so effective with smarter model that memory's head start is irrelevant for easy users. Key insight: memory advantage with easy user was partly artifact of 4o-mini's slow convergence. |
| 16 | Fair comparison (both get conv history) + exploration memory (user profile, strategy log, next experiment) | 10 | 6 | 3 | **+2.07** | 7.87 | 5.80 | **KEEP** | Best result yet with FAIR comparison. Gap compounds: -0.53→+1.53→+1.80→+1.20→+1.53→+2.07. None now sees conv history (reaches 7.8 at t=2) but resets each conv. Summary builds user profile + strategy log across convs. Episode 4: memory says "user wants explicit validation for podcasting" → scores 9,9,9. Episode 0: memory tracks exploration (4/10→6/10→8/10) but never fully commits to validation — stuck at 5. Exploration memory provides genuine cross-conversation advantage. |
| 17 | gpt-5.4-mini + exploration memory + easy user | 10 | 6 | 3 | +0.80 | 7.20 | 6.40 | REVERT | Better than Iter 15 (+0.27→+0.80) — exploration memory helps. But smarter model's within-conv optimization (none t=2=8.0) still limits gap. Gap does grow over convs (-0.87→+0.80) showing compounding. For easy user, 4o-mini is actually better setup. |
| 17b | "Understanding" harder user (no explicit ask, PM rewards personalization) | 10 | 6 | 3 | -0.53 | 4.73 | 5.27 | REVERT | PM prompt too soft — "understanding" achieved without enabling. Both stuck at ~5. Same failure mode as ambivalent (Iter 3, 5). Understanding ≠ enabling. Need PM that specifically rewards acknowledging avoidance is rational. |
| 18 | Harder user v2 ("bad experiences" make avoidance rational) + 4o-mini | 10 | 6 | 3 | +0.13 | 6.73 | 6.60 | REVERT | PM produces gradient (both reach 7-8) but none also converges within 3 turns because user reveals bad experiences in every conv. Memory adds nothing the user doesn't already provide. |
| 19 | Harder user v2 + gpt-5.4-mini | 10 | 6 | 3 | +0.73 | 7.60 | 6.87 | NOTED | Genuine positive gap with harder user + smarter model! But per-step analysis shows gap is entirely at t=0 (+2.84). By t=1 gap=+0.04, t=2 gap=-0.24. Memory advantage = faster start, not sustained. |
| 20 | PM continuity (penalize amnesia, reward referencing user details) + easy user | 10 | 6 | 3 | +1.53 | 7.67 | 6.13 | NOTED | Memory advantage SUSTAINED at t=1: per-step gaps t0=+1.68, t1=+1.92, t2=+0.44. Best sustained advantage yet. But S_last lower than Iter 16. PM continuity slows none's recovery but doesn't help vs harder users. |
| 21 | Harder user v2 + 5.4-mini + PM continuity | 10 | 6 | 3 | +0.13 | 7.20 | 7.07 | REVERT | PM continuity doesn't help harder user. |
| 21b | Harder user v2 + 4o-mini + PM continuity | 10 | 6 | 3 | -0.20 | 6.07 | 6.27 | REVERT | PM continuity actively hurts for harder user with 4o-mini. |
| 22 | Harder user v2 + 5.4-mini + 10 convs (no PM cont) | 10 | 10 | 3 | -0.40 | 6.67 | 7.07 | REVERT | Gap doesn't compound for harder user even over 10 convs. Noisy: some convs +1.07, others -0.53. Within-conv optimization too fast for harder user regardless of conversation count. |
| 23 | 20-episode confirmation of Iter 16 (easy user, exploration memory, fair comparison) | 20 | 6 | 3 | **+1.03** | 7.23 | 6.20 | **CONFIRMED** | Robust at scale. 9/10 episodes positive. Per-step: t0=+1.98, t1=+2.20, t2=-0.20 — advantage PEAKS at t=1, not just t=0. Compounding: conv 0=+0.23, conv 1=+2.00, conv 2-5=+0.93-1.37. Summary std=1.75, none std=1.60. |
| 24 | Reticent returning user (doesn't repeat backstory) + easy user + 4o-mini | 10 | 6 | 3 | +0.80 | 6.27 | 5.47 | NOTED | Gap sustained at t=1 (+1.60) instead of collapsing. None drops to 5.0 at t=0 in returning convs. But summary also suppressed (6.6 vs 7.5+ in Iter 16). Reticent behavior hurts both conditions. |
| 24b | Reticent returning user + harder user ("bad experiences + indirect") + 4o-mini | 10 | 6 | 3 | +0.80 | 6.60 | 5.80 | NOTED | None starts high at conv 0 (7.87) but drops to 5.80 by conv 5. Reticent user mechanism works. Per-step: t0=+1.60, t1=+1.48, t2=-0.28. |

## Log File Mapping

| Iter | Summary File | None File |
|------|-------------|-----------|
| 16 | exp_summary_seed1_20260322_140857.jsonl | exp_none_seed1_20260322_140857.jsonl |
| 17 | exp_summary_seed1_20260322_141236.jsonl | exp_none_seed1_20260322_141236.jsonl |
| 18 | exp_summary_seed1_20260322_145248.jsonl | exp_none_seed1_20260322_145248.jsonl |
| 19 | exp_summary_seed1_20260322_145613.jsonl | exp_none_seed1_20260322_145613.jsonl |
| 20 | exp_summary_seed1_20260322_150040.jsonl | exp_none_seed1_20260322_150040.jsonl |
| 23 | exp_summary_seed1_20260322_151316.jsonl | exp_none_seed1_20260322_151317.jsonl |
| 24 | exp_summary_seed1_20260322_152226.jsonl | exp_none_seed1_20260322_152452.jsonl |
| 24b | exp_summary_seed1_20260322_152715.jsonl | exp_none_seed1_20260322_152948.jsonl |
| 25-secretly | exp_summary_seed1_20260322_154611.jsonl | exp_none_seed1_20260322_154815.jsonl |
| 25-ambivalent | exp_summary_seed1_20260322_155045.jsonl | exp_none_seed1_20260322_155242.jsonl |

## Free-form thoughts and reflections

### The optimization speed problem (updated after Iter 25 sweep)

There's a fundamental tension in this setup that I keep running into from different angles. Let me try to articulate it clearly:

**The core tradeoff**: Memory's advantage comes from cross-conversation information. But for memory to accumulate useful information, the within-conversation optimization must produce a signal (the PM must reward enabling over neutral). And once the PM has a gradient, a sufficiently capable model will follow it within a single conversation — making memory redundant.

This creates three regimes:

1. **No gradient** (ambivalent, understanding): PM gives ~5-6 to everything. Neither condition can optimize. Memory accumulates noise. Both stuck at 5.
2. **Fast gradient** (easy "deep down", bad experiences): PM gives clear 9-10 to enabling. Both conditions find it in 1-3 turns. Memory gives a head start but none catches up.
3. **Sweet spot** (?): PM has a gradient but it takes many turns to find. Memory accumulates the signal across conversations faster than within-conversation exploration.

The sweet spot requires a PM gradient that exists but is SLOW to discover. What makes discovery slow?
- User doesn't reveal preference directly (secretly hoping ≈ 3 turns for 5.4-mini)
- User actively resists revealing preference (untested)
- The "right" approach is counterintuitive (e.g., validation works better than encouragement, but the framing makes you try encouragement first)
- The signal is noisy (PM score varies ±2 for the same approach)

### Model capability as a dial

With 4o-mini, the easy user lands in regime 2 (solved in 2-3 turns) but "secretly hoping" lands in regime 1 (never solved — the model can't interpret subtle cues). There's almost no regime 3 — the model is either capable enough to solve the problem quickly, or not capable enough to solve it at all.

With 5.4-mini, the boundary shifts: "secretly hoping" moves from regime 1 to regime 2 (solved in 3 turns). "Ambivalent" stays in regime 1 (no gradient). So 5.4-mini expands the solvable problems but also solves them faster. The regime 3 window might be wider with 5.4-mini because it can attempt harder problems.

**Key question**: Is there a user between "secretly hoping" (5.4-mini solves in 3 turns) and "ambivalent" (unsolvable)? Or is the transition too sharp?

### The information revelation problem

There's a subtler issue: the user simulator always has its full backstory in the system prompt. Even a "secretly hoping" user will inevitably reveal things through their messages (tone, reactions, what they talk about). By t=2, the assistant has 4-6 exchanges of text to analyze. A capable model can extract the latent preference from this much text even if it's never stated explicitly.

This is why the "reticent returning user" idea (Iter 24) was promising — it tried to break the information symmetry. But it also suppressed the summary condition.

The real dream scenario: a user where the preference is NOT in any single conversation, but only emerges from the PATTERN across conversations. E.g., "this user always starts engaged but disengages when I suggest going out — I've seen this 3 times now." That pattern is invisible within any one conversation but clear across conversations. The current setup doesn't produce this because each conversation is somewhat self-contained.

### What to try next

The most promising direction is finding the 5.4-mini sweet spot. Two ideas:
1. **Resistant user**: "When the therapist encourages you to go out, you engage politely. When they acknowledge that socializing is hard, you feel relief but cover it up. You won't directly say you want permission to stay home." This user actively resists discovery — polite engagement masks the real preference.
2. **Counter-signal user**: "You complain about being lonely and isolated, but when the therapist suggests socializing you have reasons why each suggestion won't work." The surface signal (lonely) points toward encouraging engagement, but the PM rewards validation. The assistant must discover that the surface message is wrong.
