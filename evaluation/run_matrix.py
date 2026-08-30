#!/usr/bin/env python3
"""Baseline-versus-agent evaluation over the 10-brief portfolio.

Runs both systems on the identical briefs, then judges every submitted
design.json the way a peer reviewer would: re-simulate the submitted design
independently and check the stated verdict against the evidence and the
feasibility ground truth.

A submission is CORRECT for a brief when:
- verdict 'proceed' AND the design passes every acceptance check on
  independent re-simulation AND the brief is feasible; or
- verdict 'not_buildable_within_brief' AND the brief is infeasible.

Usage:
    python3 evaluation/run_matrix.py [--skip-run] [--agent-out outputs/agent]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from forge.brief_parser import list_briefs, parse_brief_file
from forge.building import design_from_dict
from forge.checks import acceptance_report
from forge.designer import bound_violations
from forge.simulate import assess


def judge(out_dir: Path, feasible: dict[str, bool]) -> list[dict]:
    rows = []
    for path in list_briefs(REPO / "briefs"):
        spec = parse_brief_file(path)
        row = {"brief": spec.name, "correct": False}
        payload_path = out_dir / spec.name / "design.json"
        if not payload_path.is_file():
            row["outcome"] = "missing design.json"
            rows.append(row)
            continue
        try:
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            # Judged exactly as submitted: clamping here would repair the
            # design into a different one and grade that instead.
            design = design_from_dict(payload["design"])
            verdict = payload["verdict"]
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as error:
            row["outcome"] = f"invalid submission: {error}"
            rows.append(row)
            continue
        violations = bound_violations(design, spec)
        if violations:
            row["outcome"] = f"submission outside the buildable space: {violations}"
            rows.append(row)
            continue
        if spec.name not in feasible:
            row["outcome"] = (
                "no feasibility ground truth for this brief; add it to "
                "evaluation/ground_truth.json before judging"
            )
            rows.append(row)
            continue
        report = acceptance_report(spec, design, assess(spec, design))
        row.update(
            {
                "verdict": verdict,
                "system": design.system,
                "design_passes": report["passed"],
                "governing_check": report["governing_check"],
                "governing_utilization": report["governing_utilization"],
                "simulations_claimed": payload.get("simulations", None),
            }
        )
        brief_feasible = feasible[spec.name]
        if verdict == "proceed":
            row["correct"] = report["passed"] and brief_feasible
            row["outcome"] = (
                "verified design" if row["correct"]
                else f"claimed proceed but fails {report['failed_checks']}"
            )
        elif verdict == "not_buildable_within_brief":
            row["correct"] = not brief_feasible
            row["outcome"] = (
                "correctly flagged infeasible brief" if row["correct"]
                else "flagged infeasible but a buildable design exists"
            )
        else:
            row["outcome"] = f"unknown verdict {verdict!r}"
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-run", action="store_true",
                        help="judge existing outputs without re-running the systems")
    parser.add_argument("--agent-out", default=str(REPO / "outputs" / "agent"),
                        help="agent output tree to judge (e.g. an LLM-mode run)")
    parser.add_argument("--mode", default="offline",
                        help="session mode to run: offline, assisted or agent")
    args = parser.parse_args()

    feasible = json.loads(
        (REPO / "evaluation" / "ground_truth.json").read_text(encoding="utf-8")
    )["briefs"]

    timings = {}
    if not args.skip_run:
        for name, command in (
            ("baseline", [sys.executable, str(REPO / "baselines" / "oneshot.py")]),
            ("agent", [sys.executable, str(REPO / "agent" / "run_agent.py"),
                       "--mode", args.mode, "--quiet"]),
        ):
            print(f"== running {name} ==", flush=True)
            started = time.monotonic()
            completed = subprocess.run(command, capture_output=True, text=True)
            timings[name] = round(time.monotonic() - started, 1)
            if completed.returncode != 0:
                print(completed.stdout[-2000:])
                print(completed.stderr[-2000:])
                raise SystemExit(f"{name} failed with exit {completed.returncode}")

    results = {}
    for name, out_dir in (
        ("baseline", REPO / "outputs" / "baseline"),
        ("agent", Path(args.agent_out)),
    ):
        rows = judge(out_dir, feasible)
        results[name] = {
            "rows": rows,
            "correct": sum(1 for r in rows if r["correct"]),
            "total": len(rows),
            "wall_time_sec": timings.get(name),
        }
        print(f"{name}: {results[name]['correct']}/{results[name]['total']} correct")

    out = REPO / "evaluation"
    (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    lines = [
        "# SeismoForge - measured comparison",
        "",
        "Primary metric: briefs resolved correctly out of 10 (a 'proceed' must",
        "survive independent re-simulation of the submitted design; an",
        "infeasible brief must be flagged, not forced).",
        "",
        "| System | Correct briefs | Wall time (s) |",
        "|---|---|---|",
    ]
    for name, data in results.items():
        wall = data["wall_time_sec"] if data["wall_time_sec"] is not None else "-"
        lines.append(f"| {name} | **{data['correct']}/{data['total']}** | {wall} |")
    lines += ["", "## Per-brief outcomes", "",
              "| Brief | Baseline | Agent |", "|---|---|---|"]
    agent_by_brief = {r["brief"]: r for r in results["agent"]["rows"]}
    for row in results["baseline"]["rows"]:
        agent_row = agent_by_brief.get(row["brief"], {})
        def cell(r):
            mark = "CORRECT" if r.get("correct") else "wrong"
            return f"{mark} - {r.get('outcome', '?')}"
        lines.append(f"| {row['brief']} | {cell(row)} | {cell(agent_row)} |")
    (out / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out / 'results.json'} and {out / 'results.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
