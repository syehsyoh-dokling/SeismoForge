"""One design session: brief in, verified deliverable out.

Every entry point in SeismoForge - the CLI, the design-center GUI, and the
evaluation harness - runs a brief through this module. There is deliberately
no second path: what a demo shows is what the evaluation measures, and every
run leaves the same trajectory behind.

Two things vary, and they are independent:

- **Intake**: how the brief becomes a BuildingSpec. The deterministic parser
  needs labelled datasheet lines; the LLM intake reads free prose.
- **Search**: who decides which design to try next. The scripted policy walks
  a fixed strategy; the LLM agent decides for itself.

Both search drivers go through the identical 9-tool surface, so both are
bound by the same evidence lock: no number reaches a report without coming
back from an OpenSees simulation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

AGENT_DIR = Path(__file__).resolve().parent
REPO = AGENT_DIR.parent
for path in (str(REPO), str(AGENT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

from forge.brief_parser import parse_brief_text  # noqa: E402
from forge.building import BuildingSpec, Design, design_from_dict  # noqa: E402
from forge.motions import DT  # noqa: E402
from forge.policy import search  # noqa: E402
from forge.simulate import TAIL_SEC  # noqa: E402
from tools import TOOL_DEFINITIONS, ForgeTools, dispatch  # noqa: E402
from trajectory import TrajectoryLogger  # noqa: E402

MODES = ("offline", "assisted", "agent")
DEFAULT_MODEL = "claude-opus-5"
MAX_TURNS_PER_BRIEF = 30

# Progress lines are for a human watching a run; the trajectory is the record.
Progress = Callable[[str], None]


def _noop(_line: str) -> None:
    return None


class ToolError(RuntimeError):
    """A tool call failed; the session cannot continue on this brief."""


# ----------------------------------------------------------------------
# Search backend that drives the tool surface


class ToolSearch:
    """Runs the shared search loop through the agent's tools.

    Same strategy as the LLM is prompted to follow, same tools, same evidence
    ledger - the only difference is that the next move comes from code.
    """

    def __init__(
        self,
        tools: ForgeTools,
        log: TrajectoryLogger,
        brief: str,
        spec: BuildingSpec,
        progress: Progress = _noop,
    ) -> None:
        self.tools = tools
        self.log = log
        self.brief = brief
        self.spec = spec
        self.progress = progress
        self._steps = int(round((spec.site.duration_sec + TAIL_SEC) / DT))

    def call(self, name: str, **payload: Any) -> Any:
        self.log.event("tool_call", name=name, input=payload)
        try:
            result = getattr(self.tools, name)(**payload)
        except Exception as error:  # surfaced to the caller, recorded first
            self.log.event("tool_error", name=name, error=f"{type(error).__name__}: {error}")
            raise ToolError(f"tool {name} failed: {type(error).__name__}: {error}") from error
        self.log.event("tool_result", name=name, result=result)
        return result

    # -- SearchBackend -------------------------------------------------
    def rule_of_thumb(self) -> Design:
        return design_from_dict(self.call("propose_rule_of_thumb", brief=self.brief))

    def candidates(self) -> list[Design]:
        entries = self.call("candidate_designs", brief=self.brief)
        self.progress(f"coarse screen: {len(entries)} candidate designs to simulate")
        return [design_from_dict(entry["design"]) for entry in entries]

    def evaluate(self, design: Design, stage: str) -> dict[str, Any]:
        self.progress(f"{stage}: {self._describe(design)}")
        self.progress(
            f"    OpenSees: {self.spec.site.records} records x {self._steps} steps, "
            "nonlinear Newmark integration"
        )
        outcome = self.call(
            "simulate_design", brief=self.brief, design=design.as_dict(), stage=stage
        )
        for line in self._demands(outcome):
            self.progress(f"    {line}")
        self.progress(
            f"    -> {'PASSES every limit' if outcome['passed'] else 'fails ' + str(outcome['failed_checks'])}"
        )
        return outcome

    def refinement(self, design: Design, report: dict[str, Any]) -> Design | None:
        outcome = self.call(
            "suggest_refinement", brief=self.brief, design=design.as_dict()
        )
        suggestion = outcome.get("suggestion")
        return design_from_dict(suggestion) if suggestion else None

    # -- progress rendering --------------------------------------------
    def _describe(self, design: Design) -> str:
        if design.system == "fixed_base":
            return "conventional fixed-base frame"
        iso = design.isolation
        return (
            f"lead-rubber isolation, Qd {iso.qd_kn:,.0f} kN, "
            f"Kd {iso.kd_kn_m:,.0f} kN/m, Dy {iso.dy_m * 1000:.0f} mm"
        )

    @staticmethod
    def _demands(outcome: dict[str, Any]) -> list[str]:
        lines = []
        for check in outcome.get("checks", ()):
            if check["check"] == "all_records_converged" or check["value"] is None:
                continue
            mark = "ok" if check["satisfied"] else "OVER"
            lines.append(
                f"{check['check']}: {check['value']:.4g} of {check['limit']:.4g} [{mark}]"
            )
        return lines


# ----------------------------------------------------------------------
# The LLM driver: one conversation per brief over the same tools


def _llm_client(api_key: str | None):
    import anthropic

    return anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()


def _create(client, model: str, system_prompt: str, tool_defs, messages):
    import anthropic

    try:
        return client.beta.messages.create(
            model=model, max_tokens=16000, system=system_prompt,
            tools=tool_defs, messages=messages,
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        )
    except (TypeError, anthropic.BadRequestError):
        return client.messages.create(
            model=model, max_tokens=16000, system=system_prompt,
            tools=tool_defs, messages=messages,
        )


def run_llm_search(
    tools: ForgeTools,
    log: TrajectoryLogger,
    brief: str,
    model: str,
    api_key: str | None = None,
    progress: Progress = _noop,
) -> dict[str, Any]:
    """Let the model drive the tools for one brief. Returns usage + summary."""
    client = _llm_client(api_key)
    system_prompt = (AGENT_DIR / "system_prompt.md").read_text(encoding="utf-8")
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                f"Forge the prototype design for brief {brief!r}: follow the "
                "workflow, write the report, verify it, then give the "
                "client-facing summary paragraph."
            ),
        }
    ]
    usage = {"input_tokens": 0, "output_tokens": 0}
    final_text = ""

    for _turn in range(MAX_TURNS_PER_BRIEF):
        response = _create(client, model, system_prompt, TOOL_DEFINITIONS, messages)
        usage["input_tokens"] += response.usage.input_tokens
        usage["output_tokens"] += response.usage.output_tokens
        if response.stop_reason == "refusal":
            log.event("refusal", brief=brief,
                      detail=str(getattr(response, "stop_details", None)))
            progress("the model declined the request")
            break
        for block in response.content:
            if block.type == "text" and block.text.strip():
                log.event("assistant_text", text=block.text)
                final_text = block.text
                progress(f"agent: {block.text.strip()[:300]}")
        tool_blocks = [b for b in response.content if b.type == "tool_use"]
        if response.stop_reason != "tool_use" or not tool_blocks:
            break
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in tool_blocks:
            progress(f"agent calls {block.name}")
            log.event("tool_call", name=block.name, input=dict(block.input))
            try:
                result = dispatch(tools, block.name, dict(block.input))
                content, is_error = json.dumps(result, default=str), False
                log.event("tool_result", name=block.name, result=result)
            except Exception as error:
                content, is_error = f"{type(error).__name__}: {error}", True
                log.event("tool_error", name=block.name, error=content)
                progress(f"tool error: {content}")
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": content,
                    **({"is_error": True} if is_error else {}),
                }
            )
        messages.append({"role": "user", "content": results})

    return {"summary": final_text, "usage": usage}


# ----------------------------------------------------------------------
# One brief, end to end


def run_brief(
    tools: ForgeTools,
    log: TrajectoryLogger,
    brief: str,
    mode: str = "offline",
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    progress: Progress = _noop,
) -> dict[str, Any]:
    """Search, report, and verify one brief. The spec must already parse."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    spec = tools.spec(brief)
    progress(
        f"brief '{brief}': {spec.n_stories}-story {spec.occupancy}, "
        f"PGA {spec.site.pga_g} g, site period {spec.site.soil_period_sec} s, "
        f"moat {spec.moat_clearance_m} m"
    )

    if mode == "agent":
        progress(f"LLM agent drives the tools ({model})")
        llm = run_llm_search(tools, log, brief, model, api_key, progress)
        payload_path = tools.out_root / brief / "design.json"
        if not payload_path.is_file():
            raise ToolError("the agent finished without writing design.json")
        verification = tools.verify_output(brief)
        log.event("verification", brief=brief, **verification)
        return {
            "brief": brief,
            "mode": mode,
            "driver": "llm",
            "summary": llm["summary"],
            "usage": llm["usage"],
            "verification": verification,
        }

    progress("scripted policy: rule of thumb -> coarse screen -> refinement")
    backend = ToolSearch(tools, log, brief, spec, progress)
    # Read and parse through the tools as well, so the trajectory tells the
    # whole story - brief in, report out - exactly as the LLM path does.
    backend.call("read_brief", brief=brief)
    backend.call("parse_brief", brief=brief)
    outcome = search(backend)
    design, report = outcome["design"], outcome["report"]

    verdict = "proceed" if report["passed"] else "not_buildable_within_brief"
    governing = report["governing_utilization"]
    notes = (
        f"Governing check: {report['governing_check']} at utilization "
        + (f"{governing:.2f}." if governing is not None
           else "n/a - the record suite did not converge on this design.")
    )
    progress(f"writing the report: verdict {verdict}")
    written = backend.call(
        "write_report", brief=brief, design=design.as_dict(),
        verdict=verdict, engineer_notes=notes,
    )
    if "error" in written:
        raise ToolError(f"{brief}: evidence lock rejected the report: {written['error']}")
    verification = backend.call("verify_output", brief=brief)
    if not verification["ok"]:
        raise ToolError(f"{brief}: verification failed: {verification['problems']}")

    return {
        "brief": brief,
        "mode": mode,
        "driver": "scripted",
        "verdict": verdict,
        "system": design.system,
        "passed": report["passed"],
        "governing_check": report["governing_check"],
        "governing_utilization": governing,
        "summary": notes,
        "verification": verification,
    }


