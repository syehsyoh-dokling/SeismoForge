"""Design-report rendering: the client-facing deliverable per brief.

Every number in the report is taken from the simulation results passed in -
the renderer accepts no free-text numeric claims. The optional engineer notes
paragraph is prose only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .building import RESIDUAL_LIMIT_M, BuildingSpec, Design
from .checks import finite
from .designer import isolation_period
from .motions import DT, HIGHPASS_CORNER_HZ, N_HARMONICS

VERDICTS = ("proceed", "not_buildable_within_brief")

REVIEW_HEADLINE = "Concept-stage prototype study - not for construction."
REVIEW_BODY = (
    "This report is produced by an automated design agent. It must be reviewed "
    "and signed off by a licensed structural engineer before it informs any "
    "design, procurement, or construction decision. The model class, acceptance "
    "limits, and synthetic ground motions are SeismoForge's own benchmark "
    "basis, not a substitute for code-compliant analysis of a project-specific "
    "hazard."
)
REVIEW_NOTICE = f"> **{REVIEW_HEADLINE}** {REVIEW_BODY}"
REVIEW_NOTICE_TEXT = f"{REVIEW_HEADLINE} {REVIEW_BODY}"


def _num(value: Any, spec: str = ".4g") -> str:
    """Render one numeric cell; a demand the suite never produced reads n/a."""
    number = finite(value)
    return format(number, spec) if number is not None else "n/a"


def render_report(
    spec: BuildingSpec,
    design: Design,
    assessment: dict[str, Any],
    acceptance: dict[str, Any],
    verdict: str,
    history: list[dict[str, Any]],
    engineer_notes: str = "",
) -> str:
    if verdict not in VERDICTS:
        raise ValueError(f"verdict must be one of {VERDICTS}")
    lines: list[str] = []
    add = lines.append
    add(f"# SeismoForge prototype design report - {spec.name.replace('_', ' ')}")
    add("")
    add(f"**Verdict: {'PROCEED' if verdict == 'proceed' else 'NOT BUILDABLE WITHIN BRIEF'}**")
    add("")
    add(REVIEW_NOTICE)
    add("")

    add("## Building and site")
    add("")
    add(f"- Occupancy: {spec.occupancy} | stories: {spec.n_stories} | "
        f"story height: {spec.story_height_m} m")
    add(f"- Seismic floor weight: {spec.floor_mass_t} t/floor "
        f"(total seismic weight {spec.seismic_weight_kn:,.0f} kN)")
    add(f"- Story lateral stiffness: {spec.story_stiffness_kn_m:,.0f} kN/m")
    add(f"- Site: PGA {spec.site.pga_g} g, predominant period "
        f"{spec.site.soil_period_sec} s, duration {spec.site.duration_sec} s")
    add(f"- Moat clearance available: {spec.moat_clearance_m} m | "
        f"residual limit: {RESIDUAL_LIMIT_M} m")
    add("")

    add("## Selected structural system")
    add("")
    if design.system == "fixed_base":
        add("Conventional fixed-base frame. Base isolation is not required to "
            "meet the performance targets on this site.")
    else:
        iso = design.isolation
        weight = spec.seismic_weight_kn
        add("Lead-rubber base isolation layer under the full frame:")
        add("")
        add(f"- Characteristic strength Qd = {iso.qd_kn:,.0f} kN "
            f"({iso.qd_kn / weight:.1%} of seismic weight)")
        add(f"- Post-yield stiffness Kd = {iso.kd_kn_m:,.0f} kN/m "
            f"(isolated period {isolation_period(spec, iso.kd_kn_m):.2f} s)")
        add(f"- Yield displacement Dy = {iso.dy_m * 1000:.0f} mm")
    add("")

    add("## Verification basis")
    add("")
    add(f"- Nonlinear response-history analysis in OpenSees (Newmark average "
        f"acceleration, dt = {DT} s, Newton iteration with ModifiedNewton retry).")
    add(f"- Record suite: {len(assessment['per_record'])} site-consistent "
        f"synthetic accelerograms (soil-filtered, {N_HARMONICS} harmonics, "
        f"Clough-Penzien high-pass at {HIGHPASS_CORNER_HZ} Hz), seeds "
        f"{[r['seed'] for r in assessment['per_record']]} - fully reproducible "
        f"from this brief.")
    calib = assessment.get("calibration", {})
    if "rayleigh_alpha_m" in calib:
        add(f"- Damping: {calib['damping_ratio']:.0%} Rayleigh "
            f"(alpha_m = {calib['rayleigh_alpha_m']:.4f}, "
            f"beta_k = {calib['rayleigh_beta_k']:.6f}; anchors "
            f"{calib['omega_low_rad_s']:.2f} / {calib['omega_high_rad_s']:.2f} rad/s).")
    add("")

    add("## Acceptance checks (suite envelope)")
    add("")
    add("| Check | Demand | Limit | Utilization | Status |")
    add("|---|---|---|---|---|")
    for check in acceptance["checks"]:
        if check["check"] == "all_records_converged":
            status = "OK" if check["satisfied"] else "**FAIL**"
            add(f"| all records converged | {'yes' if check['satisfied'] else 'no'} "
                f"| required | - | {status} |")
            continue
        status = "OK" if check["satisfied"] else "**FAIL**"
        add(f"| {check['check']} | {_num(check['value'])} | {_num(check['limit'])} "
            f"| {_num(check['utilization'], '.2f')} | {status} |")
    add("")
    if acceptance["governing_check"]:
        add(f"Governing check: **{acceptance['governing_check']}** at "
            f"utilization {_num(acceptance['governing_utilization'], '.2f')}.")
    add("")

    add("## Per-record results")
    add("")
    add("| Record | Seed | Converged | Iso disp (m) | Drift | Floor acc (g) | V/W | Residual (m) |")
    add("|---|---|---|---|---|---|---|---|")
    for record in assessment["per_record"]:
        add(
            f"| {record['record_id']} | {record['seed']} | "
            f"{'yes' if record['converged'] else 'NO'} | "
            f"{_num(record['peak_isolator_disp_m'], '.4f')} | "
            f"{_num(record['peak_drift_ratio'], '.5f')} | "
            f"{_num(record['peak_floor_accel_g'], '.4f')} | "
            f"{_num(record['base_shear_coeff'], '.4f')} | "
            f"{_num(record['residual_disp_m'], '.4f')} |"
        )
    add("")

    add("## Design search history")
    add("")
    add(f"{len(history)} simulation-backed design evaluations:")
    add("")
    add("| # | Stage | System | Qd (kN) | Kd (kN/m) | Dy (mm) | Result | Worst utilization |")
    add("|---|---|---|---|---|---|---|---|")
    for index, entry in enumerate(history, start=1):
        design_entry = entry["design"]
        iso = design_entry.get("isolation")
        qd_cell = "{:,.0f}".format(iso["qd_kn"]) if iso else "-"
        kd_cell = "{:,.0f}".format(iso["kd_kn_m"]) if iso else "-"
        dy_cell = "{:.0f}".format(iso["dy_m"] * 1000) if iso else "-"
        add(
            f"| {index} | {entry['stage']} | {design_entry['system']} | "
            f"{qd_cell} | {kd_cell} | {dy_cell} | "
            f"{'pass' if entry['passed'] else 'fail'} | "
            f"{_num(entry['worst_utilization'], '.2f')} |"
        )
    add("")

    if verdict != "proceed":
        add("## Why the brief is not buildable as posed")
        add("")
        add("No design in the buildable isolation space met every acceptance "
            "target on this site; the table above shows the binding "
            "constraints. The recommendation is to revisit the brief itself "
            "(site, moat clearance, or supplemental damping outside the "
            "standard system) rather than to accept a design that fails "
            "verification.")
        add("")

    if engineer_notes.strip():
        add("## Engineering notes")
        add("")
        add(engineer_notes.strip())
        add("")
        add("*Commentary written by the design agent. Unlike the tables above "
            "it is prose, not a simulation output, and carries no independent "
            "verification.*")
        add("")

    add("---")
    add("*Generated by SeismoForge. Every number in the tables above comes "
        "from the simulation suite described in the verification basis; the "
        "suite is deterministic and reproducible from the project brief. "
        "Known modelling limitations of that basis are listed in the "
        "repository README - read them before acting on this report.*")
    add("")
    add(REVIEW_NOTICE)
    add("")
    return "\n".join(lines)


def write_outputs(
    out_dir: Path,
    spec: BuildingSpec,
    design: Design,
    assessment: dict[str, Any],
    acceptance: dict[str, Any],
    verdict: str,
    history: list[dict[str, Any]],
    engineer_notes: str = "",
) -> dict[str, str]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_md = render_report(
        spec, design, assessment, acceptance, verdict, history, engineer_notes
    )
    (out_dir / "design_report.md").write_text(report_md, encoding="utf-8")
    machine = {
        "brief": spec.name,
        "spec": spec.as_dict(),
        "design": design.as_dict(),
        "verdict": verdict,
        "envelope": assessment["envelope"],
        "acceptance": acceptance,
        "simulations": len(history),
    }
    (out_dir / "design.json").write_text(
        json.dumps(machine, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "design_report": str(out_dir / "design_report.md"),
        "design_json": str(out_dir / "design.json"),
    }
