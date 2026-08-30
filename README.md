# SeismoForge

*Dokumen ini juga tersedia dalam [bahasa Indonesia](README.id.md).*

## An Evidence-Gated AI Design Engineer for Seismic Concept Design

**From a natural-language building brief to a simulation-verified seismic concept — where every reported number comes from physics, and no verdict may contradict it.**

SeismoForge is an agentic design center for early-stage seismic engineering. It reads a project brief written in ordinary language, develops a structural protection concept — either a conventional fixed-base frame or lead-rubber base isolation — verifies candidate designs through nonlinear response-history analysis in OpenSees, iterates when performance targets are not met, and refuses to publish an engineering verdict that the simulation evidence contradicts.

> **The model handles ambiguity. The tools handle physics. The evidence gate decides what can be claimed.**

SeismoForge is a **concept-stage prototype, not a construction design system**. Every report is intended for review and sign-off by a licensed structural engineer before it informs any real-world design, procurement, or construction decision.

---

# What is SeismoForge?

Imagine a client sends you this:

> *"We are planning a five-storey hospital on reclaimed coastal ground, deep
> soft soil. Each floor carries about 550 tonnes, design PGA 0.32 g. The site
> leaves us 0.9 m of clearance around the building. Does this need base
> isolation?"*

SeismoForge reads that message, designs the earthquake protection system,
**tests it against simulated earthquakes**, revises it when it fails, and
returns one engineering conclusion - or refuses, if what the client is asking
for cannot be built.

## How it works, in four sentences

1. **A language model reads the brief.** It pulls nine engineering parameters
   out of ordinary prose, and may not invent any of them: every value has to
   quote the phrase of your text it came from.
2. **The design engine proposes a concept** - a conventional frame, or a
   lead-rubber isolation layer under the building.
3. **OpenSees shakes it.** Five synthetic ground-motion records, each a full
   nonlinear response-history analysis, and every performance limit is checked
   against the result.
4. **The evidence gate decides.** Before the report is written the design is
   re-simulated; if the evidence contradicts the conclusion, the report
   **refuses to be written**.

### Quick links

