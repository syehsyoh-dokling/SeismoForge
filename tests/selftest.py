#!/usr/bin/env python3
"""SeismoForge self-tests: parser, physics, policy, reporting, evidence lock."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from forge.brief_parser import list_briefs, parse_brief_file
from forge.building import Design, IsolationDesign
from forge.checks import acceptance_report, finite
from forge.designer import bound_violations, clamp, rule_of_thumb, worst_utilization
from forge.motions import synthesize
from forge.policy import forge_design
from forge.report import render_report
from forge.simulate import assess


def main() -> int:
    briefs = list_briefs(REPO / "briefs")
    assert len(briefs) == 10, f"expected 10 briefs, found {len(briefs)}"

    specs = [parse_brief_file(path) for path in briefs]
    names = {spec.name for spec in specs}
    assert len(names) == 10

    # Motion determinism: same brief -> identical record, different seed -> different.
    site = specs[0].site
    _, a1 = synthesize(site, site.seed_base)
    _, a2 = synthesize(site, site.seed_base)
    _, a3 = synthesize(site, site.seed_base + 1)
    assert (a1 == a2).all(), "synthesis must be deterministic"
    assert not (a1 == a3).all(), "different seeds must differ"
    peak = max(abs(a1))
    assert abs(peak - site.pga_g * 9.81) < 1e-6, "record must scale to design PGA"

    # Physics + policy on the easiest brief (fast).
    warehouse = next(spec for spec in specs if "hillside" in spec.name)
    result = forge_design(warehouse, assess)
    assert result["report"]["passed"], "hillside warehouse must be solvable"
    assert result["design"].system == "fixed_base"

    # Isolation reduces floor acceleration on a demanding site.
    hospital = next(spec for spec in specs if "coastal" in spec.name)
    fixed = assess(hospital, Design(system="fixed_base"))
    isolated = assess(hospital, clamp(rule_of_thumb(hospital), hospital))
    assert (
        isolated["envelope"]["peak_floor_accel_g"]
        < fixed["envelope"]["peak_floor_accel_g"]
    ), "isolation must reduce floor acceleration on the coastal hospital"

    # Report renders and refuses free-text numbers by construction.
    report = acceptance_report(hospital, clamp(rule_of_thumb(hospital), hospital), isolated)
    text = render_report(
        hospital, clamp(rule_of_thumb(hospital), hospital), isolated, report,
        "not_buildable_within_brief" if not report["passed"] else "proceed",
        history=[],
    )
    assert "Acceptance checks" in text and "Per-record results" in text

    # Evidence lock: a 'proceed' verdict for a failing design must be rejected.
    sys.path.insert(0, str(REPO / "agent"))
    from tools import ForgeTools

    tools = ForgeTools(REPO / "outputs" / "_selftest")
    bad = {
        "system": "base_isolated",
        "isolation": {"qd_kn": 1000.0, "kd_kn_m": 20000.0, "dy_m": 0.02},
    }
    outcome = tools.write_report(hospital.name, bad, "proceed")
    assert "error" in outcome, "evidence lock must reject a contradicted verdict"

    # A suite that produced no usable demand (non-converged records) must
    # degrade into unmet checks and a renderable, JSON-clean artifact - never
    # an infinity that no browser or client can parse.
    design = clamp(rule_of_thumb(hospital), hospital)
    starved = {
        "all_converged": False,
        "per_record": [dict(r, residual_disp_m=None) for r in isolated["per_record"]],
        "envelope": dict.fromkeys(isolated["envelope"], None),
        "calibration": isolated["calibration"],
    }
    starved_report = acceptance_report(hospital, design, starved)
    assert not starved_report["passed"]
    assert all(
        c["utilization"] is None for c in starved_report["checks"]
        if c["check"] != "all_records_converged"
    ), "a missing demand has no utilization"
    assert "Infinity" not in json.dumps(starved_report)
    assert finite(worst_utilization(starved_report)) is None
    starved_text = render_report(
        hospital, design, starved, starved_report,
        "not_buildable_within_brief", history=[],
    )
    assert "n/a" in starved_text, "missing demands must render, not crash"

    # A degenerate limit (a brief offering no moat at all) still has a
    # verdict, even though it has no meaningful utilization.
    no_moat = replace(hospital, moat_clearance_m=0.0)
    zero_report = acceptance_report(no_moat, design, isolated)
    moat_check = next(
        c for c in zero_report["checks"] if c["check"] == "peak_isolator_disp_m"
    )
    assert moat_check["utilization"] is None and not moat_check["satisfied"]
    render_report(no_moat, design, isolated, zero_report,
                  "not_buildable_within_brief", history=[])

    # The judge rejects out-of-bounds submissions instead of repairing them.
    assert bound_violations(design, hospital) == []
    unbuildable = Design(
        system="base_isolated",
        isolation=IsolationDesign(qd_kn=1.0e9, kd_kn_m=1.0, dy_m=0.5),
    )
    assert bound_violations(unbuildable, hospital), "bounds must reject this design"

    # Screening candidates stay copyable into the strict design schema, and a
    # refinement move is never read off some other design's result.
    candidates = tools.candidate_designs(hospital.name)
    assert candidates and set(candidates[0]) == {"design", "isolated_period_sec"}
    assert set(candidates[0]["design"]) == {"system", "isolation"}
    stale = tools.suggest_refinement(hospital.name, candidates[0]["design"])
    assert "error" in stale, "refinement must require this design's own simulation"

    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
