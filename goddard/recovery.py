"""Staged reefed recovery: drogue, reefed main, full main.

Spec section 8, register section J.

Bounding the opening load is the entire purpose of reefing, so peak load per
stage is a primary output rather than a diagnostic.

Each stage inflates over a filling time ``t_fill = n * D0 / V`` rather than
snapping open, and the drag area ramps across that interval. Opening load is

    F = Cx * q * (Cd*S)

with ``Cx`` the opening-force coefficient for the canopy type.

OpenRocket already flags the current single-chute-at-apogee configuration with
"deployment at high speed (151 ft/s)". This module is the fix for that.

Reference
---------
Knacke, T. W., *Parachute Recovery Systems Design Manual*, NWC TP 6575, 1992.
See ``docs/references.bib``.
"""

from __future__ import annotations

import math
from enum import Enum
from dataclasses import dataclass


class Stage(Enum):
    """Recovery stage, in deployment order."""

    STOWED = "stowed"
    DROGUE = "drogue"
    MAIN_REEFED = "main_reefed"
    MAIN_FULL = "main_full"


class ChuteOverload(RuntimeError):
    """Opening load exceeded the allowable (register J9)."""


@dataclass(frozen=True)
class RecoveryConfig:
    """Staged recovery system.

    Attributes
    ----------
    drogue_cds_m2   : drogue drag area Cd*S, m^2
    main_cds_m2     : main drag area at full inflation, m^2
    reefing_ratio   : reefed diameter as a fraction of full diameter. Drag area
                      scales with its square.
    disreef_altitude_m : altitude AGL at which the main disreefs
    filling_constant   : ``n`` in ``t_fill = n*D0/V``. Knacke gives 8-10 for
                      solid cloth.
    opening_force_coefficient : ``Cx``
    max_opening_load_N : allowable, register J9
    """

    drogue_cds_m2: float
    main_cds_m2: float
    reefing_ratio: float
    disreef_altitude_m: float
    filling_constant: float = 8.0
    opening_force_coefficient: float = 1.7
    max_opening_load_N: float = math.inf

    def __post_init__(self) -> None:
        if self.drogue_cds_m2 < 0.0 or self.main_cds_m2 <= 0.0:
            raise ValueError("drag areas must be non-negative, main positive")
        if not 0.0 < self.reefing_ratio <= 1.0:
            raise ValueError(
                f"reefing ratio must be in (0, 1], got {self.reefing_ratio}"
            )
        if self.filling_constant <= 0.0:
            raise ValueError("filling constant must be positive")

    @property
    def main_reefed_cds_m2(self) -> float:
        """Reefed drag area -- scales with the square of the diameter ratio."""
        return self.main_cds_m2 * self.reefing_ratio ** 2

    def target_cds(self, stage: Stage) -> float:
        """Fully-inflated drag area for a stage, m^2."""
        return {
            Stage.STOWED: 0.0,
            Stage.DROGUE: self.drogue_cds_m2,
            Stage.MAIN_REEFED: self.main_reefed_cds_m2,
            Stage.MAIN_FULL: self.main_cds_m2,
        }[stage]


def nominal_diameter(cds_m2: float, cd: float = 1.5) -> float:
    """Back out a canopy diameter from a drag area, m."""
    if cds_m2 <= 0.0:
        return 0.0
    return math.sqrt(4.0 * cds_m2 / (math.pi * cd))


def filling_time(
    config: RecoveryConfig, stage: Stage, velocity_ms: float, cd: float = 1.5
) -> float:
    """Canopy filling time, s. ``t_fill = n * D0 / V``."""
    if velocity_ms <= 0.0:
        return 0.0
    d0 = nominal_diameter(config.target_cds(stage), cd)
    if d0 <= 0.0:
        return 0.0
    return config.filling_constant * d0 / abs(velocity_ms)


def inflation_fraction(elapsed_s: float, fill_time_s: float) -> float:
    """Fraction of target drag area developed, 0 to 1.

    Drag area is taken to grow with the square of the elapsed filling fraction,
    which matches the canopy's projected area opening roughly linearly in
    diameter.
    """
    if fill_time_s <= 0.0:
        return 1.0
    if elapsed_s <= 0.0:
        return 0.0
    if elapsed_s >= fill_time_s:
        return 1.0
    return (elapsed_s / fill_time_s) ** 2


def drag_area(
    config: RecoveryConfig,
    stage: Stage,
    elapsed_in_stage_s: float,
    velocity_at_deploy_ms: float,
) -> float:
    """Current drag area ``Cd*S``, m^2, accounting for inflation transient."""
    target = config.target_cds(stage)
    if target <= 0.0:
        return 0.0
    t_fill = filling_time(config, stage, velocity_at_deploy_ms)
    return target * inflation_fraction(elapsed_in_stage_s, t_fill)


def opening_load(
    config: RecoveryConfig, stage: Stage, dynamic_pressure_Pa: float
) -> float:
    """Peak opening load for a stage, N. ``F = Cx * q * Cd*S``."""
    return (
        config.opening_force_coefficient
        * dynamic_pressure_Pa
        * config.target_cds(stage)
    )


def check_load(
    config: RecoveryConfig, stage: Stage, dynamic_pressure_Pa: float
) -> float:
    """Opening load, raising ``ChuteOverload`` if it exceeds the allowable."""
    load = opening_load(config, stage, dynamic_pressure_Pa)
    if load > config.max_opening_load_N:
        raise ChuteOverload(
            f"{stage.value} opening load {load:.0f} N exceeds the allowable "
            f"{config.max_opening_load_N:.0f} N (register J9). Reduce the "
            "reefing ratio or deploy lower."
        )
    return load


def terminal_velocity(
    mass_kg: float, cds_m2: float, density: float, gravity: float = 9.80665
) -> float:
    """Steady descent speed under a given drag area, m/s."""
    if cds_m2 <= 0.0:
        raise ValueError("drag area must be positive")
    if density <= 0.0:
        raise ValueError("density must be positive")
    return math.sqrt(2.0 * mass_kg * gravity / (density * cds_m2))


def next_stage(current: Stage, altitude_agl_m: float, config: RecoveryConfig) -> Stage:
    """Stage that should be active given the current altitude."""
    if current is Stage.MAIN_REEFED and altitude_agl_m <= config.disreef_altitude_m:
        return Stage.MAIN_FULL
    return current
