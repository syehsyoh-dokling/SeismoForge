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
| 5 | The changelog | 119 | 3:43 | `stills/05a` changelog, `05b` the 50-point sweep under both verifiers, `05c` the two spectra, `05d` the governing check moving, `05e` the veto firing |
| 6 | The agency experiment | 77 | 4:16 | `stills/06a` three modes with token counts; `06b` where the evidence lives |
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

*[`stills/05a_changelog.md` → `05b_verifier_sweep.txt`, hold on the 0 / 50 row →
`05c_spectrum.svg` → `05d_coupling.txt`, hold on the list of governing checks →
`05e_report_veto.txt`, hold on the returned error]*

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

*[`stills/06a_agency.txt`, hold on the three 10/10 rows, then on 8,421 beside
518,386 → `06b_tree.txt` under the last line]*

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

## Stills for sections 5 and 6

Sections 1 to 4 have something to point a camera at: the report, the results
table, the GUI. Sections 5 and 6 are about experiments, and one of those
experiments was removed. These stills are generated from the code rather than
drawn, so what is on screen is what the repository does.

```bash
python3 video/make_stills.py
```

About a minute; the two sweeps are 500 nonlinear analyses. `--skip-sweep`
regenerates everything else in seconds.

| Still | Shows | Reconstructed? |
|---|---|---|
| `05a_changelog.md` | The five changelog rows the narration walks | No - quoted from README.md at generation time |
| `05b_verifier_sweep.txt` | The same 50 candidates swept under both motion generators: **0 / 50** passing, then **1 / 50**, closest miss 1.18 → 0.93 | Yes - the iteration-1 generator is the shipped one with the Clough-Penzien stage removed |
| `05c_spectrum.svg` | Displacement spectra of one record under both generators. Across the 1.8-4.5 s isolation band the unfiltered process demands up to **2.50×** the displacement | Yes - same reconstruction |
| `05d_coupling.txt` | The governing check moving between four different limits and back | No - the shipped refinement loop, run now |
| `05e_report_veto.txt` | `write_report` as code, then the veto firing on a real submission | No - live call |
| `06a_agency.txt` | Three modes at 10/10 with wall times and token counts, each traced to its file and line | No - read from the committed files |
| `06b_tree.txt` | Where the evidence lives, and which parts need no API key | No |

Two honesty notes, both stated on the stills themselves:

- **The 0 / 50 sweep is a reconstruction.** The generator that produced it was
  replaced, so the still runs the shipped generator against a copy of itself
  with one line removed. The narration's claim is that the verifier was wrong,
  and that is what the two rows show.
- **The fifteen non-converging iterations are not reproduced.** Those belong to
  refinement moves that were retuned when the strategy was replaced. Attempting
  to recover them from the current code produces a converging run, not an
  oscillating one, so `05d` shows the coupling that caused the problem instead
  and points at the changelog for the historical result. Do not put a fabricated
  oscillation trace on screen.

`05c` is an SVG - open it in a browser at full width. The rest are plain text;
a terminal or an editor at a large font size reads best.

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
| 50 candidates, zero passing | Changelog iteration 1, and reproduced on screen by `video/make_stills.py` → `stills/05b_verifier_sweep.txt` |
| 15 iterations without converging | Changelog iteration 2 only. Not reproducible against current code - see the honesty note above |
| The evidence gate was the change that mattered most | Changelog iteration 4; the veto firing is `stills/05e_report_veto.txt` |
| Sixty-two times | 518,386 ÷ 8,421 = 61.6, from the `usage` events at `trajectories/trajectory_agent.jsonl:343` and `trajectories/trajectory_assisted.jsonl:401` |

The one figure not drawn from the repository is "days or even weeks". That is a
statement about practice, and the README says so plainly in the note under it.
