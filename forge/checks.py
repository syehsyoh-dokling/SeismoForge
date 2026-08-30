"""Acceptance checks: the deterministic pass/fail gate every design faces.

The same checks are applied to the baseline and the agent, and re-applied by
the evaluation harness - a design "passes" only if the full record suite
converges and every limit holds on the suite envelope.
"""

from __future__ import annotations

from typing import Any

from .building import RESIDUAL_LIMIT_M, BuildingSpec, Design


def acceptance_report(spec: BuildingSpec, design: Design, assessment: dict[str, Any]) -> dict[str, Any]:
    envelope = assessment["envelope"]
    limits = spec.limits
    checks: list[dict[str, Any]] = []

    def add(name: str, value: float, limit: float, satisfied: bool, note: str = "") -> None:
        checks.append(
            {
                "check": name,
                "value": value,
                "limit": limit,
                "satisfied": bool(satisfied),
                "utilization": (value / limit) if limit else None,
                **({"note": note} if note else {}),
            }
        )

    add(
        "all_records_converged",
        1.0 if assessment["all_converged"] else 0.0,
        1.0,
        assessment["all_converged"],
        "every record in the suite must complete under the convergence test",
    )
    add("peak_drift_ratio", envelope["peak_drift_ratio"], limits["peak_drift_ratio"],
        envelope["peak_drift_ratio"] <= limits["peak_drift_ratio"])
    add("peak_floor_accel_g", envelope["peak_floor_accel_g"], limits["peak_floor_accel_g"],
        envelope["peak_floor_accel_g"] <= limits["peak_floor_accel_g"])
    add("base_shear_coeff", envelope["base_shear_coeff"], limits["base_shear_coeff"],
        envelope["base_shear_coeff"] <= limits["base_shear_coeff"])
    if design.system == "base_isolated":
        add("peak_isolator_disp_m", envelope["peak_isolator_disp_m"], spec.moat_clearance_m,
            envelope["peak_isolator_disp_m"] <= spec.moat_clearance_m,
            "isolator travel must stay inside the moat clearance")
        add("residual_disp_m", envelope["residual_disp_m"], RESIDUAL_LIMIT_M,
            envelope["residual_disp_m"] <= RESIDUAL_LIMIT_M,
            "the building must recentre after the event")

    failed = [c for c in checks if not c["satisfied"]]
    governing = max(
        (
            c for c in checks
            if c["utilization"] is not None and c["check"] != "all_records_converged"
        ),
        key=lambda c: c["utilization"],
        default=None,
    )
    return {
        "passed": not failed,
        "checks": checks,
        "failed_checks": [c["check"] for c in failed],
        "governing_check": governing["check"] if governing else None,
        "governing_utilization": governing["utilization"] if governing else None,
    }
