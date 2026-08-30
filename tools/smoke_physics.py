"""Quick physics smoke test for the SeismoForge core."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forge.building import BuildingSpec, Site
from forge.checks import acceptance_report
from forge.designer import fixed_base_period, rule_of_thumb, refine, clamp
from forge.simulate import assess


def main() -> None:
    spec = BuildingSpec(
        name="smoke_hospital",
        occupancy="hospital",
        n_stories=5,
        floor_mass_t=550.0,
        story_stiffness_kn_m=180_000.0,
        story_height_m=3.6,
        site=Site(pga_g=0.32, soil_period_sec=1.1, duration_sec=25.0, records=3),
        moat_clearance_m=0.45,
    )
    print(f"fixed-base period estimate: {fixed_base_period(spec):.3f} s")

    for label, design in (
        ("fixed_base", clamp(rule_of_thumb(spec), spec).__class__(system="fixed_base")),
        ("rule_of_thumb", clamp(rule_of_thumb(spec), spec)),
    ):
        started = time.monotonic()
        assessment = assess(spec, design)
        report = acceptance_report(spec, design, assessment)
        wall = time.monotonic() - started
        print(f"--- {label} ({design.as_dict()}) in {wall:.1f}s")
        print(json.dumps(assessment["envelope"], indent=1))
        print("passed:", report["passed"], "failed:", report["failed_checks"],
              "governing:", report["governing_check"], f"{report['governing_utilization']:.2f}")
        if label == "rule_of_thumb":
            move = refine(spec, design, report)
            print("refine move:", move.as_dict() if move else None)


if __name__ == "__main__":
    main()
