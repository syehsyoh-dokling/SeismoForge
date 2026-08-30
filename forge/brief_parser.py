"""Brief parsing: from a natural-language project brief to a BuildingSpec.

Briefs are what the intended user actually writes: a short project datasheet
with labelled values inside prose. The deterministic parser below extracts the
labelled fields; the LLM driver reads the same brief and may catch intent the
labels do not carry, but both drivers land on the identical BuildingSpec
fields so every downstream number is reproducible.
"""

from __future__ import annotations

import re
import zlib
from pathlib import Path

from .building import OCCUPANCY_LIMITS, BuildingSpec, Site

RECORDS_PER_SUITE = 5

_FIELDS: dict[str, str] = {
    "occupancy": r"building use:\s*([a-z_ ]+)",
    "n_stories": r"stories above grade:\s*([0-9]+)",
    "floor_mass_t": r"seismic floor weight:\s*([0-9.,]+)\s*tonnes",
    "story_stiffness_kn_m": r"story lateral stiffness:\s*([0-9.,]+)\s*kn/m",
    "story_height_m": r"story height:\s*([0-9.]+)\s*m",
    "pga_g": r"design pga:\s*([0-9.]+)\s*g",
    "soil_period_sec": r"predominant site period:\s*([0-9.]+)\s*s",
    "duration_sec": r"strong-motion duration:\s*([0-9.]+)\s*s",
    "moat_clearance_m": r"moat clearance available:\s*([0-9.]+)\s*m",
}


def _number(raw: str) -> float:
    return float(raw.replace(",", ""))


def parse_brief_text(name: str, text: str) -> BuildingSpec:
    lowered = text.lower()
    values: dict[str, str] = {}
    missing: list[str] = []
    for field, pattern in _FIELDS.items():
        match = re.search(pattern, lowered)
        if match:
            values[field] = match.group(1).strip()
        else:
            missing.append(field)
    if missing:
        raise ValueError(f"brief {name!r} is missing labelled fields: {missing}")
    occupancy = values["occupancy"].strip().replace(" ", "_")
    if occupancy not in OCCUPANCY_LIMITS:
        raise ValueError(f"brief {name!r} names unknown occupancy {occupancy!r}")
    # Deterministic per-brief suite seeding: same brief -> same records, always.
    seed_base = 1000 + (zlib.crc32(name.encode("utf-8")) % 9000)
    return BuildingSpec(
        name=name,
        occupancy=occupancy,
        n_stories=int(values["n_stories"]),
        floor_mass_t=_number(values["floor_mass_t"]),
        story_stiffness_kn_m=_number(values["story_stiffness_kn_m"]),
        story_height_m=_number(values["story_height_m"]),
        site=Site(
            pga_g=_number(values["pga_g"]),
            soil_period_sec=_number(values["soil_period_sec"]),
            duration_sec=_number(values["duration_sec"]),
            records=RECORDS_PER_SUITE,
            seed_base=seed_base,
        ),
        moat_clearance_m=_number(values["moat_clearance_m"]),
    )


def parse_brief_file(path: Path) -> BuildingSpec:
    path = Path(path)
    return parse_brief_text(path.stem, path.read_text(encoding="utf-8"))


def list_briefs(brief_dir: Path) -> list[Path]:
    return sorted(Path(brief_dir).glob("*.md"))
