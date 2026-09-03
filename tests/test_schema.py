"""The OPEN-parameter sentinel and config tree walking."""

import dataclasses

import pytest

from goddard.config import schema as s


def test_open_raises_on_arithmetic_naming_the_register_entry():
    o = s.Open("B14", "fin root chord", "m")
    with pytest.raises(s.OpenParameter) as exc:
        _ = o * 2.0
    msg = str(exc.value)
    assert "B14" in msg
    assert "fin root chord" in msg
    assert "assumptions_register" in msg


def test_open_raises_in_either_operand_position():
    o = s.Open("B15", "fin span", "m")
    for op in (
        lambda: 2.0 + o,
        lambda: o + 2.0,
        lambda: 2.0 - o,
        lambda: o / 2.0,
        lambda: 2.0 / o,
        lambda: o ** 2,
        lambda: -o,
        lambda: abs(o),
        lambda: float(o),
        lambda: o < 1.0,
    ):
        with pytest.raises(s.OpenParameter):
            op()


def test_open_is_not_silently_falsy():
    """An OPEN value must not read as 'absent' in a truthiness check."""
    assert bool(s.Open("A4", "wind"))


def test_the_default_config_is_now_complete():
    """Every register parameter is answered.

    This is the milestone the Open sentinel existed to drive towards: the
    default config no longer contains a single unfilled value. If this starts
    failing, a NEW parameter was added and needs answering -- the failure names
    it.
    """
    missing = s.RocketConfig().missing()
    assert missing == [], (
        "unfilled parameters: "
        + ", ".join(f"{o.register_id} ({o.description})" for _, o in missing)
    )


def test_report_missing_says_so_when_nothing_is_missing():
    assert s.RocketConfig().report_missing() == "All parameters filled."


def test_report_missing_is_readable_when_something_is_open():
    """The reporting machinery must still work -- it will be needed again."""
    cfg = dataclasses.replace(
        s.RocketConfig(),
        environment=dataclasses.replace(
            s.Environment(), mean_wind_speed_ms=s.Open("A4", "mean wind speed", "m/s")
        ),
    )
    report = cfg.report_missing()
    assert "still OPEN" in report
    assert "A4" in report
    assert "mean wind speed" in report


def test_assert_complete_passes_on_the_real_config():
    """Nothing is unfilled any more, so this must not raise."""
    s.assert_complete(s.RocketConfig())


def test_assert_complete_lists_everything_at_once():
    """One run must reveal the whole gap, not just the first missing value.

    The real config is complete now, so this injects two sentinels to keep the
    machinery under test -- it will be needed again the moment a new parameter
    is added.
    """
    env = dataclasses.replace(
        s.Environment(),
        mean_wind_speed_ms=s.Open("A4", "mean wind speed", "m/s"),
        rail_length_m=s.Open("A6", "launch rail length", "m"),
    )
    with pytest.raises(s.OpenParameter) as exc:
        s.assert_complete(env)
    msg = str(exc.value)
    assert "A4" in msg and "A6" in msg, "stopped at the first missing value"


def test_assert_complete_passes_when_filled():
    filled = s.Environment(
        field_elevation_m=1216.0,
        ground_temperature_K=303.15,
        mean_wind_speed_ms=4.0,
        rail_length_m=9.0,
        rail_angle_rad=0.0,
    )
    s.assert_complete(filled)  # must not raise


def test_confirmed_values_are_present_and_correct():
    cfg = s.RocketConfig()
    assert cfg.environment.field_elevation_m == 1216.0     # A1 Tularosa Basin
    assert cfg.geometry.body.diameter_m == pytest.approx(0.1524)  # B1, 6 in
    assert cfg.geometry.fins.count == 3                    # B10
    assert cfg.geometry.fins.taper_ratio == pytest.approx(0.425)  # B12
    assert cfg.motor.tank.ullage_noncondensable_fraction == 0.0   # D10


def test_fin_cant_is_one_degree():
    import math
    cant = s.RocketConfig().geometry.fins.cant_angle_rad
    assert math.degrees(cant) == pytest.approx(1.0, rel=1e-4)


def test_calibration_nominals_sit_inside_their_bands():
    c = s.Calibration()
    for value, (lo, hi) in (
        (c.regression_calibration, c.regression_band),
        (c.injector_cd, c.injector_cd_band),
        (c.eta_cstar, c.eta_cstar_band),
    ):
        assert lo <= value <= hi


def test_derived_tip_chord_propagates_open():
    """A derived quantity built from an OPEN input must itself stay OPEN.

    The root chord is now confirmed, so this substitutes one back in to prove
    the propagation still works -- the guarantee matters regardless of which
    fields happen to be filled today.
    """
    fins = dataclasses.replace(
        s.FinSet(), root_chord_m=s.Open("B14", "fin root chord", "m")
    )
    with pytest.raises(s.OpenParameter):
        _ = float(fins.tip_chord_m)


def test_derived_tip_chord_uses_the_confirmed_taper_ratio():
    assert s.FinSet().tip_chord_m == pytest.approx(0.200 * 0.425)
    assert s.FinSet().tip_chord_m == pytest.approx(0.085, abs=1e-9)


def test_config_is_frozen():
    cfg = s.RocketConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.name = "other"  # type: ignore[misc]
