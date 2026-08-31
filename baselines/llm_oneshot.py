#!/usr/bin/env python3
"""The other baseline: ask a general assistant directly, and judge the answer.

`oneshot.py` is a rule-of-thumb script - what a competent engineer writes down
before analysis. This is the other way people actually reach for an answer
today: describe the building to a capable model and ask it to size the system.

The prompt is deliberately generous. The model is given the full brief, the
acceptance limits it must satisfy, the meaning of every design parameter, and
the buildable range of each. It is asked for a verdict as well as a design.
Nothing is withheld that a well-prompted assistant would have.

What it is not given is a simulator - which is the point. Its answer is then
handed to the same judge that scores every other system: re-simulate the
submitted design, and check the verdict against the evidence.

Usage:
    python3 baselines/llm_oneshot.py [--out outputs/baseline_llm] [--model gpt-5.5]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "agent"))

from forge.brief_parser import list_briefs, parse_brief_file  # noqa: E402
from forge.building import RESIDUAL_LIMIT_M, BuildingSpec  # noqa: E402
from forge.designer import (  # noqa: E402
    DY_RANGE_M,
    ISOLATION_PERIOD_RANGE_S,
    QD_FRACTION_RANGE,
    kd_for_period,
)

SYSTEM_PROMPT = """\
You are a structural engineer sizing seismic protection at concept stage. You \
will be given a project brief and the performance limits the design must \
satisfy. Choose the structural system and, if isolated, size the lead-rubber \
isolation layer.

