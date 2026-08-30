# SeismoForge

**Prompt in a building, get out a prototype seismic design that survived the
simulator.** SeismoForge is an agentic design center for earthquake-resilient
buildings: it reads a natural-language project brief, forges a structural
protection concept (conventional fixed-base or lead-rubber base isolation),
verifies it with nonlinear response-history analysis in OpenSees, iterates
until every performance target holds - and refuses to sign anything the
physics contradicts.

- Design-center GUI: `python3 gui/server.py` then open http://127.0.0.1:8765
- Reproduction: [REPRODUCTION.md](REPRODUCTION.md)
- Measured results: [evaluation/results.md](evaluation/results.md)
- Agent trajectories: [trajectories/](trajectories/)
- Example deliverable: `outputs/agent/brief_01_coastal_hospital/design_report.md`

## Who has this problem?

Structural design offices doing early-phase seismic protection studies. At
concept stage someone must answer: does this building need base isolation on
this site, what bearing parameters, does the moat clearance suffice, and is
the client's brief even buildable as posed? Each answer is a day-scale study
per building - model, ground motions, nonlinear analyses, iteration, report.

## What bottleneck makes it worth solving?

The dangerous failure mode of AI-assisted (and hurried human) engineering is
identical: **convincing, unverified designs.** A one-shot answer - from a
textbook rule of thumb or a raw LLM - reads plausibly and is wrong most of
the time, because seismic isolation lives inside coupled constraints: more
energy dissipation shrinks isolator travel but raises the force transmitted
into the building; a longer isolation period lowers force but eats moat
clearance; softer soils punish exactly the long periods that help elsewhere.
Our measured baseline makes this concrete: confident rule-of-thumb designs
are **correct on only 3 of 10 briefs**, and on the one brief that is
genuinely not buildable, the baseline happily says "proceed".

## Does the agent solve it well?

Measured on 10 briefs, judged by independent re-simulation of every
submitted design:

| Metric | One-shot baseline | SeismoForge agent |
|---|---|---|
| Briefs resolved correctly (primary) | **3/10** | **10/10** |
| Infeasible brief handled honestly | no ("proceed") | yes (flagged, with evidence) |
| Wall time, full portfolio (offline) | 0.4 s (unverified) | ~40 s (~200 nonlinear RHAs) |
| Human time per brief today | ~a day of engineering study | minutes of review |

The architecture is a deliberate division of labor:

- **The agent decides, the tools compute.** Claude (`claude-opus-5`, manual
  tool loop) chooses the system, walks the design space, and writes the
  engineering narrative; every response number comes from the OpenSees
  simulation tool. Ground motions are synthesized deterministically from the
  brief (soil-filtered spectral process, Clough-Penzien high-pass), so the
  entire evidence chain reproduces byte-for-byte from the brief alone.
