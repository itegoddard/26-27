"""Aerodynamic geometry, drag build-up, normal force and roll."""

from __future__ import annotations

import math

import pytest

from goddard.aero import drag as drag_mod
from goddard.aero import geometry as geom_mod
from goddard.aero import normal_force as nf_mod
from goddard.aero import roll as roll_mod


# ------------------------------------------------------------------ geometry


def test_reference_area_is_body_cross_section(vehicle_geometry):
    expected = math.pi * (0.1524 / 2.0) ** 2
    assert vehicle_geometry.reference_area_m2 == pytest.approx(expected)


def test_haack_wetted_area_is_between_cone_and_cylinder(vehicle_geometry):
    """Sanity bound: a Haack nose lies between a cone and a full cylinder."""
    nose = vehicle_geometry.nose
    R, L = nose.base_diameter_m / 2.0, nose.length_m
    cone = math.pi * R * math.hypot(R, L)
    cylinder = 2.0 * math.pi * R * L
    assert cone < nose.wetted_area_m2 < cylinder


def test_wetted_area_is_cached_and_stable(vehicle_geometry):
    first = vehicle_geometry.nose.wetted_area_m2
    second = vehicle_geometry.nose.wetted_area_m2
    assert first == second


def test_fin_aspect_ratio_is_low_for_the_ork_planform(vehicle_geometry):
    assert 0.4 < vehicle_geometry.fins.aspect_ratio < 0.9


def test_absent_transition_reports_not_present(vehicle_geometry):
    assert not vehicle_geometry.transition.present
    assert vehicle_geometry.transition.area_change_m2 == pytest.approx(0.0)


def test_flare_reports_present_and_adds_area():
    t = geom_mod.TransitionGeometry(
        length_m=0.2, fore_diameter_m=0.127, aft_diameter_m=0.1524
    )
    assert t.present
    assert t.area_change_m2 > 0.0


# ---------------------------------------------------------------------- drag


def test_skin_friction_falls_with_reynolds():
    low = drag_mod.skin_friction_coefficient(1e6, 0.0, 4.0, 0.3)
    high = drag_mod.skin_friction_coefficient(1e8, 0.0, 4.0, 0.3)
    assert high < low


def test_roughness_sets_a_friction_floor():
    smooth = drag_mod.skin_friction_coefficient(1e8, 0.0, 4.0, 0.3)
    rough = drag_mod.skin_friction_coefficient(1e8, 200e-6, 4.0, 0.3)
    assert rough > smooth


def test_no_wave_drag_below_critical_mach():
    assert drag_mod.nose_wave_drag(5.0, 0.5) == 0.0
    assert drag_mod.nose_wave_drag(5.0, 0.85) == 0.0


def test_wave_drag_appears_transonically_and_is_continuous():
    """No step at M = 0.9, or the integrator sees a discontinuity."""
    just_below = drag_mod.nose_wave_drag(5.0, 0.899)
    just_above = drag_mod.nose_wave_drag(5.0, 0.901)
    assert just_below == 0.0
    assert just_above < 0.01


def test_slenderer_nose_has_less_wave_drag():
    """The 1/f**2 slender-body scaling."""
    blunt = drag_mod.nose_wave_drag(3.0, 2.0)
    slender = drag_mod.nose_wave_drag(6.0, 2.0)
    assert slender < blunt
    assert blunt / slender == pytest.approx(4.0, rel=1e-6)


def test_base_drag_peaks_transonically_then_decays():
    subsonic = drag_mod.base_drag(0.5)
    transonic = drag_mod.base_drag(0.99)
    supersonic = drag_mod.base_drag(2.5)
    assert transonic > subsonic
    assert supersonic < transonic


def test_jet_blockage_reduces_base_drag():
    assert drag_mod.base_drag(2.0, jet_blockage=0.8) < drag_mod.base_drag(2.0)
    assert drag_mod.base_drag(2.0, jet_blockage=1.0) == 0.0


def test_rounded_leading_edge_costs_more_than_a_wedge(vehicle_geometry):
    """Prices register B17. The ORK specifies rounded."""
    import dataclasses

    rounded = vehicle_geometry
    wedge = dataclasses.replace(
        vehicle_geometry,
        fins=dataclasses.replace(
            vehicle_geometry.fins, cross_section="double_wedge"
        ),
    )
    assert drag_mod.fin_wave_drag(rounded, 2.5) > drag_mod.fin_wave_drag(wedge, 2.5)


def test_buildup_total_is_the_sum_of_its_parts(vehicle_geometry):
    b = drag_mod.buildup(vehicle_geometry, mach=2.0, reynolds=5e7)
    assert b.total == pytest.approx(
        b.friction + b.nose_wave + b.transition_wave
        + b.fin_wave + b.base + b.interference
    )


def test_buildup_is_flagged_unvalidated(vehicle_geometry):
    """Supersonic terms are approximations and must say so."""
    assert drag_mod.buildup(vehicle_geometry, 2.0, 5e7).validated is False


def test_drag_varies_substantially_across_mach(vehicle_geometry):
    subsonic = drag_mod.buildup(vehicle_geometry, 0.5, 2e7).total
    supersonic = drag_mod.buildup(vehicle_geometry, 2.0, 5e7).total
    assert supersonic != pytest.approx(subsonic, rel=0.05)


# -------------------------------------------------------------- normal force


