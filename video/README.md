# Solution video

Place the submission video here. Up to 5 minutes.

The script below is 602 words, which is 4:49 at 125 words per minute - leaving about 11 seconds for the three marked pauses. Every number in it is
checked against the repository; the source for each is listed at the bottom.

## Scene plan

| # | Section | Words | Ends at | On screen |
|---|---|---:|---:|---|
| 1 | The problem | 86 | 0:41 | Building model shaking, then an engineer at a drawing |
| 2 | The baseline | 65 | 1:12 | A tidy baseline report, then **3/10**, then one brief marked red |
| 3 | One execution | 127 | 2:13 | The GUI: paste a prose brief, stage tracker advancing, intake evidence table, candidate table, verdict banner |
| 4 | The comparison | 37 | 2:31 | `evaluation/results.md`, **3/10 → 10/10** |
| 5 | Changelog | 105 | 3:21 | The changelog table, a 50-point sweep all failing, an oscillation trace, the evidence lock |
| 6 | The agency experiment | 90 | 4:04 | Three mode columns; **8,421** beside **518,386** |
| 7 | Hot take and close | 97 | 4:51 | The two harness defects, then an engineer signing, then the closing card |

Record section 3 as one continuous screen capture. It is the only part that
has to be real time, and it is the part that proves the rest.

---

## Voice-over

### 1 · The problem — 0:00

*[Building model shaking → engineer reviewing a drawing → title]*

> What if an AI gives you an engineering answer that sounds completely
> reasonable, and is physically wrong?
>
> Depending on the building, early-stage structural work takes days to weeks
> of engineering time - and most of it is the computational loop: model,
> ground motions, nonlinear analysis, read, revise, repeat.
>
> That loop is not overhead. It is where the trust comes from. An AI that only
> speeds up the guess has skipped the part that mattered.
>
> **The hard part is knowing when an answer should not be trusted.**  ⏸

### 2 · The baseline — 0:41

*[Baseline report, confident prose → 3/10 → brief 10 in red]*

> So we built a baseline: textbook rule-of-thumb sizing, submitted without
> simulation. Ten building briefs, judged by independently re-simulating every
> design.
>
> Three correct out of ten.
>
> On one brief that is genuinely impossible, it said: proceed.
>
> And it was not wildly wrong. Four of its seven failures missed by under ten
> percent, the closest by half a percent. A wrong number here does not look
> wrong.

### 3 · One execution — 1:12

*[GUI, one continuous take. Paste the prose brief → stage tracker → intake
evidence table → candidate table filling → conclusion]*

> Here is one run, start to finish.
>
> A coastal hospital, written as ordinary prose.
>
> The intake agent extracts nine engineering parameters, and cannot invent one.
> Every value must quote the phrase it came from, checked against your text.
> **Source lock.**
>
> Then the design engine proposes a concept, and OpenSees answers: five
> synthetic records per candidate, each a full nonlinear response-history
> analysis.
>
> The first concept fails. Floor acceleration and base shear are both over the
> limit. So the workflow screens the buildable space, then refines. Nineteen
> designs, ninety-five nonlinear analyses, twelve seconds.
>
> Before the report is written, the submitted design is re-simulated once more.
> If the evidence contradicted the verdict, the report would refuse to write
> it. **Evidence lock.**
>
> Every limit met. The tightest sits at ninety-three percent.

### 4 · The comparison — 2:13

*[`evaluation/results.md` → 3/10 becomes 10/10]*

> Same ten briefs, same judge. Baseline, three out of ten. The deterministic
> path, ten out of ten, including the impossible brief, correctly refused.
>
> That result needs no API key. A judge reproduces it from a clean checkout.

### 5 · Changelog, the biggest change, the removed experiment — 2:31

*[Changelog table → sweep of 50 candidates all failing → oscillating utilization
trace → write_report rejecting a verdict]*

> The changelog shows how we got there. It was not a straight line.
>
> Our first physics loop failed everything. Fifty candidates, zero passing. The
> defect was not in the designs. It was in our ground motions.
>
> Then we tried pure failure-driven refinement: fix the worst failed check, run
> again. On the hard hospital brief it oscillated for fifteen iterations and
> never converged. The constraints are coupled, so every fix breaks something
> else. **We removed it,** and replaced it with coarse screening, then
> refinement.
>
> **The single change that contributed most was giving the report writer a
> veto.** That is what turned plausible output into defensible output.

### 6 · The agency experiment — 3:21