Answer with your best engineering judgment. You have no simulator; do the \
sizing the way an experienced engineer would before analysis."""


def submit_tool(spec: BuildingSpec) -> dict:
    # Quote the range inwards. A bound rounded outwards would invite an answer
    # the judge then rejects for being out of bounds - the model would be
    # failed for obeying us.
    weight = spec.seismic_weight_kn
    qd_lo = math.ceil(QD_FRACTION_RANGE[0] * weight)
    qd_hi = math.floor(QD_FRACTION_RANGE[1] * weight)
    kd_lo = math.ceil(kd_for_period(spec, ISOLATION_PERIOD_RANGE_S[1]))
    kd_hi = math.floor(kd_for_period(spec, ISOLATION_PERIOD_RANGE_S[0]))
    return {
        "name": "submit_design",
        "description": "Submit the concept design and the verdict for this brief.",
        "input_schema": {
            "type": "object",
            "properties": {
                "system": {
                    "type": "string",
                    "enum": ["fixed_base", "base_isolated"],
                    "description": "Conventional frame, or lead-rubber base isolation.",
                },
                "qd_kn": {
                    "type": "number",
                    "description": (
                        "Characteristic (lead) strength in kN. Buildable range for "
                        f"this building: {qd_lo:,} to {qd_hi:,} kN "
                        f"({QD_FRACTION_RANGE[0]:.0%} to {QD_FRACTION_RANGE[1]:.0%} "
                        "of seismic weight). Stay inside it. Omit for fixed_base."
                    ),
                },
                "kd_kn_m": {
                    "type": "number",
                    "description": (
                        "Post-yield (rubber) stiffness in kN/m. Buildable range: "
                        f"{kd_lo:,} to {kd_hi:,} kN/m, which is an isolated period "
                        f"of {ISOLATION_PERIOD_RANGE_S[1]} down to "
                        f"{ISOLATION_PERIOD_RANGE_S[0]} s. Stay inside it. "
                        "Omit for fixed_base."
                    ),
                },
                "dy_m": {
                    "type": "number",
                    "description": (
                        "Yield displacement in metres. Buildable range: "
                        f"{DY_RANGE_M[0]} to {DY_RANGE_M[1]} m. Omit for fixed_base."
                    ),
                },
                "verdict": {
                    "type": "string",
                    "enum": ["proceed", "not_buildable_within_brief"],
                    "description": (
                        "'proceed' if your design meets every limit; "
                        "'not_buildable_within_brief' if no buildable design can."
                    ),
                },
                "reasoning": {
                    "type": "string",
                    "description": "One paragraph explaining the sizing.",
                },
            },
            "required": ["system", "verdict", "reasoning"],
            "additionalProperties": False,
        },
    }


def request(spec: BuildingSpec, brief_text: str) -> str:
    limits = spec.limits
    return (
        f"{brief_text}\n\n"
        "--- PERFORMANCE LIMITS THIS DESIGN MUST SATISFY ---\n"
        f"peak interstorey drift ratio   <= {limits['peak_drift_ratio']}\n"
        f"peak floor acceleration        <= {limits['peak_floor_accel_g']} g\n"
        f"base shear coefficient (V/W)   <= {limits['base_shear_coeff']}\n"
        f"peak isolator displacement     <= {spec.moat_clearance_m} m "
        "(the available moat clearance)\n"
        f"residual isolator displacement <= {RESIDUAL_LIMIT_M} m "
        "(the building must recentre)\n\n"
        "Demands are envelopes over a five-record suite of site-consistent "
        "nonlinear response-history analyses.\n\n"
        "Submit your design and verdict."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(REPO / "outputs" / "baseline_llm"))
    parser.add_argument("--model", default=None)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--brief-dir", default=str(REPO / "briefs_prose"))
    args = parser.parse_args()

    from llm import estimate_cost, open_conversation

    out_root = Path(args.out)
    brief_dir = Path(args.brief_dir)
    usage = {"input_tokens": 0, "output_tokens": 0}
    model_used = ""
    started = time.monotonic()

    for path in list_briefs(REPO / "briefs"):
        spec = parse_brief_file(path)
        brief_text = (brief_dir / f"{spec.name}.md").read_text(encoding="utf-8")
        conversation = open_conversation(
            system=SYSTEM_PROMPT,
            tools=[submit_tool(spec)],
            model=args.model,
            provider=args.provider,
            max_tokens=4000,
            force_tool="submit_design",
        )
        model_used = conversation.model
        reply = conversation.start(request(spec, brief_text))
        for key in usage:
            usage[key] += conversation.usage[key]

        if not reply.tool_calls:
            print(f"{spec.name}: model returned no design")
            continue
        answer = reply.tool_calls[0].arguments
        isolated = answer.get("system") == "base_isolated"
        design = {
            "system": answer.get("system", "fixed_base"),
            "isolation": {
                "qd_kn": float(answer.get("qd_kn", 0.0)),
                "kd_kn_m": float(answer.get("kd_kn_m", 0.0)),
                "dy_m": float(answer.get("dy_m", 0.0)),
            } if isolated else None,
        }

        out_dir = out_root / spec.name
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "design.json").write_text(json.dumps({
            "brief": spec.name,
            "spec": spec.as_dict(),
            "design": design,
            "verdict": answer.get("verdict", "proceed"),
            "basis": f"one-shot answer from {conversation.model}; not simulation-verified",
            "reasoning": answer.get("reasoning", ""),
            "simulations": 0,
        }, indent=2) + "\n", encoding="utf-8")
        (out_dir / "design_report.md").write_text("\n".join([
            f"# Direct-model design note - {spec.name.replace('_', ' ')}",
            "",
            f"**Verdict: {answer.get('verdict', '?').upper()}** "
            f"(one-shot answer from {conversation.model}, no simulation)",
            "",
            f"- System: {design['system']}",
            *([f"- Qd = {design['isolation']['qd_kn']:,.0f} kN",
               f"- Kd = {design['isolation']['kd_kn_m']:,.0f} kN/m",
               f"- Dy = {design['isolation']['dy_m'] * 1000:.0f} mm"] if isolated else []),
            "",
            answer.get("reasoning", ""),
            "",
            "*No response-history verification was performed. Every number above "
            "is the model's judgment, not a simulation output.*",
            "",
        ]), encoding="utf-8")
        print(f"{spec.name}: {design['system']}, verdict {answer.get('verdict')}")

    wall = round(time.monotonic() - started, 1)
    cost = estimate_cost(model_used, usage)
    print(json.dumps({
        "model": model_used,
        "wall_time_sec": wall,
        "usage": usage,
        "estimated_cost_usd": cost,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
