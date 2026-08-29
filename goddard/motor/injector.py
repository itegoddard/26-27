"""Showerhead injector: flashing flow of saturated N2O.

Spec section 4.2.

Saturated N2O flashes and cavitates in straight drilled orifices, so neither
limit is right on its own: single-phase incompressible (SPI) over-predicts the
flow, homogeneous equilibrium (HEM) under-predicts it. The Dyer non-equilibrium
blend interpolates between them using the degree of superheat.

    k     = sqrt( (P1 - P2) / (Pv - P2) )
    mdot  = ( k * mdot_SPI + mdot_HEM ) / (1 + k)

Enthalpy dependency
-------------------
``mass_flow_hem`` needs the upstream and downstream specific enthalpies, and
``props.n2o.enthalpy_vaporisation`` cannot yet supply them (the ESDU 91022
latent-heat coefficients could not be verified). Rather than block this whole
module, the enthalpies are **parameters**: the physics is complete and tested,
and only the caller is waiting on data. ``mass_flow_spi`` needs no enthalpy and
is usable now.

Reference
---------
Dyer, Zilliac, Sadhwani, Karabeyoglu, Cantwell, AIAA 2007-5702,
doi:10.2514/6.2007-5702. See ``docs/references.bib``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


class ChugRisk(UserWarning):
    """Injector pressure drop has fallen below the feed-stability criterion."""


@dataclass(frozen=True)
class InjectorGeometry:
    """Straight-drilled showerhead plate."""

    n_holes: int
    hole_diameter_m: float
    plate_thickness_m: float

    def __post_init__(self) -> None:
        if self.n_holes < 1:
            raise ValueError(f"need at least one orifice, got {self.n_holes}")
        if self.hole_diameter_m <= 0.0:
            raise ValueError("hole diameter must be positive")
        if self.plate_thickness_m <= 0.0:
            raise ValueError("plate thickness must be positive")

    @property
    def area_m2(self) -> float:
        """Total orifice area."""
        return self.n_holes * math.pi * self.hole_diameter_m ** 2 / 4.0

    @property
    def length_to_diameter(self) -> float:
        """``L/d`` -- sets the discharge-coefficient regime."""
        return self.plate_thickness_m / self.hole_diameter_m


def discharge_coefficient_estimate(length_to_diameter: float) -> float:
    """Rough ``C_d`` from orifice ``L/d``, for straight-drilled holes.

    ESTIMATE ONLY. This is register item E5, a BANDED constant swept from 0.61
    to 0.82 because no cold-flow data exists. Use it to pick a sensible band
    centre, not as a substitute for measurement.

        L/d < 1      ~0.61   sharp-edged orifice limit
        L/d 2 to 5   ~0.75-0.82   short-tube regime, flow reattaches
    """
    if length_to_diameter <= 1.0:
        return 0.61
    if length_to_diameter >= 5.0:
        return 0.82
    return 0.61 + (0.82 - 0.61) * (length_to_diameter - 1.0) / 4.0


def mass_flow_spi(
    area_m2: float, cd: float, rho_liquid: float, dp: float
) -> float:
    """Single-phase incompressible mass flow, kg/s. Over-predicts for N2O."""
    if dp <= 0.0:
        return 0.0
    if rho_liquid <= 0.0:
        raise ValueError("liquid density must be positive")
    return cd * area_m2 * math.sqrt(2.0 * rho_liquid * dp)


def mass_flow_hem(
    area_m2: float,
    cd: float,
    rho_downstream: float,
    h_upstream: float,
    h_downstream: float,
) -> float:
    """Homogeneous-equilibrium mass flow, kg/s. Under-predicts for N2O.

    Enthalpies are in J/kg. If the downstream enthalpy exceeds the upstream
    value there is no expansion to drive flow and this returns zero.
    """
    dh = h_upstream - h_downstream
    if dh <= 0.0:
        return 0.0
    if rho_downstream <= 0.0:
        raise ValueError("downstream density must be positive")
    return cd * area_m2 * rho_downstream * math.sqrt(2.0 * dh)


def dyer_weight(p_upstream: float, p_downstream: float, p_vapour: float) -> float:
    """Non-equilibrium parameter ``k``.

    ``k`` is the ratio of bubble-growth time to fluid residence time. Large
    ``k`` means the flow leaves before it can flash, so SPI dominates; small
    ``k`` means equilibrium is reached and HEM dominates.
    """
    denom = p_vapour - p_downstream
    if denom <= 0.0:
        # Downstream is at or above vapour pressure: no flashing, pure SPI.
        return math.inf
    numer = p_upstream - p_downstream
    if numer <= 0.0:
        return 0.0
    return math.sqrt(numer / denom)


def mass_flow(
    geometry: InjectorGeometry,
    cd: float,
    p_upstream: float,
    p_downstream: float,
    p_vapour: float,
    rho_liquid: float,
    rho_downstream: float | None = None,
    h_upstream: float | None = None,
    h_downstream: float | None = None,
) -> float:
    """Dyer NHNE mass flow, kg/s.

    When the enthalpies are not supplied this degrades to pure SPI and is
    therefore an OVER-estimate of oxidiser flow. That is a deliberate,
    documented fallback so the pipeline runs before the ESDU data lands -- it is
    not a substitute for it.
    """
    dp = p_upstream - p_downstream
    if dp <= 0.0:
        return 0.0

    spi = mass_flow_spi(geometry.area_m2, cd, rho_liquid, dp)

    if h_upstream is None or h_downstream is None or rho_downstream is None:
        return spi

    hem = mass_flow_hem(
        geometry.area_m2, cd, rho_downstream, h_upstream, h_downstream
    )
    k = dyer_weight(p_upstream, p_downstream, p_vapour)
    if math.isinf(k):
        return spi
    return (k * spi + hem) / (1.0 + k)


def pressure_drop_ratio(p_injector: float, p_chamber: float) -> float:
    """``dP_inj / P_c``, the feed-system stability parameter."""
    if p_chamber <= 0.0:
        return math.inf
    return (p_injector - p_chamber) / p_chamber


def chug_margin(
    p_injector: float, p_chamber: float, minimum_ratio: float = 0.20
) -> float:
    """Ratio of actual to required injector pressure drop.

    Below 1.0 the feed system can couple to the chamber and chug. This is the
    governing instability for a showerhead on a blowdown feed system, and the
    risk grows through the burn: as the tank blows down, ``dP_inj`` collapses
    faster than ``P_c``, so the worst point is the tail, not ignition.

    Reference: Harrje & Reardon, NASA SP-194.
    """
    if minimum_ratio <= 0.0:
        raise ValueError("minimum ratio must be positive")
    return pressure_drop_ratio(p_injector, p_chamber) / minimum_ratio
