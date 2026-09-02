"""Solid fuel grain properties for the paraffin / SEBS-MA / carbon black blend.

Spec section 4.3.

Composition is fixed by team decision at 89 % paraffin, 10 % SEBS-MA, 1 %
carbon black by mass.

Regression law
--------------
    rdot = calib * a * G_ox ** n

``a`` and ``n`` are published for *pure* paraffin (Karabeyoglu et al. 2004,
doi:10.2514/1.3340). The blend perturbs the regression rate in both directions
and the net effect is not resolvable from the literature:

  - 10 % SEBS-MA raises melt viscosity and stabilises the liquid film, which
    suppresses entrainment and LOWERS rdot (doi:10.2514/2.5976).
  - 1 % carbon black opacifies the fuel and raises surface absorption, which
    RAISES rdot.

The entire net effect is carried in ``calib`` (``regression_calibration``).
There are no other correction factors anywhere in this module. That constant is
unmeasured -- no static fire is planned -- so it is swept in band mode rather
than trusted as a point value. See spec section 6 and assumption register F8.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# ------------------------------------------------- composition (mass fraction)
FRAC_PARAFFIN = 0.89
FRAC_SEBS_MA = 0.10
FRAC_CARBON_BLACK = 0.01

# Component densities, kg/m^3. All three are ESTIMATED -- see assumption
# register F2, F3, F4. Paraffin density in particular varies with melting-point
# grade, so this should be replaced with a measured value for the actual wax.
RHO_PARAFFIN = 924.0
RHO_SEBS_MA = 910.0
RHO_CARBON_BLACK = 1900.0

# Regression law constants for pure paraffin (Karabeyoglu 2004).
# rdot in m/s with G_ox in kg/(m^2 s).
REGRESSION_A = 1.55e-4
REGRESSION_N = 0.5


def blend_density() -> float:
    """Mass-weighted density of the fuel blend, kg/m^3.

    Mass-weighting (rather than volume-weighting) is the right choice here
    because the composition is specified by mass fraction.
    """
    return (
        FRAC_PARAFFIN * RHO_PARAFFIN
        + FRAC_SEBS_MA * RHO_SEBS_MA
        + FRAC_CARBON_BLACK * RHO_CARBON_BLACK
    )


RHO_FUEL = blend_density()  # ~932 kg/m^3


@dataclass(frozen=True)
class RegressionResult:
    """Result of a regression-rate evaluation.

    Attributes
    ----------
    r_dot : surface regression rate, m/s
    G_ox  : oxidiser mass flux through the port, kg/(m^2 s)
    m_dot_fuel : fuel mass generation rate, kg/s
    of_ratio : oxidiser-to-fuel mass ratio, dimensionless
    """

    r_dot: float
    G_ox: float
    m_dot_fuel: float
    of_ratio: float


def oxidiser_flux(m_dot_ox: float, r_port: float) -> float:
    """Oxidiser mass flux (kg/m^2/s) through a circular port.

    Parameters
    ----------
    m_dot_ox : oxidiser mass flow, kg/s
    r_port   : current port radius, m
    """
    if r_port <= 0.0:
        raise ValueError(f"port radius must be positive, got {r_port}")
    return m_dot_ox / (math.pi * r_port ** 2)


# Lower flame-holding limit, kg/(m^2 s). Below this the diffusion flame cannot
# anchor and combustion blows out; the grain stops regressing even though
# oxidiser is still trickling through.
#
# This matters at the END of a blowdown burn, not the start. Without it the
# regression law returns a non-zero rate for ANY non-zero flux, so the model
# keeps eating fuel through the whole vapour tail: on the v1 config the liquid
# phase ended at 18 s with 18 % of the web intact, and the phantom tail burn
# then consumed all of it and reported burnthrough. Both the burnthrough and
# the impulse it added were artefacts.
#
# ESTIMATE. The upper flame-holding limit (~650 for single-port paraffin/N2O)
# is far better characterised than the lower one. Treat 20 as a placeholder
# until a static fire shows where this motor actually blows out.
MIN_FLUX_FOR_COMBUSTION = 20.0


def regression_rate(
    G_ox: float,
    calibration: float,
    min_flux: float = MIN_FLUX_FOR_COMBUSTION,
) -> float:
    """Surface regression rate (m/s).

    Parameters
    ----------
    G_ox        : oxidiser mass flux, kg/(m^2 s)
    calibration : ``regression_calibration``, the single unmeasured constant
                  carrying the whole SEBS-MA / carbon-black net effect.
    min_flux    : flame-holding floor. Returns zero below it -- the flame has
                  blown out, so the grain stops regressing. Pass 0.0 to
                  disable, which restores the old always-burning behaviour.
    """
    if G_ox < 0.0:
        raise ValueError(f"oxidiser flux must be non-negative, got {G_ox}")
    if G_ox < min_flux:
        return 0.0
    return calibration * REGRESSION_A * G_ox ** REGRESSION_N


def evaluate(
    m_dot_ox: float,
    r_port: float,
    grain_length: float,
    calibration: float,
    rho_fuel: float = RHO_FUEL,
) -> RegressionResult:
    """Evaluate regression, fuel mass flow and O/F for a single circular port.

    Parameters
    ----------
    m_dot_ox     : oxidiser mass flow, kg/s
    r_port       : current port radius, m
    grain_length : grain length, m
    calibration  : ``regression_calibration``
    rho_fuel     : fuel density, kg/m^3 (defaults to the blend value)

    Notes
    -----
    Oxidiser mass flow is set by the tank and injector, NOT by the grain.
    Consequently a lower regression rate produces LESS fuel and therefore a
    HIGHER O/F. Since c* peaks near O/F 7-8, "conservative regression" does not
    reliably mean "conservative apogee" -- the sign depends on which side of the
    c* peak the design sits. This is the argument in spec section 6.1 and it is
    why band mode exists. Do not collapse it to a point estimate without
    re-examining port burnthrough separately.
    """
    if grain_length <= 0.0:
        raise ValueError(f"grain length must be positive, got {grain_length}")

    G_ox = oxidiser_flux(m_dot_ox, r_port)
    r_dot = regression_rate(G_ox, calibration)
    burn_area = 2.0 * math.pi * r_port * grain_length
    m_dot_fuel = rho_fuel * burn_area * r_dot

    if m_dot_fuel <= 0.0:
        of_ratio = math.inf
    else:
        of_ratio = m_dot_ox / m_dot_fuel

    return RegressionResult(
        r_dot=r_dot, G_ox=G_ox, m_dot_fuel=m_dot_fuel, of_ratio=of_ratio
    )
