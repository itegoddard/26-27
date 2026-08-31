"""Mass properties, recovery staging, heating, dynamics and event detection."""

from __future__ import annotations

import math

import pytest

from goddard import dynamics, mass as mass_mod, recovery as rec_mod
from goddard.events import Event, EventLog, EventRecord, bisect_crossing, \
    interpolate_crossing
from goddard.structures import heating as heat_mod


# ---------------------------------------------------------------------- mass


def test_combine_finds_the_centre_of_gravity():
    parts = [
        mass_mod.MassComponent("fore", 10.0, 1.0),
        mass_mod.MassComponent("aft", 10.0, 3.0),
    ]
    state = mass_mod.combine(parts)
    assert state.mass_kg == pytest.approx(20.0)
    assert state.x_cg_m == pytest.approx(2.0)


def test_parallel_axis_theorem_is_applied():
    """Two point masses about their midpoint: I = sum(m d**2)."""
    parts = [
        mass_mod.MassComponent("a", 5.0, 0.0),
        mass_mod.MassComponent("b", 5.0, 4.0),
    ]
    state = mass_mod.combine(parts)
    assert state.i_pitch == pytest.approx(5.0 * 4.0 + 5.0 * 4.0)


def test_cylinder_inertia_matches_closed_form():
    i_ax, i_lat = mass_mod.cylinder_inertia(10.0, 0.05, 1.0)
    assert i_ax == pytest.approx(0.5 * 10.0 * 0.05 ** 2)
    assert i_lat == pytest.approx(10.0 * (3 * 0.05 ** 2 + 1.0) / 12.0)


def test_tube_inertia_exceeds_solid_cylinder():
    solid, _ = mass_mod.cylinder_inertia(10.0, 0.05, 1.0)
    tube, _ = mass_mod.tube_inertia(10.0, 0.04, 0.05, 1.0)
    assert tube > solid  # mass concentrated at larger radius


def test_propellant_shifts_the_cg(mass_model):
    loaded = mass_model.at(oxidiser_mass_kg=20.0, fuel_mass_kg=8.0)
    empty = mass_model.at(oxidiser_mass_kg=0.0, fuel_mass_kg=0.0)
    assert loaded.mass_kg > empty.mass_kg
    assert loaded.x_cg_m != pytest.approx(empty.x_cg_m)


def test_empty_component_list_rejected():
    with pytest.raises(ValueError):
        mass_mod.combine([])


# ------------------------------------------------------------------ recovery


def test_reefed_drag_area_scales_with_diameter_squared():
    cfg = rec_mod.RecoveryConfig(14.0, 0.35, 300.0)
    assert cfg.reefed_cds_m2 == pytest.approx(14.0 * 0.35 ** 2)
    assert cfg.reefed_cds_m2 < cfg.canopy_cds_m2


def test_reefing_bounds_the_opening_load():
    """The entire point of reefing."""
    cfg = rec_mod.RecoveryConfig(14.0, 0.35, 300.0)
    q = 3000.0
    reefed = rec_mod.opening_load(cfg, rec_mod.Stage.REEFED, q)
    full = rec_mod.opening_load(cfg, rec_mod.Stage.FULL, q)
    assert reefed < full
    assert reefed / full == pytest.approx(0.35 ** 2, rel=1e-9)


def test_inflation_ramps_rather_than_snapping():
    assert rec_mod.inflation_fraction(0.0, 1.0) == 0.0
    assert 0.0 < rec_mod.inflation_fraction(0.5, 1.0) < 1.0
    assert rec_mod.inflation_fraction(1.0, 1.0) == 1.0
    assert rec_mod.inflation_fraction(5.0, 1.0) == 1.0


def test_filling_time_shortens_at_higher_speed():
    cfg = rec_mod.RecoveryConfig(14.0, 0.35, 300.0)
    slow = rec_mod.filling_time(cfg, rec_mod.Stage.FULL, 20.0)
    fast = rec_mod.filling_time(cfg, rec_mod.Stage.FULL, 80.0)
    assert fast < slow
    assert slow / fast == pytest.approx(4.0, rel=1e-9)


def test_drag_area_grows_through_the_transient():
    cfg = rec_mod.RecoveryConfig(14.0, 0.35, 300.0)
    early = rec_mod.drag_area(cfg, rec_mod.Stage.REEFED, 0.01, 60.0)
    late = rec_mod.drag_area(cfg, rec_mod.Stage.REEFED, 10.0, 60.0)
    assert early < late
    assert late == pytest.approx(cfg.reefed_cds_m2)


def test_overload_raises_with_actionable_message():
    cfg = rec_mod.RecoveryConfig(14.0, 1.0, 300.0, max_opening_load_N=100.0)
    with pytest.raises(rec_mod.ChuteOverload) as exc:
        rec_mod.check_load(cfg, rec_mod.Stage.FULL, 5000.0)
    assert "J9" in str(exc.value)


def test_terminal_velocity_falls_with_more_drag_area():
    slow = rec_mod.terminal_velocity(40.0, 14.0, 1.0)
    fast = rec_mod.terminal_velocity(40.0, 0.6, 1.0)
    assert slow < fast


def test_disreef_triggers_below_the_set_altitude():
    cfg = rec_mod.RecoveryConfig(14.0, 0.35, 300.0)
    assert rec_mod.next_stage(rec_mod.Stage.REEFED, 400.0, cfg) is \
        rec_mod.Stage.REEFED
    assert rec_mod.next_stage(rec_mod.Stage.REEFED, 200.0, cfg) is \
        rec_mod.Stage.FULL


def test_invalid_reefing_ratio_rejected():
    with pytest.raises(ValueError):
        rec_mod.RecoveryConfig(14.0, 0.0, 300.0)
    with pytest.raises(ValueError):
        rec_mod.RecoveryConfig(14.0, 1.5, 300.0)