# ----------------------------------------------------------------------
# Convenience entry point for a single ad-hoc brief (the GUI)


def run_session(
    brief_text: str,
    *,
    mode: str,
    run_dir: Path,
    trajectory_path: Path,
    name: str = "user_brief",
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    progress: Progress = _noop,
) -> dict[str, Any]:
    """Run one free-standing brief and return the deliverable payload."""
    run_dir = Path(run_dir)
    brief_dir = run_dir / "brief"
    brief_dir.mkdir(parents=True, exist_ok=True)

    spec = resolve_spec(brief_text, name=name, mode=mode, model=model,
                        api_key=api_key, progress=progress)
    canonical = canonical_brief(spec, name)
    (brief_dir / f"{name}.md").write_text(canonical, encoding="utf-8")

    log = TrajectoryLogger(Path(trajectory_path))
    log.event("session_start", brief=name, mode=mode)
    tools = ForgeTools(run_dir, brief_dir=brief_dir)
    outcome = run_brief(tools, log, name, mode=mode, model=model,
                        api_key=api_key, progress=progress)
    log.event("session_complete", brief=name, mode=mode)
    log.render_markdown(
        Path(trajectory_path).with_suffix(".md"),
        f"SeismoForge trajectory ({mode} mode, brief {name})",
    )

    payload = json.loads(
        (run_dir / name / "design.json").read_text(encoding="utf-8")
    )
    return {
        "outcome": outcome,
        "payload": payload,
        "spec": spec,
        "report_markdown": (run_dir / name / "design_report.md").read_text(encoding="utf-8"),
        "trajectory": str(trajectory_path),
    }


