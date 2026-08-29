"""Converging-diverging nozzle performance.

Spec section 4.4.

Pure functions of thermodynamic state and geometry -- nothing here reads config,
so this module is fully implementable and testable ahead of the motor sizing
being settled.

The altitude-compensation term ``(Pe - Pa) * Ae`` is the reason thrust rises
with altitude. Over a climb to 50,000 ft that is a first-order effect, and the
25-26 model could not represent it at all.

References
----------
Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed., ch. 3.
See ``docs/references.bib`` (key ``sutton2017rocket``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


class UnchokedNozzle(ValueError):
    """Chamber pressure is too low to choke the throat.

    Below this the isentropic relations used here do not apply. Raised rather
    than returning a thrust figure that would be meaningless.
    """


@dataclass(frozen=True)
class NozzlePerformance:
    """Nozzle operating point.

    Attributes
    ----------
    exit_mach       : exit Mach number
    pressure_ratio  : Pe / Pc
    exit_pressure   : Pa
    cf_ideal        : ideal thrust coefficient (before efficiency)
    cf              : delivered thrust coefficient (after eta_cf)
    thrust          : N
    separated       : True if the Summerfield criterion suggests flow separation
    """

    exit_mach: float
    pressure_ratio: float
    exit_pressure: float
    cf_ideal: float
    cf: float
    thrust: float
    separated: bool


def area_ratio(mach: float, gamma: float) -> float:
    """Area ratio A/A* for a given Mach number (isentropic area-Mach relation)."""
    if mach <= 0.0:
        raise ValueError(f"Mach number must be positive, got {mach}")
    g = gamma
    t = 1.0 + 0.5 * (g - 1.0) * mach * mach
    return (1.0 / mach) * (2.0 / (g + 1.0) * t) ** ((g + 1.0) / (2.0 * (g - 1.0)))


def exit_mach(expansion_ratio: float, gamma: float) -> float:
    """Supersonic exit Mach number for a given expansion ratio.

    Solved by bisection on the area-Mach relation, which is monotonic for
    M > 1 and therefore robust -- no initial guess to tune, no Newton
    divergence at high area ratios.
    """
    if expansion_ratio < 1.0:
        raise ValueError(
            f"expansion ratio must be >= 1, got {expansion_ratio}"
        )
    if expansion_ratio == 1.0:
        return 1.0

    lo, hi = 1.0 + 1e-12, 2.0
    while area_ratio(hi, gamma) < expansion_ratio:
        hi *= 2.0
        if hi > 1e6:
            raise ValueError(
                f"expansion ratio {expansion_ratio} is unreachable for "
                f"gamma = {gamma}"
            )

    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if area_ratio(mid, gamma) < expansion_ratio:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def pressure_ratio(mach: float, gamma: float) -> float:
    """Static-to-total pressure ratio at a given Mach number."""
    t = 1.0 + 0.5 * (gamma - 1.0) * mach * mach
    return t ** (-gamma / (gamma - 1.0))


def throat_mass_flux(p_chamber: float, c_star: float) -> float:
    """Mass flow per unit throat area (kg/s/m^2) for a choked throat."""
    if c_star <= 0.0:
        raise ValueError(f"c* must be positive, got {c_star}")
    return p_chamber / c_star


def thrust_coefficient(
    p_chamber: float,
    p_ambient: float,
    expansion_ratio: float,
    gamma: float,
) -> tuple[float, float, float]:
    """Ideal thrust coefficient.

    Returns ``(cf_ideal, exit_mach, exit_pressure)``.

    The momentum term is the standard isentropic result; the pressure term
    ``(Pe - Pa)/Pc * eps`` is what makes thrust altitude-dependent.
    """
    if p_chamber <= 0.0:
        raise ValueError(f"chamber pressure must be positive, got {p_chamber}")

    g = gamma
    me = exit_mach(expansion_ratio, g)
    pe_pc = pressure_ratio(me, g)
    pe = pe_pc * p_chamber

    momentum = math.sqrt(
        (2.0 * g * g / (g - 1.0))
        * (2.0 / (g + 1.0)) ** ((g + 1.0) / (g - 1.0))
        * (1.0 - pe_pc ** ((g - 1.0) / g))
    )
    pressure = (pe - p_ambient) / p_chamber * expansion_ratio
    return momentum + pressure, me, pe


def performance(
    p_chamber: float,
    p_ambient: float,
    throat_area: float,
    expansion_ratio: float,
    gamma: float,
    eta_cf: float = 0.97,
) -> NozzlePerformance:
    """Full nozzle operating point.

    Parameters
    ----------
    p_chamber       : chamber stagnation pressure, Pa
    p_ambient       : ambient pressure, Pa
    throat_area     : throat area, m^2
    expansion_ratio : Ae / At
    gamma           : ratio of specific heats of the combustion products
    eta_cf          : nozzle efficiency (register G10)

    Raises
    ------
    UnchokedNozzle
        If the chamber-to-ambient pressure ratio cannot choke the throat.
    """
    if throat_area <= 0.0:
        raise ValueError(f"throat area must be positive, got {throat_area}")

    # Choking requires Pc/Pa above the critical ratio.
    critical = (2.0 / (gamma + 1.0)) ** (-gamma / (gamma - 1.0))
    if p_ambient > 0.0 and p_chamber / p_ambient < critical:
        raise UnchokedNozzle(
            f"chamber/ambient pressure ratio {p_chamber / p_ambient:.3f} is "
            f"below the critical value {critical:.3f} for gamma = {gamma}; "
            "the throat is not choked and isentropic nozzle relations do not "
            "apply."
        )

    cf_ideal, me, pe = thrust_coefficient(
        p_chamber, p_ambient, expansion_ratio, gamma
    )
    cf = eta_cf * cf_ideal

    # Summerfield criterion: separation is likely once the exit plane is
    # over-expanded below roughly 40 % of ambient.
    separated = p_ambient > 0.0 and pe < 0.4 * p_ambient

    return NozzlePerformance(
        exit_mach=me,
        pressure_ratio=pe / p_chamber,
        exit_pressure=pe,
        cf_ideal=cf_ideal,
        cf=cf,
        thrust=cf * p_chamber * throat_area,
        separated=separated,
    )
