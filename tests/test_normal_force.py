"""Fin placement in the Barrowman centre-of-pressure build-up."""

from __future__ import annotations

import math

import pytest

from goddard.aero import geometry as geom_mod
from goddard.aero import normal_force as nf


def test_fin_root_station_is_a_layout_input_not_an_assumption():
    """Regression test: fins are not always flush with the tail.

    fin_contribution() used to hard-code x_root = total_length - root_chord.
    On this vehicle the nozzle occupies 4.167-4.332 m, so the fins sit 150 mm
    forward of the tail. Assuming flush put the centre of pressure 103 mm aft
    and the static margin at 2.64 calibers instead of 2.00 -- the difference
    between the intended design and a noticeably over-stable one.
    """
    def build(root_station):
        return geom_mod.VehicleGeometry(
            nose=geom_mod.NoseGeometry(0.762, 0.1524, 0.00381),
            transition=geom_mod.TransitionGeometry(0.0, 0.1524, 0.1524),
            body=geom_mod.BodyGeometry(0.1524, 3.60),
            fins=geom_mod.FinGeometry(
                3, 0.200, 0.085, 0.1097, 0.00635,
                math.radians(50.0), math.radians(1.0),
                "hexagonal", root_station,
            ),
            surface_roughness_m=20e-6,
        )

    flush = nf.evaluate(build(None), 0.3, 0.0).x_cp_m
    placed = nf.evaluate(build(4.012), 0.3, 0.0).x_cp_m

    # Moving the fins forward must move the centre of pressure forward.
    assert placed < flush
    assert flush - placed == pytest.approx(0.098, abs=0.01)


def test_default_is_still_flush_with_the_tail():
    """Omitting the station keeps the previous behaviour."""
    fins = geom_mod.FinGeometry(
        3, 0.200, 0.085, 0.1097, 0.00635,
        math.radians(50.0), math.radians(1.0),
    )
    assert fins.root_station_m is None
