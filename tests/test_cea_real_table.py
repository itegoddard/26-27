"""The real CEA table for the 89/10/1 blend — register G11.

``data/cea_S10W1_N2O_35bar.csv`` is a NASA CEA O/F sweep at 35 bar for the
S10W1 blend (89 % SasolWax 0907 / 10 % SEBS-g-MA / 1 % carbon black) with
nitrous oxide. This replaces the PLACEHOLDER.

These tests pin the properties the motor model depends on, so a corrupted or
swapped file fails loudly rather than quietly shifting every apogee.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from goddard.props import cea as cea_mod

TABLE = Path(__file__).resolve().parent.parent / "data" / "cea_S10W1_N2O_35bar.csv"
PRESSURE = 35e5  # the sweep was run at 35 bar


@pytest.fixture(scope="module")
def table() -> cea_mod.CEATable:
    return cea_mod.load_of_sweep(TABLE, PRESSURE)


def test_table_file_is_present():
    assert TABLE.exists(), f"missing {TABLE} -- register G11"


def test_covers_the_operating_range(table):
    """Design sweeps O/F 6.75 -> 8.00 through the burn."""
    lo, hi = table.of_range
    assert lo <= 6.75 and hi >= 8.00


def test_peak_c_star_is_at_of_seven(table):
    """Published peak for this blend is 1598.1 m/s at O/F 7.00."""
    assert table.peak_of_ratio(PRESSURE) == pytest.approx(7.00, abs=0.05)
    assert table.c_star(7.00, PRESSURE) == pytest.approx(1598.1, rel=1e-3)


def test_gamma_is_physical(table):
    """Combustion products, so gamma sits well below the 1.4 of cold air."""
    for of in (2.0, 5.0, 7.0, 10.0, 14.0):
        g = table.gamma(of, PRESSURE)
        assert 1.10 < g < 1.35


def test_chamber_temperature_peaks_near_stoichiometric(table):
    """Tc must rise to a peak and fall again, not run away."""
    assert table.temperature(7.0, PRESSURE) > table.temperature(2.0, PRESSURE)
    assert table.temperature(7.0, PRESSURE) > table.temperature(14.0, PRESSURE)
    assert 3000.0 < table.temperature(7.0, PRESSURE) < 3400.0


def test_c_star_falls_away_from_the_peak_in_both_directions(table):
    """The behaviour spec 6.1 turns on: either side of the peak costs c*."""
    peak = table.c_star(7.0, PRESSURE)
    assert table.c_star(5.0, PRESSURE) < peak
    assert table.c_star(10.0, PRESSURE) < peak


def test_interpolates_between_tabulated_points(table):
    """Table is on a 0.1 O/F grid; 7.05 must land between its neighbours."""
    lo = table.c_star(7.00, PRESSURE)
    hi = table.c_star(7.10, PRESSURE)
    mid = table.c_star(7.05, PRESSURE)
    assert min(lo, hi) <= mid <= max(lo, hi)


def test_single_pressure_table_is_flat_in_pressure(table):
    """Documented limitation, asserted so nobody mistakes it for real data.

    c* is nearly flat in chamber pressure for this propellant (1592 m/s at
    20 bar vs 1602 at 50 bar), which is why a single-pressure sweep is usable.
    """
    assert table.c_star(7.0, 20e5) == table.c_star(7.0, 50e5)


def test_load_of_sweep_rejects_bad_pressure():
    with pytest.raises(ValueError):
        cea_mod.load_of_sweep(TABLE, 0.0)


def test_missing_file_still_raises_placeholder():
    with pytest.raises(cea_mod.PlaceholderData):
        cea_mod.load_of_sweep("data/does_not_exist.csv", 35e5)
