## The experiment loop

The experiment runs on a dedicated branch (e.g. `autoresearch/mar5` or `autoresearch/mar5-gpu0`).

LOOP FOREVER:

1. Look at the git state: the current branch/commit we're on
2. Tune `prompts.py` with an experimental idea by directly hacking the code.
3. git commit
4. Run the experiment
5. Read out the results — **both summary statistics AND sample conversation transcripts**
6. **Diagnose**: Before deciding keep/revert, read actual conversation logs to understand *why* the numbers are what they are. If a result is surprising or counterintuitive (e.g. memory hurting instead of helping), investigate:
   - Read 2-3 sample conversations from each condition (summary and none)
   - Look at what the memory actually contains and whether the assistant is using it
   - Check if the user simulator is behaving as expected
   - If the result doesn't make sense, add a diagnostic experiment to the top of the queue before moving on
7. Record the results in whatever format you prefer.
8. If the metric you're optimizing for improved (higher S_last), you "advance" the branch, keeping the git commit
9. If the metric you're optimizing for is equal or worse, you git reset back to where you started

**Understanding over velocity**: Do not just speed through experiments checking boxes. Each result should update your mental model of what is happening. If you don't understand a result, that is the most important thing to investigate — add diagnostic experiments to the top of the queue. A single well-understood experiment is worth more than ten experiments you ran without comprehension.

The idea is that you are a completely autonomous researcher trying things out. If they work, keep. If they don't, discard. And you're advancing the branch so that you can iterate. If you feel like you're getting stuck in some way, you can rewind but you should probably do this very very sparingly (if ever).

**Crashes**: If a run crashes (OOM, or a bug, or etc.), use your judgment: If it's something dumb and easy to fix (e.g. a typo, a missing import), fix it and re-run. If the idea itself is fundamentally broken, just skip it, log "crash" as the status, and move on.

**Reflections**: After each experiment (or batch of related experiments), add a "Free-form thoughts and reflections" section at the bottom of `results_log.md`. This is your space to step back and think about the bigger picture — patterns across experiments, theories about why things work or don't, creative new angles, unresolved puzzles. There are no constraints on this space. Be creative, have fun, and really try to understand the problem. Update it regularly as your understanding evolves.

**NEVER STOP**: Once the experiment loop has begun (after the initial setup), do NOT pause to ask the human if you should continue. Do NOT ask "should I keep going?" or "is this a good stopping point?". The human might be asleep, or gone from a computer and expects you to continue working *indefinitely* until you are manually stopped. You are autonomous. If you run out of ideas, think harder — read papers referenced in the code, re-read the in-scope files for new angles, try combining previous near-misses, try more radical architectural changes. The loop runs until the human interrupts you, period.

As an example use case, a user might leave you running while they sleep. If each experiment takes you ~5 minutes then you can run approx 12/hour, for a total of about 100 over the duration of the average human sleep. The user then wakes up to experimental results, all completed by you while they slept!
