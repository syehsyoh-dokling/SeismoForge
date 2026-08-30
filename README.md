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
- Scope and limits: [Scope, review and safety](#scope-review-and-safety) -
  [Known modelling limitations](#known-modelling-limitations)

> **Concept-stage prototype studies, not construction documents.** Every
> report SeismoForge writes requires review and sign-off by a licensed
> structural engineer before it informs a real decision. See
> [Scope, review and safety](#scope-review-and-safety).

## One brief in, one report out

A user hands SeismoForge **one** project and gets **one** engineering
conclusion back. That is the product, and it is what `gui/server.py` does.

The ten briefs in `briefs/` are not part of a session - they are the exam.
Ten different buildings, run independently, so the claim "this works" can be
checked instead of asserted. `briefs_prose/` holds the same ten projects
written as ordinary prose, which is how the intake step is measured.

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

| Metric | One-shot baseline | `offline` | `assisted` |
|---|---|---|---|
| Brief the system can read | labelled datasheet | labelled datasheet | **free prose** |
| Briefs resolved correctly (primary) | **3/10** | **10/10** | **10/10** |
| Infeasible brief handled honestly | no ("proceed") | yes (flagged, with evidence) | yes (flagged, with evidence) |
| Wall time, full portfolio | 0.4 s (unverified) | 37.8 s | 80.5 s |
| Simulation done | none | 110 design evaluations, 550 nonlinear RHAs | same |
| Model tokens, full portfolio | none | none | 8,291 in / 2,201 out (`gpt-5.5`) |
| Human time per brief today | ~a day of engineering study | minutes of review | minutes of review |

`offline` and `assisted` reach the identical designs - the model's reading of
the prose lands on the same nine values the strict parser reads out of the
datasheet, brief for brief. What changes is what the system will accept as
input: the strict parser scores **0/10** on `briefs_prose/`, failing all nine
fields on all ten briefs. That is the axis the model earns its place on.

`agent` mode (the model also drives the search) runs end to end and reproduces
the offline design on the coastal hospital - Qd 2158 kN, Kd 6785 kN/m, Dy 45 mm,
verification clean - but has not been scored across the portfolio yet, and this
table will not carry a number until it has been.

The architecture is a deliberate division of labor:

- **The agent decides, the tools compute.** Claude (`claude-opus-5`, manual
  tool loop) chooses the system, walks the design space, and writes the
  engineering narrative; every response number comes from the OpenSees
  simulation tool. Ground motions are synthesized deterministically from the
  brief file (soil-filtered spectral process, Clough-Penzien high-pass), so
  the entire evidence chain reproduces byte-for-byte from this repository -
  no downloads, no record database, nothing to drift.
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
- **One session, three modes.** Every entry point - CLI, GUI, evaluation
  harness - runs a brief through `agent/session.py`. There is no second code
  path, so what a demo shows is what the evaluation measures, and every run
  leaves a trajectory. Two things vary, independently:

  | Mode | Who reads the brief | Who picks the next design | API key |
  |---|---|---|---|
  | `offline` | strict parser | scripted policy | no |
  | `assisted` | the model | scripted policy | yes |
  | `agent` | the model | the model | yes |

  Either provider drives them. `agent/llm.py` holds the one place the wire
  formats differ - Anthropic carries tool results as content blocks inside a
  user turn, OpenAI as separate `tool` messages keyed by call id - so the 9
  tools are declared once and the session never learns which vendor answered.
  Measured here on `gpt-5.5`; `claude-opus-5` runs the same code path.

  Splitting intake from search is deliberate: it makes the model's
  contribution measurable one axis at a time rather than asserted as a whole.
- **The model's own job: reading the brief.** The strict parser wants nine
  labelled datasheet lines and rejects everything else - including the same
  project written as prose, which it fails on all nine fields, ten times out
  of ten (`tests/selftest.py` asserts this). No policy loop can fix that; it
  is a language problem. So `assisted` and `agent` put the model in front of
  the parser, and hold it to the same standard the output side is held to:
  every extracted value must quote the span of the brief it came from, that
  quote is checked against the source text, and the assembled datasheet is
  handed back to the strict parser for validation. A value the brief does not
  state is reported missing, never assumed. Evidence lock on the way out,
  source lock on the way in.
- **Same flow for every building.** The model class is parameterized
  (1-20 story shear frames, any occupancy class, any site in the hazard
  band); all 10 briefs - hospitals to warehouses, 2 to 12 stories - run
  through the same unmodified pipeline.

## Scope, review and safety

SeismoForge produces **concept-stage prototype studies, not construction
documents.** Every deliverable it writes - CLI, GUI, and the baseline - carries
that notice, and the intended workflow keeps a qualified human in the loop:

- A **licensed structural engineer reviews and signs off** every report before
  it informs any design, procurement, or construction decision. The agent's job
  is to bring that reviewer a defensible starting point and the evidence behind
  it, not to replace their judgment or their seal.
- The system takes **no consequential action.** It reads briefs, runs
  simulations, and writes files under `outputs/`. Nothing is ordered, filed,
  submitted, or sent anywhere.
- Acceptance limits, the model class, and the ground motions are SeismoForge's
  **own benchmark basis** (`forge/building.py`, `forge/motions.py`), inspired
  by performance-based-design practice but not a code-compliant hazard
  analysis for any real site.
- All ten briefs are **synthetic**. No client, site, or personal data is in
  this repository; the model modes send only brief text and tool results to the
  API, and API keys are read from the environment or held in memory, never
  written to disk.
- Reports are built to be **audited**: every table cell traces to a simulation,
  the agent's prose is labelled as unverified commentary, and the search
  history lists every design tried and rejected on the way to the verdict.

## What existed before the competition vs what we added

Pre-existing: the open-source stack (OpenSeesPy, NumPy, and the Anthropic and
OpenAI SDKs) and the author's structural-engineering domain knowledge.
Everything in this repository - physics core, motion synthesis, briefs, the
agents and their instructions, baseline, evaluation harness, docs - was
written during the hackathon.

Two agents are used, and both have their instructions in the repository:
`agent/system_prompt.md` shapes the design agent, `agent/intake_prompt.md`
shapes the brief reader. Their trajectories are in `trajectories/`.

Coding-agent disclosure: this project was built with Claude Code; development
trajectories are available on request.

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
| Final | The scripted policy over the locked tool surface, kept as the path judges can reproduce with no API key | **10/10**, including the honest "not buildable within brief" verdict ([evaluation/results.md](evaluation/results.md)) | Main contribution: physics-in-the-loop + a report writer that can refuse. Stated plainly: this number is the deterministic search, not a model |
| Unification | One session for every entry point, after finding the GUI ran a second code path that skipped the tool layer and logged no trajectory; the search strategy and the LLM tool loop each existed twice and had already drifted | **10/10 unchanged**, and a GUI run now reproduces the CLI's 19 design evaluations on brief 01 | Kept. A demo that does not exercise the measured path is not evidence of anything |
| Intake | Asked what the model does that the scripted policy cannot, and found the answer was: read. The strict parser rejects the same ten projects written as prose on all nine fields, 10/10 (`briefs_prose/`) | 10/10 rejected by the parser; source-lock and round-trip checks in `tests/selftest.py` | Kept. This is the axis where the model's contribution is real rather than substitutable - and it is measured separately from the search axis, so the two do not hide behind each other |
| Provider layer | The design center advertised a provider choice and shipped one vendor, hard-wired in three places. Pulled the wire-format difference into `agent/llm.py` so the tool surface is declared once | `assisted` and `agent` both run on `gpt-5.5`; the same code path takes `claude-opus-5` | Kept. A tool surface that only one vendor can drive is a claim about the vendor, not about the design |
| Intake measured | Ran `assisted` over the prose set - the model reads, the scripted policy searches | **10/10**, 80.5 s, 8,291 in / 2,201 out tokens; the strict parser scores 0/10 on the same input | The model's contribution is real and it is *specific*: it changes what the system can read, not how well it searches. Both reach the same designs |
| Hardening | Adversarial pass over the harness itself, after the result was in: the judge now grades submissions exactly as submitted instead of clamping them into bounds first, a suite that produced no usable demand degrades into unmet checks rather than an unparseable infinity, refinement moves read the design they were asked about instead of whichever was simulated last, and the GUI runs one simulation at a time | **10/10 unchanged**, same evaluator and same briefs | Kept. None of it moved the score - which is the point: the result survives a stricter harness, and the two paths that could have flattered it (a repairing judge, a stale refinement source) are closed |

The challenging case: `brief_10_cliffside_clinic` is deliberately not
buildable (severe near-fault soft-soil site, 0.40 m moat cap). It revealed
that "success rate" alone is a corruptible metric - a system rewarded only
for passing designs will force one. Scoring honesty (flagging infeasibility
counts as correct; a forced "proceed" counts as wrong) is what makes the
10/10 meaningful.

## Known modelling limitations

The 3/10 -> 10/10 result is a comparison *inside this benchmark*, and the
benchmark is deliberately narrow. Below are the simplifications a reviewing
engineer should know about. They are disclosed rather than fixed: each one
shifts absolute demand numbers, and re-basing them this close to the deadline
would invalidate the calibration the whole comparison rests on.

| Simplification | What it does to the numbers |
|---|---|
| Rayleigh damping is anchored on **pre-yield** eigenvalues (`forge/simulate.py`) | The mass-proportional term over-damps the post-yield isolation mode - nearer 4-6% than the 2% the report states - so isolator displacement and residual offset are under-predicted. |
| A **1-story fixed-base** frame returns one mode, so no Rayleigh damping is applied while the calibration block still claims 5% | Affects the 1-story fixed-base case only; every brief here is 2 stories or more. |
| The isolated model carries **n+1 floor masses** (base mat plus n floors) while `isolation_period`, `kd_for_period`, and `seismic_weight` use n | The realized isolated period is sqrt((n+1)/n) longer than the reported one and the base-shear coefficient is inflated by that ratio - worst on low-rise buildings. |
| **Residual offset** is sampled at the end of a 10 s free-vibration tail | It is a phase-dependent snapshot of a lightly damped long-period oscillation, so residual pass/fail carries record-to-record noise. This is exactly why the limit is an envelope over the suite instead of a per-record tolerance (see Iteration 3). |
| The Clough-Penzien **high-pass corner (0.22 Hz)** and the spectral grid floor attenuate the 1.8-4.5 s isolation band | The suite slightly under-excites isolator travel - the very demand the moat check exists to bound. |
| The record-suite **seed derives from the brief's file name** (`forge/brief_parser.py`) | Identical brief files reproduce byte-for-byte, but the same text under another name draws a different suite. GUI runs are all named `user_brief`, so a GUI run and a CLI run of the same brief are not the same suite. |
| `evaluation/ground_truth.json` is a **hand-maintained** feasibility map | It was established by exhaustive sweeps (`tools/sweep_brief.py`; 75 points for brief 10), but it does not re-derive itself: change the physics or the limits and it has to be re-proven. |

None of these bias the comparison - baseline and agent face the identical
model, motions, and limits - but they do bound what the absolute demands mean.

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
briefs/        10 project briefs in strict datasheet form (the exam)
briefs_prose/  the same 10 projects as free prose (the intake exam)
gui/           local design-center web app (stdlib http server + one page)
forge/         physics core: building model, motion synthesis, OpenSees RHA,
               acceptance checks, design rules, policy, report renderer
agent/         session.py (the one entry point), tools.py (the 9 tools),
               intake.py (free-prose reading), system_prompt.md
baselines/     one-shot unverified baseline
evaluation/    ground truth + judge harness + committed results
outputs/       per-brief deliverables (design_report.md + design.json)
trajectories/  run trajectories (JSONL + Markdown); GUI runs land in gui/
tests/         selftest.py (parser, physics, policy, evidence lock,
               degraded-evidence and judge-integrity cases)
tools/         development calibration utilities (sweeps, smoke tests)
video/         solution video slot + outline
LICENSE        MIT, plus the not-for-construction scope notice
```
