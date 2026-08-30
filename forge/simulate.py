"""Nonlinear response-history simulation of a SeismoForge prototype.

Model: N-story shear frame (lumped floor masses, elastic story springs) with
an optional bilinear lead-rubber isolation layer at the base (elastic-
perfectly-plastic lead element in parallel with an elastic rubber spring).
Integration: Newmark average acceleration with Newton iteration; a
ModifiedNewton retry per step before a case is declared non-converged.

Damping: 2% Rayleigh for isolated systems (mass term on all masses,
initial-stiffness term on the story springs only - the isolator dissipates
through its own hysteresis), 5% for fixed-base systems, anchored on the first
and third model modes.

Reported response metrics per record:
- peak_isolator_disp_m     (isolated only; 0.0 for fixed base)
- peak_drift_ratio         worst interstory drift ratio over all stories
- peak_floor_accel_g       worst total floor acceleration (all floors)
- base_shear_coeff         peak base force / seismic weight
- residual_disp_m          isolator offset after a 10 s free-vibration tail
"""

from __future__ import annotations

import math
from typing import Any

import openseespy.opensees as ops

from .building import G, BuildingSpec, Design
from .motions import DT, suite, synthesize

TAIL_SEC = 10.0
METRICS = (
    "peak_isolator_disp_m",
    "peak_drift_ratio",
    "peak_floor_accel_g",
    "base_shear_coeff",
    "residual_disp_m",
)


def _build_model(spec: BuildingSpec, design: Design) -> dict[str, float]:
    """Assemble the model; returns the Rayleigh calibration actually applied."""
    ops.wipe()
    ops.model("basic", "-ndm", 1, "-ndf", 1)

    isolated = design.system == "base_isolated"
    mass_kg = spec.floor_mass_t * 1000.0

    # Node 0 is the ground. For isolated systems node 1 is the base mat
    # (carrying one floor mass as the mat + first floor package would in the
    # prototype); floors continue upward.
    ops.node(0, 0.0)
    ops.fix(0, 1)
    n_mass_nodes = spec.n_stories + (1 if isolated else 0)
    for node in range(1, n_mass_nodes + 1):
        ops.node(node, 0.0)
        ops.mass(node, mass_kg)

    story_tags = []
    next_mat = 10
    if isolated:
        iso = design.isolation
        # Forces in N, displacements in m inside the model.
        k_lead = (iso.qd_kn * 1000.0) / max(iso.dy_m, 1.0e-6)
        ops.uniaxialMaterial("ElasticPP", 1, k_lead, iso.dy_m)
        ops.uniaxialMaterial("Elastic", 2, iso.kd_kn_m * 1000.0)
        ops.element("zeroLength", 1, 0, 1, "-mat", 1, 2, "-dir", 1, 1)
        first_story_bottom = 1
    else:
        first_story_bottom = 0

    k_story = spec.story_stiffness_kn_m * 1000.0
    for story in range(spec.n_stories):
        bottom = first_story_bottom + story
        tag = next_mat + story
        ops.uniaxialMaterial("Elastic", tag, k_story)
        ops.element(
            "zeroLength", tag, bottom, bottom + 1,
            "-mat", tag, "-dir", 1, "-doRayleigh", 1,
        )
        story_tags.append(tag)

    ratio = 0.02 if isolated else 0.05
    n_modes = min(n_mass_nodes, 4)
    try:
        eigenvalues = ops.eigen("-fullGenLapack", n_modes)
        omegas = sorted(math.sqrt(v) for v in eigenvalues if v > 0.0)
    except Exception:
        omegas = []
    calibration: dict[str, float] = {"damping_ratio": ratio}
    if len(omegas) >= 2:
        low = omegas[0]
        high = omegas[min(2, len(omegas) - 1)]
        alpha_m = ratio * 2.0 * low * high / (low + high)
        beta_k = ratio * 2.0 / (low + high)
        if isolated:
            # Mass term everywhere; initial-stiffness term only on the story
            # springs so the isolator is not artificially damped.
            ops.rayleigh(alpha_m, 0.0, 0.0, 0.0)
            ops.region(
                1, "-eleOnly", *story_tags,
                "-rayleigh", alpha_m, 0.0, beta_k, 0.0,
            )
        else:
            ops.rayleigh(alpha_m, 0.0, beta_k, 0.0)
        calibration.update(
            {
                "rayleigh_alpha_m": alpha_m,
                "rayleigh_beta_k": beta_k,
                "omega_low_rad_s": low,
                "omega_high_rad_s": high,
            }
        )
    return calibration


