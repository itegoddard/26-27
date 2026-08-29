"""Motor internals: CEA lookup, injector, tank blowdown, grain, chamber."""

from __future__ import annotations

import math

import pytest

from goddard.config.schema import PlaceholderData
from goddard.motor import chamber as chamber_mod
from goddard.motor import grain as grain_mod
from goddard.motor import injector as inj_mod
from goddard.motor import tank as tank_mod
from goddard.props import cea as cea_mod


# ----------------------------------------------------------------------- CEA


def test_missing_cea_table_refuses_to_guess(tmp_path):
    with pytest.raises(PlaceholderData) as exc:
        cea_mod.load(tmp_path / "nope.csv")
    msg = str(exc.value)
    assert "G11" in msg
    assert "CEA" in msg


def test_cea_round_trips_through_csv(tmp_path, cea_table):
    path = tmp_path / "cea.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("of_ratio,pressure_Pa,c_star_ms,gamma,temperature_K\n")
        for p in cea_table.points:
            f.write(
                f"{p.of_ratio},{p.pressure_Pa},{p.c_star_ms},"
                f"{p.gamma},{p.temperature_K}\n"
            )
    loaded = cea_mod.load(path)
    assert loaded.c_star(7.0, 3e6) == pytest.approx(
        cea_table.c_star(7.0, 3e6), rel=1e-9
    )


def test_cea_peak_is_near_of_seven(cea_table):
    """The fixture is built with a peak at O/F 7; the finder must locate it."""
    assert cea_table.peak_of_ratio(3e6) == pytest.approx(7.0, abs=0.5)


def test_cea_interpolates_between_grid_points(cea_table):
    lo = cea_table.c_star(7.0, 3e6)
    hi = cea_table.c_star(7.5, 3e6)
    mid = cea_table.c_star(7.25, 3e6)
    assert min(lo, hi) <= mid <= max(lo, hi)


def test_cea_clamps_and_records_it(cea_table):
    assert not cea_table.was_clamped
    cea_table.c_star(500.0, 3e6)
    assert cea_table.was_clamped, (
        "an out-of-envelope query must be recorded, not silently clamped"
    )


# ------------------------------------------------------------------ injector


def test_injector_area_is_the_sum_of_orifices():
    g = inj_mod.InjectorGeometry(32, 0.0018, 0.005)
    assert g.area_m2 == pytest.approx(32 * math.pi * 0.0018 ** 2 / 4.0)
    assert g.length_to_diameter == pytest.approx(0.005 / 0.0018)


def test_discharge_coefficient_spans_the_documented_regimes():
    assert inj_mod.discharge_coefficient_estimate(0.5) == pytest.approx(0.61)
    assert inj_mod.discharge_coefficient_estimate(6.0) == pytest.approx(0.82)
    mid = inj_mod.discharge_coefficient_estimate(3.0)
    assert 0.61 < mid < 0.82


def test_spi_scales_with_square_root_of_pressure_drop():
    a, cd, rho = 1e-4, 0.7, 780.0
    low = inj_mod.mass_flow_spi(a, cd, rho, 1e6)
    high = inj_mod.mass_flow_spi(a, cd, rho, 4e6)
    assert high / low == pytest.approx(2.0, rel=1e-9)


def test_no_flow_without_pressure_drop():
    assert inj_mod.mass_flow_spi(1e-4, 0.7, 780.0, 0.0) == 0.0
    assert inj_mod.mass_flow_spi(1e-4, 0.7, 780.0, -1e5) == 0.0


def test_hem_needs_an_enthalpy_drop():
    assert inj_mod.mass_flow_hem(1e-4, 0.7, 150.0, 1e5, 1e5) == 0.0
    assert inj_mod.mass_flow_hem(1e-4, 0.7, 150.0, 2e5, 1e5) > 0.0


def test_dyer_blend_lies_between_spi_and_hem():
    g = inj_mod.InjectorGeometry(32, 0.0018, 0.005)
    cd, p1, p2, pv = 0.7, 5.0e6, 3.0e6, 5.0e6
    rho_l, rho_2 = 780.0, 150.0
    h1, h2 = 3.0e5, 2.0e5

    spi = inj_mod.mass_flow_spi(g.area_m2, cd, rho_l, p1 - p2)
    hem = inj_mod.mass_flow_hem(g.area_m2, cd, rho_2, h1, h2)
    blended = inj_mod.mass_flow(
        g, cd, p1, p2, pv, rho_l,
        rho_downstream=rho_2, h_upstream=h1, h_downstream=h2,
    )
    assert min(spi, hem) <= blended <= max(spi, hem)


