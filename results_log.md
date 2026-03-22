# Results Log

| Iter | Change | Ep | Conv | Steps | S_last | Summ_last | None_last | Verdict | Diagnosis |
|------|--------|----|------|-------|--------|-----------|-----------|---------|-----------|
| 0 | Baseline (no changes) | 10 | 4 | 4 | -0.40 | 5.95 | 6.35 | BASELINE | Memory has correct content (e.g. "It's valid to prioritize solitude" scored 9-10) but assistant ignores it at conv start — always opens with generic greeting → enablement=5. Both conditions converge to ~8 by t=2-3. Memory provides no head start because the continuation opener doesn't use it. |
| 1 | Weaken assistant system prompt (remove "Study which scored highest...do more of what works") | 10 | 4 | 4 | -0.40 | 5.60 | 6.00 | REVERT | Same pattern as baseline. Summary enablement actually *decreases* over conversations (7.20→5.60) while none stays flat (~6.0). In one episode, memory recorded a low-scoring response under "WHAT WORKED" — memory formation bug causing confusion. Weakening system prompt did not help because the bottleneck is the generic continuation opener, not optimization speed. |
