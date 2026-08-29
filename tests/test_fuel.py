"""Fuel blend properties and the regression law."""

import math

import pytest

from goddard.props import fuel


def test_composition_sums_to_unity():
    total = fuel.FRAC_PARAFFIN + fuel.FRAC_SEBS_MA + fuel.FRAC_CARBON_BLACK
    assert total == pytest.approx(1.0)


def test_blend_density():
    """89/10/1 mass-weighted blend, expected ~932 kg/m^3."""
    assert fuel.blend_density() == pytest.approx(932.4, abs=0.5)


def test_blend_density_lies_between_components():
    assert fuel.RHO_SEBS_MA < fuel.RHO_FUEL < fuel.RHO_CARBON_BLACK


def test_regression_follows_half_power_law():
    """Doubling flux should raise rdot by sqrt(2) at n = 0.5."""
    r1 = fuel.regression_rate(100.0, 1.0)
    r2 = fuel.regression_rate(200.0, 1.0)
    assert r2 / r1 == pytest.approx(math.sqrt(2.0), rel=1e-9)


def test_regression_magnitude_is_paraffin_like():
    """At G_ox = 100 kg/m^2/s, paraffin regresses at roughly 1.5 mm/s.

    This is the headline result of the liquefying-fuel literature -- three to
    four times HTPB. If this drifts, the coefficients are wrong.
    """
    r = fuel.regression_rate(100.0, 1.0)
    assert 1.2e-3 < r < 1.8e-3


def test_calibration_scales_linearly():
    base = fuel.regression_rate(100.0, 1.0)
    assert fuel.regression_rate(100.0, 0.85) == pytest.approx(0.85 * base)


def test_lower_regression_raises_of_ratio():
    """The sign relationship that spec section 6.1 turns on.

    Oxidiser flow is fixed by the tank and injector, not the grain. So less
    regression means less fuel, which means a HIGHER O/F -- not a uniformly
    'conservative' outcome. This test pins that behaviour so nobody
    accidentally inverts it.
    """
    kw = dict(m_dot_ox=2.0, r_port=0.03, grain_length=0.7)
    low = fuel.evaluate(**kw, calibration=0.75)
    high = fuel.evaluate(**kw, calibration=1.00)
    assert low.m_dot_fuel < high.m_dot_fuel
    assert low.of_ratio > high.of_ratio


def test_flux_falls_as_port_opens_up():
    assert fuel.oxidiser_flux(2.0, 0.03) > fuel.oxidiser_flux(2.0, 0.05)


def test_evaluate_is_self_consistent():
    r = fuel.evaluate(
        m_dot_ox=2.0, r_port=0.03, grain_length=0.7, calibration=0.85
    )
    expected_flux = 2.0 / (math.pi * 0.03 ** 2)
    assert r.G_ox == pytest.approx(expected_flux)
    assert r.of_ratio == pytest.approx(2.0 / r.m_dot_fuel)
    burn_area = 2.0 * math.pi * 0.03 * 0.7
    assert r.m_dot_fuel == pytest.approx(fuel.RHO_FUEL * burn_area * r.r_dot)


def test_rejects_nonphysical_geometry():
    with pytest.raises(ValueError):
        fuel.oxidiser_flux(2.0, 0.0)
    with pytest.raises(ValueError):
        fuel.evaluate(
            m_dot_ox=2.0, r_port=0.03, grain_length=0.0, calibration=1.0
        )
    with pytest.raises(ValueError):
        fuel.regression_rate(-1.0, 1.0)