- **Local GUI:** run `python3 gui/server.py`, then open `http://127.0.0.1:8765`
- **Reproduction guide:** `REPRODUCTION.md`
- **Measured results:** `evaluation/results.md`
- **Agent trajectories, with an index of what is in each:** [trajectories/README.md](trajectories/README.md)
- **Example deliverable:** `outputs/agent/brief_01_coastal_hospital/design_report.md`
- **Evaluation cases:** `briefs/` (strict format) and `briefs_prose/` (the same ten as free-form prose)
- **Scope and safety:** see [Scope, Review, and Safety](#scope-review-and-safety)
- **Known modeling limitations:** see [Known Modeling Limitations](#known-modeling-limitations)
- **Solution video, script and scene plan:** [video/README.md](video/README.md)

---

# The result in one screen

## **3/10 → 10/10 correct engineering outcomes**

Measured on the same fixed 10-building benchmark and judged by independent re-simulation of every submitted design.

| Metric | Unverified baseline | Deterministic Forge (`offline`) | Hybrid Evidence Agent (`assisted`) | Full-Agent Experimental Mode (`agent`) |
|---|---:|---:|---:|---:|
| Who reads the brief | — | strict parser | **model** | **model** |
| Who chooses the next design | — | written policy | written policy | **model** |
| Input format supported | labeled datasheet | labeled datasheet | **free-form prose** | **free-form prose** |
| Correctly resolved briefs — primary metric | **3/10** | **10/10** | **10/10** | **10/10** |
| Correctly identifies infeasible brief | no — says "proceed" | yes | yes | yes |
| Full-portfolio runtime | 0.4 s | 38.6 s | 71.3 s | 337.8 s |
| Model tokens, full portfolio | — | — | **8,421 in / 2,081 out** | **518,386 in / 17,272 out** |
| Human effort per brief | the full study still required | review | review | review |

Measured on `gpt-5.5` for the model-driven modes.

The headline result is 3/10 → 10/10. But the more important finding is what happened **between the two 10/10 systems**:

> **Full model control of the design search produced the same engineering score with 62× more input tokens and 4.7× more runtime than the hybrid workflow.**

That experiment changed the architecture.

---

# Why this problem is worth solving

## Who has this problem?

Engineers - and specifically **civil and structural engineers** handling
earthquake protection at concept stage:

- **structural consultancies** screening several protection options before
  committing to one concept;
- **individual practising engineers** working without an analysis team behind
  them;
- **architects** who need to know early whether a protection concept fits
  inside the site constraints - the moat gap in particular, because it moves
  the floor plan and the setback line.

What they share is a decision that has to be made *before* there is a budget
for a full study.

At concept stage, an engineer may need to answer:

- Does this building need base isolation at this site?
- What bearing parameters should be considered?
- Is the available moat gap sufficient?
- Will the selected protection strategy satisfy the coupled performance limits?
- Is the client brief even feasible as proposed?

Reaching a defensible seismic concept is not a one-shot calculation. Depending on the building and the information available, the structural work can take **days to weeks of engineering time** before review.

What consumes it is not writing formulas. It is the computational loop: build the model, select ground motions, run nonlinear response-history analyses, read the results, revise the design, repeat.

SeismoForge does not claim to replace that work. It compresses **the computational and iterative portion** into seconds, and leaves the rest - engineering judgment, site investigation, and the signature - to the engineer.

> On the numbers: conceptual design processes have been benchmarked in the literature - Gane and Haymaker's CIFE study of conceptual high-rise design analyses team size, composition, and time investment ([CIFE TR174, Stanford, 2008](https://purl.stanford.edu/xm514gk6039); peer-reviewed as *Benchmarking Current Conceptual High-Rise Design Processes*, ASCE Journal of Architectural Engineering 16(3)). No published figure exists for engineering hours on this specific decision, so this document quotes a range from practice rather than inventing one. A full seismic evaluation under ASCE/SEI 41 - site investigation, material testing, drawing verification, peer review - is a larger activity again, and is not what SeismoForge does.

## What bottleneck makes it worth solving?

The dangerous failure mode of AI-assisted engineering — and of rushed manual engineering — is the same:

> **A plausible design that has not actually been verified.**

One-shot sizing can look convincing while still being wrong because seismic isolation sits inside a coupled design space:

- more energy dissipation can reduce isolator displacement while increasing force transferred to the superstructure;
- a longer isolation period can reduce force while consuming more moat clearance;
- softer soil can penalize the same long-period behavior that helps elsewhere.

Our simple rule-of-thumb baseline makes that problem measurable. It resolves only **3 of 10** benchmark briefs correctly and, on one deliberately infeasible project, confidently recommends proceeding.

SeismoForge exists to close the gap between **plausible** and **defensible**.

---

# The product

## One brief in. One engineering conclusion out.

A user submits **one project** and receives **one concept-stage engineering conclusion**.

That is the product, and that is what `gui/server.py` runs.

The 10 files in `briefs/` are not one giant session. They are **evaluation cases**: ten different buildings, each run independently so the claim "this works" can be tested instead of asserted.

`briefs_prose/` contains those same ten projects rewritten as ordinary prose. That second set isolates a different question: can the system understand a human brief without requiring a rigid machine-readable template?

---

# The core design principle: Evidence-Gated Agency

SeismoForge does not ask an LLM to be its own calculator, simulator, and judge.

It separates the work according to what each component is actually good at.

```text
                 HUMAN ENGINEER
                       │
                       ▼
              Natural-language brief
                       │
                       ▼
              ┌──────────────────┐
              │   INTAKE AGENT   │
              │ Understand intent│
              │ Extract + cite   │
              └────────┬─────────┘
                       │
                  SOURCE LOCK
                       │
                       ▼
              ┌──────────────────┐
              │  DESIGN ENGINE   │
              │ Generate/search  │
              │ candidates       │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │     OPENSEES     │
              │ Nonlinear RHA    │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  EVIDENCE GATE   │
              │ Pass / Reject /  │
              │ Iterate          │
              └────────┬─────────┘
                       │
                       ▼
              VERIFIED DESIGN REPORT
                       │
                       ▼
                 HUMAN APPROVAL
```

## Source-Locked In. Evidence-Locked Out.

**Source lock on the way in:** every value extracted from free-form prose must cite the exact source text that supports it. The citation is checked against the original brief, and the reconstructed datasheet must pass the same strict parser used by the deterministic path. Values that are not stated are reported missing rather than invented.

**Evidence lock on the way out:** every quantitative response value comes from the engineering toolchain. `write_report` re-simulates the submitted design and refuses a verdict contradicted by the evidence. `verify_output` then checks the written deliverable again using the same logic as the evaluator.

The result is a deliberately asymmetric system:

> **AI may interpret. AI may propose. AI may explain. But AI cannot overrule the physics evidence.**

---

# How SeismoForge works

## 1. Read the brief

The model converts free-form project prose into the nine required engineering fields.

This is where model capability is genuinely valuable. The strict parser gets **0/10** on `briefs_prose/`: on every one of the ten projects it fails all nine fields because the information is not expressed in the required labeled format.

The Hybrid Evidence Agent closes that gap completely, using **8,421 input tokens for the full 10-case portfolio**.

The strongest evidence that this reading is faithful is not the score — both modes reach 10/10 — but the designs underneath it. **On all ten briefs, the Hybrid Evidence Agent and the Deterministic Forge submit identical designs.** The model's reading of ordinary prose lands on exactly the nine values the strict parser extracts from the labeled datasheet, project after project. What changed is what the system will accept as input, not what it concludes.

## 2. Generate a first engineering concept

The workflow begins with a rule-of-thumb concept rather than an expensive blind search.

## 3. Challenge it with physics

Every candidate goes through the OpenSees simulation toolchain. Ground motions are synthesized deterministically from the brief using a soil-filtered spectral process with a Clough-Penzien high-pass stage.

Each design evaluation runs a five-record suite, so a single candidate costs five nonlinear response-history analyses. The full deterministic portfolio performs 110 design evaluations — 550 nonlinear analyses — in 38.6 seconds.

No design driver — deterministic or model-based — gets to manufacture response values directly.

## 4. Search only when needed

If the first concept fails, the deterministic workflow moves through:

**rule of thumb → coarse feasible-space screening → failure-informed refinement**

The refinement rules encode coupled engineering behavior, for example: if transmitted force is too high, lengthen the period or soften the yield transition rather than blindly changing one scalar at a time.

## 5. Let the report say "no"

The reporting layer has veto power.

A submitted design that fails the acceptance checks cannot be reported as "proceed." A design that passes cannot be reported as infeasible. The final deliverable is re-simulated before the verdict is written.

## 6. Keep a qualified human in control

The final output is a reviewable engineering starting point with a traceable basis of evidence. It is not a substitute for professional judgment or a licensed engineering stamp.

---

# The most important experiment: Where should the agent actually think?

The deterministic path was built first, and it already scored **10/10** on the
labeled briefs. So the question was not whether a model could reach that score
— it was what a model adds that a written policy cannot.

We split the workflow at its two seams and measured them one at a time.

**First seam — reading the brief.** The model interprets free-form prose; the
written policy still runs the search. That is the Hybrid Evidence Agent, and
it scored **10/10** on the prose set the strict parser cannot read at all.

**Second seam — driving the search.** The model gets the design search as
well. That is the Full-Agent Experimental Mode, and it also scored **10/10**.

Same score. Radically different resource profile:

| Workflow | Correct cases | Runtime | Model input tokens |
|---|---:|---:|---:|
| Hybrid Evidence Agent | **10/10** | 71.3 s | **8,421** |
| Full-Agent Experimental Mode | **10/10** | 337.8 s | **518,386** |

Full agency bought **no measurable improvement in engineering outcome** on this design space.

That is not a failure of the model. It is evidence about the shape of the problem.

The design space is small enough and the constraint coupling regular enough that the search strategy can be written once. Natural-language intake, by contrast, is genuinely ambiguous and cannot be replaced by the strict parser.

## The architectural lesson

> **Use AI where ambiguity requires judgment. Use deterministic tools where the problem already has physics.**

The most agentic architecture was not the best architecture.

The best architecture was the one that gave the model responsibility **only where model capability changed the result**.

---

# A challenging case: sometimes the correct design is no design

`brief_10_cliffside_clinic` is intentionally infeasible within the benchmark assumptions: a severe near-fault soft-soil site combined with a 0.40 m moat limit.

An exhaustive 75-point sweep found **zero feasible designs** under the benchmark rules.

This case matters because a conventional "success rate" metric can be gamed. If a system is rewarded only for producing a passing design, it is incentivized to force one into existence.

SeismoForge scores honest infeasibility as correct and a forced "proceed" as wrong.

> **Sometimes the safest and most useful engineering answer is: the brief must change.**

That is why 10/10 is meaningful here: one of those ten correct answers is a refusal to pretend a feasible design exists.

---

# Three operating modes, one execution path

Every entry point — CLI, GUI, and evaluation harness — sends a brief through `agent/session.py`. There is no separate demo implementation. The path shown in the GUI is the path measured in evaluation, and each run leaves a trajectory.

Two responsibilities can vary independently: who reads the brief, and who chooses the next design.

| Mode | Brief reader | Design-search driver | API key required |
|---|---|---|---|
| **Deterministic Forge** (`offline`) | strict parser | written policy | no |
| **Hybrid Evidence Agent** (`assisted`) | model | written policy | yes |
| **Full-Agent Experimental Mode** (`agent`) | model | model | yes |

The names above are documentation labels; the flags in parentheses are what the code, the CLI, and `evaluation/results.md` actually use.

The wire-format differences between providers live in one place: `agent/llm.py`. Anthropic tool results are represented as content blocks in a user turn; OpenAI tool results are separate tool messages keyed to a call id. The nine tools are declared once, and the session logic does not need vendor-specific branches.

The measured runs reported here use `gpt-5.5`. The same code path also accepts `claude-opus-5`.

---

# Engineering choices that matter

## Tools calculate; drivers decide

Whether the driver is the model or the written policy, quantitative structural response comes from the toolchain. The decision layer can choose a candidate, but it cannot fabricate a demand value.

## Search shaped like engineering practice

The workflow does not begin with an unrestricted agentic exploration. It starts from a reasonable sizing rule, screens the feasible design region when necessary, and refines based on the failed constraints.

## Reports are allowed to refuse

`write_report` re-simulates the final submission and will not write a verdict that disagrees with the evidence. `verify_output` independently checks the completed deliverable.

## One session implementation

CLI, GUI, and evaluation share `agent/session.py`, preventing the common failure where the polished demo takes a different path from the measured system.

## Deterministic evidence chain

Ground-motion generation is deterministic from repository inputs. The evaluation chain can therefore be rerun without downloading external record databases or depending on mutable remote datasets.

## Same pipeline across buildings

The structural model is parameterized for shear-frame buildings from 1–20 stories, arbitrary occupancy class, and sites within the benchmark hazard bands. All ten cases — from hospital to warehouse, 2 to 12 stories — pass through the same workflow without per-case code modifications.

---

# Evaluation design

## Primary metric

**Number of briefs resolved correctly.**

The same evaluator and the same 10 briefs are used throughout development.

A final submission is independently re-simulated before it is scored. A brief counts as correct when a "proceed" verdict survives that re-simulation on a feasible brief, or when an infeasible brief is flagged rather than forced.

## Why ten cases?

The benchmark spans different building types and heights and includes one deliberately infeasible challenge case. The cases are synthetic so they can be shared and reproduced without client or personal data.

## Fair-comparison principle

Baseline and final systems face the same structural model, generated motions, performance limits, and evaluation rules. The comparison therefore measures workflow differences inside this benchmark rather than differences in underlying physics assumptions.

---

# Improvement Changelog

The evaluator and ten benchmark briefs remain fixed throughout this progression. The primary metric is **briefs resolved correctly**.

| Stage | What we tried and why | Evidence | Decision / learning |
|---|---|---|---|
| **Baseline** | One-shot rule-of-thumb sizing, representing a competent first pass or raw LLM-style answer before nonlinear verification | **3/10**; incorrectly says "proceed" on the infeasible case | Established the real bottleneck: confident sizing is often wrong on demanding sites |
| **Iteration 1 — calibrate the verifier** | First physics loop using plain Kanai-Tajimi motion synthesis | 50-point hospital sweep: **0 passing designs**; every candidate failed everywhere | The verifier was wrong, not the design space. Unfiltered long-period energy made isolation effectively impossible. Added the Clough-Penzien high-pass stage |
| **Iteration 2 — redesign the search** | Pure local failure-based refinement: fix the worst check and rerun | Difficult hospital case oscillated for 15 iterations without convergence | Removed as the sole strategy. Coupled constraints made single-failure steps chase each other. Replaced with coarse screening → refinement; the same case then converged after screening + 1 refinement step |
| **Iteration 3 — make record variability honest** | Five-record suite with a per-brief deterministic seed | Residual displacement envelope exceeded its limit for every candidate even when peak demands were acceptable | Residual offset was realization-dominated. Rebased the criterion to an upper envelope across the suite rather than a per-record tolerance |
| **Iteration 4 — evidence-gated reporting** | `write_report` re-simulates and vetoes contradictory verdicts; `verify_output` independently checks the deliverable | Exhaustive 75-point sweep confirms the infeasible brief has 0 feasible candidates; neither agent nor human path can write "proceed" for it | **Kept. This was the change that turned plausible output into defensible output** |
| **Final deterministic path** | Written search policy over the locked simulation tool surface, retained so judges can reproduce the main result without an API key | **10/10**, including an honest "not feasible under the brief" verdict | Main contribution: physics-in-the-loop plus an evidence-gated report writer. Stated plainly: this number is the deterministic search, not a model claim |
| **Unification** | Replaced separate GUI and CLI paths after discovering the GUI bypassed the tool layer and did not record trajectories; duplicated search and LLM loops had diverged | **10/10 unchanged**; GUI run now reproduces the 19 design evaluations made by CLI for brief 01 | **Kept. A demo that does not exercise the measured path is not evidence** |
| **Intake experiment** | Asked what the model can do that a written policy cannot. Tested the same ten projects as ordinary prose | Strict parser rejects all ten prose briefs across all nine fields; source-lock and round-trip checks enforced in `tests/selftest.py` | **Kept. Language understanding is the axis where the model provides unique value** |
| **Provider layer** | Removed vendor-specific logic that had been hard-coded in three places and centralized the wire-format difference in `agent/llm.py` | Hybrid and full-agent modes run on `gpt-5.5`; the same interface accepts `claude-opus-5` | **Kept. A tool surface that only works for one vendor is a vendor demo, not an architectural claim** |
| **Measured intake** | Hybrid Evidence Agent: model reads prose, written policy searches | **10/10**, 71.3 s, **8,421 in / 2,081 out**; strict parser gets 0/10 on the same prose; submitted designs identical to the deterministic path on all ten briefs | Model contribution is real and specific: it changes what the system can read, not what it concludes |
| **Measured full agency** | Full-Agent Experimental Mode: model reads the prose and drives the search | **10/10**, 337.8 s, **518,386 in / 17,272 out** | Same engineering score with 62× input tokens. Retained because the negative result is the architectural finding |
| **Hardening** | Adversarial pass over the evaluation harness: judge exactly the submitted design rather than clamping inputs first; degraded motion suites become unmet checks rather than unparsable infinity; refinement reads the requested candidate rather than stale simulation state; GUI serializes simulations | **10/10 unchanged** on the same evaluator and briefs | **Kept. The result survives a stricter harness after two flattering failure paths were removed** |

---

# What failed — and why that matters

The most important failures were not LLM hallucinations.

Twice, every candidate looked wrong because the **verification harness itself was wrong**:

1. the first motion generator carried nonphysical long-period energy that made every isolation candidate fail;
2. the first residual-displacement criterion treated a realization-dependent end-state as though it were a stable repeatable quantity.

This produced the central engineering-agent lesson of the project:

> **The most dangerous agent is not one that fails. It is one that successfully optimizes against the wrong verifier.**

Simulation-in-the-loop makes the simulator part of the system's attack surface. A capable agent facing a miscalibrated checker may not look broken at all — it may converge efficiently and confidently to the wrong place.

So the correct sequence is:

1. calibrate the test;
2. sweep the design space;
3. confirm feasible problems really have solutions and infeasible ones do not;
4. only then allow the agent to optimize against that test.

And after optimization, give the reporting layer the right to say **no**.

---

# The 518K-token lesson

We spent **518,386 input tokens** to answer a question that became more valuable than another point on the benchmark:

> **Where should agency live?**

On these ten identical cases:

- letting the model read the human brief was indispensable to handling free-form prose;
- letting the model additionally steer a structured design search produced **zero additional correct cases**;
- the extra agency cost 62× more input tokens and 4.7× more runtime than the hybrid path.

The lesson is not "agents are bad."

It is more useful:

> **Put the model where the ambiguity is, not automatically where the loop is.**

If the strategy can already be encoded reliably, deterministic search can be the more agentic choice in the systems sense: cheaper, auditable, reproducible, and easier to constrain.

Had we reported only one number — "agentic vs baseline" — we would have credited design search for an improvement actually won by language understanding and verification.

---

# Scope, Review, and Safety

SeismoForge produces **concept-stage prototype studies, not construction documents**.

Every CLI, GUI, and baseline deliverable carries that notice.

- **Licensed engineer review is required.** A structural engineer must review and sign off each report before it affects design, procurement, or construction. The system's job is to bring the reviewer a defensible starting point and its evidence, not replace professional judgment or stamping authority.
- **No consequential action is automated.** SeismoForge reads a brief, runs simulations, and writes files under `outputs/`. It does not order equipment, submit permits, issue drawings, transmit instructions, or take physical action.
- **Benchmark assumptions are internal to SeismoForge.** Acceptance limits, structural model classes, and ground motions in `forge/building.py` and `forge/motions.py` are inspired by performance-based engineering practice but are not a code-compliant site-specific hazard analysis for any real location.
- **All ten benchmark briefs are synthetic.** The repository contains no client, private-location, or personal data. Model modes send only brief text and tool results to the selected API. API keys are read from the environment or held in memory and are never written to disk.
- **Reports are designed to be auditable.** Each table value is traceable to a simulation, model-generated narrative is labeled as unverified commentary, and the search history records every candidate tried and rejected before the final verdict.

---

# Known Modeling Limitations

The **3/10 → 10/10** result is a comparison **inside this intentionally narrow benchmark**.

The following simplifications matter to the absolute demand values. They are disclosed rather than silently corrected because changing them at the end of the experiment would require recalibrating the benchmark and re-establishing the ground truth.

| Simplification | Effect on the numbers |
|---|---|
| Rayleigh damping is anchored to **pre-yield eigenvalues** in `forge/simulate.py` | The mass-proportional term over-damps the post-yield isolation mode — approximately 4–6% rather than the 2% stated in the report — so isolator displacement and residual offset are under-predicted |
| A **1-story fixed-base frame** returns only one mode, so Rayleigh damping is not applied even though the calibration block still states 5% | Affects only 1-story fixed-base cases; every benchmark brief here is at least 2 stories |
| The isolated model carries **n+1 floor masses** — base mat plus n floors — while `isolation_period`, `kd_for_period`, and `seismic_weight` use n | Realized isolation period is longer than reported by `sqrt((n+1)/n)`, and the base-shear coefficient is inflated by that ratio; effect is largest for low-rise buildings |
| **Residual offset** is sampled at the end of a 10-second free-vibration tail | It is a phase-dependent snapshot of a lightly damped long-period oscillation, so record-to-record pass/fail carries noise. This is why the criterion uses an upper envelope across the suite rather than a per-record tolerance |
| **0.22 Hz Clough-Penzien high-pass corner** and the lower bound of the spectral grid attenuate the 1.8–4.5 s isolation band | The suite slightly under-excites isolator displacement — the demand that the moat check is intended to constrain |
| **Record-suite seed is derived from the brief filename** in `forge/brief_parser.py` | Identical brief files reproduce bit-for-bit, but identical text under a different filename receives a different suite. GUI runs are named `user_brief`, so GUI and CLI runs of identical text do not necessarily use the same suite |
| `evaluation/ground_truth.json` is a **manually maintained feasibility map** | It was established through exhaustive sweeps — including 75 points for brief 10 — but does not regenerate itself. Change the physics or acceptance limits and the feasibility map must be proven again |

These limitations constrain the meaning of the absolute engineering demands. They do **not** create an asymmetric advantage in the reported benchmark comparison because the baseline and the final systems face the same structural model, motions, and limits.

---

# Reproducibility

A judge should be able to start from a clean environment and reproduce the main claim without trusting screenshots or a hosted demo.

The repository contains:

- the deterministic physics and motion-generation code;
- all ten evaluation briefs;
- the equivalent ten free-form prose briefs;
- the baseline;
- the evaluation harness and committed results;
- agent instructions;
- representative trajectories;
- example deliverables;
- a no-API-key deterministic path for the main engineering result.

See **`REPRODUCTION.md`** for environment setup, exact commands, expected outputs, versions, approximate runtime, and model-dependent execution details.

Because the deterministic mode reproduces the 10/10 engineering result without an API key, judges can verify the primary outcome independently of model availability. Model access is only required to reproduce the free-form intake and full-agent experiments.

**Cost note:** runs report their token counts, but a dollar figure is printed only for models with a published price recorded in `PRICES` (`agent/llm.py`). An unrecognized model reports tokens and states that no price is configured, rather than quoting a number that has not been checked.

---

# GUI Design Center

The local GUI lives in `gui/` and uses only Python standard-library web serving — no additional web-framework dependency.

Run:

```bash
python3 gui/server.py
```

Then open:

```text
http://127.0.0.1:8765
```

From one screen, a user can:

- type or load a brief, and select `offline`, `assisted`, or `agent` mode;
- follow a **stage tracker** — read the brief, first concept, screen the space, refine, write the report, verify — that advances as the run does;
- watch **live counters**: elapsed time, designs simulated, nonlinear analyses run;
- inspect the **brief intake evidence**: every extracted value beside the exact phrase of the brief it was quoted from, and any unit conversion applied;
- follow the **candidate table**: each design tried, its governing demand against its limit, and whether it passed;
- read the **agent trajectory** as it happens — tool calls, stages, timings, and any source-lock retry;
- read the final verdict, selected system, margins, engineering notes, evidence basis, and the path to the machine-readable trajectory with model and token counts.

Nothing on that screen is a re-enactment. The stage tracker, the candidate
table, and the trajectory panel are all rendered from the run's own trajectory
file while it is being written, so the screen cannot claim a step the run did
not take.

API keys are kept in memory only. Leaving the key field blank falls back to the
key in the server's own environment — which is also how you record a demo
without a key on screen.

Most importantly, the GUI does not run a special demo path. It enters the same `agent/session.py` workflow used by CLI and evaluation, and records its trajectory under `trajectories/gui/`.

---

# What existed before the hackathon

Existing components:

- OpenSeesPy;
- NumPy;
- Anthropic SDK;
- OpenAI SDK;
- the author's pre-existing structural-engineering domain knowledge.

Built during the hackathon:

- structural physics core;
- ground-motion synthesis;
- benchmark briefs;
- free-form prose intake set;
- both agents and their instructions;
- baseline;
- design-search policy;
- evidence-gated report generation;
- verification harness;
- evaluation framework;
- GUI;
- provider abstraction;
- trajectories;
- documentation.

Two agents are used in the repository:

- `agent/system_prompt.md` — design agent instructions;
- `agent/intake_prompt.md` — brief-reading agent instructions.

Their trajectories are included under `trajectories/`.

**Coding-agent disclosure:** the project was built with Claude Code; the development trajectory is available on request.

---

# Repository Map

```text
briefs/              10 strict-format project briefs used as evaluation cases

briefs_prose/        the same 10 projects written as ordinary prose for intake testing

gui/                 local web design center

forge/               core engineering physics:
                     building model, ground-motion synthesis, OpenSees RHA,
                     acceptance checks, sizing rules, design policy,
                     report rendering

agent/               session.py      single execution entry point
                     tools.py        9 engineering tools
                     llm.py          provider abstraction
                     intake.py       free-form brief reader
                     system_prompt.md
                     intake_prompt.md

baselines/           one-shot unverified baseline

evaluation/          ground truth, judge harness, committed results

outputs/             per-brief deliverables:
                     design_report.md + design.json

trajectories/        representative run trajectories in JSONL + Markdown;
                     GUI runs are also recorded

tests/               selftest.py:
                     parser, physics, policy, source/evidence lock,
                     degraded-evidence cases, judge integrity

tools/               development calibration utilities:
                     sweeps, smoke tests

video/               <=5-minute solution video slot + outline

LICENSE              MIT + concept-stage / not-for-construction notice
```

---

# Solution Video Story

The recommended <=5-minute story is intentionally simple:

1. **The problem:** plausible seismic concepts can be wrong without nonlinear verification.
2. **The baseline:** 3/10 and a false "proceed" on an infeasible brief.
3. **One full run:** coastal hospital from human brief → candidate → OpenSees → iteration → evidence-gated report.
4. **The result:** 3/10 → 10/10.
5. **The experiment we removed from the optimal path:** full-agent design search.
6. **The surprising finding:** handing the model the design search too scored the same 10/10, for 518,386 input tokens against 8,421.
7. **The hot take:** reliable engineering agents need a calibrated verifier and a clear boundary for where agency actually adds value.

An outline is available in `video/README.md`.

---

# Final Takeaway

We started by asking:

> **Can an agent design a seismic protection concept?**

The more useful question turned out to be:

> **What parts of engineering should an agent be allowed to own?**

The benchmark produced three answers.

**First:** a plausible one-shot design is not enough. The baseline scored **3/10**.

**Second:** physics-in-the-loop plus evidence-gated reporting can turn that into **10/10** within this benchmark, including the ability to reject an infeasible brief.

**Third:** more autonomy is not automatically more capability. Full model control of the design search matched the hybrid result but used **62× more input tokens**.

So SeismoForge is not built around the idea that the AI should do everything.

It is built around a stricter principle:

> **Let the model resolve ambiguity. Let deterministic tools calculate. Let simulation challenge the proposal. Let evidence control the claim. And keep the engineer responsible for the decision.**

That is the architecture SeismoForge is testing.
