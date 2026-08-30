#!/usr/bin/env python3
"""SeismoForge self-tests: parser, physics, policy, reporting, evidence lock."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from forge.brief_parser import list_briefs, parse_brief_file
from forge.building import Design
from forge.checks import acceptance_report
from forge.designer import clamp, rule_of_thumb
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

    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
