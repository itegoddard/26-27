"""US Standard Atmosphere 1976 — analytic, 0 to 86 km geopotential.

Spec section 2.1 and 9.

This is deliberately *analytic* rather than a lookup table. The 25-26 model used
a 1 m-resolution table spanning 500 to 15,420 m MSL and returned ``#N/A`` the
moment the vehicle left that range -- which it did, silently, mid-flight. There
is no table edge here to fall off.

Reference
---------
NOAA / NASA / USAF, *U.S. Standard Atmosphere, 1976*, NOAA-S/T 76-1562.
Also issued as NASA-TM-X-74335. See ``docs/references.bib`` (key ``usstd1976``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# --------------------------------------------------------------- constants
# Values are those *defined by* the 1976 standard. In particular R_STAR is
# 8.31432, not the modern CODATA gas constant -- using the modern value would
# put the model subtly out of agreement with the published tables.

G0 = 9.80665            # standard gravity, m/s^2
R_STAR = 8.31432        # universal gas constant used by the standard, J/(mol K)
M_AIR = 0.0289644       # mean molar mass of air, kg/mol
R_AIR = R_STAR / M_AIR  # specific gas constant, J/(kg K)  ~= 287.0528
GAMMA = 1.4             # ratio of specific heats
R_EARTH = 6356766.0     # effective earth radius used by the standard, m

# Sutherland viscosity constants from the standard
_BETA = 1.458e-6        # kg/(s m K^0.5)
_S = 110.4              # K

# Layer base geopotential altitudes (m'), lapse rates (K/m'), base temperatures
# (K) and base pressures (Pa). Base pressures are the standard's own values,
# carried explicitly rather than integrated up, so that round-off cannot
# accumulate across layers.
_H_BASE = (0.0, 11000.0, 20000.0, 32000.0, 47000.0, 51000.0, 71000.0)
_LAPSE = (-0.0065, 0.0, 0.001, 0.0028, 0.0, -0.0028, -0.002)
_T_BASE = (288.15, 216.65, 216.65, 228.65, 270.65, 270.65, 214.65)
_P_BASE = (101325.0, 22632.06, 5474.889, 868.0187, 110.9063, 66.93887, 3.956420)

H_MAX = 84852.0  # top of the modelled region, geopotential metres


class AltitudeOutOfRange(ValueError):
    """Requested altitude lies outside the modelled 0-86 km band.

    Raised rather than silently clamping. A trajectory that leaves this band is
    telling you something, and swallowing it is how the previous model produced
    a plausible-looking apogee that was actually the edge of a table.
    """


@dataclass(frozen=True)
class AtmState:
    """Atmospheric state at a point.

    Attributes
    ----------
    rho : density, kg/m^3
    P   : pressure, Pa
    T   : temperature, K
    a   : speed of sound, m/s
    mu  : dynamic viscosity, Pa s
    """

    rho: float
    P: float
    T: float
    a: float
    mu: float


def geopotential(z: float) -> float:
    """Geometric altitude (m) to geopotential altitude (m')."""
    return R_EARTH * z / (R_EARTH + z)


def geometric(h: float) -> float:
    """Geopotential altitude (m') to geometric altitude (m)."""
    return R_EARTH * h / (R_EARTH - h)


def _layer(h: float) -> int:
    """Index of the layer containing geopotential altitude ``h``."""
    i = 0
    for k, hb in enumerate(_H_BASE):
        if h >= hb:
            i = k
        else:
            break
    return i


def state(z: float) -> AtmState:
    """Atmospheric state at geometric altitude ``z`` (m above mean sea level).

    Parameters
    ----------
    z : geometric altitude, metres MSL. Negative values down to -610 m are
        permitted (the standard's lower bound).

    Raises
    ------
    AltitudeOutOfRange
        If ``z`` is below -610 m or above roughly 86 km geometric.
    """
    h = geopotential(z)
    if h < -610.0 or h > H_MAX:
        raise AltitudeOutOfRange(
            f"geometric altitude {z:.1f} m (geopotential {h:.1f} m') is outside "
            f"the US Standard Atmosphere 1976 range of -610 to {H_MAX:.0f} m'. "
            "This is a real signal, not a nuisance: check the trajectory."
        )

    i = _layer(h)
    hb, lapse, tb, pb = _H_BASE[i], _LAPSE[i], _T_BASE[i], _P_BASE[i]

    T = tb + lapse * (h - hb)

    if lapse == 0.0:
        P = pb * math.exp(-G0 * (h - hb) / (R_AIR * tb))
    else:
        P = pb * (tb / T) ** (G0 / (R_AIR * lapse))

    rho = P / (R_AIR * T)
    a = math.sqrt(GAMMA * R_AIR * T)
    mu = _BETA * T ** 1.5 / (T + _S)

    return AtmState(rho=rho, P=P, T=T, a=a, mu=mu)


def density(z: float) -> float:
    """Density (kg/m^3) at geometric altitude ``z`` (m MSL)."""
    return state(z).rho


def speed_of_sound(z: float) -> float:
    """Speed of sound (m/s) at geometric altitude ``z`` (m MSL)."""
    return state(z).a


def pressure(z: float) -> float:
    """Pressure (Pa) at geometric altitude ``z`` (m MSL)."""
    return state(z).P
