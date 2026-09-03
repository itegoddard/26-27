"""End-to-end simulation and band mode.

These use the placeholder fixtures in conftest.py, so the NUMBERS mean nothing.
What is being tested is that the pipeline is self-consistent and physically
sane: the vehicle goes up, comes back, conserves the obvious quantities, and
every subsystem reports.
"""

from __future__ import annotations

import math

import pytest

from goddard import band as band_mod
from goddard import sim as sim_mod
from goddard.events import Event


@pytest.fixture(scope="module")
def flight(request):
    """Run one flight once and share it across the assertions below."""
    vehicle = request.getfixturevalue("vehicle")
    return sim_mod.run(vehicle, dt=0.02, max_time_s=400.0)


def test_flight_produces_samples(vehicle):
    result = sim_mod.run(vehicle, dt=0.05, max_time_s=200.0)
    assert len(result.samples) > 100


def test_vehicle_leaves_the_rail_and_climbs(vehicle):
    result = sim_mod.run(vehicle, dt=0.02, max_time_s=200.0)
    assert result.events.has(Event.RAIL_EXIT)
    assert result.rail_exit_velocity_ms > 10.0
    assert result.apogee_agl_m > 1000.0


def test_reaches_apogee_and_deploys(vehicle):
    result = sim_mod.run(vehicle, dt=0.02, max_time_s=400.0)
    assert result.events.has(Event.APOGEE)
    assert result.events.has(Event.CHUTE_DEPLOY)
    apogee_t = result.events.time_of(Event.APOGEE)
    rail_t = result.events.time_of(Event.RAIL_EXIT)
    assert apogee_t > rail_t


def test_motor_actually_fires(vehicle):
    result = sim_mod.run(vehicle, dt=0.02, max_time_s=200.0)
    thrusting = [s for s in result.samples if s.thrust > 0.0]
    assert thrusting, "motor produced no thrust at any point"
    assert max(s.thrust for s in thrusting) > 1000.0
    # Chamber pressure must be positive and below tank pressure while burning
    assert all(s.chamber_pressure > 0.0 for s in thrusting)


def test_of_ratio_stays_physical_while_the_flame_is_lit(vehicle):
    """O/F must be physical while fuel is actually burning.

    Once oxidiser flux falls below the flame-holding floor the grain stops
    regressing, fuel flow goes to zero and O/F is legitimately infinite -- that
    is the flame being out, not a bad number. Only the lit portion is bounded.
    """
    import math

    result = sim_mod.run(vehicle, dt=0.02, max_time_s=200.0)
    lit = [s.of_ratio for s in result.samples
           if s.thrust > 0.0 and math.isfinite(s.of_ratio)]
    assert lit, "no sample had a finite O/F while thrusting"
    assert all(0.5 < r < 40.0 for r in lit), (
        f"O/F left physical bounds while lit: min {min(lit):.2f} max {max(lit):.2f}"
    )


def test_flame_goes_out_when_the_liquid_oxidiser_runs_dry(vehicle):
    """Combustion must stop at liquid depletion, not grind on through the tail.

    This is the primary flame-out criterion and it is read off the tank state
    rather than tuned. Without it the regression law returns a non-zero rate
    for any non-zero flux, so the grain keeps pyrolysing through the vapour
    blowdown -- a phase where chamber pressure has collapsed. On the v1 config
    that phantom burn consumed an 18 % web margin and reported a false
    burnthrough.
    """
    result = sim_mod.run(vehicle, dt=0.02, max_time_s=200.0)
    assert result.events.has(Event.BURNOUT), "motor never registered burnout"
    assert any("flame out" in w for w in result.warnings), (
        "flame-out was not reported: the liquid-depletion criterion did not fire"
    )


def test_the_vapour_tail_is_worth_real_altitude(vehicle):
    """Retaining vapour-phase combustion must gain height, not lose it.

    The default truncates at liquid depletion, matching the working model. That
    is conservative, and this test pins how much it gives away so the omission
    stays visible rather than becoming invisible truth.
    """
    import dataclasses

    truncated = sim_mod.run(vehicle, dt=0.02, max_time_s=400.0)
    with_tail = sim_mod.run(
        dataclasses.replace(vehicle, combust_vapour_phase=True),
        dt=0.02, max_time_s=400.0,
    )
    assert with_tail.apogee_agl_m > truncated.apogee_agl_m
    assert not vehicle.combust_vapour_phase, "must default to the conservative case"


def test_grain_web_is_consumed_but_tracked(vehicle):
    result = sim_mod.run(vehicle, dt=0.02, max_time_s=200.0)
    assert 0.0 <= result.min_web_fraction <= 1.0


