"""Map the admissible design region for a brief by grid sweep.

Used during development to calibrate briefs, limits, and refinement moves.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forge.building import BuildingSpec, Design, IsolationDesign, Site
from forge.checks import acceptance_report
from forge.designer import kd_for_period
from forge.simulate import assess


def sweep(spec: BuildingSpec) -> None:
    weight = spec.seismic_weight_kn
    print(f"=== {spec.name}: W={weight:.0f} kN, limits={spec.limits}, moat={spec.moat_clearance_m}")
    best = []
    for qd_frac in (0.04, 0.07, 0.10, 0.13, 0.16):
        for period in (2.0, 2.5, 3.0, 3.5, 4.0):
            for dy in (0.015, 0.03):
                design = Design(
                    system="base_isolated",
                    isolation=IsolationDesign(
                        qd_kn=qd_frac * weight,
                        kd_kn_m=kd_for_period(spec, period),
                        dy_m=dy,
                    ),
                )
                assessment = assess(spec, design)
                report = acceptance_report(spec, design, assessment)
                env = assessment["envelope"]
                tag = "PASS" if report["passed"] else "    "
                print(
                    f"{tag} qd={qd_frac:.2f}W T={period:.1f}s dy={dy:.3f} | "
                    f"iso={env['peak_isolator_disp_m']:.3f} drift={env['peak_drift_ratio']:.4f} "
                    f"acc={env['peak_floor_accel_g']:.3f} V={env['base_shear_coeff']:.3f} "
                    f"res={env['residual_disp_m']:.4f} conv={assessment['all_converged']}"
                )
                if report["passed"]:
                    best.append((qd_frac, period, dy))
    print("passing corner count:", len(best), best[:5])


if __name__ == "__main__":
    sweep(
        BuildingSpec(
            name="cliffside_clinic",
            occupancy="hospital",
            n_stories=6,
            floor_mass_t=700.0,
            story_stiffness_kn_m=400_000.0,
            story_height_m=3.6,
            site=Site(pga_g=0.38, soil_period_sec=1.3, duration_sec=28.0, records=3),
            moat_clearance_m=0.40,
        )
    )
