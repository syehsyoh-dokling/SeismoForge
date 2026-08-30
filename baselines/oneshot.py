#!/usr/bin/env python3
"""The simple baseline: one-shot rule-of-thumb design, no simulation loop.

This is the "reasonable basic way" the task is handled today: an engineer (or
a one-shot LLM prompt) writes down a textbook initial sizing and asserts it
meets the intent. No response-history verification, no iteration, no
feasibility check. The evaluation harness then simulates these designs
independently - which is exactly what a peer reviewer would do.

Usage:
    python3 baselines/oneshot.py [--out outputs/baseline]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from forge.brief_parser import list_briefs, parse_brief_file
from forge.designer import clamp, isolation_period, rule_of_thumb
from forge.report import REVIEW_NOTICE


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(REPO / "outputs" / "baseline"))
    args = parser.parse_args()
    out_root = Path(args.out)

    started = time.monotonic()
    for path in list_briefs(REPO / "briefs"):
        spec = parse_brief_file(path)
        design = clamp(rule_of_thumb(spec), spec)
        out_dir = out_root / spec.name
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "brief": spec.name,
            "spec": spec.as_dict(),
            "design": design.as_dict(),
            "verdict": "proceed",
            "basis": "rule-of-thumb sizing; not simulation-verified",
            "simulations": 0,
        }
        (out_dir / "design.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
        lines = [
            f"# Baseline design note - {spec.name.replace('_', ' ')}",
            "",
            "**Verdict: PROCEED** (rule-of-thumb basis)",
            "",
            f"- System: {design.system}",
        ]
        if design.isolation:
            iso = design.isolation
            lines += [
                f"- Qd = {iso.qd_kn:,.0f} kN "
                f"({iso.qd_kn / spec.seismic_weight_kn:.1%} of W)",
                f"- Kd = {iso.kd_kn_m:,.0f} kN/m "
                f"(target period {isolation_period(spec, iso.kd_kn_m):.2f} s)",
                f"- Dy = {iso.dy_m * 1000:.0f} mm",
            ]
        lines += [
            "",
            "Sized to standard practice targets; expected to meet the brief's "
            "performance intent. (No response-history verification performed.)",
            "",
            REVIEW_NOTICE,
            "",
        ]
        (out_dir / "design_report.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"{spec.name}: {design.system}")
    print(f"baseline wall time: {time.monotonic() - started:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
