#!/usr/bin/env python3
"""SeismoForge design-center GUI - local web app, standard library only.

Serves the single-page UI and a small JSON API around the same engine and
agent the CLI uses. Binds to 127.0.0.1 only. API keys are held in memory for
the duration of a run and are never written to disk or logged.

Usage:
    python3 gui/server.py [--port 8765]
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "agent"))

from forge.brief_parser import list_briefs, parse_brief_text
from forge.building import RESIDUAL_LIMIT_M
from forge.report import REVIEW_NOTICE_TEXT
from session import MODES, run_session

# How each mode is described in the conclusion's evidence basis.
MODE_BASIS = {
    "offline": "deterministic parser, scripted search",
    "assisted": "the model read the brief, scripted search",
    "agent": "the model read the brief and drove the search",
}

GUI_DIR = Path(__file__).resolve().parent
RUN_ROOT = REPO / "outputs" / "gui"
TRAJECTORY_ROOT = REPO / "trajectories" / "gui"

JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()

# OpenSees keeps its model in process-global state, so two simulations running
# at once would interleave into one corrupt model. Jobs queue here and run one
# at a time; the browser keeps polling and sees the wait in the run log.
ENGINE_LOCK = threading.Lock()

# Model menus per provider. The tool surface is identical either way; only
# the wire format differs, and agent/llm.py owns that.
PROVIDER_MODELS = {
    "anthropic": ("claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5"),
    "openai": ("gpt-5.5", "gpt-5.4", "gpt-5.1", "gpt-4.1"),
}
DEFAULT_PROVIDER = "anthropic"


def _log(job: dict, line: str) -> None:
    with JOBS_LOCK:
        job["log"].append(f"[{time.strftime('%H:%M:%S')}] {line}")


def _snapshot(job: dict) -> dict:
    """A consistent copy for the poller: the log list is appended to live."""
    return {
        "id": job["id"],
        "log": list(job["log"]),
        "done": job["done"],
        "error": job["error"],
        "result": job["result"],
    }


def compose_conclusion(payload: dict, llm_summary: str, mode: str) -> dict:
    """One engineering conclusion from the physics evidence + agent narrative."""
    verdict = payload["verdict"]
    acceptance = payload["acceptance"]
    design = payload["design"]
    checks = [c for c in acceptance["checks"] if c.get("utilization") is not None]
    margins = [
        f"{c['check']} at {c['utilization']:.0%} of its limit"
        for c in checks if c["check"] != "all_records_converged"
    ]
    governing = acceptance["governing_check"] or "not determined"
    utilization = acceptance["governing_utilization"]
    # A non-converged suite leaves no comparable utilization to quote.
    util_text = f"{utilization:.0%}" if utilization is not None else "n/a"
    if design["system"] == "base_isolated":
        iso = design["isolation"]
        system_line = (
            f"lead-rubber base isolation (Qd = {iso['qd_kn']:,.0f} kN, "
            f"Kd = {iso['kd_kn_m']:,.0f} kN/m, Dy = {iso['dy_m'] * 1000:.0f} mm)"
        )
    else:
        system_line = "a conventional fixed-base frame (isolation not required)"
    if verdict == "proceed":
        headline = "PROCEED - a verified design exists"
        margin = (
            f"{max(0.0, 1.0 - utilization):.0%}" if utilization is not None else "n/a"
        )
        body = (
            f"The recommended system is {system_line}. Every performance target "
            f"holds across the full 5-record nonlinear simulation suite; the "
            f"governing criterion is {governing} at {util_text} utilization, so "
            f"the design carries a {margin} working margin on its tightest "
            f"constraint."
        )
    else:
        headline = "NOT BUILDABLE WITHIN BRIEF - the site/brief must change, not the evidence"
        body = (
            f"No buildable design met every target; the best candidate was "
            f"{system_line}, still failing {acceptance['failed_checks']} "
            f"(governing: {governing} at {util_text}). The honest engineering "
            f"recommendation is to revisit the brief - site, moat clearance, or "
            f"supplemental damping - rather than accept an unverified design."
        )
    return {
        "headline": headline,
        "verdict": verdict,
        "body": body,
        "margins": margins,
        "review": REVIEW_NOTICE_TEXT,
        "agent_narrative": llm_summary.strip(),
        "basis": (
            f"Every number comes from OpenSees nonlinear response-history "
            f"analysis on a deterministic site-consistent record suite "
            f"({payload['simulations']} design evaluations run; "
            f"{MODE_BASIS.get(mode, mode)}); the verdict is locked to that "
            "evidence and cannot be overwritten by narrative."
        ),
    }


def start_job(brief_text: str, mode: str, provider: str, model: str,
              api_key: str) -> dict:
    job_id = uuid.uuid4().hex[:12]
    job = {"id": job_id, "log": [], "done": False, "error": None, "result": None}
    with JOBS_LOCK:
        JOBS[job_id] = job

    def work() -> None:
        try:
            if mode not in MODES:
                raise RuntimeError(f"unknown mode {mode!r}; expected one of {MODES}")
            if mode != "offline":
                if provider not in PROVIDER_MODELS:
                    raise RuntimeError(
                        f"unknown provider {provider!r}; expected one of "
                        f"{sorted(PROVIDER_MODELS)}"
                    )
                if model not in PROVIDER_MODELS[provider]:
                    raise RuntimeError(
                        f"model {model!r} is not offered for {provider}"
                    )
                if not api_key:
                    raise RuntimeError(f"an API key is required for {mode} mode")
            if not ENGINE_LOCK.acquire(blocking=False):
                _log(job, "another design run holds the simulation engine; queued")
                ENGINE_LOCK.acquire()
            try:
                # One shared entry point: the GUI runs exactly what the CLI
                # and the evaluation harness run, and leaves the same
                # trajectory behind.
                outcome = run_session(
                    brief_text,
                    mode=mode,
                    run_dir=RUN_ROOT / job_id,
                    trajectory_path=TRAJECTORY_ROOT / f"{job_id}.jsonl",
                    model=model,
                    api_key=api_key or None,
                    provider=provider if mode != "offline" else None,
                    progress=lambda line: _log(job, line),
                )
            finally:
                ENGINE_LOCK.release()
            payload = outcome["payload"]
            job["result"] = {
                "conclusion": compose_conclusion(
                    payload, outcome["outcome"].get("summary", ""), mode
                ),
                "design": payload["design"],
                "acceptance": payload["acceptance"],
                "report_markdown": outcome["report_markdown"],
                "trajectory": outcome["trajectory"],
            }
            _log(job, f"run complete; trajectory written to {outcome['trajectory']}")
        except Exception as error:  # surfaced to the UI
            with JOBS_LOCK:
                job["error"] = f"{type(error).__name__}: {error}"
            _log(job, f"ERROR: {job['error']}")
        finally:
            with JOBS_LOCK:
                job["done"] = True

    threading.Thread(target=work, daemon=True).start()
    return {"job_id": job_id}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, code: int = 200) -> None:
        self._send(code, json.dumps(payload, default=str).encode("utf-8"),
                   "application/json")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            body = (GUI_DIR / "index.html").read_bytes()
            self._send(200, body, "text/html; charset=utf-8")
        elif parsed.path == "/api/briefs":
            briefs = [
                {"name": path.stem,
                 "text": path.read_text(encoding="utf-8")}
                for path in list_briefs(REPO / "briefs")
            ]
            self._json({
                "briefs": briefs,
                "providers": {name: list(models)
                              for name, models in PROVIDER_MODELS.items()},
            })
        elif parsed.path == "/api/status":
            job_id = parse_qs(parsed.query).get("id", [""])[0]
            with JOBS_LOCK:
                job = JOBS.get(job_id)
                snapshot = _snapshot(job) if job else None
            if snapshot is None:
                self._json({"error": "unknown job", "done": True, "log": []}, 404)
            else:
                self._json(snapshot)
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/run":
            self._json({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            self._json({"error": "invalid JSON"}, 400)
            return
        brief_text = str(payload.get("brief_text", "")).strip()
        if not brief_text:
            self._json({"error": "brief text is empty"}, 400)
            return
        mode = str(payload.get("mode", "offline"))
        if mode == "offline":
            try:
                # Offline intake is the strict parser, so fail fast here with
                # a helpful message instead of spawning a job that cannot run.
                # The other modes accept free prose and are checked in-session.
                parse_brief_text("user_brief", brief_text)
            except ValueError as error:
                self._json({"error": str(error)}, 400)
                return
        self._json(start_job(
            brief_text,
            mode,
            str(payload.get("provider", DEFAULT_PROVIDER)),
            str(payload.get("model", PROVIDER_MODELS[DEFAULT_PROVIDER][0])),
            str(payload.get("api_key", "")),
        ))

    def log_message(self, fmt: str, *args) -> None:  # keep the console quiet
        return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"SeismoForge design center: http://127.0.0.1:{args.port}")
    print(f"residual limit note: envelope basis {RESIDUAL_LIMIT_M} m")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
