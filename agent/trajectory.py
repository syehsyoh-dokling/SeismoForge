"""Trajectory logging: every agent step to JSONL plus a readable Markdown view."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class TrajectoryLogger:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.events: list[dict[str, Any]] = []
        self._start = time.time()
        self.path.write_text("", encoding="utf-8")

    def event(self, kind: str, **payload: Any) -> None:
        record = {"t_sec": round(time.time() - self._start, 2), "kind": kind, **payload}
        self.events.append(record)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str) + "\n")

    def render_markdown(self, path: Path, title: str) -> None:
        lines = [f"# {title}", ""]
        for record in self.events:
            kind = record["kind"]
            stamp = f"`t+{record['t_sec']}s`"
            if kind == "assistant_text":
                lines += [f"**Agent** ({stamp}):", "", record.get("text", "").strip(), ""]
            elif kind == "tool_call":
                pretty = json.dumps(record.get("input", {}), indent=2, default=str)
                if len(pretty) > 1500:
                    pretty = pretty[:1500] + "\n...[input truncated for display]"
                lines += [
                    f"**Tool call** `{record.get('name')}` ({stamp}):",
                    "", "```json", pretty, "```", "",
                ]
            elif kind == "tool_result":
                pretty = json.dumps(record.get("result", {}), indent=2, default=str)
                if len(pretty) > 2500:
                    pretty = pretty[:2500] + "\n...[result truncated for display]"
                lines += [
                    f"**Tool result** `{record.get('name')}` ({stamp}):",
                    "", "```json", pretty, "```", "",
                ]
            elif kind == "tool_error":
                lines += [f"**Tool error** `{record.get('name')}` ({stamp}): {record.get('error')}", ""]
            else:
                payload = {k: v for k, v in record.items() if k not in ("kind", "t_sec")}
                lines += [f"**{kind}** ({stamp}): `{json.dumps(payload, default=str)[:500]}`", ""]
        Path(path).write_text("\n".join(lines), encoding="utf-8")
