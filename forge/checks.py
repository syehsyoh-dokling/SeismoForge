"""Acceptance checks: the deterministic pass/fail gate every design faces.

The same checks are applied to the baseline and the agent, and re-applied by
the evaluation harness - a design "passes" only if the full record suite
converges and every limit holds on the suite envelope.

A demand that the suite never produced (a non-converged record leaves no
residual offset, so the envelope carries ``None``) is an unmet check, never a
number to compare or format. The same rule covers a degenerate limit - a brief
offering 0 m of moat clearance has no meaningful utilization, but it does have
a verdict.
"""

from __future__ import annotations

import math
from typing import Any

from .building import RESIDUAL_LIMIT_M, BuildingSpec, Design


def finite(value: Any) -> float | None:
    """The value as a float when it is a usable number, otherwise None."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        if math.isfinite(number):
            return number
    return None


def _within(value: float | None, limit: float) -> bool:
    return value is not None and value <= limit


def acceptance_report(spec: BuildingSpec, design: Design, assessment: dict[str, Any]) -> dict[str, Any]:
    envelope = assessment["envelope"]
    limits = spec.limits
    checks: list[dict[str, Any]] = []

    def add(name: str, value: Any, limit: Any, satisfied: bool, note: str = "") -> None:
        demand = finite(value)
        cap = finite(limit)
        checks.append(
            {
                "check": name,
                "value": demand,
                "limit": cap,
                "satisfied": bool(satisfied),
                "utilization": (demand / cap) if (demand is not None and cap) else None,
                **({"note": note} if note else {}),
            }
        )

    def demand(key: str) -> float | None:
        return finite(envelope.get(key))

    add(
        "all_records_converged",
        1.0 if assessment["all_converged"] else 0.0,
        1.0,
        assessment["all_converged"],
        "every record in the suite must complete under the convergence test",
    )
    for key in ("peak_drift_ratio", "peak_floor_accel_g", "base_shear_coeff"):
        add(key, demand(key), limits[key], _within(demand(key), limits[key]))
    if design.system == "base_isolated":
        add("peak_isolator_disp_m", demand("peak_isolator_disp_m"), spec.moat_clearance_m,
            _within(demand("peak_isolator_disp_m"), spec.moat_clearance_m),
            "isolator travel must stay inside the moat clearance")
        add("residual_disp_m", demand("residual_disp_m"), RESIDUAL_LIMIT_M,
            _within(demand("residual_disp_m"), RESIDUAL_LIMIT_M),
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
