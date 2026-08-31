# Solution video

Place the submission video here. Up to 5 minutes.

The script below is the submitted narration, kept as written except where a
sentence repeated something the video already shows, or covered something the
brief assigns to the README rather than the video.

It is 671 words, with three marked pauses of about five seconds each. Read at
150 words per minute - a normal demo pace - that is 4:28 of speech and 4:43 in
total. At 140 wpm it is 4:48 and 5:03, which is over. Aim for 150; the timings
in the table below are the slower 140 wpm bound.

Every number in it is checked against the repository; the source for each is
listed at the bottom.

## Scene plan

Ends-at is measured at 140 wpm and excludes the pauses.

| # | Section | Words | Ends at | On screen |
|---|---|---:|---:|---|
| 1 | The problem | 92 | 0:39 | The manual loop as a cycle: model, ground motions, nonlinear analysis, revise, repeat |
| 2 | The baseline | 101 | 1:23 | **3/10** filling the screen, the ten briefs as a grid with seven going red, then **6/10** beside it |
| 3 | One complete run | 150 | 2:27 | The GUI: paste a prose brief, stage tracker advancing, intake evidence table, candidate table, verdict banner |
| 4 | The comparison | 59 | 2:52 | `evaluation/results.md`, **3/10 → 10/10** |
| 5 | The changelog | 119 | 3:43 | The changelog table, a 50-point sweep all failing, the broken motion spectrum beside the fixed one, an oscillation trace, write_report rejecting a verdict |
| 6 | The agency experiment | 77 | 4:16 | Three mode columns, all 10/10; **8,421** beside **518,386** |
| 7 | Close | 73 | 4:48 | An engineer signing a report, then the closing card |

Record section 3 as one continuous screen capture. It is the only part that
has to be real time, and it is the part that proves the rest.

---

## Voice-over

### 1 · The problem

*[The manual loop drawn as a cycle, turning slowly]*

> Before a building moves into detailed design, a structural engineer has to
> answer a simple but critical question: will this seismic concept actually
> work?
>
> The engineer builds a model, prepares ground motions, runs nonlinear
> analyses, checks what fails, adjusts the design, and runs it again. Depending
> on the project, that cycle can take days or even weeks.
>
> Today, general-purpose AI can suggest a design in seconds. But a convincing
> recommendation is not yet a verified structural response.
>
> **The real bottleneck is not generating a design. It is proving that the
> design works.**  ⏸

### 2 · The baseline

*[3/10 fills the screen → the ten briefs as a grid, seven going red → 6/10
appears beside it]*

> To measure that gap, we built a simple baseline: conventional rule-of-thumb
> sizing, submitted without an iterative simulation loop. We tested it on ten
> building briefs and independently re-simulated every submitted design.
>
> Only three out of ten were correct. And on one brief where no feasible
> solution existed within the benchmark, the baseline still recommended
> proceeding.
>
> Then we asked a capable model the same ten questions directly - the limits
> and the buildable ranges, but no simulator. Six out of ten. Better, and it
> correctly refused the impossible brief. It was also wrong four times, and
> every one of those four said proceed.

### 3 · One complete run

*[GUI, one continuous take. Paste the prose brief → stage tracker → intake
evidence table → candidate table filling → verdict banner]*

> That is where SeismoForge comes in.
>
> Here is one complete run, in Assisted mode. A coastal hospital, written as an
> ordinary project brief.
>
> First, the intake agent extracts nine engineering parameters from the
> natural-language text. Every extracted value must point back to the phrase it
> came from, and that evidence is checked against the original brief. We call
> this Source Lock.
>
> A candidate is generated and passed to OpenSees. Five synthetic ground
> motions are evaluated for each candidate, using full nonlinear
> response-history analyses.
>
> The first candidate fails. Floor acceleration and base shear exceed their
> limits. So the workflow drives the iteration an engineer would otherwise
> drive by hand. In this run it evaluates 19 designs through 95 nonlinear
> analyses.
>
> Then one final gate. Before the report is written, the submitted design is
> re-simulated. If the physics contradicts the verdict, the report writer
> refuses to write it. That is Evidence Lock.

### 4 · The comparison

*[`evaluation/results.md` → 3/10 becomes 10/10]*

> Same ten briefs, same acceptance criteria, same independent evaluation.
>
> The baseline solved three out of ten correctly. The deterministic, Assisted,
> and Full-Agent workflows each achieved ten out of ten, including correctly
> identifying the case where no feasible design existed within the benchmark.
>
> And importantly, the deterministic ten-out-of-ten result can be reproduced
> from a clean checkout without an API key.

### 5 · The changelog

*[Changelog table → sweep of 50 candidates all failing → the broken motion
spectrum beside the fixed one → oscillating utilization trace → write_report
rejecting a verdict]*

