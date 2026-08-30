"""Final calibration: parse the real briefs, run baseline vs policy, 5-record suites."""

from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from forge.brief_parser import list_briefs, parse_brief_file
from forge.checks import acceptance_report
from forge.designer import clamp, rule_of_thumb
from forge.policy import forge_design
from forge.simulate import assess

for path in list_briefs(REPO / "briefs"):
    spec = parse_brief_file(path)
    started = time.monotonic()
    baseline_design = clamp(rule_of_thumb(spec), spec)
    baseline_report = acceptance_report(spec, baseline_design, assess(spec, baseline_design))
    result = forge_design(spec, assess)
    wall = time.monotonic() - started
    print(
        f"{spec.name:32s} baseline[{baseline_design.system:13s}]="
        f"{'PASS' if baseline_report['passed'] else 'fail':4s} "
        f"agent={'PASS' if result['report']['passed'] else 'FAIL':4s} "
        f"sims={result['simulations']:2d} "
        f"gov={result['report']['governing_check']}={result['report']['governing_utilization']:.2f} "
        f"({wall:.1f}s)"
    )
