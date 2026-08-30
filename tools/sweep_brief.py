"""Sweep the design space for a parsed brief file (dev calibration)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from forge.brief_parser import parse_brief_file
from forge.building import Design, IsolationDesign
from forge.checks import acceptance_report
from forge.designer import kd_for_period
from forge.simulate import assess

spec = parse_brief_file(Path(sys.argv[1]))
weight = spec.seismic_weight_kn
print(f"=== {spec.name}: W={weight:.0f} kN, limits={spec.limits}, moat={spec.moat_clearance_m}")
passing = []
for qd_frac in (0.04, 0.06, 0.08, 0.10, 0.13):
    for period in (2.5, 3.0, 3.5, 4.0, 4.5):
        for dy in (0.02, 0.035, 0.05):
            design = Design(
                system="base_isolated",
                isolation=IsolationDesign(qd_frac * weight, kd_for_period(spec, period), dy),
            )
            report = acceptance_report(spec, design, assess(spec, design))
            env_line = " ".join(
                f"{c['check'].split('peak_')[-1]}={c['utilization']:.2f}"
                for c in report["checks"] if c["utilization"] is not None and c["check"] != "all_records_converged"
            )
            tag = "PASS" if report["passed"] else "    "
            print(f"{tag} qd={qd_frac:.2f}W T={period:.1f} dy={dy:.3f} | {env_line}")
            if report["passed"]:
                passing.append((qd_frac, period, dy))
print("passing:", len(passing), passing[:8])
