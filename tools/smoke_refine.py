"""Does the failure-driven refinement loop converge on a demanding brief?"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forge.building import BuildingSpec, Site
from forge.checks import acceptance_report
from forge.designer import clamp, refine, rule_of_thumb
from forge.simulate import assess


def run(spec: BuildingSpec, max_iters: int = 15) -> None:
    design = clamp(rule_of_thumb(spec), spec)
    for iteration in range(max_iters):
        assessment = assess(spec, design)
        report = acceptance_report(spec, design, assessment)
        iso = design.isolation.as_dict() if design.isolation else None
        print(
            f"[{spec.name}] iter {iteration}: {design.system} {iso} "
            f"passed={report['passed']} failed={report['failed_checks']} "
            f"gov={report['governing_check']}={report['governing_utilization']:.2f}"
        )
        if report["passed"]:
            return
        moved = refine(spec, design, report)
        if moved is None:
            print(f"[{spec.name}] no further move available; stuck")
            return
        design = moved
    print(f"[{spec.name}] did not converge in {max_iters} iterations")


if __name__ == "__main__":
    run(
        BuildingSpec(
            name="hard_hospital",
            occupancy="hospital",
            n_stories=5,
            floor_mass_t=550.0,
            story_stiffness_kn_m=450_000.0,
            story_height_m=3.6,
            site=Site(pga_g=0.32, soil_period_sec=1.1, duration_sec=25.0, records=3),
            moat_clearance_m=0.75,
        )
    )
    run(
        BuildingSpec(
            name="mid_office",
            occupancy="office",
            n_stories=8,
            floor_mass_t=600.0,
            story_stiffness_kn_m=380_000.0,
            story_height_m=3.4,
            site=Site(pga_g=0.25, soil_period_sec=0.7, duration_sec=22.0, records=3),
            moat_clearance_m=0.55,
        )
    )
    run(
        BuildingSpec(
            name="low_warehouse",
            occupancy="warehouse",
            n_stories=2,
            floor_mass_t=400.0,
            story_stiffness_kn_m=150_000.0,
            story_height_m=4.5,
            site=Site(pga_g=0.15, soil_period_sec=0.5, duration_sec=20.0, records=3),
            moat_clearance_m=0.35,
        )
    )
