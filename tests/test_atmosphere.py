"""US Standard Atmosphere 1976 validated against the published tables.

Reference values are taken from the standard itself (NOAA-S/T 76-1562).
Tolerances are tight on purpose: this module is analytic, so any disagreement
beyond round-off means a coefficient is wrong, not that the method is
approximate.
"""

import math

import pytest

from goddard.env import atmosphere as atm


# The US Standard Atmosphere is published in two different tabulations and it
# is easy to conflate them. The layer *breakpoints* are defined on geopotential
# altitude H; the general-purpose tables are usually listed against geometric
# altitude Z. The two differ by ~4 m at 5 km and ~19 m at 11 km -- small, but an
# order of magnitude larger than the tolerances here, so they are kept separate
# rather than mixed into one list.

# Layer-base values, tabulated on GEOPOTENTIAL altitude (m').
PUBLISHED_GEOPOTENTIAL = [
    (0, 288.150, 101325.0, 1.22500, 340.294),
    (11000, 216.650, 22632.1, 0.363918, 295.070),
    (20000, 216.650, 5474.89, 0.0880349, 295.070),
    (32000, 228.650, 868.019, 0.0132250, 303.131),
    (47000, 270.650, 110.906, 0.00142753, 329.799),
]

# In-layer values, tabulated on GEOMETRIC altitude (m MSL).
PUBLISHED_GEOMETRIC = [
    (1000, 281.651, 89876.3, 1.11164, 336.435),
    (5000, 255.676, 54048.3, 0.736116, 320.545),
]


@pytest.mark.parametrize("h,T,P,rho,a", PUBLISHED_GEOPOTENTIAL)
def test_matches_published_layer_bases(h, T, P, rho, a):
    s = atm.state(atm.geometric(float(h)))
    assert s.T == pytest.approx(T, rel=1e-5)
    assert s.P == pytest.approx(P, rel=1e-4)
    assert s.rho == pytest.approx(rho, rel=1e-4)
    assert s.a == pytest.approx(a, rel=1e-5)


@pytest.mark.parametrize("z,T,P,rho,a", PUBLISHED_GEOMETRIC)
def test_matches_published_geometric_rows(z, T, P, rho, a):
    s = atm.state(float(z))
    assert s.T == pytest.approx(T, rel=1e-5)
    assert s.P == pytest.approx(P, rel=1e-3)
    assert s.rho == pytest.approx(rho, rel=1e-3)
    assert s.a == pytest.approx(a, rel=1e-5)


def test_sea_level_viscosity():
    # Sutherland's law at 288.15 K, accepted value 1.7894e-5 Pa s
    assert atm.state(0.0).mu == pytest.approx(1.7894e-5, rel=1e-4)


def test_wsmr_field_elevation_is_sane():
    """Tularosa Basin floor, the confirmed launch site elevation."""
    s = atm.state(1216.0)
    assert 275.0 < s.T < 285.0
    assert 85000.0 < s.P < 90000.0
    assert 1.0 < s.rho < 1.15


def test_no_table_edge_where_the_old_model_broke():
    """The 25-26 spreadsheet returned #N/A above 15,420 m MSL.

    This is the specific regression that motivated an analytic atmosphere.
    Every altitude the vehicle can plausibly reach must return a finite state.
    """
    for z in (15420.0, 16000.0, 20000.0, 25000.0, 30000.0):
        s = atm.state(z)
        assert math.isfinite(s.rho) and s.rho > 0.0
        assert math.isfinite(s.a) and s.a > 0.0


def test_target_apogee_is_well_inside_range():
    """50,000 ft AGL from 1216 m MSL is ~16,456 m MSL."""
    z = 1216.0 + 50000.0 * 0.3048
    s = atm.state(z)
    assert math.isfinite(s.rho)
    assert s.rho < 0.2  # thin up there, but real


def test_monotonic_decrease_in_density():
    prev = math.inf
    for z in range(0, 80000, 500):
        rho = atm.density(float(z))
        assert rho < prev
        prev = rho


def test_layer_boundaries_are_continuous():
    """Temperature and pressure must not jump across a layer base.

    Tolerance is 1e-3 rather than machine precision because the standard's own
    published base pressures are rounded to seven significant figures. Carrying
    them verbatim (rather than integrating up from sea level) trades a ~1.6e-4
    seam at each boundary for exact agreement with the published tables, which
    is the better bargain -- but it means the seam is real and expected.
    """
    for hb in (11000.0, 20000.0, 32000.0, 47000.0, 51000.0, 71000.0):
        z = atm.geometric(hb)
        lo = atm.state(z - 0.5)
        hi = atm.state(z + 0.5)
        assert lo.T == pytest.approx(hi.T, rel=1e-4)
        assert lo.P == pytest.approx(hi.P, rel=1e-3)


def test_out_of_range_raises_rather_than_clamping():
    with pytest.raises(atm.AltitudeOutOfRange):
        atm.state(200000.0)
    with pytest.raises(atm.AltitudeOutOfRange):
        atm.state(-5000.0)


def test_geopotential_round_trip():
    for z in (0.0, 1216.0, 16456.0, 50000.0):
        assert atm.geometric(atm.geopotential(z)) == pytest.approx(z, rel=1e-9)
