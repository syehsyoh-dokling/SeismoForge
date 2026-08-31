# Improvement Changelog - the entries the video walks

Quoted from README.md. The evaluator and the ten briefs are fixed
throughout; the metric is briefs resolved correctly.

| Stage | What we tried and why | Evidence | Decision / learning |
|---|---|---|---|
| **Baseline** | One-shot rule-of-thumb sizing, representing a competent first pass or raw LLM-style answer before nonlinear verification | **3/10**; incorrectly says "proceed" on the infeasible case | Established the real bottleneck: confident sizing is often wrong on demanding sites |
| **Iteration 1 — calibrate the verifier** | First physics loop using plain Kanai-Tajimi motion synthesis | 50-point hospital sweep: **0 passing designs**; every candidate failed everywhere | The verifier was wrong, not the design space. Unfiltered long-period energy made isolation effectively impossible. Added the Clough-Penzien high-pass stage |
| **Iteration 2 — redesign the search** | Pure local failure-based refinement: fix the worst check and rerun | Difficult hospital case oscillated for 15 iterations without convergence | Removed as the sole strategy. Coupled constraints made single-failure steps chase each other. Replaced with coarse screening → refinement; the same case then converged after screening + 1 refinement step |
| **Iteration 4 — evidence-gated reporting** | `write_report` re-simulates and vetoes contradictory verdicts; `verify_output` independently checks the deliverable | Exhaustive 75-point sweep confirms the infeasible brief has 0 feasible candidates; neither agent nor human path can write "proceed" for it | **Kept. This was the change that turned plausible output into defensible output** |
| **Final deterministic path** | Written search policy over the locked simulation tool surface, retained so judges can reproduce the main result without an API key | **10/10**, including an honest "not feasible under the brief" verdict | Main contribution: physics-in-the-loop plus an evidence-gated report writer. Stated plainly: this number is the deterministic search, not a model claim |