def test_von_karman_cp_is_at_half_the_nose_length(vehicle_geometry):
    """Derived, not tabulated: the Haack C=0 volume is exactly A_base*L/2,
    so x_cp = L - V/A_base = L/2."""
    _, x_cp = nf_mod.nose_contribution(vehicle_geometry)
    assert x_cp == pytest.approx(vehicle_geometry.nose.length_m / 2.0)


def test_nose_cn_alpha_is_two_on_its_own_base_area(vehicle_geometry):
    cn_alpha, _ = nf_mod.nose_contribution(vehicle_geometry)
    ratio = (
        vehicle_geometry.nose.base_area_m2 / vehicle_geometry.reference_area_m2
    )
    assert cn_alpha == pytest.approx(2.0 * ratio)


def test_fins_dominate_the_normal_force(vehicle_geometry):
    nose_cn, _ = nf_mod.nose_contribution(vehicle_geometry)
    fin_cn, _ = nf_mod.fin_contribution(vehicle_geometry)
    assert fin_cn > nose_cn


def test_centre_of_pressure_is_aft_of_the_nose(vehicle_geometry):
    nf = nf_mod.evaluate(vehicle_geometry, mach=0.5, alpha_rad=0.02)
    assert 0.0 < nf.x_cp_m < vehicle_geometry.total_length_m
    assert nf.x_cp_m > vehicle_geometry.nose.length_m


def test_static_margin_is_positive_for_a_tail_heavy_cp(vehicle_geometry):
    margin = nf_mod.static_margin(3.5, 2.0, 0.1524)
    assert margin == pytest.approx(1.5 / 0.1524)


def test_normal_force_reverses_with_angle_of_attack(vehicle_geometry):
    pos = nf_mod.evaluate(vehicle_geometry, 0.5, 0.05).cn
    neg = nf_mod.evaluate(vehicle_geometry, 0.5, -0.05).cn
    assert pos > 0.0 > neg
    assert pos == pytest.approx(-neg, rel=1e-9)


def test_crossflow_is_negligible_at_small_alpha_and_grows(vehicle_geometry):
    small, _ = nf_mod.body_crossflow(vehicle_geometry, math.radians(1.0))
    large, _ = nf_mod.body_crossflow(vehicle_geometry, math.radians(10.0))
    assert abs(large) > 10.0 * abs(small)


def test_compressibility_factor_is_floored_transonically():
    assert nf_mod.compressibility_factor(1.0) == pytest.approx(0.5)
    assert nf_mod.compressibility_factor(0.0) == pytest.approx(1.0)


# ---------------------------------------------------------------------- roll


def test_equilibrium_roll_rate_is_proportional_to_speed(vehicle_geometry):
    p1 = roll_mod.equilibrium_roll_rate(vehicle_geometry, 100.0)
    p2 = roll_mod.equilibrium_roll_rate(vehicle_geometry, 200.0)
    assert p2 == pytest.approx(2.0 * p1)


def test_equilibrium_roll_rate_is_independent_of_density(vehicle_geometry):
    """Density cancels between the driving and damping integrals."""
    thick = roll_mod.evaluate(vehicle_geometry, 200.0, 0.0, 1.2, 0.6)
    thin = roll_mod.evaluate(vehicle_geometry, 200.0, 0.0, 0.2, 0.6)
    assert thick.equilibrium_p == pytest.approx(thin.equilibrium_p)


def test_zero_cant_produces_no_roll(vehicle_geometry):
    import dataclasses

    straight = dataclasses.replace(
        vehicle_geometry,
        fins=dataclasses.replace(vehicle_geometry.fins, cant_angle_rad=0.0),
    )
    assert roll_mod.equilibrium_roll_rate(straight, 200.0) == pytest.approx(0.0)
    state = roll_mod.evaluate(straight, 200.0, 0.0, 1.0, 0.6)
    assert state.moment_Nm == pytest.approx(0.0)


def test_roll_moment_vanishes_at_the_equilibrium_rate(vehicle_geometry):
    """Definition of equilibrium: driving and damping exactly cancel."""
    p_eq = roll_mod.equilibrium_roll_rate(vehicle_geometry, 250.0)
    state = roll_mod.evaluate(vehicle_geometry, 250.0, p_eq, 1.0, 0.7)
    assert state.moment_Nm == pytest.approx(0.0, abs=1e-6)


def test_roll_moment_opposes_excess_rate(vehicle_geometry):
    p_eq = roll_mod.equilibrium_roll_rate(vehicle_geometry, 250.0)
    over = roll_mod.evaluate(vehicle_geometry, 250.0, p_eq * 1.5, 1.0, 0.7)
    under = roll_mod.evaluate(vehicle_geometry, 250.0, p_eq * 0.5, 1.0, 0.7)
    assert over.moment_Nm < 0.0 < under.moment_Nm


def test_panel_moments_are_ordered(vehicle_geometry):
    area, m1, m2 = roll_mod.panel_moments(vehicle_geometry)
    assert area > 0.0 and m1 > 0.0 and m2 > 0.0
    # y is at least the body radius, so M1 >= R*S and M2 >= R*M1
    R = vehicle_geometry.body.diameter_m / 2.0
    assert m1 >= R * area
    assert m2 >= R * m1


def test_zero_speed_gives_no_roll(vehicle_geometry):
    state = roll_mod.evaluate(vehicle_geometry, 0.0, 0.0, 1.0, 0.0)
    assert state.moment_Nm == 0.0
    assert state.equilibrium_p == 0.0
