#!/usr/bin/env python3
"""SeismoForge agent runner.

Two drivers over the identical tool layer:

- ``--driver llm``      Claude-powered design agent (Anthropic SDK, manual
                        tool loop). Requires ANTHROPIC_API_KEY or an active
                        `ant auth` profile.
- ``--driver scripted`` Deterministic policy through the same tools: no API
                        key, no network. Offline reproduction path.

Usage:
    python3 agent/run_agent.py --driver scripted
    python3 agent/run_agent.py --driver llm --briefs brief_01_coastal_hospital
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

from tools import TOOL_DEFINITIONS, ForgeTools, dispatch  # noqa: E402
from trajectory import TrajectoryLogger  # noqa: E402

DEFAULT_MODEL = "claude-opus-5"
MAX_TURNS_PER_BRIEF = 30
PRICE_IN_PER_MTOK = 5.00
PRICE_OUT_PER_MTOK = 25.00


def _call_tool(tools: ForgeTools, log: TrajectoryLogger, name: str, tool_input: dict) -> tuple[str, bool]:
    log.event("tool_call", name=name, input=tool_input)
    try:
        result = dispatch(tools, name, tool_input)
    except Exception as error:
        log.event("tool_error", name=name, error=f"{type(error).__name__}: {error}")
        return f"{type(error).__name__}: {error}", True
    log.event("tool_result", name=name, result=result)
    return json.dumps(result, default=str), False


# ----------------------------------------------------------------------
# Scripted driver: rule-of-thumb -> coarse screen -> refine, per brief.


def run_scripted(tools: ForgeTools, log: TrajectoryLogger, briefs: list[str]) -> dict:
    def call(name: str, **tool_input):
        content, is_error = _call_tool(tools, log, name, tool_input)
        if is_error:
            raise RuntimeError(f"tool {name} failed: {content}")
        return json.loads(content)

    portfolio = {}
    for brief in briefs:
        call("read_brief", brief=brief)
        call("parse_brief", brief=brief)
        design = call("propose_rule_of_thumb", brief=brief)
        outcome = call("simulate_design", brief=brief, design=design)
        design = outcome["design_as_clamped"]
        best = (design, outcome)

        def utilization(entry: dict) -> float:
            values = [
                c["utilization"] for c in entry["checks"]
                if c["utilization"] is not None
                and c["check"] != "all_records_converged"
            ]
            return max(values) if values else float("inf")

        if not outcome["passed"] and design["system"] == "base_isolated":
            for candidate in call("candidate_designs", brief=brief):
                candidate = {k: candidate[k] for k in ("system", "isolation")}
                candidate_outcome = call("simulate_design", brief=brief, design=candidate)
                if utilization(candidate_outcome) < utilization(best[1]):
                    best = (candidate_outcome["design_as_clamped"], candidate_outcome)
            design, outcome = best

        iterations = 0
        while not outcome["passed"] and iterations < 8:
            suggestion = call("suggest_refinement", brief=brief, design=design)
            if not suggestion.get("suggestion"):
                break
            design = suggestion["suggestion"]
            outcome = call("simulate_design", brief=brief, design=design)
            design = outcome["design_as_clamped"]
            if utilization(outcome) < utilization(best[1]):
                best = (design, outcome)
            iterations += 1
        if not outcome["passed"]:
            design, outcome = best

        verdict = "proceed" if outcome["passed"] else "not_buildable_within_brief"
        notes = (
            f"Governing check: {outcome['governing_check']} at utilization "
            f"{outcome['governing_utilization']:.2f}."
        )
        written = call(
            "write_report", brief=brief, design=design, verdict=verdict,
            engineer_notes=notes,
        )
        verification = call("verify_output", brief=brief)
        if not verification["ok"]:
            raise RuntimeError(f"{brief}: verification failed: {verification['problems']}")
        portfolio[brief] = {
            "verdict": verdict,
            "system": design["system"],
            "governing_check": outcome["governing_check"],
            "governing_utilization": outcome["governing_utilization"],
            "passed": outcome["passed"],
        }
        log.event("policy", note=f"{brief}: {portfolio[brief]}")
    return {"portfolio": portfolio}


# ----------------------------------------------------------------------
# LLM driver: Claude drives the same tools, one conversation per brief.


def run_llm(tools: ForgeTools, log: TrajectoryLogger, briefs: list[str], model: str) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    system_prompt = (AGENT_DIR / "system_prompt.md").read_text(encoding="utf-8")
    usage = {"input_tokens": 0, "output_tokens": 0}
    portfolio: dict[str, str] = {}

    def _create(msgs: list[dict]):
        try:
            return client.beta.messages.create(
                model=model, max_tokens=16000, system=system_prompt,
                tools=TOOL_DEFINITIONS, messages=msgs,
                betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            )
        except (TypeError, anthropic.BadRequestError):
            return client.messages.create(
                model=model, max_tokens=16000, system=system_prompt,
                tools=TOOL_DEFINITIONS, messages=msgs,
            )

    for brief in briefs:
        messages: list[dict] = [
            {
                "role": "user",
                "content": (
                    f"Forge the prototype design for brief {brief!r}: follow "
                    "the workflow, write the report, verify it, then give me "
                    "the one-paragraph summary."
                ),
            }
        ]
        final_text = ""
        for _turn in range(MAX_TURNS_PER_BRIEF):
            response = _create(messages)
            usage["input_tokens"] += response.usage.input_tokens
            usage["output_tokens"] += response.usage.output_tokens
            if response.stop_reason == "refusal":
                log.event("refusal", brief=brief,
                          detail=str(getattr(response, "stop_details", None)))
                break
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    log.event("assistant_text", text=block.text)
                    final_text = block.text
            tool_blocks = [b for b in response.content if b.type == "tool_use"]
            if response.stop_reason != "tool_use" or not tool_blocks:
                break
            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in tool_blocks:
                content, is_error = _call_tool(tools, log, block.name, dict(block.input))
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": content,
                        **({"is_error": True} if is_error else {}),
                    }
                )
            messages.append({"role": "user", "content": results})
        portfolio[brief] = final_text
    cost = (
        usage["input_tokens"] * PRICE_IN_PER_MTOK
        + usage["output_tokens"] * PRICE_OUT_PER_MTOK
    ) / 1_000_000
    log.event("usage", **usage, estimated_cost_usd=round(cost, 4))
    return {"portfolio": portfolio, "usage": usage, "estimated_cost_usd": round(cost, 4)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--driver", choices=("llm", "scripted"), default="llm")
    parser.add_argument("--out", default=str(AGENT_DIR.parent / "outputs" / "agent"))
    parser.add_argument("--briefs", nargs="*", default=None,
                        help="brief names (default: all briefs)")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--trajectory-dir",
                        default=str(AGENT_DIR.parent / "trajectories"))
    args = parser.parse_args()

    tools = ForgeTools(Path(args.out))
    briefs = args.briefs or tools.list_briefs()
    # Trajectories live outside the deliverable output tree on purpose: the
    # agent's scratch must never contaminate what the client receives.
    log = TrajectoryLogger(Path(args.trajectory_dir) / f"trajectory_{args.driver}.jsonl")

    started = time.monotonic()
    if args.driver == "llm":
        summary = run_llm(tools, log, briefs, args.model)
    else:
        summary = run_scripted(tools, log, briefs)
    wall = round(time.monotonic() - started, 1)
    log.event("run_complete", wall_time_sec=wall)
    log.render_markdown(
        Path(args.trajectory_dir) / f"trajectory_{args.driver}.md",
        f"SeismoForge trajectory ({args.driver} driver)",
    )
    print(json.dumps({"driver": args.driver, "wall_time_sec": wall, **summary},
                     indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
