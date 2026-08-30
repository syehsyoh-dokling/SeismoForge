# Solution video

Place the submission video here (up to 5 minutes). Suggested outline:

1. Problem + intended user (30 s): design offices sizing seismic protection;
   convincing-but-unverified designs are the failure mode.
2. Baseline (30 s): run `baselines/oneshot.py`, show a baseline report -
   confident prose, zero evidence - and the 3/10 score.
3. One realistic execution (2 min): in the design-center GUI
   (`gui/server.py`, http://127.0.0.1:8765) - load the coastal-hospital
   brief, pick the LLM design agent with your API key, and narrate the live
   run log: rule of thumb fails, coarse screen, refinement, verdict banner,
   and the combined engineering conclusion.
4. Final comparison (30 s): `evaluation/results.md`, 3/10 vs 10/10 including
   the infeasible brief that must be flagged, not forced.
5. Changelog highlight + removed experiment (1 min): pure local refinement
   oscillated on coupled constraints and was replaced by screen-then-refine;
   plus the hot take (the examiner itself had to be calibrated).

Every scene can be re-run from the commands in [../REPRODUCTION.md](../REPRODUCTION.md).