def test_dyer_falls_back_to_spi_without_enthalpies():
    g = inj_mod.InjectorGeometry(32, 0.0018, 0.005)
    spi = inj_mod.mass_flow_spi(g.area_m2, 0.7, 780.0, 2.0e6)
    assert inj_mod.mass_flow(g, 0.7, 5e6, 3e6, 5e6, 780.0) == pytest.approx(spi)


def test_chug_margin_falls_as_tank_pressure_decays():
    """The reason chug risk peaks at the burn tail, not at ignition."""
    early = inj_mod.chug_margin(5.0e6, 3.0e6)   # dP/Pc = 0.67, comfortable
    late = inj_mod.chug_margin(3.4e6, 3.0e6)    # dP/Pc = 0.13, under the limit
    assert early > late
    assert early > 1.0
    assert late < 1.0

    # Exactly at the 0.20 criterion the margin is 1.0 by definition.
    assert inj_mod.chug_margin(3.6e6, 3.0e6) == pytest.approx(1.0)


def test_chug_margin_is_one_at_the_criterion():
    assert inj_mod.chug_margin(1.2e6, 1.0e6) == pytest.approx(1.0)


# ---------------------------------------------------------------------- tank


def test_initial_fill_splits_liquid_and_vapour():
    state = tank_mod.initial_state(0.03, 0.85, 293.15)
    assert state.liquid_mass_kg > state.vapour_mass_kg
    assert state.has_liquid
    assert tank_mod.liquid_fraction(state, 0.03) == pytest.approx(0.85, rel=1e-6)


def test_tank_pressure_is_saturation_pressure():
    from goddard.props import n2o

    state = tank_mod.initial_state(0.03, 0.85, 293.15)
    assert tank_mod.pressure(state) == pytest.approx(n2o.vapour_pressure(293.15))


def test_blowdown_drains_liquid_and_chills_the_tank(latent_heat):
    state = tank_mod.initial_state(0.03, 0.85, 293.15)
    m0, T0 = state.liquid_mass_kg, state.temperature_K
    for _ in range(200):
        state = tank_mod.step(state, 0.03, 2.0, 0.01, latent_heat=latent_heat)
    assert state.liquid_mass_kg < m0
    assert state.temperature_K < T0, "self-pressurizing tank must chill as it drains"


def test_tank_pressure_falls_through_blowdown(latent_heat):
    state = tank_mod.initial_state(0.03, 0.85, 293.15)
    p0 = tank_mod.pressure(state)
    for _ in range(300):
        state = tank_mod.step(state, 0.03, 2.0, 0.01, latent_heat=latent_heat)
    assert tank_mod.pressure(state) < p0


def test_liquid_phase_requires_latent_heat():
    state = tank_mod.initial_state(0.03, 0.85, 293.15)
    with pytest.raises(ValueError, match="latent_heat"):
        tank_mod.step(state, 0.03, 2.0, 0.01, latent_heat=None)


def test_vapour_phase_blowdown_cools_and_empties():
    state = tank_mod.TankState(0.0, 2.0, 280.0)
    state = tank_mod.step_vapour_phase(state, 0.03, 1.0, 0.1)
    assert state.vapour_mass_kg < 2.0
    assert state.temperature_K < 280.0


def test_empty_tank_raises():
    with pytest.raises(tank_mod.TankDepleted):
        tank_mod.step_vapour_phase(tank_mod.TankState(0.0, 0.0, 280.0), 0.03, 1.0, 0.1)


def test_rejects_bad_fill_fraction():
    with pytest.raises(ValueError):
        tank_mod.initial_state(0.03, 0.0, 293.15)
    with pytest.raises(ValueError):
        tank_mod.initial_state(0.03, 1.5, 293.15)


# --------------------------------------------------------------------- grain


def test_grain_geometry_validates_web():
    with pytest.raises(ValueError):
        grain_mod.GrainGeometry(0.75, 0.05, 0.04)  # port bigger than OD


def test_initial_fuel_mass_is_the_annulus():
    g = grain_mod.GrainGeometry(0.75, 0.030, 0.062)
    expected = 932.4 * math.pi * (0.062 ** 2 - 0.030 ** 2) * 0.75
    assert g.initial_fuel_mass() == pytest.approx(expected, rel=1e-3)


