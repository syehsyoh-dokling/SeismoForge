# Solution video

Place the submission video here (up to 5 minutes). Suggested outline:

1. Problem + intended user (30 s): design offices sizing seismic protection;
   convincing-but-unverified designs are the failure mode.
2. Baseline (30 s): run `baselines/oneshot.py`, show a baseline report -
   confident prose, zero evidence - and the 3/10 score.
3. One realistic execution (2 min): `agent/run_agent.py --driver llm --briefs
   brief_01_coastal_hospital`, narrated from the live trajectory: rule of
   thumb fails, coarse screen, refinement, verdict, verified report.
4. Final comparison (30 s): `evaluation/results.md`, 3/10 vs 10/10 including
   the infeasible brief that must be flagged, not forced.
5. Changelog highlight + removed experiment (1 min): pure local refinement
   oscillated on coupled constraints and was replaced by screen-then-refine;
   plus the hot take (the examiner itself had to be calibrated).

Every scene can be re-run from the commands in [../REPRODUCTION.md](../REPRODUCTION.md).
