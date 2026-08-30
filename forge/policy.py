"""Deterministic design policy: rule-of-thumb -> coarse screen -> refine.

This is the engineering search the scripted driver runs through the agent
tool layer, and the same strategy the LLM agent is prompted to follow with
its own judgment. Returns the selected design plus the full decision history.
"""

from __future__ import annotations

from typing import Any, Callable

from .building import BuildingSpec, Design
from .checks import acceptance_report
from .designer import (
    candidate_grid,
    clamp,
    refine,
    rule_of_thumb,
    worst_utilization,
)

MAX_REFINE_ITERS = 8

AssessFn = Callable[[BuildingSpec, Design], dict[str, Any]]


def forge_design(spec: BuildingSpec, assess_fn: AssessFn) -> dict[str, Any]:
    history: list[dict[str, Any]] = []

    def evaluate(design: Design, stage: str) -> dict[str, Any]:
        assessment = assess_fn(spec, design)
        report = acceptance_report(spec, design, assessment)
        entry = {
            "stage": stage,
            "design": design.as_dict(),
            "envelope": assessment["envelope"],
            "passed": report["passed"],
            "failed_checks": report["failed_checks"],
            "worst_utilization": worst_utilization(report),
        }
        history.append(entry)
        return {"assessment": assessment, "report": report}

    # 1. Pre-simulation engineering judgment.
    design = clamp(rule_of_thumb(spec), spec)
    outcome = evaluate(design, "rule_of_thumb")
    best = (design, outcome)

    # 2. Coarse screen when the first guess does not hold.
    if not outcome["report"]["passed"] and design.system == "base_isolated":
        for candidate in candidate_grid(spec):
            candidate = clamp(candidate, spec)
            candidate_outcome = evaluate(candidate, "screen")
            if worst_utilization(candidate_outcome["report"]) < worst_utilization(best[1]["report"]):
                best = (candidate, candidate_outcome)
        design, outcome = best

    # 3. Failure-driven local refinement from the best point found.
    iterations = 0
    while not outcome["report"]["passed"] and iterations < MAX_REFINE_ITERS:
        moved = refine(spec, design, outcome["report"])
        if moved is None:
            break
        design = moved
        outcome = evaluate(design, "refine")
        if worst_utilization(outcome["report"]) < worst_utilization(best[1]["report"]):
            best = (design, outcome)
        iterations += 1

    if not outcome["report"]["passed"]:
        design, outcome = best

    return {
        "design": design,
        "assessment": outcome["assessment"],
        "report": outcome["report"],
        "history": history,
        "simulations": len(history),
    }
