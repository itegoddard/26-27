"""Unit conversion round-trips and known anchor values."""

import pytest

from goddard import units as u


def test_six_inch_body_diameter():
    """The confirmed body diameter, in the units the config will use."""
    assert u.inches(6.0) == pytest.approx(0.1524)


def test_fifty_thousand_feet():
    """The target apogee."""
    assert u.feet(50000.0) == pytest.approx(15240.0)


def test_length_round_trips():
    for x in (0.0, 1.0, 6.0, 50000.0):
        assert u.to_inches(u.inches(x)) == pytest.approx(x)
        assert u.to_feet(u.feet(x)) == pytest.approx(x)


def test_mass_round_trip():
    assert u.to_lbm(u.lbm(150.0)) == pytest.approx(150.0)


def test_pressure_anchor():
    """One atmosphere is 14.6959 psi."""
    assert u.to_psi(101325.0) == pytest.approx(14.6959, rel=1e-4)


def test_n2o_bottle_pressure_is_sane():
    """~750 psi is the number every hybrid team quotes for N2O at room temp."""
    assert u.psi(750.0) == pytest.approx(5.171e6, rel=1e-3)


def test_temperature_conversions():
    assert u.celsius(0.0) == pytest.approx(273.15)
    assert u.celsius(30.0) == pytest.approx(303.15)  # WSMR summer estimate
    assert u.fahrenheit(32.0) == pytest.approx(273.15)
    assert u.to_celsius(u.celsius(20.0)) == pytest.approx(20.0)


def test_angle_conversions():
    assert u.degrees(180.0) == pytest.approx(3.141592653589793)
    assert u.to_degrees(u.degrees(1.0)) == pytest.approx(1.0)  # the fin cant


def test_force_round_trip():
    assert u.to_lbf(u.lbf(1000.0)) == pytest.approx(1000.0)
