# Reproduction guide

Everything starts from a clean Linux environment (native Ubuntu 22.04+ or
WSL2 on Windows). Setup ~5 minutes; the full offline comparison runs in
about a minute on a laptop.

## 1. Environment

Python 3.10-3.12 (OpenSeesPy publishes Linux wheels for these).

```bash
python3 -m venv ~/venvs/seismoforge
```

```bash
~/venvs/seismoforge/bin/pip install numpy openseespy anthropic openai
```

The two SDKs are only needed for the modes that put a model in the loop, and
only the one you actually use. The baseline, the offline mode, and the
evaluation all run with no key and no network.

All commands below run from the repository root:

```bash
PY=~/venvs/seismoforge/bin/python
```

## 2. Data

No downloads and no external datasets. The 10 project briefs under `briefs/`
are the evaluation cases, in the strict datasheet form the deterministic
parser reads. `briefs_prose/` holds the same 10 projects written as ordinary
prose - identical physical values, free wording - which is what the LLM
intake is measured on.

Every ground-motion record is synthesized deterministically from the brief
(same brief -> same suite, byte for byte), so all results are reproducible
from this repository alone.

## 3. One-shot comparison (the main result)

```bash
$PY evaluation/run_matrix.py
```

This runs the baseline (one-shot rule-of-thumb designs, no simulation) and
the offline mode (scripted search through the full tool layer) over all 10
briefs,
then judges both the way a peer reviewer would: every submitted design is
independently re-simulated and its verdict checked against the evidence.

Expected output: `baseline: 3/10 correct`, `agent: 10/10 correct`, and
regenerated `evaluation/results.json` + `evaluation/results.md` (the
committed copies are the run used in the README). Wall time: roughly a
minute, dominated by ~200 nonlinear response-history analyses.

Deliverables land under `outputs/<system>/<brief>/` as `design_report.md`
(client-facing) and `design.json` (machine-readable). The trajectory is written
to `trajectories/trajectory_offline.{jsonl,md}`; GUI runs write their own under
`trajectories/gui/<run-id>.{jsonl,md}`.

## 4. Individual pieces

Baseline only:

```bash
$PY baselines/oneshot.py
```

Agent only (offline mode - scripted search, no key):

```bash
$PY agent/run_agent.py --mode offline
```

Judge existing outputs without re-running:

```bash
$PY evaluation/run_matrix.py --skip-run
```

## 5. Modes

Two things vary independently - who reads the brief, and who picks the next
design:

| Mode | Intake | Search | API key |
|---|---|---|---|
| `offline` | strict parser | scripted policy | no |
| `assisted` | the model reads free prose | scripted policy | yes |
| `agent` | the model reads free prose | the model | yes |

Everything else is shared: the same 9 tools, the same OpenSees engine, the
same evidence lock, and a trajectory from every run.

Either provider works. Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` and the
provider is inferred; `--provider` and `--model` override it. The committed
results were produced with `gpt-5.5`.

The strict parser cannot read `briefs_prose/` at all - it fails on all nine
fields for all ten briefs, which `tests/selftest.py` asserts. That 0/10 is
the baseline the intake modes are measured against:

```bash
$PY agent/run_agent.py --mode assisted --brief-dir briefs_prose --out outputs/agent_assisted
```

```bash
$PY evaluation/run_matrix.py --mode assisted --brief-dir briefs_prose     --label assisted --agent-out outputs/agent_assisted
```

Each run adds a column to `evaluation/results.{json,md}`; `--fresh` starts a
new table instead. The committed table holds `baseline`, `offline` and
`assisted` side by side.

## 6. LLM agent mode

Requires an Anthropic API key (`export ANTHROPIC_API_KEY=...`) or an active
`ant auth login` profile. Keys never enter the repository.

```bash
$PY agent/run_agent.py --mode agent --out outputs/agent_llm
```

Then judge that run:

```bash
$PY evaluation/run_matrix.py --skip-run --agent-out outputs/agent_llm
```

The run prints token usage and estimated cost (model `claude-opus-5`;
typically well under a few dollars for the full portfolio). Trajectory: `trajectories/trajectory_agent.{jsonl,md}`. Run a single brief
with `--briefs brief_01_coastal_hospital`.

## 7. Design-center GUI (same engine, same session)

```bash
$PY gui/server.py --port 8765
```

Open http://127.0.0.1:8765. Load an example brief or write your own, pick a
mode - Offline needs the labelled datasheet lines and no key; Assisted and
Agent read ordinary prose and need an Anthropic or OpenAI key - and press
"Forge the design". Leave the key box empty to use whichever of
`ANTHROPIC_API_KEY` / `OPENAI_API_KEY` the server was started with; pasted
keys are held in memory only.

The page then shows a stage tracker, live counters, the intake evidence table
(each extracted value beside the phrase it was quoted from), every simulated
candidate against its limits, and the run trajectory as it is written. The page shows the live run log, the verdict
banner, the acceptance table, and the combined engineering conclusion. GUI runs write their deliverables under `outputs/gui/<run-id>/` and their
trajectory under `trajectories/gui/<run-id>.{jsonl,md}` - the same record the
CLI leaves.

## 8. Self-tests

```bash
$PY tests/selftest.py
```

Expected final line: `ALL TESTS PASSED` (~20 s).

## Versions used for the committed results

- Ubuntu 24.04 (WSL2), Python 3.12.3
- numpy 2.x, openseespy 3.7.x (current wheels at run date)
- Simulation and evaluation are deterministic: same repo, same numbers.

## Costs

- Baseline, scripted agent, evaluation, tests: $0 (no network).
- `assisted` and `agent` modes: pay-per-use on whichever provider you set.
  The committed `assisted` run used 8,291 input / 2,201 output tokens on
  `gpt-5.5` for the full 10-brief portfolio. Runs print their token counts;
  a dollar figure is only reported for models listed in `PRICES`
  (`agent/llm.py`), so add your provider's published price there rather than
  trusting a number nobody checked.
