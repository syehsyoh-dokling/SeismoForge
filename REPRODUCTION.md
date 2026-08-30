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
~/venvs/seismoforge/bin/pip install numpy openseespy anthropic
```

`anthropic` is only needed for the LLM driver; the baseline, the scripted
driver, and the evaluation run fully offline.

All commands below run from the repository root:

```bash
PY=~/venvs/seismoforge/bin/python
```

## 2. Data

No downloads and no external datasets. The 10 project briefs under `briefs/`
are the evaluation cases; every ground-motion record is synthesized
deterministically from the brief itself (same brief -> same suite, byte for
byte), so all results are reproducible from this repository alone.

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

## 5. LLM modes

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

## 6. Design-center GUI (optional, same engine)

```bash
$PY gui/server.py --port 8765
```

Open http://127.0.0.1:8765. Load an example brief (or write your own with the
labelled datasheet lines), pick "Offline verified engine" (no key) or "LLM
design agent" (paste your Anthropic API key - it is held in memory only), and
press "Forge the design". The page shows the live run log, the verdict
banner, the acceptance table, and the combined engineering conclusion. GUI
runs write their deliverables under `outputs/gui/<run-id>/`.

## 7. Self-tests

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
- LLM driver: pay-per-use on the Anthropic API.
