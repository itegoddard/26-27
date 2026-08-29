"""Fin flutter and torsional divergence."""

import math

import pytest

from goddard.structures import flutter as fl

# Planform ratios are the CONFIRMED shape from goddard1.0.ork; absolute sizes
# are OPEN register parameters (B14-B16) and are placeholders here.
PLANFORM = fl.FinPlanform(
    root_chord_m=0.30,
    tip_chord_m=0.30 * 0.328,   # confirmed taper ratio
    span_m=0.11,
    thickness_m=0.005,
)


def test_planform_geometry():
    p = PLANFORM
    assert p.taper_ratio == pytest.approx(0.328)
    assert p.area_m2 == pytest.approx(0.5 * (0.30 + 0.0984) * 0.11)
    assert p.aspect_ratio == pytest.approx(0.11 ** 2 / p.area_m2)
    assert p.mean_chord_m == pytest.approx(p.area_m2 / 0.11)


def test_ork_planform_aspect_ratio_is_low():
    """A heavily swept clipped delta -- AR around 0.5, as expected."""
    assert 0.4 < PLANFORM.aspect_ratio < 0.7


def test_flutter_speed_is_physically_sized():
    v = fl.flutter_speed(
        PLANFORM,
        shear_modulus_Pa=2.0e9,
        ambient_pressure_Pa=101325.0,
        speed_of_sound_ms=340.0,
    )
    assert 100.0 < v < 5000.0


def test_stiffer_fin_flutters_faster():
    kw = dict(ambient_pressure_Pa=101325.0, speed_of_sound_ms=340.0)
    soft = fl.flutter_speed(PLANFORM, shear_modulus_Pa=1.0e9, **kw)
    stiff = fl.flutter_speed(PLANFORM, shear_modulus_Pa=4.0e9, **kw)
    # V_f goes as sqrt(G)
    assert stiff / soft == pytest.approx(2.0, rel=1e-9)


def test_flutter_speed_rises_with_altitude():
    """Lower ambient pressure raises flutter speed -- V_f goes as 1/sqrt(P).

    This is why the check must run along the trajectory rather than at a single
    condition: the vehicle is fastest high up, where the fin is also safest.
    The binding case is wherever the ratio is worst, not where V or P is
    extreme.
    """
    kw = dict(shear_modulus_Pa=2.0e9, speed_of_sound_ms=340.0)
    low = fl.flutter_speed(PLANFORM, ambient_pressure_Pa=101325.0, **kw)
    high = fl.flutter_speed(PLANFORM, ambient_pressure_Pa=12000.0, **kw)
    assert high > low
    assert high / low == pytest.approx(math.sqrt(101325.0 / 12000.0), rel=1e-9)


def test_thinner_fin_is_much_worse():
    """V_f goes as (t/c)^1.5 -- thickness is the dominant flutter driver."""
    kw = dict(
        shear_modulus_Pa=2.0e9,
        ambient_pressure_Pa=101325.0,
        speed_of_sound_ms=340.0,
    )
    thick = fl.flutter_speed(PLANFORM, **kw)
    thin_planform = fl.FinPlanform(
        root_chord_m=0.30, tip_chord_m=0.0984, span_m=0.11, thickness_m=0.0025
    )
    thin = fl.flutter_speed(thin_planform, **kw)
    assert thin / thick == pytest.approx(0.5 ** 1.5, rel=1e-9)


def test_divergence_pressure_scales_with_gj():
    q1 = fl.divergence_pressure(PLANFORM, torsional_stiffness_Nm2=100.0)
    q2 = fl.divergence_pressure(PLANFORM, torsional_stiffness_Nm2=200.0)
    assert q2 == pytest.approx(2.0 * q1)


def test_divergence_pressure_is_positive():
    assert fl.divergence_pressure(PLANFORM, torsional_stiffness_Nm2=150.0) > 0.0


def test_margins_are_ratios_of_critical_to_actual():
    m = fl.margins(
        PLANFORM,
        shear_modulus_Pa=2.0e9,
        torsional_stiffness_Nm2=150.0,
        velocity_ms=600.0,
        dynamic_pressure_Pa=90000.0,
        ambient_pressure_Pa=40000.0,
        speed_of_sound_ms=320.0,
    )
    assert m.flutter_margin == pytest.approx(m.flutter_speed_ms / 600.0)
    assert m.divergence_margin == pytest.approx(m.divergence_pressure_Pa / 90000.0)


def test_critical_flag_trips_when_either_margin_falls_below_one():
    safe = fl.margins(
        PLANFORM,
        shear_modulus_Pa=5.0e9,
        torsional_stiffness_Nm2=5000.0,
        velocity_ms=100.0,
        dynamic_pressure_Pa=5000.0,
        ambient_pressure_Pa=101325.0,
        speed_of_sound_ms=340.0,
    )
    assert not safe.critical

    # Divergence alone should be able to trip it, with flutter still healthy.
    diverging = fl.margins(
        PLANFORM,
        shear_modulus_Pa=5.0e9,
        torsional_stiffness_Nm2=0.5,
        velocity_ms=100.0,
        dynamic_pressure_Pa=5000.0,
        ambient_pressure_Pa=101325.0,
        speed_of_sound_ms=340.0,
    )
    assert diverging.divergence_margin < 1.0
    assert diverging.flutter_margin > 1.0
    assert diverging.critical


def test_zero_speed_gives_infinite_margin():
    m = fl.margins(
        PLANFORM,
        shear_modulus_Pa=2.0e9,
        torsional_stiffness_Nm2=150.0,
        velocity_ms=0.0,
        dynamic_pressure_Pa=0.0,
        ambient_pressure_Pa=101325.0,
        speed_of_sound_ms=340.0,
    )
    assert math.isinf(m.flutter_margin)
    assert math.isinf(m.divergence_margin)
    assert not m.critical


def test_rejects_nonphysical_inputs():
    with pytest.raises(ValueError):
        fl.FinPlanform(root_chord_m=0.0, tip_chord_m=0.1, span_m=0.1, thickness_m=0.005)
    with pytest.raises(ValueError):
        fl.FinPlanform(root_chord_m=0.3, tip_chord_m=0.1, span_m=0.1, thickness_m=0.0)
    with pytest.raises(ValueError):
        fl.flutter_speed(PLANFORM, -1.0, 101325.0, 340.0)
    with pytest.raises(ValueError):
        fl.flutter_speed(PLANFORM, 2.0e9, 0.0, 340.0)
    with pytest.raises(ValueError):
        fl.divergence_pressure(PLANFORM, torsional_stiffness_Nm2=0.0)
    with pytest.raises(ValueError):
        fl.divergence_pressure(PLANFORM, 100.0, eccentricity=0.0)
