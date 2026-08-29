"""Shared fixtures.

IMPORTANT: every numeric value here is a PLACEHOLDER chosen to exercise the
code, not a design value. The real numbers are the OPEN entries in
``docs/assumptions_register.md``. Nothing in this file should be copied into a
config.
"""

from __future__ import annotations

import math

import pytest

from goddard import mass as mass_mod
from goddard import recovery as rec_mod
from goddard import sim as sim_mod
from goddard.aero import geometry as geom_mod
from goddard.motor import grain as grain_mod
from goddard.motor import injector as inj_mod
from goddard.props import cea as cea_mod
from goddard.structures import heating as heat_mod


@pytest.fixture
def cea_table() -> cea_mod.CEATable:
    """Synthetic c* table with a peak near O/F 7.

    NOT REAL CEA DATA. It is a smooth analytic surface with roughly the right
    magnitude and the right qualitative shape (a peak in O/F), which is what the
    chamber solver needs to be exercised. Register G11 is the real thing.
    """
    points = []
    for of in [2.0 + 0.5 * i for i in range(25)]:      # 2.0 to 14.0
        for p_mpa in [1.0 + 0.5 * i for i in range(9)]:  # 1 to 5 MPa
            c_star = 1600.0 * math.exp(-((of - 7.0) ** 2) / 40.0)
            points.append(
                cea_mod.CEAPoint(
                    of_ratio=of,
                    pressure_Pa=p_mpa * 1e6,
                    c_star_ms=c_star,
                    gamma=1.20,
                    temperature_K=3000.0,
                )
            )
    return cea_mod.CEATable(points, source="<synthetic test fixture>")


@pytest.fixture
def latent_heat():
    """Stand-in for N2O latent heat, J/kg.

    ``props.n2o.enthalpy_vaporisation`` raises because the ESDU 91022
    coefficients could not be verified. This fixture supplies a physically
    reasonable shape -- latent heat falling to zero at the critical point -- so
    the tank model can be exercised. It is NOT the real correlation.
    """
    from goddard.props import n2o

    def h_vap(T: float) -> float:
        tr = min(max(T / n2o.T_CRIT, 0.0), 1.0)
        return 3.8e5 * (1.0 - tr) ** 0.38

    return h_vap


@pytest.fixture
def vehicle_geometry() -> geom_mod.VehicleGeometry:
    """6 in body with the ORK's confirmed shape. Dimensions are placeholders."""
    body_d = 0.1524
    root = 0.30
    return geom_mod.VehicleGeometry(
        nose=geom_mod.NoseGeometry(
            length_m=0.70, base_diameter_m=body_d, tip_radius_m=0.006
        ),
        transition=geom_mod.TransitionGeometry(
            length_m=0.0, fore_diameter_m=body_d, aft_diameter_m=body_d
        ),
        body=geom_mod.BodyGeometry(diameter_m=body_d, length_m=3.2),
        fins=geom_mod.FinGeometry(
            count=3,
            root_chord_m=root,
            tip_chord_m=root * 0.328,
            span_m=0.13,
            thickness_m=0.005,
            sweep_angle_rad=1.0821,
            cant_angle_rad=math.radians(1.0),
            cross_section="rounded",
        ),
        surface_roughness_m=20e-6,
    )


@pytest.fixture
def mass_model(vehicle_geometry) -> mass_mod.MassModel:
    """Placeholder dry mass breakdown."""
    total_len = vehicle_geometry.total_length_m
    r = vehicle_geometry.body.diameter_m / 2.0

    def tube(name, m, x, length):
        i_ax, i_lat = mass_mod.tube_inertia(m, r * 0.9, r, length)
        return mass_mod.MassComponent(name, m, x, i_ax, i_lat)

    return mass_mod.MassModel(
        dry=[
            tube("nose", 3.0, 0.35, 0.7),
            tube("airframe", 14.0, 2.3, 3.2),
            tube("tank_structure", 8.0, 1.6, 1.2),
            tube("motor_case", 6.0, 3.4, 0.9),
            mass_mod.MassComponent("avionics", 4.0, 1.0, 0.01, 0.05),
            mass_mod.MassComponent("recovery", 5.0, 1.2, 0.01, 0.05),
        ],
        oxidiser_x_m=1.7,
        fuel_x_m=3.3,
        oxidiser_radius_m=r * 0.85,
        fuel_radius_m=r * 0.8,
    )


@pytest.fixture
def vehicle(vehicle_geometry, mass_model, cea_table, latent_heat) -> sim_mod.Vehicle:
    """Complete runnable vehicle. All numbers are placeholders."""
    return sim_mod.Vehicle(
        geometry=vehicle_geometry,
        mass_model=mass_model,
        injector_geometry=inj_mod.InjectorGeometry(
            n_holes=32, hole_diameter_m=0.0018, plate_thickness_m=0.005
        ),
        grain_geometry=grain_mod.GrainGeometry(
            length_m=0.75,
            initial_port_radius_m=0.030,
            outer_radius_m=0.062,
        ),
        tank_volume_m3=0.030,
        tank_fill_fraction=0.85,
        tank_initial_temperature_K=293.15,
        throat_area_m2=math.pi * (0.021 / 2.0) ** 2,
        expansion_ratio=4.5,
        cea=cea_table,
        recovery=rec_mod.RecoveryConfig(
            drogue_cds_m2=0.6,
            main_cds_m2=14.0,
            reefing_ratio=0.35,
            disreef_altitude_m=300.0,
            opening_force_coefficient=1.7,
            max_opening_load_N=12000.0,
        ),
        latent_heat=latent_heat,
        nose_tip=heat_mod.TipThermal(
            nose_radius_m=0.006, mass_kg=0.10, area_m2=2.3e-4
        ),
        field_elevation_m=1216.0,
        rail_length_m=9.0,
    )
