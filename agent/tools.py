"""Tool layer for the SeismoForge agent.

The agent decides; the tools compute. Every response quantity that reaches a
design report comes from an OpenSees simulation run through this layer, and
``write_report`` re-simulates the submitted design so the report can never
carry numbers the model did not produce.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from forge.brief_parser import list_briefs, parse_brief_file
from forge.building import BuildingSpec, Design, design_from_dict
from forge.checks import acceptance_report
from forge.designer import (
    candidate_grid,
    clamp,
    fixed_base_period,
    isolation_period,
    refine,
    rule_of_thumb,
    worst_utilization,
)
from forge.report import VERDICTS, write_outputs
from forge.simulate import assess

BRIEF_DIR = REPO / "briefs"


class ForgeTools:
    def __init__(self, out_root: Path) -> None:
        self.out_root = Path(out_root)
        self._specs: dict[str, BuildingSpec] = {}
        # Evidence ledger: every simulation this session ran, per brief.
        self.history: dict[str, list[dict[str, Any]]] = {}
        self._last: dict[str, dict[str, Any]] = {}

    # -- brief access ---------------------------------------------------
    def list_briefs(self) -> list[str]:
        return [path.stem for path in list_briefs(BRIEF_DIR)]

    def read_brief(self, brief: str) -> str:
        path = BRIEF_DIR / f"{brief}.md"
        if not path.is_file():
            return f"unknown brief {brief!r}; available: {self.list_briefs()}"
        return path.read_text(encoding="utf-8")

    def _spec(self, brief: str) -> BuildingSpec:
        if brief not in self._specs:
            self._specs[brief] = parse_brief_file(BRIEF_DIR / f"{brief}.md")
        return self._specs[brief]

    def parse_brief(self, brief: str) -> dict[str, Any]:
        spec = self._spec(brief)
        data = spec.as_dict()
        data["fixed_base_period_sec"] = fixed_base_period(spec)
        return data

    # -- design space ---------------------------------------------------
    def propose_rule_of_thumb(self, brief: str) -> dict[str, Any]:
        spec = self._spec(brief)
        design = clamp(rule_of_thumb(spec), spec)
        return design.as_dict()

    def candidate_designs(self, brief: str) -> list[dict[str, Any]]:
        spec = self._spec(brief)
        out = []
        for design in candidate_grid(spec):
            design = clamp(design, spec)
            entry = design.as_dict()
            entry["isolated_period_sec"] = isolation_period(
                spec, design.isolation.kd_kn_m
            )
            out.append(entry)
        return out

    # -- simulation -----------------------------------------------------
    def simulate_design(self, brief: str, design: dict[str, Any]) -> dict[str, Any]:
        spec = self._spec(brief)
        parsed = clamp(design_from_dict(design), spec)
        assessment = assess(spec, parsed)
        report = acceptance_report(spec, parsed, assessment)
        entry = {
            "stage": "agent",
            "design": parsed.as_dict(),
            "envelope": assessment["envelope"],
            "passed": report["passed"],
            "failed_checks": report["failed_checks"],
            "worst_utilization": worst_utilization(report),
        }
        self.history.setdefault(brief, []).append(entry)
        self._last[brief] = {
            "design": parsed,
            "assessment": assessment,
            "report": report,
        }
        return {
            "design_as_clamped": parsed.as_dict(),
            "all_converged": assessment["all_converged"],
            "envelope": assessment["envelope"],
            "passed": report["passed"],
            "failed_checks": report["failed_checks"],
            "governing_check": report["governing_check"],
            "governing_utilization": report["governing_utilization"],
            "checks": report["checks"],
        }

    def suggest_refinement(self, brief: str, design: dict[str, Any]) -> dict[str, Any]:
        spec = self._spec(brief)
        parsed = clamp(design_from_dict(design), spec)
        last = self._last.get(brief)
        if last is None:
            return {"error": "simulate the design first"}
        moved = refine(spec, parsed, last["report"])
        return {
            "suggestion": moved.as_dict() if moved else None,
            "note": (
                "failure-driven move from the last simulated result; "
                "None means no further move inside the buildable space"
            ),
        }

    # -- deliverable ----------------------------------------------------
    def write_report(
        self,
        brief: str,
        design: dict[str, Any],
        verdict: str,
        engineer_notes: str = "",
    ) -> dict[str, Any]:
        if verdict not in VERDICTS:
            return {"error": f"verdict must be one of {VERDICTS}"}
        spec = self._spec(brief)
        parsed = clamp(design_from_dict(design), spec)
        # Evidence lock: the report is rendered from a fresh simulation of
        # exactly the submitted design, never from conversational numbers.
        assessment = assess(spec, parsed)
        acceptance = acceptance_report(spec, parsed, assessment)
        if verdict == "proceed" and not acceptance["passed"]:
            return {
                "error": (
                    "verdict 'proceed' rejected: the submitted design fails "
                    f"{acceptance['failed_checks']} on re-simulation"
                ),
            }
        if verdict == "not_buildable_within_brief" and acceptance["passed"]:
            return {
                "error": (
                    "verdict 'not_buildable_within_brief' rejected: the "
                    "submitted design passes every acceptance check"
                ),
            }
        paths = write_outputs(
            self.out_root / brief,
            spec,
            parsed,
            assessment,
            acceptance,
            verdict,
            self.history.get(brief, []),
            engineer_notes,
        )
        return {"written": paths, "passed": acceptance["passed"], "verdict": verdict}

    def verify_output(self, brief: str) -> dict[str, Any]:
        """Evaluator's-eye check of the written deliverable."""
        problems: list[str] = []
        out_dir = self.out_root / brief
        report_path = out_dir / "design_report.md"
        json_path = out_dir / "design.json"
        if not report_path.is_file():
            problems.append("design_report.md is missing")
        if not json_path.is_file():
            problems.append("design.json is missing")
        payload = None
        if json_path.is_file():
            try:
                payload = json.loads(json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                problems.append(f"design.json is invalid JSON: {error}")
        if payload is not None:
            spec = self._spec(brief)
            try:
                design = clamp(design_from_dict(payload["design"]), spec)
            except (KeyError, ValueError, TypeError) as error:
                design = None
                problems.append(f"design.json carries an invalid design: {error}")
            if payload.get("verdict") not in VERDICTS:
                problems.append(f"invalid verdict {payload.get('verdict')!r}")
            if design is not None and payload.get("verdict") in VERDICTS:
                assessment = assess(spec, design)
                acceptance = acceptance_report(spec, design, assessment)
                if payload["verdict"] == "proceed" and not acceptance["passed"]:
                    problems.append(
                        "verdict says proceed but the design fails "
                        f"{acceptance['failed_checks']} on independent re-simulation"
                    )
                if payload["verdict"] == "not_buildable_within_brief" and acceptance["passed"]:
                    problems.append(
                        "verdict says not buildable but the design passes "
                        "every check on independent re-simulation"
                    )
        return {"ok": not problems, "problems": problems}


# ----------------------------------------------------------------------
# Anthropic tool schemas + dispatch


def _obj(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


_DESIGN_SCHEMA = {
    "type": "object",
    "properties": {
        "system": {"type": "string", "enum": ["fixed_base", "base_isolated"]},
        "isolation": {
            "type": ["object", "null"],
            "properties": {
                "qd_kn": {"type": "number"},
                "kd_kn_m": {"type": "number"},
                "dy_m": {"type": "number"},
            },
            "required": ["qd_kn", "kd_kn_m", "dy_m"],
            "additionalProperties": False,
        },
    },
    "required": ["system"],
    "additionalProperties": False,
}

_BRIEF = {"type": "string"}

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "list_briefs",
        "description": "List the project briefs waiting in the design center.",
        "input_schema": _obj({}, []),
    },
    {
        "name": "read_brief",
        "description": "Read one project brief (natural-language client datasheet).",
        "input_schema": _obj({"brief": _BRIEF}, ["brief"]),
    },
    {
        "name": "parse_brief",
        "description": (
            "Deterministically extract the structural/site parameters, "
            "acceptance limits, and the fixed-base period estimate from a brief."
        ),
        "input_schema": _obj({"brief": _BRIEF}, ["brief"]),
    },
    {
        "name": "propose_rule_of_thumb",
        "description": (
            "Pre-simulation engineering judgment: system choice (fixed-base vs "
            "isolated) plus initial isolation sizing for this brief. A starting "
            "point, not a verified design."
        ),
        "input_schema": _obj({"brief": _BRIEF}, ["brief"]),
    },
    {
        "name": "candidate_designs",
        "description": (
            "A coarse screening grid over the buildable isolation space "
            "(strength fraction x isolated period x yield displacement). Use "
            "when the first guess fails: acceptance constraints are coupled and "
            "pure local moves oscillate."
        ),
        "input_schema": _obj({"brief": _BRIEF}, ["brief"]),
    },
    {
        "name": "simulate_design",
        "description": (
            "Run the full nonlinear response-history suite (OpenSees, 5 "
            "site-consistent records) for a candidate design and return the "
            "envelope, acceptance checks, and governing constraint. This is the "
            "only source of response numbers."
        ),
        "input_schema": _obj(
            {"brief": _BRIEF, "design": _DESIGN_SCHEMA}, ["brief", "design"]
        ),
    },
    {
        "name": "suggest_refinement",
        "description": (
            "Failure-driven local design move based on the last simulation of "
            "this brief (e.g. transmitted force too high -> lengthen period, "
            "soften yield transition). Returns null when no move remains."
        ),
        "input_schema": _obj(
            {"brief": _BRIEF, "design": _DESIGN_SCHEMA}, ["brief", "design"]
        ),
    },
    {
        "name": "write_report",
        "description": (
            "Render the client-facing design report + machine-readable "
            "design.json for a brief. The design is re-simulated first and the "
            "verdict must match the evidence: 'proceed' is rejected if the "
            "design fails, 'not_buildable_within_brief' is rejected if it "
            "passes. engineer_notes is an optional prose paragraph."
        ),
        "input_schema": _obj(
            {
                "brief": _BRIEF,
                "design": _DESIGN_SCHEMA,
                "verdict": {"type": "string", "enum": list(VERDICTS)},
                "engineer_notes": {"type": "string"},
            },
            ["brief", "design", "verdict"],
        ),
    },
    {
        "name": "verify_output",
        "description": (
            "Independent evaluator's-eye verification of the written "
            "deliverable: files present, design valid, and the stated verdict "
            "consistent with a fresh re-simulation. Fix every problem before "
            "moving on."
        ),
        "input_schema": _obj({"brief": _BRIEF}, ["brief"]),
    },
]


def dispatch(tools: ForgeTools, name: str, tool_input: dict[str, Any]) -> Any:
    handlers: dict[str, Callable[..., Any]] = {
        "list_briefs": tools.list_briefs,
        "read_brief": tools.read_brief,
        "parse_brief": tools.parse_brief,
        "propose_rule_of_thumb": tools.propose_rule_of_thumb,
        "candidate_designs": tools.candidate_designs,
        "simulate_design": tools.simulate_design,
        "suggest_refinement": tools.suggest_refinement,
        "write_report": tools.write_report,
        "verify_output": tools.verify_output,
    }
    if name not in handlers:
        raise KeyError(f"unknown tool {name}")
    return handlers[name](**tool_input)
