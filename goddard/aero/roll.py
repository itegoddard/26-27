"""Roll dynamics driven by the 1 degree fin cant.

Spec section 5.

Strip theory over the exposed fin panel. Each spanwise strip at radius ``y``
from the roll axis sees:

* a fixed geometric incidence from the cant, ``delta``
* an induced incidence from the roll rate, ``-p * y / V``

so the net incidence is ``delta - p*y/V``.

The strip integrals collapse to three geometric moments of the panel:

    S  = integral dS          panel area
    M1 = integral y dS        drives the rolling moment from cant
    M2 = integral y**2 dS     drives the roll damping

which makes every result closed-form:

    rolling moment  = N q a0 (delta*M1 - (p/V)*M2)
    equilibrium p   = delta * V * M1 / M2
    induced drag    = N a0 (delta**2 S - 2 delta (p/V) M1 + (p/V)**2 M2)

Evaluating these directly rather than re-summing strips every step matters: the
simulation calls this tens of thousands of times, and the closed form is both
faster and exact rather than quadrature-limited.

Modelling roll rate as a state rather than assuming equilibrium matters during
the burn, when the speed changes fast enough that the fins never quite settle.
"""

from __future__ import annotations

import functools
import math
from dataclasses import dataclass

from goddard.aero.geometry import VehicleGeometry

_STRIPS = 400


@dataclass(frozen=True)
class RollState:
    """Roll aerodynamics at one flight condition.

    Attributes
    ----------
    moment_Nm       : net rolling moment on the fin set, N m
    equilibrium_p   : steady-state roll rate, rad/s
    induced_drag    : added C_D from the fins' effective incidence
    """

    moment_Nm: float
    equilibrium_p: float
    induced_drag: float


@functools.lru_cache(maxsize=64)
def _panel_moments(
    root_chord_m: float,
    tip_chord_m: float,
    span_m: float,
    body_radius_m: float,
) -> tuple[float, float, float]:
    """Return ``(S, M1, M2)`` for one exposed panel, cached per geometry.

    ``y`` is measured from the roll axis, so the panel starts at the body
    radius -- the fin root is not on the centreline, and ignoring that would
    understate both the driving moment and the damping.
    """
    total = first = second = 0.0
    dy = span_m / _STRIPS
    for i in range(_STRIPS):
        frac = (i + 0.5) / _STRIPS
        chord = root_chord_m + (tip_chord_m - root_chord_m) * frac
        y = body_radius_m + frac * span_m
        dS = chord * dy
        total += dS
        first += y * dS
        second += y * y * dS
    return total, first, second


def panel_moments(geom: VehicleGeometry) -> tuple[float, float, float]:
    """``(S, M1, M2)`` for one fin panel."""
    f = geom.fins
    return _panel_moments(
        f.root_chord_m, f.tip_chord_m, f.span_m, geom.body.diameter_m / 2.0
    )


def section_lift_slope(mach: float) -> float:
    """Two-dimensional section lift-curve slope, per radian.

    Subsonic: thin-aerofoil ``2*pi`` with a Prandtl-Glauert correction.
    Supersonic: Ackeret ``4 / sqrt(M**2 - 1)``.
    Transonic: floored, approximate through the band as elsewhere.
    """
    if mach < 0.9:
        return 2.0 * math.pi / max(math.sqrt(1.0 - mach * mach), 0.5)
    if mach > 1.1:
        return 4.0 / max(math.sqrt(mach * mach - 1.0), 0.5)
    return 4.0 / 0.5


def equilibrium_roll_rate(
    geom: VehicleGeometry, velocity_ms: float, mach: float = 0.0
) -> float:
    """Steady-state roll rate, rad/s.

    Independent of air density and of the lift-curve slope -- both cancel
    between the driving and damping terms. It depends only on the cant angle,
    the flight speed and the panel geometry.
    """
    if velocity_ms <= 0.0:
        return 0.0
    _, m1, m2 = panel_moments(geom)
    if m2 <= 0.0:
        return 0.0
    return geom.fins.cant_angle_rad * velocity_ms * m1 / m2


def evaluate(
    geom: VehicleGeometry,
    velocity_ms: float,
    roll_rate: float,
    density: float,
    mach: float,
) -> RollState:
    """Rolling moment, equilibrium rate and roll-induced drag."""
    if velocity_ms <= 0.0 or density <= 0.0:
        return RollState(0.0, 0.0, 0.0)

    f = geom.fins
    a0 = section_lift_slope(mach)
    q = 0.5 * density * velocity_ms * velocity_ms
    delta = f.cant_angle_rad
    omega = roll_rate / velocity_ms

    area, m1, m2 = panel_moments(geom)

    moment = f.count * q * a0 * (delta * m1 - omega * m2)

    # integral of incidence**2 dS, expanded over the same three moments.
    incidence_sq = (
        delta * delta * area - 2.0 * delta * omega * m1 + omega * omega * m2
    )
    drag_area = f.count * a0 * max(0.0, incidence_sq)

    return RollState(
        moment_Nm=moment,
        equilibrium_p=equilibrium_roll_rate(geom, velocity_ms, mach),
        induced_drag=drag_area / geom.reference_area_m2,
    )


def roll_inertia_acceleration(moment_Nm: float, i_roll: float) -> float:
    """Roll angular acceleration, rad/s^2."""
    if i_roll <= 0.0:
        raise ValueError("roll inertia must be positive")
    return moment_Nm / i_roll
