"""Fuel grain state: port growth and burnthrough.

Spec section 4.3. Wraps the regression law in ``props.fuel`` with the geometry
bookkeeping the chamber model needs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from goddard.props import fuel


class PortBurnthrough(RuntimeError):
    """The port has grown out to the grain outer diameter.

    The remaining web is gone and the port has reached the liner. This is the
    failure mode that a single conservative point estimate would have missed --
    see spec section 6.1. Band mode exists so that the HIGH-regression corner
    gets examined, not just the low one.
    """


@dataclass(frozen=True)
class GrainState:
    """Instantaneous grain geometry.

    Attributes
    ----------
    port_radius_m : current port radius, m
    """

    port_radius_m: float


@dataclass(frozen=True)
class GrainGeometry:
    """Fixed grain dimensions."""

    length_m: float
    initial_port_radius_m: float
    outer_radius_m: float

    def __post_init__(self) -> None:
        if self.length_m <= 0.0:
            raise ValueError("grain length must be positive")
        if self.initial_port_radius_m <= 0.0:
            raise ValueError("initial port radius must be positive")
        if self.outer_radius_m <= self.initial_port_radius_m:
            raise ValueError(
                f"outer radius {self.outer_radius_m} must exceed initial port "
                f"radius {self.initial_port_radius_m}"
            )

    @property
    def initial_web_m(self) -> float:
        """Web thickness available to burn, m."""
        return self.outer_radius_m - self.initial_port_radius_m

    def initial_fuel_mass(self, rho_fuel: float = fuel.RHO_FUEL) -> float:
        """Loaded fuel mass, kg."""
        area = math.pi * (self.outer_radius_m ** 2 - self.initial_port_radius_m ** 2)
        return rho_fuel * area * self.length_m


def web_remaining(geometry: GrainGeometry, state: GrainState) -> float:
    """Unburnt web thickness, m. Zero or negative means burnthrough."""
    return geometry.outer_radius_m - state.port_radius_m


def web_fraction(geometry: GrainGeometry, state: GrainState) -> float:
    """Fraction of the original web remaining, 0 to 1."""
    return max(0.0, web_remaining(geometry, state) / geometry.initial_web_m)


def fuel_mass_remaining(
    geometry: GrainGeometry, state: GrainState, rho_fuel: float = fuel.RHO_FUEL
) -> float:
    """Unburnt fuel mass, kg."""
    r = min(state.port_radius_m, geometry.outer_radius_m)
    area = math.pi * (geometry.outer_radius_m ** 2 - r ** 2)
    return rho_fuel * area * geometry.length_m


def evaluate(
    geometry: GrainGeometry,
    state: GrainState,
    m_dot_ox: float,
    calibration: float,
    rho_fuel: float = fuel.RHO_FUEL,
) -> fuel.RegressionResult:
    """Regression rate, fuel flow and O/F at the current port radius."""
    return fuel.evaluate(
        m_dot_ox=m_dot_ox,
        r_port=state.port_radius_m,
        grain_length=geometry.length_m,
        calibration=calibration,
        rho_fuel=rho_fuel,
    )


def step(
    geometry: GrainGeometry,
    state: GrainState,
    r_dot: float,
    dt: float,
    raise_on_burnthrough: bool = True,
) -> GrainState:
    """Advance the port radius by one time step.

    Parameters
    ----------
    raise_on_burnthrough : if True, raise ``PortBurnthrough`` the moment the
        port reaches the outer radius. Band mode sets this False so that a
        burnt-through corner is recorded as a *result* rather than aborting the
        whole sweep.
    """
    if dt <= 0.0:
        raise ValueError("time step must be positive")
    if r_dot < 0.0:
        raise ValueError("regression rate must be non-negative")

    r_new = state.port_radius_m + r_dot * dt
    if r_new >= geometry.outer_radius_m:
        if raise_on_burnthrough:
            raise PortBurnthrough(
                f"port radius {r_new * 1000:.2f} mm has reached the grain outer "
                f"radius {geometry.outer_radius_m * 1000:.2f} mm -- the web is "
                "consumed and the liner is exposed. Increase the web thickness "
                "(register F11) or reduce the burn time."
            )
        r_new = geometry.outer_radius_m
    return GrainState(port_radius_m=r_new)
