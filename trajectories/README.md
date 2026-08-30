# Agent trajectories

Every SeismoForge run writes a trajectory here, whatever started it - the CLI,
the design-center GUI, or the evaluation harness. They all enter through
`agent/session.py`, so these files are the record of the same code path the
measured results come from, not of a separate demo.

Each run produces two files with the same stem:

- **`.jsonl`** - one JSON object per event, in order. This is the machine record.
- **`.md`** - the same events rendered for reading, with timestamps.

## What is in each file

| File | Mode | Agents involved | Briefs | Design evaluations | Model | Tokens (in / out) | Wall |
|---|---|---|---|---:|---|---:|---:|
| `trajectory_offline.{jsonl,md}` | `offline` | design agent only (scripted policy) | 10 | 110 | none | none | 38.2 s |
| `trajectory_assisted.{jsonl,md}` | `assisted` | **brief intake agent** + scripted policy | 10 | 110 | `gpt-5.5` | 8,421 / 2,081 | 70.6 s |
| `trajectory_agent.{jsonl,md}` | `agent` | **brief intake agent** + **design agent** | 10 | 67 | `gpt-5.5` | 518,386 / 17,272 | 337.1 s |
| `gui/<run-id>.{jsonl,md}` | whichever the GUI ran | as above | 1 | varies | as above | as above | varies |

The committed GUI trajectory is an `offline` run of the coastal hospital brief:
19 design evaluations, the same 19 the CLI performs for that brief.

The wall times above are the runs' own, measured inside the session. The
figures in `evaluation/results.md` are a few tenths of a second longer because
the harness times the whole subprocess, interpreter startup included. Both are
correct at their own scope.

## The two agents, and where their instructions live

The brief in `agent/` shapes both of them, and both are visible in these files:

| Agent | Instructions | Its job | Appears in |
|---|---|---|---|
| **Brief intake agent** | `agent/intake_prompt.md` | Read a free-prose brief and extract the nine engineering parameters, each quoted from the source text | `assisted`, `agent` |
| **Design agent** | `agent/system_prompt.md` | Choose the structural system, walk the design space, write the engineering narrative | `agent` only |

In `offline` mode neither is used: a written policy drives the same nine tools.
That run is included because it is the reproducible baseline for the headline
result, and because the tool responses in it are identical in shape.

## What to look for

**The intake agent's source lock** - `assisted` and `agent`. Find an
`intake_start` event, then the `submit_brief_fields` tool call after it. Each
extracted field carries the exact phrase of the brief it came from, and any
unit conversion. A worked example from `trajectory_assisted`:

```
"regional acute-care hospital"   -> occupancy = hospital
"five storeys above grade"       -> n_stories = 5
"7,848 kN of seismic weight"     -> floor_mass_t = 800   (converted, /9.81)
```

An `intake_retry` event, if present, is the source lock rejecting an extraction
whose quote was not found in the brief, and handing it back with that reason.
The following `intake_validated` event carries the spec the deterministic
parser accepted - the model's reading never bypasses it.

**The evidence lock** - every mode. Find the `write_report` tool call near the
end of a brief. It re-simulates the submitted design before writing, and its
result is an error rather than a file if the verdict contradicts the evidence.
The `verify_output` call after it checks the finished deliverable again.

**The search actually happening** - every mode. `simulate_design` calls carry a
`stage` of `rule_of_thumb`, `screen`, or `refine`, and their results carry every
acceptance check with its demand and limit. Reading them in order shows the
design space being walked.

**Why full agency was not adopted** - compare the last two rows of the table.
The design agent reached the same 10/10 with **fewer** simulations than the
scripted policy - 67 against 110 - so it did search more economically in
simulation count. But each simulation costs about a third of a second, while
the conversation that produced those choices cost 62x the input tokens. The
scarce resource here was context, not compute.

## Regenerating them

From a clean checkout, with `$PY` as in [REPRODUCTION.md](../REPRODUCTION.md):

```bash
$PY agent/run_agent.py --mode offline
```

```bash
$PY agent/run_agent.py --mode assisted --brief-dir briefs_prose --model gpt-5.5
```

```bash
$PY agent/run_agent.py --mode agent --brief-dir briefs_prose --model gpt-5.5
```

The `offline` command needs no API key. The other two read
`OPENAI_API_KEY` or `ANTHROPIC_API_KEY` from the environment, and accept
`--provider` to be explicit.

GUI runs write themselves here automatically, under `gui/<run-id>`.

## Event kinds

| Kind | Meaning |
|---|---|
| `session_start`, `session_complete` | A single-brief GUI session opening and closing |
| `intake_start` | The brief intake agent beginning, with its model and instruction file |
| `tool_call`, `tool_result` | One tool invoked, and what it answered |
| `tool_error` | A tool raised; the driver sees the message and continues or stops |
| `intake_retry` | The source lock rejected an extraction and fed the reason back |
| `intake_validated` | The extraction passed the deterministic parser; carries the spec |
| `llm_start` | The design agent beginning its tool loop for one brief |
| `assistant_text` | Prose the design agent wrote |
| `verification` | The independent check of a written deliverable |
| `brief_complete`, `run_complete` | One brief finished, and the whole portfolio finished |
| `usage` | Token counts and the model that produced them |

Events carrying `"agent": "brief_intake"` belong to the intake agent; the rest
belong to the design agent or to the scripted policy driving the same tools.
