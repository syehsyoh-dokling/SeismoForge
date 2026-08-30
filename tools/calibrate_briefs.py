"""Calibrate the 10 evaluation briefs: baseline vs policy outcome per brief."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forge.building import BuildingSpec, Site
from forge.checks import acceptance_report
from forge.designer import clamp, rule_of_thumb
from forge.policy import forge_design
from forge.simulate import assess

SPECS = [
    BuildingSpec("coastal_hospital", "hospital", 5, 550, 450_000, 3.6,
                 Site(0.32, 1.1, 25.0, records=3), 0.75),
    BuildingSpec("valley_office", "office", 8, 600, 380_000, 3.4,
                 Site(0.25, 0.7, 22.0, records=3), 0.55),
    BuildingSpec("hillside_warehouse", "warehouse", 2, 400, 150_000, 4.5,
                 Site(0.15, 0.5, 20.0, records=3), 0.35),
    BuildingSpec("metro_datacenter", "data_center", 3, 800, 500_000, 4.0,
                 Site(0.28, 0.9, 24.0, records=3), 0.60),
    BuildingSpec("riverside_school", "school", 4, 480, 300_000, 3.5,
                 Site(0.30, 1.0, 24.0, records=3), 0.60),
    BuildingSpec("downtown_residential", "residential", 12, 650, 550_000, 3.0,
                 Site(0.26, 0.8, 22.0, records=3), 0.50),
    BuildingSpec("plains_office", "office", 6, 580, 320_000, 3.5,
                 Site(0.18, 0.6, 20.0, records=3), 0.45),
    BuildingSpec("lakeside_hospital", "hospital", 3, 500, 420_000, 3.6,
                 Site(0.22, 0.8, 22.0, records=3), 0.55),
    BuildingSpec("port_warehouse", "warehouse", 3, 450, 200_000, 4.2,
                 Site(0.24, 0.9, 23.0, records=3), 0.45),
    BuildingSpec("cliffside_clinic", "hospital", 6, 700, 400_000, 3.6,
                 Site(0.38, 1.3, 28.0, records=3), 0.40),
]


def main() -> None:
    for spec in SPECS:
        started = time.monotonic()
        baseline_design = clamp(rule_of_thumb(spec), spec)
        baseline_report = acceptance_report(spec, baseline_design, assess(spec, baseline_design))
        result = forge_design(spec, assess)
        wall = time.monotonic() - started
        print(
            f"{spec.name:22s} baseline[{baseline_design.system:13s}]="
            f"{'PASS' if baseline_report['passed'] else 'fail':4s} "
            f"agent={'PASS' if result['report']['passed'] else 'FAIL':4s} "
            f"sims={result['simulations']:2d} "
            f"gov={result['report']['governing_check']}"
            f"={result['report']['governing_utilization']:.2f} "
            f"({wall:.1f}s)"
        )
        if not result["report"]["passed"]:
            print(f"    agent failed checks: {result['report']['failed_checks']}")


if __name__ == "__main__":
    main()