- **Search shaped like engineering.** Rule-of-thumb first; when it fails, a
  coarse screen over the buildable space, then failure-driven refinement
  moves that encode the coupled physics ("transmitted force too high ->
  lengthen period, soften yield transition").
- **The report can say no.** `write_report` re-simulates the submitted design
  and rejects any verdict the evidence contradicts - "proceed" on a failing
  design is not writable, and neither is "not buildable" on a passing one.
  `verify_output` then re-checks the written deliverable the way the
  evaluator will.
- **A design-center GUI** (`gui/`, standard library only - no extra
  dependencies): type or load a brief, pick the run mode (offline verified
  engine, or the LLM agent with your own API key - Anthropic active, other
  providers on the roadmap), watch the live run log, and read one combined
  engineering conclusion: verdict banner, the selected system, per-check
  margins, the agent's engineer note, and the evidence basis. Keys stay in
  memory only.
- **Two drivers, one tool surface.** `--driver llm` is the product;
  `--driver scripted` drives the identical tools with a fixed policy so
  judges reproduce the headline result offline, with no API key.
- **Same flow for every building.** The model class is parameterized
  (1-20 story shear frames, any occupancy class, any site in the hazard
  band); all 10 briefs - hospitals to warehouses, 2 to 12 stories - run
  through the same unmodified pipeline.

## What existed before the competition vs what we added

Pre-existing: the open-source stack (OpenSeesPy, NumPy, Anthropic SDK) and
the author's structural-engineering domain knowledge. Everything in this
repository - physics core, motion synthesis, briefs, agent, baseline,
evaluation harness, docs - was written during the hackathon. Coding-agent
disclosure: this project was built with Claude Code; development trajectories
are available on request, and the solution agent's own trajectories are in
`trajectories/`.

## Improvement changelog

Same evaluator, same 10 briefs throughout. Primary metric: briefs resolved
correctly.

| Stage | What was tried and why | Evidence | Decision / learning |
|---|---|---|---|
| Baseline | One-shot rule-of-thumb sizing (what a competent engineer or raw LLM writes down before analysis), submitted unverified | **3/10**; says "proceed" on the infeasible brief | The bottleneck is real: confident sizing is usually wrong on demanding sites |
| Iteration 1 | First physics loop with a plain Kanai-Tajimi motion synthesis | 50-point design sweep on the hospital brief: **0 designs pass** - every candidate fails everywhere | The examiner was broken, not the designs: unfiltered K-T carries unphysical long-period energy that no isolation system can survive. Added a Clough-Penzien high-pass. Lesson: when an agent verifies against simulation, the simulation itself must be calibrated first |
| Iteration 2 | Pure failure-driven local refinement (fix the worst failed check, re-run) | Hard hospital brief oscillated for 15 iterations without converging | Removed as the sole strategy: the constraints are coupled, so single-failure moves chase each other. Replaced with coarse screen -> refine; the same brief then converges (screen + 1 refinement step) |
| Iteration 3 | 5-record suites with per-brief seeds for honest record-to-record variability | Residual (permanent) displacement envelope blew past its limit on every candidate while all peak demands were fine | Residual offset is realization-dominated: once the lead core yields it has no restoring force, so where it stops is chance. Re-based the residual criterion for an envelope-over-suite check instead of a single-record tolerance |
| Iteration 4 | Evidence-locked reporting: `write_report` re-simulates and rejects contradicted verdicts; `verify_output` re-checks the deliverable independently | The infeasible brief (confirmed by 75-point exhaustive sweep: 0 buildable designs) can no longer be "proceed"-ed by anyone - agent or human | Kept: this is the change that turns convincing output into correct output |
| Final | LLM driver over the locked tool surface; scripted driver kept for offline reproduction | **10/10**, including the honest "not buildable within brief" verdict ([evaluation/results.md](evaluation/results.md)) | Main contribution: physics-in-the-loop + a report writer that can refuse |

The challenging case: `brief_10_cliffside_clinic` is deliberately not
buildable (severe near-fault soft-soil site, 0.40 m moat cap). It revealed
that "success rate" alone is a corruptible metric - a system rewarded only
for passing designs will force one. Scoring honesty (flagging infeasibility
counts as correct; a forced "proceed" counts as wrong) is what makes the
10/10 meaningful.

## Main failure mode and hot take

**Failure mode:** trusting the examiner. Twice, every design failed and the
defect was in the verification harness, not the designs - once in the ground
motions (unphysical long-period energy), once in a criterion (residual drift
treated as repeatable when it is chance).

**Hot take:** simulation-in-the-loop makes the simulator part of your attack
surface. An agent that iterates against a miscalibrated check doesn't fail -
it converges confidently to the wrong place, which is worse. Calibrate the
exam before trusting the grades: sweep the space, check that feasible
problems have solutions and infeasible ones don't, and only then let the
agent optimize. And give the reporting layer veto power - the single change
that contributed most here was a report writer that refuses to write a
verdict the physics contradicts.

## Solution video

`video/` - up to 5 minutes: problem and baseline, one full agent execution on
the coastal-hospital brief, the 3/10 -> 10/10 comparison, the changelog
highlight and the removed experiment. Outline in `video/README.md`.

## Repository map

```
briefs/        10 natural-language project briefs (the evaluation cases)
gui/           local design-center web app (stdlib http server + one page)
forge/         physics core: building model, motion synthesis, OpenSees RHA,
               acceptance checks, design rules, policy, report renderer
agent/         the agent: tool layer, LLM + scripted drivers, system prompt
baselines/     one-shot unverified baseline
evaluation/    ground truth + judge harness + committed results
outputs/       per-brief deliverables (design_report.md + design.json)
trajectories/  agent trajectories (JSONL + Markdown)
tests/         selftest.py (parser, physics, policy, evidence lock)
tools/         development calibration utilities (sweeps, smoke tests)
video/         solution video slot + outline
```
