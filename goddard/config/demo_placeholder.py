"""DEMO CONFIG -- PLACEHOLDER NUMBERS. NOT A DESIGN.

===========================================================================
 EVERY NUMBER IN THIS FILE IS INVENTED.

 It exists for exactly one purpose: to let you see what the Excel report and
 the plots look like before the real parameters are known. It is a format
 preview, not a performance prediction.

 Do NOT quote any number this produces. Do NOT copy values out of here into
 a real config. The apogee it reports is meaningless -- it is the apogee of
 a rocket nobody is building.

 The real values are the 50 OPEN entries in docs/assumptions_register.md.
 Run `python -m goddard.cli check` to list them.
===========================================================================

Usage:

    python -m goddard.cli run --config goddard.config.demo_placeholder --out out

Once the register is filled in, write a real config module beside this one
(``goddard/config/goddard_v2.py``) and delete this file.
"""

from __future__ import annotations

import math

from goddard import mass as mass_mod
from goddard import recovery as rec_mod
from goddard import sim as sim_mod
from goddard.aero import geometry as geom_mod
from goddard.motor import grain as grain_mod
from goddard.motor import injector as inj_mod
from goddard.props import cea as cea_mod
from goddard.props import n2o
from goddard.structures import heating as heat_mod

BODY_DIAMETER_M = 0.1524  # B1 -- the one genuinely CONFIRMED dimension


def _synthetic_cea() -> cea_mod.CEATable:
    """NOT REAL CEA DATA.

    A smooth analytic surface with roughly the right magnitude and a peak in
    O/F near 7, which is the qualitative shape the chamber solver needs. The
    real table is register G11 and must come from NASA CEA (RP-1311) run for
    the actual 89/10/1 blend against N2O.
    """
    points = []
    for i in range(25):
        of = 2.0 + 0.5 * i
        for j in range(9):
            p = (1.0 + 0.5 * j) * 1e6
            points.append(
                cea_mod.CEAPoint(
                    of_ratio=of,
                    pressure_Pa=p,
                    c_star_ms=1600.0 * math.exp(-((of - 7.0) ** 2) / 40.0),
                    gamma=1.20,
                    temperature_K=3000.0,
                )
            )
    return cea_mod.CEATable(points, source="<synthetic placeholder, not real CEA>")


def _placeholder_latent_heat(T: float) -> float:
    """NOT THE REAL CORRELATION.

    ``props.n2o.enthalpy_vaporisation`` raises because the ESDU 91022
    coefficients could not be verified. This is a physically-shaped stand-in
    (latent heat falling to zero at the critical point) so the tank blowdown
    can run at all.
    """
    tr = min(max(T / n2o.T_CRIT, 0.0), 1.0)
    return 3.8e5 * (1.0 - tr) ** 0.38


def build_vehicle() -> sim_mod.Vehicle:
    """Return a runnable vehicle built entirely from invented numbers."""
    root_chord = 0.30
    r_body = BODY_DIAMETER_M / 2.0

    geometry = geom_mod.VehicleGeometry(
        nose=geom_mod.NoseGeometry(
            length_m=0.70,
            base_diameter_m=BODY_DIAMETER_M,
            tip_radius_m=0.006,
        ),
        # Flare collapsed to zero length: the demo runs the no-flare variant.
        # Register B7 asks whether the sub-body-diameter nose is intended.
        transition=geom_mod.TransitionGeometry(
            length_m=0.0,
            fore_diameter_m=BODY_DIAMETER_M,
            aft_diameter_m=BODY_DIAMETER_M,
        ),
        body=geom_mod.BodyGeometry(diameter_m=BODY_DIAMETER_M, length_m=3.2),
        fins=geom_mod.FinGeometry(
            count=3,                                # B10 CONFIRMED
            root_chord_m=root_chord,                # B14 invented
            tip_chord_m=root_chord * 0.328,         # B12 CONFIRMED ratio
            span_m=0.13,                            # B15 invented
            thickness_m=0.005,                      # B16 invented
            sweep_angle_rad=1.0821,                 # B13 CONFIRMED, 62 deg
            cant_angle_rad=math.radians(1.0),       # B18 CONFIRMED, 1 deg
            cross_section="rounded",                # B17 per ORK
        ),
        surface_roughness_m=20e-6,
    )

    def tube(name, m, x, length):
        i_ax, i_lat = mass_mod.tube_inertia(m, r_body * 0.9, r_body, length)
        return mass_mod.MassComponent(name, m, x, i_ax, i_lat)

    mass_model = mass_mod.MassModel(
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
        oxidiser_radius_m=r_body * 0.85,
        fuel_radius_m=r_body * 0.8,
    )

    return sim_mod.Vehicle(
        geometry=geometry,
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
        cea=_synthetic_cea(),
        recovery=rec_mod.RecoveryConfig(
            canopy_cds_m2=14.0,
            reefing_ratio=0.35,
            disreef_altitude_m=300.0,
            opening_force_coefficient=1.7,
            max_opening_load_N=12000.0,
        ),
        latent_heat=_placeholder_latent_heat,
        nose_tip=heat_mod.TipThermal(
            nose_radius_m=0.006, mass_kg=0.10, area_m2=2.3e-4
        ),
        field_elevation_m=1216.0,   # A1 CONFIRMED, Tularosa Basin
        rail_length_m=9.0,          # A6 invented
    )
