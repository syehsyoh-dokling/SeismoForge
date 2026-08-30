"""Design generation: the rule-of-thumb starting point and failure-driven
refinement moves.

``rule_of_thumb`` is what a competent engineer writes down before any
simulation - and it is exactly what the SeismoForge *baseline* submits
unverified. The agent starts from the same point but then closes the loop:
simulate, read the failed checks, apply a targeted move, and re-test.
"""

from __future__ import annotations

import math
from typing import Any

from .building import G, BuildingSpec, Design, IsolationDesign

TARGET_ISOLATION_PERIOD_S = 2.8
QD_WEIGHT_FRACTION = 0.06
DY_DEFAULT_M = 0.02

# Bounds keep every design physically buildable (available bearing hardware).
QD_FRACTION_RANGE = (0.02, 0.14)
ISOLATION_PERIOD_RANGE_S = (1.8, 4.5)
DY_RANGE_M = (0.008, 0.05)


def isolation_period(spec: BuildingSpec, kd_kn_m: float) -> float:
    mass_kg = spec.total_mass_t * 1000.0
    return 2.0 * math.pi * math.sqrt(mass_kg / (kd_kn_m * 1000.0))


def kd_for_period(spec: BuildingSpec, period_s: float) -> float:
    mass_kg = spec.total_mass_t * 1000.0
    return mass_kg * (2.0 * math.pi / period_s) ** 2 / 1000.0


def fixed_base_period(spec: BuildingSpec) -> float:
    """First-mode estimate of the fixed-base frame (uniform shear building)."""
    mass_kg = spec.floor_mass_t * 1000.0
    k = spec.story_stiffness_kn_m * 1000.0
    n = spec.n_stories
    # First-mode frequency of a uniform shear building.
    omega = 2.0 * math.sqrt(k / mass_kg) * math.sin(math.pi / (2.0 * (2.0 * n + 1)))
    return 2.0 * math.pi / omega


def rule_of_thumb(spec: BuildingSpec) -> Design:
    """Pre-simulation engineering judgment: system choice + initial sizing."""
    demanding_site = spec.site.pga_g >= 0.25 or spec.site.soil_period_sec >= 1.0
    strict_occupancy = spec.limits["peak_floor_accel_g"] <= 0.45
    if not (demanding_site or strict_occupancy):
        return Design(system="fixed_base")
    weight = spec.seismic_weight_kn
    return Design(
        system="base_isolated",
        isolation=IsolationDesign(
            qd_kn=QD_WEIGHT_FRACTION * weight,
            kd_kn_m=kd_for_period(spec, TARGET_ISOLATION_PERIOD_S),
            dy_m=DY_DEFAULT_M,
        ),
    )


def clamp(design: Design, spec: BuildingSpec) -> Design:
    if design.system == "fixed_base":
        return design
    iso = design.isolation
    weight = spec.seismic_weight_kn
    qd = min(max(iso.qd_kn, QD_FRACTION_RANGE[0] * weight), QD_FRACTION_RANGE[1] * weight)
    kd_lo = kd_for_period(spec, ISOLATION_PERIOD_RANGE_S[1])
    kd_hi = kd_for_period(spec, ISOLATION_PERIOD_RANGE_S[0])
    kd = min(max(iso.kd_kn_m, kd_lo), kd_hi)
    dy = min(max(iso.dy_m, DY_RANGE_M[0]), DY_RANGE_M[1])
    return Design(system="base_isolated", isolation=IsolationDesign(qd, kd, dy))


def refine(spec: BuildingSpec, design: Design, report: dict[str, Any]) -> Design | None:
    """One failure-driven design move; None when no move is available.

    The moves encode the coupled physics of an isolated system:
    - too much drift / floor acceleration -> the isolation layer is too stiff
      or too strong: lengthen the period, trim Qd;
    - isolator travel over the moat -> more energy dissipation (raise Qd) or
      a stiffer rubber (shorten the period);
    - residual offset over the limit -> more restoring force per strength:
      stiffer rubber and smaller yield displacement;
    - a fixed-base frame failing drift/acceleration -> switch to isolation.
    """
    failed = set(report.get("failed_checks", ()))
    if not failed:
        return None
    if design.system == "fixed_base":
        return clamp(rule_of_thumb_isolated(spec), spec)
    iso = design.isolation
    qd, kd, dy = iso.qd_kn, iso.kd_kn_m, iso.dy_m
    if "all_records_converged" in failed:
        # Numerically hard corner: soften the nonlinearity slightly.
        dy *= 1.4
    elif "peak_floor_accel_g" in failed or "base_shear_coeff" in failed:
        # Transmitted force governs first: lengthen the period and soften the
        # yield transition before worrying about travel.
        kd *= 0.85
        dy = min(dy * 1.2, DY_RANGE_M[1])
        if "peak_isolator_disp_m" in failed:
            qd *= 1.10  # a little more dissipation to hold travel meanwhile
    elif "peak_isolator_disp_m" in failed and "residual_disp_m" in failed:
        qd *= 1.20
        kd *= 1.25
        dy *= 0.8
    elif "peak_isolator_disp_m" in failed:
        qd *= 1.25  # dissipation controls travel; leave the period alone
    elif "residual_disp_m" in failed:
        kd *= 1.30
        dy *= 0.75
    elif "peak_drift_ratio" in failed:
        qd *= 0.85
        kd *= 0.90
    else:
        return None
    candidate = clamp(
        Design(system="base_isolated", isolation=IsolationDesign(qd, kd, dy)), spec
    )
    same = (
        abs(candidate.isolation.qd_kn - iso.qd_kn) < 1e-9
        and abs(candidate.isolation.kd_kn_m - iso.kd_kn_m) < 1e-9
        and abs(candidate.isolation.dy_m - iso.dy_m) < 1e-9
    )
    return None if same else candidate


def candidate_grid(spec: BuildingSpec) -> list[Design]:
    """Coarse screening candidates over the buildable isolation space.

    Pure failure-driven local moves oscillate on this problem because the
    acceptance constraints are coupled (more dissipation lowers travel but
    raises transmitted force). A coarse screen followed by local refinement
    converges where local moves alone do not.
    """
    weight = spec.seismic_weight_kn
    designs = []
    for qd_frac in (0.05, 0.08, 0.11):
        for period in (2.4, 3.2, 4.0):
            for dy in (0.03, 0.045):
                designs.append(
                    Design(
                        system="base_isolated",
                        isolation=IsolationDesign(
                            qd_kn=qd_frac * weight,
                            kd_kn_m=kd_for_period(spec, period),
                            dy_m=dy,
                        ),
                    )
                )
    return designs


def worst_utilization(report: dict[str, Any]) -> float:
    values = [
        c["utilization"] for c in report.get("checks", ())
        if c.get("utilization") is not None
    ]
    return max(values) if values else float("inf")


def rule_of_thumb_isolated(spec: BuildingSpec) -> Design:
    weight = spec.seismic_weight_kn
    return Design(
        system="base_isolated",
        isolation=IsolationDesign(
            qd_kn=QD_WEIGHT_FRACTION * weight,
            kd_kn_m=kd_for_period(spec, TARGET_ISOLATION_PERIOD_S),
            dy_m=DY_DEFAULT_M,
        ),
    )
