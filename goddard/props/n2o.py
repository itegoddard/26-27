"""Saturated nitrous oxide thermophysical properties.

Spec section 4.1.

At the specified 99.9 % purity the pure-component correlations apply directly;
no mixture model is used. See ``ullage_noncondensable_fraction`` in the tank
config, which exists as a sensitivity knob and defaults to zero.

Reference
---------
ESDU International, *Thermophysical Properties of Nitrous Oxide*, ESDU 91022,
London, 1991. See ``docs/references.bib`` (key ``esdu91022``).

Validation
----------
The three implemented correlations were checked against independently known
values for N2O at 20 degC (293.15 K):

    quantity              this module    accepted
    vapour pressure       5.060 MPa      ~5.05-5.09 MPa
    liquid density        786.6 kg/m3    ~786 kg/m3
    vapour density        158.2 kg/m3    ~158 kg/m3

See ``tests/test_n2o.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# ------------------------------------------------------------- critical point
T_CRIT = 309.57      # K
P_CRIT = 7.251e6     # Pa
RHO_CRIT = 452.0     # kg/m^3

T_TRIPLE = 182.33    # K, triple point

# Correlation coefficients, ESDU 91022 reduced form.
_B_PSAT = (-6.71893, 1.35966, -1.37780, -4.05100)
_E_PSAT = (1.0, 1.5, 2.5, 5.0)

_B_RHOL = (1.72328, -0.83950, 0.51060, -0.10412)
_E_RHOL = (1.0 / 3.0, 2.0 / 3.0, 1.0, 4.0 / 3.0)

_B_RHOV = (-1.00900, -6.28792, 7.50332, -7.90463, 0.629427)
_E_RHOV = (1.0 / 3.0, 2.0 / 3.0, 1.0, 4.0 / 3.0, 5.0 / 3.0)


class SubTriplePoint(ValueError):
    """Temperature is at or below the N2O triple point.

    A self-pressurizing tank chilling this far through blowdown means the model
    has left the region where the saturated-liquid assumption holds. Raised
    rather than extrapolated.
    """


class SuperCritical(ValueError):
    """Temperature is at or above the N2O critical point.

    There is no liquid/vapour distinction above 309.57 K, so saturation
    properties are meaningless. Raised rather than returning a number.
    """


@dataclass(frozen=True)
class N2OSaturated:
    """Saturated N2O state at a given temperature.

    Attributes
    ----------
    T     : temperature, K
    P_sat : saturation pressure, Pa
    rho_l : saturated liquid density, kg/m^3
    rho_v : saturated vapour density, kg/m^3
    """

    T: float
    P_sat: float
    rho_l: float
    rho_v: float


def _check(T: float) -> None:
    if T <= T_TRIPLE:
        raise SubTriplePoint(
            f"T = {T:.2f} K is at or below the N2O triple point "
            f"({T_TRIPLE} K). Saturated-liquid properties do not apply."
        )
    if T >= T_CRIT:
        raise SuperCritical(
            f"T = {T:.2f} K is at or above the N2O critical point "
            f"({T_CRIT} K). There is no saturation state to return."
        )


def vapour_pressure(T: float) -> float:
    """Saturation pressure (Pa) at temperature ``T`` (K)."""
    _check(T)
    Tr = T / T_CRIT
    s = sum(b * (1.0 - Tr) ** e for b, e in zip(_B_PSAT, _E_PSAT))
    return P_CRIT * math.exp(s / Tr)


def liquid_density(T: float) -> float:
    """Saturated liquid density (kg/m^3) at temperature ``T`` (K)."""
    _check(T)
    Tr = T / T_CRIT
    s = sum(b * (1.0 - Tr) ** e for b, e in zip(_B_RHOL, _E_RHOL))
    return RHO_CRIT * math.exp(s)


def vapour_density(T: float) -> float:
    """Saturated vapour density (kg/m^3) at temperature ``T`` (K)."""
    _check(T)
    Tr = T / T_CRIT
    s = sum(b * (1.0 / Tr - 1.0) ** e for b, e in zip(_B_RHOV, _E_RHOV))
    return RHO_CRIT * math.exp(s)


def saturated(T: float) -> N2OSaturated:
    """Full saturated state at temperature ``T`` (K)."""
    return N2OSaturated(
        T=T,
        P_sat=vapour_pressure(T),
        rho_l=liquid_density(T),
        rho_v=vapour_density(T),
    )


def enthalpy_vaporisation(T: float) -> float:
    """Latent heat of vaporisation (J/kg) at temperature ``T`` (K).

    NOT YET IMPLEMENTED -- deliberately.

    This is required by the Dyer NHNE injector model (spec section 4.2), whose
    homogeneous-equilibrium term needs the enthalpy difference across the
    orifice. The ESDU 91022 latent-heat correlation has a different coefficient
    set from the three implemented above, and those coefficients were not
    available to verify at implementation time.

    Fabricating plausible-looking coefficients here would produce a model that
    runs, returns numbers, and is wrong in a way nobody would catch. That is
    precisely the failure mode this rewrite exists to eliminate, so this raises
    instead.

    To implement: take the latent-heat coefficients from ESDU 91022 and verify
    against the accepted values ~376 kJ/kg at the normal boiling point
    (184.65 K) and ~145-150 kJ/kg at 293.15 K before trusting any result.

    Tracked as assumption register item G11's sibling; see
    ``docs/assumptions_register.md``.
    """
    raise NotImplementedError(
        "N2O latent heat requires the ESDU 91022 coefficient set, which has "
        "not been verified. See the docstring -- this raises on purpose rather "
        "than guessing. Needed before motor/injector.py can be completed."
    )