def analyze_record(spec: BuildingSpec, design: Design, seed: int) -> dict[str, Any]:
    """Run one record through the prototype; returns metrics + convergence."""
    time, accel = synthesize(spec.site, seed)
    calibration = _build_model(spec, design)

    isolated = design.system == "base_isolated"
    n_mass_nodes = spec.n_stories + (1 if isolated else 0)
    tail_steps = int(round(TAIL_SEC / DT))
    series = list(accel) + [0.0] * tail_steps
    ops.timeSeries("Path", 1, "-dt", DT, "-values", *[float(v) for v in series])
    ops.pattern("UniformExcitation", 1, 1, "-accel", 1)
    ops.wipeAnalysis()
    ops.constraints("Plain")
    ops.numberer("Plain")
    ops.system("BandGeneral")
    ops.test("NormDispIncr", 1.0e-8, 25)
    ops.algorithm("Newton")
    ops.integrator("Newmark", 0.5, 0.25)
    ops.analysis("Transient")

    steps = len(time) - 1
    peak_iso = 0.0
    peak_drift = 0.0
    peak_accel = 0.0
    peak_base_force = 0.0
    completed = 0
    height = spec.story_height_m
    first_floor = 1 + (1 if isolated else 0)
    for index in range(steps):
        code = ops.analyze(1, DT)
        if code != 0:
            ops.algorithm("ModifiedNewton")
            code = ops.analyze(1, DT)
            ops.algorithm("Newton")
        if code != 0:
            break
        completed += 1
        disp = [ops.nodeDisp(node, 1) for node in range(n_mass_nodes + 1)]
        if isolated:
            peak_iso = max(peak_iso, abs(disp[1] - disp[0]))
            drift_pairs = range(1, n_mass_nodes)
        else:
            drift_pairs = range(0, n_mass_nodes)
        for bottom in drift_pairs:
            drift = abs(disp[bottom + 1] - disp[bottom]) / height
            peak_drift = max(peak_drift, drift)
        ground = series[index + 1]
        total_acc = [
            abs(ops.nodeAccel(node, 1) + ground)
            for node in range(first_floor, n_mass_nodes + 1)
        ]
        if isolated:
            total_acc.append(abs(ops.nodeAccel(1, 1) + ground))
        peak_accel = max(peak_accel, *total_acc)
        base_ele = 1 if isolated else 10
        peak_base_force = max(peak_base_force, abs(ops.eleForce(base_ele, 1)))

    converged = completed == steps
    residual = float("nan")
    if converged:
        for _ in range(tail_steps):
            code = ops.analyze(1, DT)
            if code != 0:
                ops.algorithm("ModifiedNewton")
                code = ops.analyze(1, DT)
                ops.algorithm("Newton")
            if code != 0:
                converged = False
                break
        if converged:
            residual = abs(ops.nodeDisp(1, 1) - ops.nodeDisp(0, 1)) if isolated else 0.0
    ops.wipe()

    weight_n = spec.seismic_weight_kn * 1000.0
    return {
        "seed": seed,
        "converged": bool(converged),
        "peak_isolator_disp_m": float(peak_iso),
        "peak_drift_ratio": float(peak_drift),
        "peak_floor_accel_g": float(peak_accel / G),
        "base_shear_coeff": float(peak_base_force / weight_n),
        "residual_disp_m": float(residual) if converged else None,
        "calibration": calibration,
    }


def assess(spec: BuildingSpec, design: Design) -> dict[str, Any]:
    """Run the full deterministic record suite; return per-record + envelope."""
    records = []
    for record in suite(spec.site):
        outcome = analyze_record(spec, design, record["seed"])
        outcome["record_id"] = record["record_id"]
        records.append(outcome)
    # A metric with no finite sample across the suite (e.g. residual offset
    # when a record never converged) has no envelope. It is reported as None,
    # not as infinity: the acceptance layer treats a missing demand as an
    # unmet check, and JSON has no representation for infinity - emitting one
    # would produce artifacts no client (or browser) can parse.
    envelope: dict[str, float | None] = {}
    for key in METRICS:
        values = [
            float(item[key]) for item in records
            if isinstance(item.get(key), (int, float)) and math.isfinite(float(item[key]))
        ]
        envelope[key] = max(values) if values else None
    return {
        "all_converged": all(item["converged"] for item in records),
        "per_record": records,
        "envelope": envelope,
        "calibration": records[0]["calibration"] if records else {},
    }
