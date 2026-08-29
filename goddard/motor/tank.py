"""Self-pressurizing N2O tank blowdown.

Spec section 4.1.

Two regimes:

1. **Liquid phase.** Liquid drains, vapour expands into the freed volume, and
   liquid boils to hold saturation. The latent heat of that boiling comes out of
   the remaining propellant, so the tank chills and its pressure falls. This is
   what makes a blowdown hybrid's thrust taper.
2. **Vapour phase.** Once the liquid is gone the remaining vapour blows down
   adiabatically at much lower pressure -- the thrust tail.

Method
------
Adiabatic quasi-equilibrium (Zilliac & Karabeyoglu, AIAA 2005-3549), selected
over the alternatives on the evidence in Zimmerman et al., AIAA 2013-4045.

The vapour mass required to fill the ullage is set by the volume constraint

    V = m_liquid / rho_liquid(T) + m_vapour / rho_vapour(T)

and temperature is advanced from an energy balance on the tank contents. That
balance needs the latent heat of vaporisation, which ``props.n2o`` cannot yet
supply -- so it is an injected callable, exactly as in ``injector.py``. The
physics here is complete; only the data is outstanding.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from goddard.props import n2o


class SaturationThermo(Protocol):
    """The thermodynamic data the blowdown model needs."""

    def vapour_pressure(self, T: float) -> float: ...
    def liquid_density(self, T: float) -> float: ...
    def vapour_density(self, T: float) -> float: ...
    def enthalpy_vaporisation(self, T: float) -> float: ...


class TankDepleted(RuntimeError):
    """Both liquid and vapour are exhausted."""


@dataclass(frozen=True)
class TankState:
    """Instantaneous tank contents.

    Attributes
    ----------
    liquid_mass_kg : saturated liquid remaining, kg
    vapour_mass_kg : saturated vapour remaining, kg
    temperature_K  : bulk temperature, K
    """

    liquid_mass_kg: float
    vapour_mass_kg: float
    temperature_K: float

    @property
    def total_mass_kg(self) -> float:
        return self.liquid_mass_kg + self.vapour_mass_kg

    @property
    def has_liquid(self) -> bool:
        return self.liquid_mass_kg > 1e-9


def initial_state(
    volume_m3: float, fill_fraction: float, temperature_K: float
) -> TankState:
    """Fill a tank to ``fill_fraction`` of its volume with saturated liquid.

    The remaining ullage is saturated vapour at the same temperature.
    """
    if volume_m3 <= 0.0:
        raise ValueError("tank volume must be positive")
    if not 0.0 < fill_fraction <= 1.0:
        raise ValueError(f"fill fraction must be in (0, 1], got {fill_fraction}")

    rho_l = n2o.liquid_density(temperature_K)
    rho_v = n2o.vapour_density(temperature_K)
    liquid_volume = volume_m3 * fill_fraction
    return TankState(
        liquid_mass_kg=liquid_volume * rho_l,
        vapour_mass_kg=(volume_m3 - liquid_volume) * rho_v,
        temperature_K=temperature_K,
    )


def pressure(state: TankState) -> float:
    """Tank pressure, Pa. Saturation pressure while liquid remains."""
    return n2o.vapour_pressure(state.temperature_K)


def liquid_fraction(state: TankState, volume_m3: float) -> float:
    """Fraction of tank volume occupied by liquid."""
    rho_l = n2o.liquid_density(state.temperature_K)
    return (state.liquid_mass_kg / rho_l) / volume_m3


def step_liquid_phase(
    state: TankState,
    volume_m3: float,
    m_dot_out: float,
    dt: float,
    latent_heat: Callable[[float], float],
    liquid_heat_capacity: float = 2200.0,
) -> TankState:
    """Advance one step while saturated liquid remains.

    Parameters
    ----------
    m_dot_out : liquid mass flow leaving through the injector, kg/s
    latent_heat : callable ``T -> h_vap`` in J/kg. ``props.n2o`` cannot supply
        this yet; pass your own once the ESDU 91022 coefficients are in hand.
    liquid_heat_capacity : specific heat of saturated liquid N2O, J/(kg K).
        The 2200 default is representative near room temperature and should be
        replaced with a temperature-dependent value from the same source.

    Notes
    -----
    Energy balance: draining liquid frees volume that vapour must fill, so a
    mass ``dm_vap`` boils. The latent heat comes out of the remaining liquid,
    dropping the temperature by ``dm_vap * h_vap / (m_liquid * c_liquid)``.
    """
    if dt <= 0.0:
        raise ValueError("time step must be positive")
    if m_dot_out < 0.0:
        raise ValueError("mass flow must be non-negative")
    if not state.has_liquid:
        raise TankDepleted("no liquid remains; use step_vapour_phase")

    T = state.temperature_K
    rho_l = n2o.liquid_density(T)
    rho_v = n2o.vapour_density(T)

    drained = min(m_dot_out * dt, state.liquid_mass_kg)
    m_l = state.liquid_mass_kg - drained

    # Vapour must expand to fill the whole ullage volume at saturation.
    ullage = volume_m3 - m_l / rho_l
    m_v_required = ullage * rho_v
    boiled = max(0.0, m_v_required - state.vapour_mass_kg)
    boiled = min(boiled, m_l)

    m_l -= boiled
    m_v = m_v_required

    if m_l > 1e-9:
        dT = boiled * latent_heat(T) / (m_l * liquid_heat_capacity)
        T_new = T - dT
    else:
        T_new = T

    T_new = max(T_new, n2o.T_TRIPLE + 0.5)
    return TankState(liquid_mass_kg=max(0.0, m_l), vapour_mass_kg=m_v, temperature_K=T_new)


def step_vapour_phase(
    state: TankState,
    volume_m3: float,
    m_dot_out: float,
    dt: float,
    gamma: float = 1.27,
) -> TankState:
    """Advance one step after the liquid is gone -- adiabatic vapour blowdown.

    The remaining vapour expands isentropically as it drains, so temperature
    falls with density as ``T ~ rho**(gamma - 1)``. Thrust in this regime is a
    small fraction of the liquid-phase value; it is modelled so the tail is
    represented rather than truncated.
    """
    if dt <= 0.0:
        raise ValueError("time step must be positive")
    if state.vapour_mass_kg <= 1e-12:
        raise TankDepleted("tank is empty")

    drained = min(m_dot_out * dt, state.vapour_mass_kg)
    m_v = state.vapour_mass_kg - drained
    if m_v <= 1e-12:
        return TankState(0.0, 0.0, state.temperature_K)

    ratio = m_v / state.vapour_mass_kg
    T_new = max(
        state.temperature_K * ratio ** (gamma - 1.0), n2o.T_TRIPLE + 0.5
    )
    return TankState(liquid_mass_kg=0.0, vapour_mass_kg=m_v, temperature_K=T_new)


def step(
    state: TankState,
    volume_m3: float,
    m_dot_out: float,
    dt: float,
    latent_heat: Callable[[float], float] | None = None,
    gamma_vapour: float = 1.27,
) -> TankState:
    """Advance the tank one step, choosing the regime automatically."""
    if state.has_liquid:
        if latent_heat is None:
            raise ValueError(
                "liquid-phase blowdown needs a latent_heat(T) callable. "
                "props.n2o.enthalpy_vaporisation raises until the ESDU 91022 "
                "coefficients are verified -- see docs/assumptions_register.md."
            )
        return step_liquid_phase(state, volume_m3, m_dot_out, dt, latent_heat)
    return step_vapour_phase(state, volume_m3, m_dot_out, dt, gamma_vapour)
