"""Free-prose intake: let the model read a brief the way a colleague would.

The deterministic parser in ``forge/brief_parser.py`` is strict by design -
nine labelled datasheet lines, exact wording, or nothing. That is the right
contract for a reproducible benchmark and the wrong one for a person, who
writes "a five-storey hospital on reclaimed coastal ground, design PGA around
0.32 g" and expects to be understood.

This module gives the language model the one job no policy loop can do: turn
that sentence into the nine values. It does not get to be trusted for it.
Every extracted field must carry the phrase it came from, that phrase must
actually appear in the brief, and the assembled datasheet is then handed to
the same strict parser for validation. The model widens what the system can
read; it never widens what the system will believe.

That is the input-side mirror of the evidence lock on the output side: no
number without a source.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from forge.building import OCCUPANCY_LIMITS  # noqa: E402

MAX_ATTEMPTS = 2

# name, datasheet label, unit suffix, what the model is being asked for
FIELDS: tuple[tuple[str, str, str, str], ...] = (
    ("occupancy", "Building use", "",
     f"one of {sorted(OCCUPANCY_LIMITS)}; map the client's words onto the "
     "closest class (a clinic is a hospital, a logistics shed is a warehouse)"),
    ("n_stories", "Stories above grade", "",
     "whole number of storeys above ground, 1 to 20"),
    ("floor_mass_t", "Seismic floor weight", " tonnes per floor",
     "seismic weight of one floor in tonnes; convert if the brief gives kN "
     "(divide by 9.81) or another unit"),
    ("story_stiffness_kn_m", "Story lateral stiffness", " kN/m",
     "lateral stiffness of one storey in kN/m"),
    ("story_height_m", "Story height", " m", "floor-to-floor height in metres"),
    ("pga_g", "Design PGA", " g", "design peak ground acceleration in g"),
    ("soil_period_sec", "Predominant site period", " s",
     "predominant site period in seconds; soft or deep soils are long"),
    ("duration_sec", "Strong-motion duration", " s",
     "strong-motion duration in seconds"),
    ("moat_clearance_m", "Moat clearance available", " m",
     "clearance available around the building for isolator travel, in metres"),
)

SYSTEM_PROMPT = """\
You read structural project briefs and extract the nine parameters a seismic \
prototyping engine needs. The brief is written by an engineer in ordinary \
prose; the values may be scattered, phrased loosely, or given in units you \
must convert.

Rules you must not break:

1. Every value you report must come from the brief. Never infer a typical \
value, never carry one over from a similar project, never fill a gap with \
engineering judgment. If a parameter is genuinely absent, list its name in \
`missing` and omit it from `fields`.
2. For each value, quote the exact span of the brief it came from, copied \
character for character. The quote is checked against the source text; a \
paraphrase will be rejected.
3. If you convert units, report the converted value and say what you did in \
`conversion`. The quote must still be the original phrase.

Extract what is there. Report what is not."""


def _tool_schema() -> dict[str, Any]:
    return {
        "name": "submit_brief_fields",
        "description": "Report the parameters extracted from the project brief.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fields": {
                    "type": "array",
                    "description": "One entry per parameter you found.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {
                                "type": "string",
                                "enum": [name for name, _, _, _ in FIELDS],
                            },
                            "value": {
                                "type": "string",
                                "description": "The value alone, no unit, no commas.",
                            },
                            "source": {
                                "type": "string",
                                "description": "Exact span copied from the brief.",
                            },
                            "conversion": {
                                "type": "string",
                                "description": "How you converted units, if you did.",
                            },
                        },
                        "required": ["field", "value", "source"],
                        "additionalProperties": False,
                    },
                },
                "missing": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Parameters the brief does not state at all.",
                },
            },
            "required": ["fields", "missing"],
            "additionalProperties": False,
        },
    }


def _normalise(text: str) -> str:
    """Whitespace- and case-insensitive form, for quote checking."""
    return re.sub(r"\s+", " ", text).strip().lower()


def _check_sources(brief_text: str, fields: list[dict[str, Any]]) -> list[str]:
    """Fields whose quoted source is not actually in the brief."""
    haystack = _normalise(brief_text)
    unfounded = []
    for entry in fields:
        source = _normalise(str(entry.get("source", "")))
        if not source or source not in haystack:
            unfounded.append(entry.get("field", "?"))
    return unfounded


def render_datasheet(values: dict[str, str], title: str = "Extracted brief") -> str:
    """Assemble the labelled form the deterministic parser expects."""
    lines = [f"# Project brief: {title}", ""]
    for name, label, unit, _ in FIELDS:
        lines.append(f"- {label}: {values[name]}{unit}")
    lines.append("")
    return "\n".join(lines)


def understand_brief(
    brief_text: str,
    *,
    model: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Extract the nine parameters from free prose.

    Returns ``{"fields": [...], "datasheet": str}``. Raises ValueError when
    the brief is missing a parameter or the model quotes a source that is not
    in the text - in both cases the caller should show the message to the
    person who wrote the brief.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    wanted = "\n".join(
        f"- {name} ({label}): {description}" for name, label, _, description in FIELDS
    )
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                f"Extract these parameters:\n\n{wanted}\n\n"
                f"--- PROJECT BRIEF ---\n{brief_text}\n--- END BRIEF ---"
            ),
        }
    ]

    last_error = "the model returned no extraction"
    for _attempt in range(MAX_ATTEMPTS):
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            tools=[_tool_schema()],
            tool_choice={"type": "tool", "name": "submit_brief_fields"},
            messages=messages,
        )
        blocks = [b for b in response.content if b.type == "tool_use"]
        if not blocks:
            last_error = "the model did not call submit_brief_fields"
            break
        extraction = dict(blocks[0].input)
        fields = list(extraction.get("fields", []))
        missing = [name for name, _, _, _ in FIELDS
                   if name not in {entry.get("field") for entry in fields}]

        if missing:
            raise ValueError(
                "the brief does not state: " + ", ".join(missing)
                + ". Add them and run again - values are never assumed."
            )

        # Source lock: a quoted span that is not in the brief means the value
        # was invented, whatever it looks like. Hand it back once, then stop.
        unfounded = _check_sources(brief_text, fields)
        if not unfounded:
            values = {entry["field"]: str(entry["value"]).replace(",", "").strip()
                      for entry in fields}
            return {
                "fields": fields,
                "datasheet": render_datasheet(values),
            }

        last_error = (
            "these fields quote text that is not in the brief: "
            + ", ".join(unfounded)
        )
        messages += [
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": blocks[0].id,
                        "is_error": True,
                        "content": (
                            f"{last_error}. Copy each source span character for "
                            "character from the brief, or list the field under "
                            "`missing` if it is not there."
                        ),
                    }
                ],
            },
        ]

    raise ValueError(f"brief intake failed: {last_error}")


def describe(extraction: dict[str, Any]) -> str:
    """One-line human summary of what was read out of the brief."""
    return json.dumps(
        {entry["field"]: entry["value"] for entry in extraction["fields"]},
        sort_keys=True,
    )
