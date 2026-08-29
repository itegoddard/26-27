"""Saturated N2O properties validated against independently known values.

The ESDU 91022 reduced correlations are checked at 20 degC, where N2O
properties are very well established (this is the condition every hybrid team
quotes), and for internal consistency elsewhere.
"""

import math

import pytest

from goddard.props import n2o


T20 = 293.15  # 20 degC


def test_vapour_pressure_at_20C():
    """Accepted N2O vapour pressure at 20 degC is ~5.05-5.09 MPa."""
    P = n2o.vapour_pressure(T20)
    assert 5.00e6 < P < 5.15e6


def test_liquid_density_at_20C():
    """Accepted saturated liquid density at 20 degC is ~786 kg/m^3."""
    assert n2o.liquid_density(T20) == pytest.approx(786.0, rel=0.01)


def test_vapour_density_at_20C():
    """Accepted saturated vapour density at 20 degC is ~158 kg/m^3."""
    assert n2o.vapour_density(T20) == pytest.approx(158.0, rel=0.02)


def test_densities_converge_at_critical_point():
    """Liquid and vapour densities must both approach rho_crit as T -> T_crit.

    Convergence is cube-root slow: the leading term goes as (1 - Tr)**(1/3), so
    even 0.01 K below Tc the liquid branch still reads ~477 kg/m^3 (5.6 % high).
    That is the correlation behaving correctly, not an error. Approach within
    1e-6 K to see it close.
    """
    T = n2o.T_CRIT - 1e-6
    assert n2o.liquid_density(T) == pytest.approx(n2o.RHO_CRIT, rel=0.005)
    assert n2o.vapour_density(T) == pytest.approx(n2o.RHO_CRIT, rel=0.005)


def test_critical_convergence_is_monotonic():
    """Approaching Tc must tighten the liquid/vapour gap, never widen it."""
    gaps = [
        n2o.liquid_density(n2o.T_CRIT - d) - n2o.vapour_density(n2o.T_CRIT - d)
        for d in (1e-2, 1e-3, 1e-4, 1e-5, 1e-6)
    ]
    assert all(a > b > 0 for a, b in zip(gaps, gaps[1:]))


def test_vapour_pressure_reaches_critical_pressure():
    T = n2o.T_CRIT - 0.001
    assert n2o.vapour_pressure(T) == pytest.approx(n2o.P_CRIT, rel=1e-3)


def test_liquid_denser_than_vapour_across_range():
    for T in range(190, 309, 5):
        Tf = float(T)
        assert n2o.liquid_density(Tf) > n2o.vapour_density(Tf)


def test_vapour_pressure_monotonic_in_temperature():
    prev = 0.0
    for T in range(190, 309, 2):
        P = n2o.vapour_pressure(float(T))
        assert P > prev
        prev = P


def test_liquid_density_falls_with_temperature():
    """A self-pressurizing tank chills as it drains; liquid must expand."""
    assert n2o.liquid_density(280.0) > n2o.liquid_density(300.0)


def test_saturated_bundle_is_consistent_with_scalars():
    s = n2o.saturated(T20)
    assert s.P_sat == n2o.vapour_pressure(T20)
    assert s.rho_l == n2o.liquid_density(T20)
    assert s.rho_v == n2o.vapour_density(T20)


def test_below_triple_point_raises():
    with pytest.raises(n2o.SubTriplePoint):
        n2o.vapour_pressure(180.0)


def test_above_critical_raises():
    with pytest.raises(n2o.SuperCritical):
        n2o.liquid_density(315.0)


def test_latent_heat_refuses_rather_than_guessing():
    """Unverified coefficients must raise, not return a plausible number.

    This is the behaviour that distinguishes this model from the spreadsheet it
    replaces. If this test ever starts failing because someone implemented the
    correlation, they must also add validation against ~376 kJ/kg at the normal
    boiling point and ~145-150 kJ/kg at 293.15 K.
    """
    with pytest.raises(NotImplementedError):
        n2o.enthalpy_vaporisation(T20)