> Getting there was not a straight line.
>
> Our first physics loop rejected every design we tried: fifty candidates, zero
> passing. The problem was not the candidate designs. It was the verification
> setup itself. We had to calibrate the examiner before we could trust its
> grades.
>
> Then we tried a purely local refinement strategy: fix the worst failed check
> and run again. On the difficult hospital case, it oscillated for fifteen
> iterations without converging. The reason was physical coupling: improving
> one response could make another one worse. **We removed that strategy** and
> replaced it with coarse screening followed by refinement.
>
> **But the most important change was adding the final evidence gate. The
> report writer gained the right to say no.**  ⏸

### 6 · The agency experiment

*[Three mode columns, all reading 10/10 → token counts side by side]*

> One last question: if some AI is useful, does more agency make the system
> better?
>
> Assisted mode achieved ten out of ten using 8,421 input tokens across the
> portfolio. Then we gave the model control of the design search as well.
> Full-Agent mode also achieved ten out of ten, but consumed 518,386 input
> tokens. About sixty-two times more input, for the same primary outcome.
>
> So we kept Full-Agent mode as an experiment, but not as the default.

### 7 · Close

*[An engineer signing a report → closing card]*

> SeismoForge does not replace the structural engineer. Its output is a
> concept-stage prototype study that remains subject to review and approval by
> a licensed structural engineer.
>
> Instead of manually driving every iteration, the engineer receives a
> candidate design, the failed alternatives, the margins, and the evidence
> behind the conclusion.
>
> **Use AI where language is ambiguous. Use engineering tools where physics
> matters. Keep the engineer in control of the final decision.**  ⏸
>
> That is SeismoForge.

---

## Closing card

```
                       SEISMOFORGE
        From Engineering Brief to Simulation-Backed Concept

   3/10  →  10/10            measured correct outcomes
   6/10                      a capable model, asked directly
   8,421 vs 518,386          input tokens, same score

        AI for ambiguity
        Automation for iteration
        Simulation for evidence
        Engineer for the final decision
```

Do not use an arrow between the token counts. The two figures are two systems
measured on the same cases, not a before and an after.

## The three lines to pause on

Read the rest at an even pace and let these land:

> **The real bottleneck is not generating a design. It is proving that the
> design works.**

> **The report writer gained the right to say no.**

> **Keep the engineer in control of the final decision.**

## Recording notes

- Start the GUI with the key already in the environment, so section 3 never
  shows one being typed:

  ```bash
  OPENAI_API_KEY=... python3 gui/server.py
  ```

  The key field then says *"leave blank to use the key already in the server's
  environment"*, and the run works with it empty.

- **Record section 3 in `assisted` mode.** The narration says Hybrid, or
  Assisted, and the numbers it quotes - 19 designs, 95 nonlinear analyses - are
  that mode's. It finishes in about nine seconds and shows the intake evidence
  table, the stage tracker and the candidate table filling.

  `agent` mode is the alternative: it is the only mode where the model is
  called again after OpenSees answers, so it is the one that shows a loop
  driven by the model. A verified run of brief 01: model reached at t+0, nine
  fields extracted and parser-accepted by t+4.7 s, first OpenSees result at
  t+11.6 s, and at t+13.7 s the model calls the next tool having read those
  numbers. Eleven tool calls, no human step anywhere, about thirty seconds end
  to end. If you record this mode instead, the candidate count in section 3
  changes and the narration must change with it.

- Paste the prose brief from `briefs_prose/brief_01_coastal_hospital.md`. The
  strict parser cannot read that file at all, which is the point.

- Every scene is reproducible from the commands in
  [../REPRODUCTION.md](../REPRODUCTION.md).

## Where each number comes from

| Claim | Source |
|---|---|
| 3/10, 6/10, 10/10 and the wall times | `evaluation/results.json`, keys `baseline`, `llm_direct`, `offline`, `assisted`, `agent` |
| The model asked directly was wrong four times, all saying proceed | `baselines/llm_oneshot.py` output, judged by `evaluation/run_matrix.py` |
| No feasible design exists for brief 10 | `evaluation/ground_truth_sweep.json`, re-derived by exhaustive sweep |
| Nine engineering parameters | `FIELDS` in `agent/intake.py` |
| Five ground motions per candidate | `RECORDS_PER_SUITE` in `forge/brief_parser.py` |
| First candidate fails on acceleration and base shear | 0.6166 against 0.40, and 0.3728 against 0.30 |
| 19 designs, 95 nonlinear analyses | A GUI run of brief 01 in assisted mode, recorded in `trajectories/gui/` |
| 50 candidates zero passing; 15 iterations without converging | Changelog, iterations 1 and 2 |
| The evidence gate was the change that mattered most | Changelog, iteration 4 |
| Sixty-two times | 518,386 ÷ 8,421 = 61.6 |

The one figure not drawn from the repository is "days or even weeks". That is a
statement about practice, and the README says so plainly in the note under it.
