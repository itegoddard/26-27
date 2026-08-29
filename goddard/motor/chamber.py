"""Chamber pressure balance -- ties tank, injector, grain and nozzle together.

Spec section 4.4.

At every instant the chamber pressure is the value that balances what the
injector delivers against what the nozzle can pass:

    m_dot_ox  = injector(P_tank, P_c)          falls as P_c rises
    m_dot_f   = grain(m_dot_ox)
    P_c       = (m_dot_ox + m_dot_f) * eta_c* * c*(O/F, P_c) / A_t

The left side falls with ``P_c`` and the right side rises, so the balance is
found by bisection -- robust, no initial guess to tune, and it cannot diverge
the way a fixed-point iteration can at low injector stiffness.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from goddard.motor import grain as grain_mod
from goddard.motor import injector as inj_mod
from goddard.motor import nozzle as nozzle_mod
from goddard.props.cea import CEATable


class ChamberSolveFailed(RuntimeError):
    """No chamber pressure balances the injector against the nozzle."""


@dataclass(frozen=True)
class ChamberState:
    """Motor operating point at one instant.

    Attributes
    ----------
    chamber_pressure_Pa : Pa
    m_dot_ox            : oxidiser mass flow, kg/s
    m_dot_fuel          : fuel mass flow, kg/s
    of_ratio            : oxidiser/fuel mass ratio
    c_star_ms           : delivered characteristic velocity, m/s
    regression_rate_ms  : port surface regression rate, m/s
    thrust_N            : N
    injector_dp_ratio   : dP_inj / P_c
    chug_margin         : ratio to the 0.20 stability criterion; < 1 is at risk
    web_fraction        : fraction of the original grain web remaining
    """

    chamber_pressure_Pa: float
    m_dot_ox: float
    m_dot_fuel: float
    of_ratio: float
    c_star_ms: float
    regression_rate_ms: float
    thrust_N: float
    injector_dp_ratio: float
    chug_margin: float
    web_fraction: float

    @property
    def m_dot_total(self) -> float:
        return self.m_dot_ox + self.m_dot_fuel


def _residual(
    p_chamber: float,
    tank_pressure: float,
    vapour_pressure: float,
    rho_liquid: float,
    injector_geom: inj_mod.InjectorGeometry,
    injector_cd: float,
    grain_geom: grain_mod.GrainGeometry,
    grain_state: grain_mod.GrainState,
    calibration: float,
    eta_cstar: float,
    throat_area: float,
    cea: CEATable,
) -> tuple[float, dict]:
    """``P_c_from_nozzle - P_c_guess`` plus the intermediate quantities."""
    m_dot_ox = inj_mod.mass_flow(
        geometry=injector_geom,
        cd=injector_cd,
        p_upstream=tank_pressure,
        p_downstream=p_chamber,
        p_vapour=vapour_pressure,
        rho_liquid=rho_liquid,
    )

    if m_dot_ox <= 0.0:
        return -p_chamber, {
            "m_dot_ox": 0.0,
            "m_dot_fuel": 0.0,
            "of_ratio": math.inf,
            "c_star": 0.0,
            "r_dot": 0.0,
        }

    reg = grain_mod.evaluate(
        grain_geom, grain_state, m_dot_ox, calibration
    )
    of_ratio = reg.of_ratio
    c_star = cea.c_star(of_ratio, p_chamber)
    m_dot_total = m_dot_ox + reg.m_dot_fuel
    p_predicted = m_dot_total * eta_cstar * c_star / throat_area

    return p_predicted - p_chamber, {
        "m_dot_ox": m_dot_ox,
        "m_dot_fuel": reg.m_dot_fuel,
        "of_ratio": of_ratio,
        "c_star": eta_cstar * c_star,
        "r_dot": reg.r_dot,
    }


def solve(
    tank_pressure: float,
    vapour_pressure: float,
    rho_liquid: float,
    ambient_pressure: float,
    injector_geom: inj_mod.InjectorGeometry,
    injector_cd: float,
    grain_geom: grain_mod.GrainGeometry,
    grain_state: grain_mod.GrainState,
    calibration: float,
    eta_cstar: float,
    throat_area: float,
    expansion_ratio: float,
    cea: CEATable,
    eta_cf: float = 0.97,
    min_dp_ratio: float = 0.20,
) -> ChamberState:
    """Solve the chamber balance and evaluate motor output."""
    if throat_area <= 0.0:
        raise ValueError("throat area must be positive")
    if tank_pressure <= ambient_pressure:
        raise ChamberSolveFailed(
            f"tank pressure {tank_pressure:.0f} Pa does not exceed ambient "
            f"{ambient_pressure:.0f} Pa; the motor cannot flow"
        )

    args = (
        tank_pressure,
        vapour_pressure,
        rho_liquid,
        injector_geom,
        injector_cd,
        grain_geom,
        grain_state,
        calibration,
        eta_cstar,
        throat_area,
        cea,
    )

    lo, hi = max(ambient_pressure, 1.0), tank_pressure * 0.999
    r_lo, _ = _residual(lo, *args)
    r_hi, _ = _residual(hi, *args)

    if r_lo < 0.0:
        raise ChamberSolveFailed(
            "even at ambient pressure the nozzle passes more than the injector "
            "delivers -- the throat is oversized for this feed system"
        )
    if r_hi > 0.0:
        # Nozzle cannot pass the flow even at tank pressure: throat too small.
        raise ChamberSolveFailed(
            "chamber pressure would exceed tank pressure -- the throat is "
            "undersized for this injector (register G4 vs E2/E3)"
        )

    # Bisection to 1 Pa over a range of a few MPa needs about 23 halvings; 60 is
    # a generous cap and the early exit almost always fires first. This runs at
    # every integration step, so the bound matters.
    info: dict = {}
    for _ in range(60):
        if hi - lo < 1.0:
            break
        mid = 0.5 * (lo + hi)
        r_mid, info = _residual(mid, *args)
        if r_mid > 0.0:
            lo = mid
        else:
            hi = mid
    p_chamber = 0.5 * (lo + hi)
    _, info = _residual(p_chamber, *args)

    gamma = cea.gamma(info["of_ratio"], p_chamber)
    perf = nozzle_mod.performance(
        p_chamber=p_chamber,
        p_ambient=ambient_pressure,
        throat_area=throat_area,
        expansion_ratio=expansion_ratio,
        gamma=gamma,
        eta_cf=eta_cf,
    )

    dp_ratio = inj_mod.pressure_drop_ratio(tank_pressure, p_chamber)

    return ChamberState(
        chamber_pressure_Pa=p_chamber,
        m_dot_ox=info["m_dot_ox"],
        m_dot_fuel=info["m_dot_fuel"],
        of_ratio=info["of_ratio"],
        c_star_ms=info["c_star"],
        regression_rate_ms=info["r_dot"],
        thrust_N=perf.thrust,
        injector_dp_ratio=dp_ratio,
        chug_margin=dp_ratio / min_dp_ratio,
        web_fraction=grain_mod.web_fraction(grain_geom, grain_state),
    )
