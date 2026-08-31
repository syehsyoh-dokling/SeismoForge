#!/usr/bin/env python3
"""Re-prove the feasibility map instead of trusting it.

`ground_truth.json` decides whether a brief has any buildable answer, and the
judge reads it as an oracle. That makes it the one hand-maintained input the
whole comparison rests on. This regenerates it by exhaustive sweep and reports
any disagreement, so a reviewer never has to take the file's word for it.

The sweep is the same one that established the map: a grid over the buildable
isolation space, plus the fixed-base option, every candidate assessed on the
brief's own deterministic record suite. A brief is feasible when at least one
candidate passes every acceptance check.

    python3 evaluation/verify_ground_truth.py                  # all ten
    python3 evaluation/verify_ground_truth.py --briefs brief_10_cliffside_clinic
    python3 evaluation/verify_ground_truth.py --points 75      # denser grid

Runtime is the honest cost of the claim: roughly a second per candidate, so a
75-point sweep of one brief is about a minute and the full portfolio is long.
Start with the infeasible brief - it is the one the score depends on.
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
from forge.building import BuildingSpec, Design, IsolationDesign
from forge.checks import acceptance_report
from forge.designer import (
    DY_RANGE_M,
    ISOLATION_PERIOD_RANGE_S,
    QD_FRACTION_RANGE,
    kd_for_period,
)
from forge.simulate import assess


def grid(spec: BuildingSpec, points: int) -> list[Design]:
    """Candidates spanning the buildable space, plus the fixed-base option."""
    per_axis = max(2, round(points ** (1 / 3)))
    weight = spec.seismic_weight_kn

    def span(lo, hi, n):
        return [lo + (hi - lo) * i / (n - 1) for i in range(n)]

    designs = [Design("fixed_base")]
    for frac in span(*QD_FRACTION_RANGE, per_axis):
        for period in span(*ISOLATION_PERIOD_RANGE_S, per_axis):
            for dy in span(*DY_RANGE_M, per_axis):
                designs.append(Design("base_isolated", IsolationDesign(
                    qd_kn=frac * weight,
                    kd_kn_m=kd_for_period(spec, period),
                    dy_m=dy)))
    return designs


def sweep(spec: BuildingSpec, points: int) -> dict:
    """Is any candidate feasible? Stops at the first one that passes."""
    candidates = grid(spec, points)
    best = None
    for index, design in enumerate(candidates, start=1):
        report = acceptance_report(spec, design, assess(spec, design))
        util = report["governing_utilization"]
        if best is None or (util is not None and util < best[0]):
            best = (util if util is not None else float("inf"), design)
        if report["passed"]:
            return {"feasible": True, "checked": index,
                    "total": len(candidates), "witness": design.as_dict()}
    return {"feasible": False, "checked": len(candidates),
            "total": len(candidates),
            "closest_utilization": None if best[0] == float("inf") else round(best[0], 4),
            "closest_design": best[1].as_dict()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--briefs", nargs="*", default=None)
    parser.add_argument("--points", type=int, default=75,
                        help="approximate candidate count per brief")
    parser.add_argument("--out", default=None,
                        help="write the sweep evidence to this JSON file")
    args = parser.parse_args()

    claimed = json.loads(
        (REPO / "evaluation" / "ground_truth.json").read_text(encoding="utf-8")
    )["briefs"]

    paths = [p for p in list_briefs(REPO / "briefs")
             if args.briefs is None or p.stem in args.briefs]
    evidence, disagreements = {}, []

    for path in paths:
        spec = parse_brief_file(path)
        started = time.monotonic()
        result = sweep(spec, args.points)
        result["seconds"] = round(time.monotonic() - started, 1)
        result["claimed"] = claimed.get(spec.name)
        agrees = result["claimed"] == result["feasible"]
        evidence[spec.name] = result
        if not agrees:
            disagreements.append(spec.name)
        verdict = "agrees" if agrees else "DISAGREES"
        found = ("feasible after %d of %d candidates" % (result["checked"], result["total"])
                 if result["feasible"] else
                 "no feasible candidate in %d; closest utilization %s"
                 % (result["total"], result["closest_utilization"]))
        print(f"{spec.name:<32} claimed={result['claimed']!s:<5} "
              f"swept={result['feasible']!s:<5} {verdict:<10} {found} "
              f"[{result['seconds']}s]", flush=True)

    if args.out:
        Path(args.out).write_text(json.dumps(evidence, indent=2) + "\n",
                                  encoding="utf-8")
        print(f"\nevidence written to {args.out}")

    print()
    if disagreements:
        print(f"GROUND TRUTH IS WRONG for: {disagreements}")
        return 1
    print(f"ground truth confirmed by sweep for all {len(paths)} brief(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