*[Three mode columns, all reading 10/10 → token counts side by side]*

> One last experiment. The deterministic path already scored ten out of ten. So
> what does a model add that a written policy cannot?
>
> Let the model read the brief: ten out of ten, on prose the strict parser
> fails on all nine fields. And its designs matched the deterministic path on
> all ten briefs.
>
> Give the model the design search as well: also ten out of ten, for sixty-two
> times the input tokens.
>
> Same score. So we kept that mode in the repository, and did not make it the
> default.

### 7 · Hot take and close — 4:04

*[The two harness defects → an engineer signing a report → closing card]*

> Twice during development, every design failed, and the fault was in our
> verifier, not our designs.
>
> Simulation-in-the-loop makes the simulator part of your attack surface. An
> agent optimizing against a broken test does not look broken. It converges
> confidently to the wrong answer.
>
> So: **don't just verify the agent. Verify the verifier.**  ⏸
>
> And put the model where the ambiguity is, not where the loop is.
>
> SeismoForge does not replace the structural engineer. Its studies are
> concept-stage, and a licensed engineer signs them.
>
> **Our goal is narrower, and harder: to make AI-generated engineering hard to
> trust without evidence.**

---

## Closing card

```
                    SEISMOFORGE
        Evidence-Gated AI for Seismic Design

     3/10 → 10/10          correct outcomes
     8,421 vs 518,386      input tokens, same score
     Plausible → Verified
```

Do not use an arrow between the token counts. The two figures are two systems
measured on the same cases, not a before and an after.

## The three lines to pause on

Read the rest at an even pace and let these land:

> **The hard part is knowing when an answer should not be trusted.**

> **Don't just verify the agent. Verify the verifier.**

> **Our goal is narrower, and harder: to make AI-generated engineering hard to
> trust without evidence.**

## Recording notes

- Start the GUI with the key already in the environment, so section 3 never
  shows one being typed:

  ```bash
  OPENAI_API_KEY=... python3 gui/server.py
  ```

  The key field then says *"leave blank to use the key already in the server's
  environment"*, and the run works with it empty.

- **Use `agent` mode for section 3** if the point of the shot is that an agent
  is driving. It is the only mode where the model is called again after
  OpenSees answers - the loop the narration describes. A verified run of
  brief 01: the model reached at t+0, nine fields extracted and parser-accepted
  by t+4.7 s, first OpenSees result at t+11.6 s, and at t+13.7 s the model
  calls the next tool having read those numbers. Eleven tool calls driven by
  the model, no human step anywhere, about thirty seconds end to end.

  `assisted` mode also shows the intake evidence table and finishes in about
  nine seconds, but the model is never called a second time: the scripted
  policy runs the search. It fills more candidate rows - nineteen against five
  - so it looks busier, and it is the honest choice only if the narration says
  the search is deterministic. Agent mode shows everything assisted shows,
  plus the loop.

- Paste the prose brief from `briefs_prose/brief_01_coastal_hospital.md`. The
  strict parser cannot read that file at all, which is the point.

- Every scene is reproducible from the commands in
  [../REPRODUCTION.md](../REPRODUCTION.md).

## Where each number comes from

| Claim | Source |
|---|---|
| 3/10, 10/10, and the wall times | `evaluation/results.json` |
| Four of seven baseline failures under 10%, closest 0.4% | Baseline governing utilizations: 1.004, 1.044, 1.080, 1.094, 1.133, 1.316, 2.341 |
| Nine engineering parameters | `FIELDS` in `agent/intake.py` |
| Five records per candidate | `RECORDS_PER_SUITE` in `forge/brief_parser.py` |
| First concept fails on acceleration and base shear | 0.6166 against 0.40, and 0.3728 against 0.30 |
| 19 designs, 95 nonlinear analyses, ~12 s | A GUI run of brief 01, recorded in `trajectories/gui/` |
| Tightest check at 93% | Governing `base_shear_coeff` 0.9301 |
| 50 candidates, zero passing; 15 iterations without converging | Changelog, iterations 1 and 2 |
| "plausible output into defensible output" | Changelog, iteration 4 |
| Strict parser fails all nine fields, ten times | Asserted in `tests/selftest.py` |
| Designs matched on all ten briefs | `outputs/agent` against `outputs/agent_assisted` |
| Sixty-two times | 518,386 ÷ 8,421 = 61.6 |

The one figure not drawn from the repository is "days to weeks of engineering
time". That is a statement about practice, and the README says so plainly in
the note under it.
