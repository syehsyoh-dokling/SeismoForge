"""End-to-end policy smoke test on three calibration briefs."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forge.building import BuildingSpec, Site
from forge.policy import forge_design
from forge.simulate import assess

SPECS = [
    BuildingSpec(
        name="hard_hospital", occupancy="hospital", n_stories=5,
        floor_mass_t=550.0, story_stiffness_kn_m=450_000.0, story_height_m=3.6,
        site=Site(pga_g=0.32, soil_period_sec=1.1, duration_sec=25.0, records=3),
        moat_clearance_m=0.75,
    ),
    BuildingSpec(
        name="mid_office", occupancy="office", n_stories=8,
        floor_mass_t=600.0, story_stiffness_kn_m=380_000.0, story_height_m=3.4,
        site=Site(pga_g=0.25, soil_period_sec=0.7, duration_sec=22.0, records=3),
        moat_clearance_m=0.55,
    ),
    BuildingSpec(
        name="low_warehouse", occupancy="warehouse", n_stories=2,
        floor_mass_t=400.0, story_stiffness_kn_m=150_000.0, story_height_m=4.5,
        site=Site(pga_g=0.15, soil_period_sec=0.5, duration_sec=20.0, records=3),
        moat_clearance_m=0.35,
    ),
]

for spec in SPECS:
    result = forge_design(spec, assess)
    stages = [f"{e['stage']}:{'P' if e['passed'] else 'f'}" for e in result["history"]]
    print(
        f"[{spec.name}] passed={result['report']['passed']} "
        f"sims={result['simulations']} design={result['design'].as_dict()} "
        f"gov={result['report']['governing_check']}={result['report']['governing_utilization']:.2f}"
    )
    print("   path:", " ".join(stages))