def test_web_fraction_starts_at_one_and_falls():
    g = grain_mod.GrainGeometry(0.75, 0.030, 0.062)
    start = grain_mod.GrainState(0.030)
    assert grain_mod.web_fraction(g, start) == pytest.approx(1.0)
    later = grain_mod.step(g, start, r_dot=0.001, dt=1.0)
    assert grain_mod.web_fraction(g, later) < 1.0


def test_burnthrough_raises_when_requested():
    g = grain_mod.GrainGeometry(0.75, 0.030, 0.032)
    with pytest.raises(grain_mod.PortBurnthrough):
        grain_mod.step(g, grain_mod.GrainState(0.030), r_dot=0.01, dt=1.0)


def test_burnthrough_can_be_recorded_instead_of_raised():
    """Band mode needs a burnt-through corner to be data, not a crash."""
    g = grain_mod.GrainGeometry(0.75, 0.030, 0.032)
    state = grain_mod.step(
        g, grain_mod.GrainState(0.030), r_dot=0.01, dt=1.0,
        raise_on_burnthrough=False,
    )
    assert state.port_radius_m == pytest.approx(g.outer_radius_m)
    assert grain_mod.web_fraction(g, state) == pytest.approx(0.0)


def test_fuel_mass_falls_as_the_port_opens():
    g = grain_mod.GrainGeometry(0.75, 0.030, 0.062)
    full = grain_mod.fuel_mass_remaining(g, grain_mod.GrainState(0.030))
    partial = grain_mod.fuel_mass_remaining(g, grain_mod.GrainState(0.045))
    assert partial < full


# ------------------------------------------------------------------- chamber


def _chamber_kwargs(cea_table, **overrides):
    kw = dict(
        tank_pressure=5.0e6,
        vapour_pressure=5.0e6,
        rho_liquid=780.0,
        ambient_pressure=87000.0,
        injector_geom=inj_mod.InjectorGeometry(32, 0.0018, 0.005),
        injector_cd=0.70,
        grain_geom=grain_mod.GrainGeometry(0.75, 0.030, 0.062),
        grain_state=grain_mod.GrainState(0.030),
        calibration=0.85,
        eta_cstar=0.88,
        throat_area=math.pi * (0.021 / 2.0) ** 2,
        expansion_ratio=4.5,
        cea=cea_table,
    )
    kw.update(overrides)
    return kw


def test_chamber_balance_is_self_consistent(cea_table):
    """Chamber pressure must reproduce itself through the c* relation."""
    state = chamber_mod.solve(**_chamber_kwargs(cea_table))
    predicted = (
        state.m_dot_total * state.c_star_ms / (math.pi * (0.021 / 2.0) ** 2)
    )
    assert predicted == pytest.approx(state.chamber_pressure_Pa, rel=1e-3)


def test_chamber_pressure_sits_below_tank_pressure(cea_table):
    state = chamber_mod.solve(**_chamber_kwargs(cea_table))
    assert 0.0 < state.chamber_pressure_Pa < 5.0e6


def test_thrust_and_flows_are_positive(cea_table):
    state = chamber_mod.solve(**_chamber_kwargs(cea_table))
    assert state.thrust_N > 0.0
    assert state.m_dot_ox > 0.0
    assert state.m_dot_fuel > 0.0
    assert 0.5 < state.of_ratio < 40.0


def test_lower_regression_raises_of_ratio(cea_table):
    """Spec 6.1 again, now through the full chamber balance."""
    low = chamber_mod.solve(**_chamber_kwargs(cea_table, calibration=0.75))
    high = chamber_mod.solve(**_chamber_kwargs(cea_table, calibration=1.00))
    assert low.of_ratio > high.of_ratio
    assert low.m_dot_fuel < high.m_dot_fuel


def test_thrust_rises_as_ambient_pressure_falls(cea_table):
    sea = chamber_mod.solve(**_chamber_kwargs(cea_table, ambient_pressure=101325.0))
    high = chamber_mod.solve(**_chamber_kwargs(cea_table, ambient_pressure=10000.0))
    assert high.thrust_N > sea.thrust_N


def test_tank_below_ambient_cannot_flow(cea_table):
    with pytest.raises(chamber_mod.ChamberSolveFailed):
        chamber_mod.solve(
            **_chamber_kwargs(cea_table, tank_pressure=5.0e4, ambient_pressure=1.0e5)
        )


def test_undersized_throat_is_reported(cea_table):
    with pytest.raises(chamber_mod.ChamberSolveFailed):
        chamber_mod.solve(**_chamber_kwargs(cea_table, throat_area=1e-8))
