"""Building and site specifications for SeismoForge.

Everything downstream of the brief parser works from these two dataclasses.
Units are SI: metres, seconds, tonnes (Mg), kilonewtons. g = 9.81 m/s^2.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

G = 9.81  # m/s^2

# Acceptance limits by occupancy class. These are SeismoForge's own benchmark
# targets, inspired by common performance-based-design practice (stricter for
# occupancies whose contents or continuity of operation matter more).
OCCUPANCY_LIMITS: dict[str, dict[str, float]] = {
    # peak_drift_ratio: max interstory drift ratio (structure damage)
    # peak_floor_accel_g: max total floor acceleration in g (contents/equipment)
    # base_shear_coeff: peak base shear / seismic weight (foundation demand)
    "hospital": {"peak_drift_ratio": 0.007, "peak_floor_accel_g": 0.40, "base_shear_coeff": 0.30},
    "data_center": {"peak_drift_ratio": 0.008, "peak_floor_accel_g": 0.30, "base_shear_coeff": 0.35},
    "school": {"peak_drift_ratio": 0.010, "peak_floor_accel_g": 0.45, "base_shear_coeff": 0.40},
    "residential": {"peak_drift_ratio": 0.012, "peak_floor_accel_g": 0.55, "base_shear_coeff": 0.45},
    "office": {"peak_drift_ratio": 0.012, "peak_floor_accel_g": 0.55, "base_shear_coeff": 0.45},
    "warehouse": {"peak_drift_ratio": 0.015, "peak_floor_accel_g": 0.70, "base_shear_coeff": 0.55},
}

# Isolated systems additionally must respect the moat clearance and leave the
# building recentred after the event. The residual limit is judged on the
# suite envelope, and permanent offset is the least repeatable response
# quantity record-to-record (once the lead core yields it carries no restoring
# force), so the envelope limit is set wider than a single-record tolerance.
RESIDUAL_LIMIT_M = 0.12


@dataclass
class Site:
    """Seismic hazard description used to synthesize the record suite."""

    pga_g: float          # design peak ground acceleration
    soil_period_sec: float  # predominant site period (soft soil -> long)
    duration_sec: float   # strong-motion duration
    records: int = 5      # suite size per assessment
    seed_base: int = 1000  # deterministic suite seeding

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BuildingSpec:
    """A parameterized shear-frame building: the SeismoForge model class."""

    name: str
    occupancy: str                    # key into OCCUPANCY_LIMITS
    n_stories: int
    floor_mass_t: float               # tonnes per floor (uniform)
    story_stiffness_kn_m: float       # lateral stiffness per story (uniform)
    story_height_m: float
    site: Site = field(default_factory=lambda: Site(0.3, 0.8, 25.0))
    moat_clearance_m: float = 0.45    # available isolator travel if isolated

    def __post_init__(self) -> None:
        if self.occupancy not in OCCUPANCY_LIMITS:
            raise ValueError(
                f"unknown occupancy {self.occupancy!r}; "
                f"known: {sorted(OCCUPANCY_LIMITS)}"
            )
        if not 1 <= self.n_stories <= 20:
            raise ValueError("SeismoForge supports 1-20 story shear frames")

    @property
    def limits(self) -> dict[str, float]:
        return dict(OCCUPANCY_LIMITS[self.occupancy])

    @property
    def seismic_weight_kn(self) -> float:
        return self.n_stories * self.floor_mass_t * G

    @property
    def total_mass_t(self) -> float:
        return self.n_stories * self.floor_mass_t

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["limits"] = self.limits
        data["seismic_weight_kn"] = self.seismic_weight_kn
        return data


@dataclass
class IsolationDesign:
    """Bilinear lead-rubber isolation layer: the design the agent forges."""

    qd_kn: float        # characteristic (lead) strength
    kd_kn_m: float      # post-yield (rubber) stiffness
    dy_m: float         # yield displacement (initial stiffness = qd/dy + kd)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Design:
    """Complete prototype design decision."""

    system: str                        # "fixed_base" or "base_isolated"
    isolation: IsolationDesign | None = None

    def __post_init__(self) -> None:
        if self.system not in ("fixed_base", "base_isolated"):
            raise ValueError("system must be fixed_base or base_isolated")
        if self.system == "base_isolated" and self.isolation is None:
            raise ValueError("base_isolated design requires isolation parameters")

    def as_dict(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "isolation": self.isolation.as_dict() if self.isolation else None,
        }


def design_from_dict(data: dict[str, Any]) -> Design:
    isolation = data.get("isolation")
    return Design(
        system=data["system"],
        isolation=IsolationDesign(
            qd_kn=float(isolation["qd_kn"]),
            kd_kn_m=float(isolation["kd_kn_m"]),
            dy_m=float(isolation["dy_m"]),
        ) if isolation else None,
    )


def spec_from_dict(data: dict[str, Any]) -> BuildingSpec:
    site = data["site"]
    return BuildingSpec(
        name=str(data["name"]),
        occupancy=str(data["occupancy"]),
        n_stories=int(data["n_stories"]),
        floor_mass_t=float(data["floor_mass_t"]),
        story_stiffness_kn_m=float(data["story_stiffness_kn_m"]),
        story_height_m=float(data["story_height_m"]),
        site=Site(
            pga_g=float(site["pga_g"]),
            soil_period_sec=float(site["soil_period_sec"]),
            duration_sec=float(site["duration_sec"]),
            records=int(site.get("records", 5)),
            seed_base=int(site.get("seed_base", 1000)),
        ),
        moat_clearance_m=float(data.get("moat_clearance_m", 0.45)),
    )