# ------------------------------------------------------------------- heating


def test_heat_flux_scales_with_velocity_cubed():
    a = heat_mod.stagnation_heat_flux(0.5, 500.0, 0.006)
    b = heat_mod.stagnation_heat_flux(0.5, 1000.0, 0.006)
    assert b / a == pytest.approx(8.0, rel=1e-9)


def test_blunter_tip_sees_less_heating():
    sharp = heat_mod.stagnation_heat_flux(0.5, 800.0, 0.003)
    blunt = heat_mod.stagnation_heat_flux(0.5, 800.0, 0.012)
    assert blunt < sharp
    assert sharp / blunt == pytest.approx(2.0, rel=1e-9)


def test_tip_heats_then_radiates_back_down():
    tip = heat_mod.TipThermal(0.006, 0.1, 2.3e-4)
    hot = heat_mod.step_temperature(tip, 300.0, 5e6, 250.0, 0.01)
    assert hot > 300.0
    cooling = heat_mod.step_temperature(tip, 900.0, 0.0, 250.0, 0.01)
    assert cooling < 900.0


def test_service_margin_below_one_means_exceeded():
    tip = heat_mod.TipThermal(0.006, 0.1, 2.3e-4, service_limit_K=550.0)
    assert heat_mod.margin(tip, 500.0) > 1.0
    assert heat_mod.margin(tip, 700.0) < 1.0


def test_zero_velocity_gives_no_heating():
    assert heat_mod.stagnation_heat_flux(0.5, 0.0, 0.006) == 0.0


# ------------------------------------------------------------------ dynamics


def test_angle_of_attack_is_body_minus_flight_path():
    s = dynamics.State(vx=10.0, vz=100.0, theta=math.radians(10.0))
    assert s.flight_path_angle == pytest.approx(math.atan2(10.0, 100.0))
    assert s.angle_of_attack == pytest.approx(
        math.radians(10.0) - math.atan2(10.0, 100.0)
    )


def test_free_fall_accelerates_at_one_g():
    state = dynamics.State(z=1000.0)
    forces = dynamics.Forces(0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 1.0, 1.0)
    d = dynamics.derivatives(state, forces, on_rail=False)
    assert d[3] == pytest.approx(-dynamics.GRAVITY)


def test_thrust_along_a_vertical_body_axis_is_purely_upward():
    state = dynamics.State(theta=0.0)
    forces = dynamics.Forces(1000.0, 0.0, 0.0, 0.0, 0.0, 10.0, 1.0, 1.0)
    d = dynamics.derivatives(state, forces, on_rail=False)
    assert d[2] == pytest.approx(0.0)
    assert d[3] == pytest.approx(1000.0 / 10.0 - dynamics.GRAVITY)


def test_rail_suppresses_rotation():
    state = dynamics.State(theta=0.1, q=0.5)
    forces = dynamics.Forces(1000.0, 0.0, 500.0, 200.0, 50.0, 10.0, 1.0, 1.0)
    on = dynamics.derivatives(state, forces, on_rail=True)
    off = dynamics.derivatives(state, forces, on_rail=False)
    assert on[4] == 0.0 and on[5] == 0.0
    assert off[5] != 0.0


def test_rk4_matches_the_analytic_free_fall_solution():
    state = dynamics.State(z=1000.0)
    forces = dynamics.Forces(0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 1.0, 1.0)
    for _ in range(100):
        state = dynamics.rk4_step(state, forces, 0.01, on_rail=False)
    # z = z0 - g t^2 / 2 after 1 s
    assert state.z == pytest.approx(1000.0 - dynamics.GRAVITY / 2.0, rel=1e-9)
    assert state.vz == pytest.approx(-dynamics.GRAVITY, rel=1e-9)


def test_dynamic_pressure_formula():
    assert dynamics.dynamic_pressure(1.2, 100.0) == pytest.approx(0.5 * 1.2 * 1e4)


def test_zero_mass_rejected():
    forces = dynamics.Forces(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0)
    with pytest.raises(ValueError):
        dynamics.derivatives(dynamics.State(), forces, on_rail=False)


# -------------------------------------------------------------------- events


def test_bisection_finds_a_known_root():
    root = bisect_crossing(lambda t: t - 3.7, 0.0, 10.0)
    assert root == pytest.approx(3.7, abs=1e-5)


def test_bisection_requires_a_sign_change():
    with pytest.raises(ValueError):
        bisect_crossing(lambda t: t + 1.0, 0.0, 10.0)


def test_linear_interpolation_to_a_crossing():
    """Apogee: vz goes +1 to -1 across a step, so the crossing is the midpoint."""
    assert interpolate_crossing(1.0, 1.0, 2.0, -1.0) == pytest.approx(1.5)


def test_event_log_keeps_the_first_occurrence():
    log = EventLog()
    log.record(EventRecord(Event.APOGEE, 50.0, 15000.0, 0.0))
    log.record(EventRecord(Event.APOGEE, 60.0, 14000.0, 0.0))
    assert log.time_of(Event.APOGEE) == 50.0
    assert len(log) == 1


def test_event_log_orders_chronologically():
    log = EventLog()
    log.record(EventRecord(Event.APOGEE, 50.0, 15000.0, 0.0))
    log.record(EventRecord(Event.LAUNCH, 0.0, 0.0, 0.0))
    log.record(EventRecord(Event.BURNOUT, 6.0, 2000.0, 400.0))
    assert [r.event for r in log.all()] == [
        Event.LAUNCH, Event.BURNOUT, Event.APOGEE
    ]


def test_missing_event_reports_none():
    log = EventLog()
    assert not log.has(Event.LANDING)
    assert log.time_of(Event.LANDING) is None
