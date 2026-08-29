"""Isentropic nozzle relations."""

import math

import pytest

from goddard.motor import nozzle as nz

# Representative of paraffin/N2O combustion products.
GAMMA = 1.2


def test_area_ratio_is_unity_at_the_throat():
    assert nz.area_ratio(1.0, GAMMA) == pytest.approx(1.0)


def test_area_ratio_increases_supersonically():
    prev = 0.0
    for m in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
        ar = nz.area_ratio(m, GAMMA)
        assert ar > prev
        prev = ar


def test_exit_mach_round_trips_through_area_ratio():
    """The strongest available check: solver inverts the analytic relation."""
    for m in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0):
        eps = nz.area_ratio(m, GAMMA)
        assert nz.exit_mach(eps, GAMMA) == pytest.approx(m, rel=1e-6)


def test_exit_mach_is_unity_at_unit_expansion():
    assert nz.exit_mach(1.0, GAMMA) == pytest.approx(1.0)


def test_throat_pressure_ratio_matches_closed_form():
    """At M = 1 the ratio must equal (2/(g+1))**(g/(g-1))."""
    expected = (2.0 / (GAMMA + 1.0)) ** (GAMMA / (GAMMA - 1.0))
    assert nz.pressure_ratio(1.0, GAMMA) == pytest.approx(expected)


def test_pressure_ratio_falls_with_mach():
    prev = 1.0
    for m in (1.0, 2.0, 3.0, 4.0):
        pr = nz.pressure_ratio(m, GAMMA)
        assert pr < prev
        prev = pr


def test_thrust_coefficient_is_physically_sized():
    """C_f for a real nozzle lands between roughly 1.2 and 2.0."""
    cf, _, _ = nz.thrust_coefficient(
        p_chamber=3.0e6, p_ambient=101325.0, expansion_ratio=4.0, gamma=GAMMA
    )
    assert 1.2 < cf < 2.0


def test_thrust_rises_with_altitude():
    """The whole point of the (Pe - Pa)*Ae term.

    The 25-26 model had no ambient-pressure term at all, so its thrust was
    altitude-independent. Over a climb to 50,000 ft that is a first-order error.
    """
    kw = dict(p_chamber=3.0e6, expansion_ratio=4.0, gamma=GAMMA)
    sea_level, _, _ = nz.thrust_coefficient(p_ambient=101325.0, **kw)
    altitude, _, _ = nz.thrust_coefficient(p_ambient=12000.0, **kw)
    vacuum, _, _ = nz.thrust_coefficient(p_ambient=0.0, **kw)
    assert sea_level < altitude < vacuum


def test_larger_expansion_helps_in_vacuum():
    kw = dict(p_chamber=3.0e6, p_ambient=0.0, gamma=GAMMA)
    small, _, _ = nz.thrust_coefficient(expansion_ratio=3.0, **kw)
    large, _, _ = nz.thrust_coefficient(expansion_ratio=8.0, **kw)
    assert large > small


def test_optimum_expansion_reduces_to_momentum_term():
    """When Pe == Pa the pressure term vanishes."""
    p_c, eps = 3.0e6, 4.0
    me = nz.exit_mach(eps, GAMMA)
    p_e = nz.pressure_ratio(me, GAMMA) * p_c
    cf, _, pe_out = nz.thrust_coefficient(p_c, p_e, eps, GAMMA)
    assert pe_out == pytest.approx(p_e)
    cf_vac, _, _ = nz.thrust_coefficient(p_c, 0.0, eps, GAMMA)
    assert cf == pytest.approx(cf_vac - p_e / p_c * eps)


def test_performance_thrust_is_cf_times_pc_times_at():
    perf = nz.performance(
        p_chamber=3.0e6,
        p_ambient=101325.0,
        throat_area=0.002,
        expansion_ratio=4.0,
        gamma=GAMMA,
        eta_cf=0.97,
    )
    assert perf.thrust == pytest.approx(perf.cf * 3.0e6 * 0.002)
    assert perf.cf == pytest.approx(0.97 * perf.cf_ideal)


def test_over_expansion_is_flagged_as_separated():
    """Summerfield: exit below ~40 % of ambient risks separation."""
    perf = nz.performance(
        p_chamber=5.0e5,
        p_ambient=101325.0,
        throat_area=0.002,
        expansion_ratio=12.0,
        gamma=GAMMA,
    )
    assert perf.separated

    healthy = nz.performance(
        p_chamber=3.0e6,
        p_ambient=101325.0,
        throat_area=0.002,
        expansion_ratio=4.0,
        gamma=GAMMA,
    )
    assert not healthy.separated


def test_unchoked_nozzle_raises():
    with pytest.raises(nz.UnchokedNozzle):
        nz.performance(
            p_chamber=1.1e5,
            p_ambient=101325.0,
            throat_area=0.002,
            expansion_ratio=4.0,
            gamma=GAMMA,
        )


def test_mass_flux_is_choked_form():
    assert nz.throat_mass_flux(3.0e6, 1600.0) == pytest.approx(3.0e6 / 1600.0)


def test_rejects_nonphysical_inputs():
    with pytest.raises(ValueError):
        nz.exit_mach(0.5, GAMMA)
    with pytest.raises(ValueError):
        nz.area_ratio(0.0, GAMMA)
    with pytest.raises(ValueError):
        nz.throat_mass_flux(3.0e6, 0.0)
    with pytest.raises(ValueError):
        nz.performance(3.0e6, 0.0, 0.0, 4.0, GAMMA)
