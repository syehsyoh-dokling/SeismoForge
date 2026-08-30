"""The design search: rule-of-thumb -> coarse screen -> failure-driven refine.

This is the one place the search strategy is written down. It is expressed
over a *backend* so the identical loop can be driven two ways:

- ``DirectSearch`` calls the physics straight through - fast, no logging, used
  by the calibration utilities and the self-tests.
- ``ToolSearch`` (in ``agent/session.py``) drives the same loop through the
  agent's 9-tool surface, so every step lands in the evidence ledger and the
  trajectory.

Both reach the same designs; only the bookkeeping around them differs. A
backend supplies four things: a starting design, a screening set, an
evaluation, and a refinement move.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Protocol

from .building import BuildingSpec, Design
from .checks import acceptance_report, finite
from .designer import (
    candidate_grid,
    clamp,
    refine,
    rule_of_thumb,
    worst_utilization,
)

MAX_REFINE_ITERS = 8

AssessFn = Callable[[BuildingSpec, Design], dict[str, Any]]


def design_key(design: Design) -> str:
    """Stable identity for a design, for keying results by what was run."""
    return json.dumps(design.as_dict(), sort_keys=True)


class SearchBackend(Protocol):
    """What the search loop needs from whoever is driving it."""

    def rule_of_thumb(self) -> Design: ...

    def candidates(self) -> list[Design]: ...

    def evaluate(self, design: Design, stage: str) -> dict[str, Any]: ...

    def refinement(self, design: Design, report: dict[str, Any]) -> Design | None: ...


def search(backend: SearchBackend, max_refine: int = MAX_REFINE_ITERS) -> dict[str, Any]:
    """Run the search; returns the selected design and its report.

    Ranking is by worst limit utilization, so the best design found is kept
    even when nothing passes - that is the evidence an infeasible brief needs.
    """
    design = backend.rule_of_thumb()
    report = backend.evaluate(design, "rule_of_thumb")
    best = (design, report)

    # Coarse screen when the first guess does not hold. Pure local moves
    # oscillate here because the acceptance constraints are coupled.
    if not report["passed"] and design.system == "base_isolated":
        for candidate in backend.candidates():
            candidate_report = backend.evaluate(candidate, "screen")
            if worst_utilization(candidate_report) < worst_utilization(best[1]):
                best = (candidate, candidate_report)
        design, report = best

    iterations = 0
    while not report["passed"] and iterations < max_refine:
        moved = backend.refinement(design, report)
        if moved is None:
            break
        design = moved
        report = backend.evaluate(design, "refine")
        if worst_utilization(report) < worst_utilization(best[1]):
            best = (design, report)
        iterations += 1

    if not report["passed"]:
        design, report = best
    return {"design": design, "report": report}


class DirectSearch:
    """Backend that calls the physics directly - no tool layer, no logging."""

    def __init__(self, spec: BuildingSpec, assess_fn: AssessFn) -> None:
        self.spec = spec
        self._assess = assess_fn
        self.history: list[dict[str, Any]] = []
        self.assessments: dict[str, dict[str, Any]] = {}

    def rule_of_thumb(self) -> Design:
        return clamp(rule_of_thumb(self.spec), self.spec)

    def candidates(self) -> list[Design]:
        return [clamp(design, self.spec) for design in candidate_grid(self.spec)]

    def evaluate(self, design: Design, stage: str) -> dict[str, Any]:
        assessment = self._assess(self.spec, design)
        report = acceptance_report(self.spec, design, assessment)
        self.assessments[design_key(design)] = assessment
        self.history.append(
            {
                "stage": stage,
                "design": design.as_dict(),
                "envelope": assessment["envelope"],
                "passed": report["passed"],
                "failed_checks": report["failed_checks"],
                # JSON-safe: a non-converged suite has no comparable
                # utilization, and infinity is not representable in JSON.
                "worst_utilization": finite(worst_utilization(report)),
            }
        )
        return report

    def refinement(self, design: Design, report: dict[str, Any]) -> Design | None:
        return refine(self.spec, design, report)


def forge_design(spec: BuildingSpec, assess_fn: AssessFn) -> dict[str, Any]:
    """Physics-level convenience wrapper around ``search``.

    Used by the calibration utilities and the self-tests, which want the
    assessment object itself rather than the agent's tool responses.
    """
    backend = DirectSearch(spec, assess_fn)
    outcome = search(backend)
    design = outcome["design"]
    return {
        "design": design,
        "assessment": backend.assessments[design_key(design)],
        "report": outcome["report"],
        "history": backend.history,
        "simulations": len(backend.history),
    }