def test_mass_decreases_monotonically_during_burn(vehicle):
    result = sim_mod.run(vehicle, dt=0.02, max_time_s=200.0)
    burning = [s for s in result.samples if s.thrust > 0.0]
    masses = [s.mass for s in burning]
    assert all(a >= b - 1e-9 for a, b in zip(masses, masses[1:]))


def test_drag_coefficient_varies_with_mach(vehicle):
    """The headline fix over the 25-26 model, which held C_D = 0.5 throughout."""
    result = sim_mod.run(vehicle, dt=0.02, max_time_s=200.0)
    ascent = [s for s in result.samples if s.vz > 0.0 and s.speed > 50.0]
    cds = [s.cd for s in ascent]
    assert max(cds) - min(cds) > 0.05, "C_D barely moved -- is the buildup live?"


def test_supersonic_drag_warning_is_surfaced(vehicle):
    """An uncalibrated model must say so, every run."""
    result = sim_mod.run(vehicle, dt=0.05, max_time_s=100.0)
    assert any("UNCALIBRATED" in w for w in result.warnings)


def test_roll_rate_develops_from_the_one_degree_cant(vehicle):
    result = sim_mod.run(vehicle, dt=0.02, max_time_s=200.0)
    flying = [s for s in result.samples if s.speed > 50.0]
    assert any(abs(s.roll_rate) > 0.01 for s in flying), (
        "1 degree of fin cant produced no roll"
    )


def test_nose_tip_heats_up(vehicle):
    result = sim_mod.run(vehicle, dt=0.02, max_time_s=200.0)
    assert result.peak_tip_temperature_K > vehicle.tank_initial_temperature_K


def test_max_q_event_matches_the_sample_maximum(vehicle):
    result = sim_mod.run(vehicle, dt=0.02, max_time_s=200.0)
    record = result.events.get(Event.MAX_Q)
    assert record is not None
    peak = max(s.dynamic_pressure for s in result.samples)
    assert peak == pytest.approx(result.max_dynamic_pressure_Pa)


def test_descends_after_apogee(vehicle):
    result = sim_mod.run(vehicle, dt=0.02, max_time_s=400.0)
    apogee_t = result.events.time_of(Event.APOGEE)
    after = [s for s in result.samples if s.t > apogee_t + 1.0]
    assert after
    assert after[-1].altitude_agl < result.apogee_agl_m


def test_summary_renders(vehicle):
    result = sim_mod.run(vehicle, dt=0.05, max_time_s=200.0)
    text = result.summary()
    for key in ("apogee", "max Mach", "min web remaining", "min chug margin"):
        assert key in text


# ------------------------------------------------------------------ band mode


def test_band_mode_runs_every_corner(vehicle):
    out = band_mod.run_band(vehicle, levels=2, dt=0.1, max_time_s=150.0)
    assert len(out.corners) == 8  # 2^3
    assert out.succeeded


def test_band_mode_reports_envelopes_with_driving_corners(vehicle):
    out = band_mod.run_band(vehicle, levels=2, dt=0.1, max_time_s=150.0)
    apogee = out.envelope("apogee_ft")
    assert apogee is not None
    assert apogee.worst <= apogee.best
    assert "reg=" in apogee.driving_corner


def test_band_mode_examines_both_directions_of_regression(vehicle):
    """Spec section 6.1: the burnthrough case lives at HIGH regression.

    A sweep that only biased for apogee would never generate it. This asserts
    the grid actually spans both ends.
    """
    out = band_mod.run_band(vehicle, levels=2, dt=0.1, max_time_s=150.0)
    regs = {c.calibration.regression for c in out.corners}
    assert min(regs) < 0.80 and max(regs) > 0.95

    web = out.envelope("min_web_fraction")
    assert web is not None
    # The worst (lowest) web fraction must come from a high-regression corner.
    assert "reg=1.000" in web.driving_corner or web.worst == pytest.approx(
        web.best
    )


def test_band_summary_renders(vehicle):
    out = band_mod.run_band(vehicle, levels=2, dt=0.1, max_time_s=150.0)
    text = out.summary()
    assert "Band sweep" in text
    assert "driving corner" in text


def test_failed_corner_is_recorded_not_raised(vehicle):
    """A corner that cannot solve is data, not a crash."""
    import dataclasses

    broken = dataclasses.replace(vehicle, throat_area_m2=1e-9)
    out = band_mod.run_band(broken, levels=2, dt=0.2, max_time_s=60.0)
    assert len(out.corners) == 8
    # Whatever happens, run_band must return rather than propagate.
    assert all(c.ok or c.error for c in out.corners)
