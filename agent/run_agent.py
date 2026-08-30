#!/usr/bin/env python3
"""SeismoForge CLI: run a portfolio of briefs through one design session each.

Modes differ in two independent places - who reads the brief, and who decides
which design to try next. Everything else (the 9 tools, OpenSees, the evidence
lock, the trajectory) is identical:

    offline    deterministic parser  +  scripted policy   no API key
    assisted   LLM reads free prose  +  scripted policy   API key
    agent      LLM reads free prose  +  LLM drives search API key

Usage:
    python3 agent/run_agent.py --mode offline
    python3 agent/run_agent.py --mode agent --briefs brief_01_coastal_hospital
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from llm import PROVIDERS, estimate_cost  # noqa: E402
from session import (  # noqa: E402
    MODES,
    ForgeTools,
    TrajectoryLogger,
    resolve_spec,
    run_brief,
)

# Older docs and scripts used --driver; keep them working.
DRIVER_ALIASES = {"scripted": "offline", "llm": "agent"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, default=None)
    parser.add_argument("--driver", choices=tuple(DRIVER_ALIASES), default=None,
                        help="deprecated alias: scripted -> offline, llm -> agent")
    parser.add_argument("--out", default=str(AGENT_DIR.parent / "outputs" / "agent"))
    parser.add_argument("--briefs", nargs="*", default=None,
                        help="brief names (default: all briefs)")
    parser.add_argument("--brief-dir", default=str(AGENT_DIR.parent / "briefs"),
                        help="directory of briefs to run (e.g. briefs_prose)")
    parser.add_argument("--model", default=None,
                        help="model id; default depends on the provider")
    parser.add_argument("--provider", choices=PROVIDERS, default=None,
                        help="anthropic or openai; inferred from the model or "
                             "the key in the environment when omitted")
    parser.add_argument("--trajectory-dir",
                        default=str(AGENT_DIR.parent / "trajectories"))
    parser.add_argument("--quiet", action="store_true",
                        help="suppress the per-step progress lines")
    args = parser.parse_args()

    mode = args.mode or DRIVER_ALIASES.get(args.driver or "", "offline")
    brief_dir = Path(args.brief_dir)
    tools = ForgeTools(Path(args.out), brief_dir=brief_dir)
    briefs = args.briefs or tools.list_briefs()

    # Trajectories live outside the deliverable output tree on purpose: the
    # agent's scratch must never contaminate what the client receives.
    log = TrajectoryLogger(Path(args.trajectory_dir) / f"trajectory_{mode}.jsonl")
    progress = (lambda line: None) if args.quiet else (lambda line: print(line, flush=True))

    started = time.monotonic()
    portfolio = {}
    usage = {"input_tokens": 0, "output_tokens": 0}
    models_used: set[str] = set()
    for brief in briefs:
        if mode != "offline":
            # Free-prose intake: the model reads the brief file as written and
            # the deterministic parser validates what it extracted.
            text = (brief_dir / f"{brief}.md").read_text(encoding="utf-8")
            intake: dict = {}
            tools.adopt_spec(
                brief,
                resolve_spec(text, name=brief, mode=mode, model=args.model,
                             provider=args.provider, record=intake, log=log,
                             progress=progress),
            )
            models_used.add(intake.get("model", ""))
            for key, value in intake.get("usage", {}).items():
                usage[key] = usage.get(key, 0) + value
        outcome = run_brief(tools, log, brief, mode=mode, model=args.model,
                            provider=args.provider, progress=progress)
        if outcome.get("model"):
            models_used.add(outcome["model"])
        if outcome.get("driver") == "llm":
            for key in usage:
                usage[key] += outcome.get("usage", {}).get(key, 0)
        portfolio[brief] = outcome
        log.event("brief_complete", brief=brief, mode=mode)

    wall = round(time.monotonic() - started, 1)
    summary = {"mode": mode, "wall_time_sec": wall, "portfolio": portfolio}
    if any(usage.values()):
        used_model = ", ".join(sorted(m for m in models_used if m))
        cost = estimate_cost(used_model, usage)
        summary["model"] = used_model
        summary["usage"] = usage
        if cost is None:
            summary["estimated_cost_usd"] = None
            summary["price_note"] = (
                f"no published price configured for {used_model!r}; "
                "add it to PRICES in agent/llm.py to get a cost figure"
            )
        else:
            summary["estimated_cost_usd"] = cost
        log.event("usage", **usage, model=used_model, estimated_cost_usd=cost)
    log.event("run_complete", wall_time_sec=wall)
    log.render_markdown(
        Path(args.trajectory_dir) / f"trajectory_{mode}.md",
        f"SeismoForge trajectory ({mode} mode)",
    )
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