# ----------------------------------------------------------------------
# Intake: free prose (LLM) or labelled datasheet (deterministic parser)


def resolve_spec(
    brief_text: str,
    *,
    name: str,
    mode: str,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    progress: Progress = _noop,
) -> BuildingSpec:
    """Turn brief text into a BuildingSpec.

    ``offline`` requires the labelled datasheet lines. ``assisted`` and
    ``agent`` let the model read free prose first; its extraction is then
    validated by the same deterministic parser, so the strict path stays the
    single source of truth for what a valid brief is.
    """
    if mode == "offline":
        return parse_brief_text(name, brief_text)

    from intake import understand_brief  # local import: needs the SDK

    progress("reading the brief with the language model")
    extraction = understand_brief(brief_text, model=model, api_key=api_key)
    progress(
        "extracted: "
        + ", ".join(f"{f['field']}={f['value']}" for f in extraction["fields"])
    )
    spec = parse_brief_text(name, extraction["datasheet"])
    progress("extraction validated by the deterministic parser")
    return spec


def canonical_brief(spec: BuildingSpec, name: str) -> str:
    """Render a spec back into the labelled datasheet form.

    Whatever the intake path, the brief stored beside the deliverable is the
    canonical one - so the run can always be repeated without the model.
    """
    title = name.replace("_", " ").title()
    return "\n".join(
        [
            f"# Project brief: {title}",
            "",
            "## Project data",
            "",
            f"- Building use: {spec.occupancy}",
            f"- Stories above grade: {spec.n_stories}",
            f"- Seismic floor weight: {spec.floor_mass_t} tonnes per floor",
            f"- Story lateral stiffness: {spec.story_stiffness_kn_m:,.0f} kN/m",
            f"- Story height: {spec.story_height_m} m",
            "",
            "## Site hazard",
            "",
            f"- Design PGA: {spec.site.pga_g} g",
            f"- Predominant site period: {spec.site.soil_period_sec} s",
            f"- Strong-motion duration: {spec.site.duration_sec} s",
            f"- Moat clearance available: {spec.moat_clearance_m} m",
            "",
        ]
    )
