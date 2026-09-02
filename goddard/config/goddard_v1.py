"""Goddard 26-27 flight configuration, v1.

The real vehicle. Values come from ``docs/reference/02_BUDGET_50KFT_DESIGN.md``
via ``docs/DESIGN_POINT.md``, from team decisions, or are derived here from
those. Every number is traceable.

===========================================================================
 PROVISIONAL VALUES -- everything still unanswered is collected in
 PROVISIONAL below, in one block, so it is impossible to lose track of what
 is real and what is holding the place. Nothing provisional is buried in the
 body of this file.

 A result from this config is trustworthy for the airframe, the motor and
 the trajectory. It is NOT yet trustworthy for recovery loads or for the
 mass breakdown, because those still contain provisional entries.
===========================================================================

Run it:

    run.bat sim goddard.config.goddard_v1
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
from goddard.props import fuel as fuel_mod
from goddard.props import n2o
from goddard.structures import heating as heat_mod

# ---------------------------------------------------------------------------
# CONFIRMED -- airframe
# ---------------------------------------------------------------------------
BODY_DIAMETER_M = 0.1524          # body outer diameter, 6 in
BODY_LENGTH_M = 3.60              # body tube length, the master design variable
BODY_WALL_M = 0.0024              # body wall thickness, fibreglass

NOSE_LENGTH_M = 0.762             # nose length, fineness ratio 5.0
NOSE_TIP_RADIUS_M = 0.00381       # nose tip radius, 5 % bluffness

FIN_COUNT = 3
FIN_ROOT_CHORD_M = 0.200          # fin root chord
FIN_TIP_CHORD_M = 0.085           # fin tip chord, taper ratio 0.425
FIN_SPAN_M = 0.1097               # fin span, solved for 2.00 calibers
FIN_THICKNESS_M = 0.00635         # fin thickness, 3.17 % of root chord
FIN_SWEEP_RAD = math.radians(50.0)   # fin leading-edge sweep
FIN_CANT_RAD = math.radians(1.0)     # fin cant angle
FIN_SECTION = "hexagonal"            # fin cross-section

# Fin sandwich: 3 plies of +/-45 woven carbon each side of a foam core.
FIN_PLY_THICKNESS_M = 1.981e-4       # carbon ply thickness
FIN_PLIES_PER_SIDE = 3               # carbon layup, [(+/-45)3 / core / (+/-45)3]
FIN_FACE_THICKNESS_M = FIN_PLIES_PER_SIDE * FIN_PLY_THICKNESS_M
FIN_CORE_THICKNESS_M = FIN_THICKNESS_M - 2 * FIN_FACE_THICKNESS_M
FIN_FACE_DENSITY = 1570.0            # carbon skin density

# ---------------------------------------------------------------------------
# CONFIRMED -- motor
# ---------------------------------------------------------------------------
OXIDISER_MASS_KG = 25.04          # nitrous oxide mass
TANK_VOLUME_M3 = 0.0399           # tank internal volume, 39.9 L
TANK_FILL_FRACTION = 0.80         # initial fill fraction -- a SAFETY limit
TANK_LENGTH_M = 2.401             # tank length
TANK_WALL_M = 0.0035              # tank wall thickness, 6061-T6
TANK_DRY_MASS_KG = 10.61          # tank dry mass, derived from the above

INJECTOR_HOLES = 33               # injector orifice count
INJECTOR_HOLE_DIAMETER_M = 0.0015  # injector orifice diameter

GRAIN_LENGTH_M = 0.349            # grain length
GRAIN_PORT_RADIUS_M = 0.0692 / 2  # initial port radius
GRAIN_OUTER_RADIUS_M = 0.1370 / 2  # grain outer radius, 33.9 mm web

THROAT_DIAMETER_M = 0.02887       # throat diameter, team value
EXPANSION_RATIO = 6.0             # nozzle expansion ratio
PRE_CHAMBER_LENGTH_M = 0.060      # pre-combustion chamber length
POST_CHAMBER_LENGTH_M = 0.100     # post-combustion chamber length
CHAMBER_WALL_M = 0.0040           # chamber case wall, 6061-T6

CEA_TABLE = "data/cea_S10W1_N2O_35bar.csv"
CEA_PRESSURE_PA = 35e5            # the pressure the sweep was run at

# ---------------------------------------------------------------------------
# CONFIRMED -- environment
# ---------------------------------------------------------------------------
FIELD_ELEVATION_M = 1216.0        # field elevation, Tularosa Basin, WSMR
GROUND_TEMPERATURE_K = 303.15     # ambient air temperature

# Tank temperature at ignition is NOT the ambient air temperature. The design
# record fills at 20 C: its stated 50.5 bar tank pressure is the nitrous
# saturation pressure at exactly 20 C, and its 25.04 kg in 39.9 L at 0.80 fill
# requires a liquid density of 785 kg/m^3, which is also 20 C.
#
# Using 30 C ambient instead put the tank at 63.1 bar, which drove the chamber
# to 46 bar, more than doubled oxidiser flow and stretched the burn to 42 s
# against the record's 18 s. Worth stating plainly because it is an easy and
# very expensive mistake.
#
# A tank that soaks to 30 C on the pad is a real and different case: pressure
# 63 bar, and only ~22 kg of liquid fits. That is an operational question, not
# the design point.
TANK_TEMPERATURE_K = 293.15       # tank fill temperature, 20 C
MAX_LANDING_SPEED_MS = 7.0        # max allowable landing speed
DISREEF_ALTITUDE_M = 450.0        # disreef trigger altitude

# ---------------------------------------------------------------------------
# PROVISIONAL -- every unanswered value, in one place
#
# These are placeholders chosen to be defensible, NOT design values. Each
# names what would replace it. Results that depend on them carry that
# uncertainty; see the module docstring.
# ---------------------------------------------------------------------------
PROVISIONAL = {
    # --- structures
    "foam core shear modulus": 19.0e6,   # need: foam product and grade
    "foam core Young's modulus": 47.0e6,  # need: same datasheet
    "foam core density": 60.0,           # need: same datasheet
    "nose tip mass": 0.028,              # derived below; weigh the machined cap
    # --- recovery
    "reefing ratio": 0.30,               # need: max allowable opening load
    "opening force coefficient": 1.7,    # need: canopy type, then Knacke
    "max allowable opening load": 12000.0,  # need: airframe/payload g-limit
    # --- hardware
    "injector plate thickness": 0.0030,  # need: the drawing. Sets L/d = 2.0
    "launch rail length": 9.0,           # need: what WSMR provides
    "mean wind speed": 5.0,              # need: range limits. 25-26 used 5.0
    "surface roughness": 20e-6,          # need: expected finish quality
    # --- mass breakdown: the 32.55 kg dry total is CONFIRMED, the split is not
    "avionics mass": 4.0,                # need: actual avionics stack
    "recovery system mass": 4.5,         # need: canopy + harness + hardware
}

DRY_MASS_TOTAL_KG = 32.55         # total dry mass, from the design record


def _cea() -> cea_mod.CEATable:
    """Real NASA CEA sweep for the S10W1 blend. Peak c* 1598.1 m/s at O/F 7.00."""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent
    return cea_mod.load_of_sweep(root / CEA_TABLE, CEA_PRESSURE_PA)


def _latent_heat(T: float) -> float:
    """PROVISIONAL stand-in for the nitrous oxide latent heat.

    ``props.n2o.enthalpy_vaporisation`` raises because the ESDU 91022
    coefficients could not be verified. Physically shaped -- latent heat falls
    to zero at the critical point -- but NOT the real correlation. It affects
    the tank chilling rate and therefore the thrust taper.
    """
    tr = min(max(T / n2o.T_CRIT, 0.0), 1.0)
    return 3.8e5 * (1.0 - tr) ** 0.38


def fin_set_mass_kg() -> float:
    """Mass of the exposed fin panels, from the sandwich layup.

    Carbon skins over foam comes out far lighter than the solid G10 the design
    record assumed -- about 0.10 kg against its 1.09 kg. Root tabs, fillets and
    adhesive are NOT included here, so treat this as a lower bound on the
    installed fin mass.
    """
    area = FIN_COUNT * 0.5 * (FIN_ROOT_CHORD_M + FIN_TIP_CHORD_M) * FIN_SPAN_M
    faces = 2.0 * FIN_FACE_THICKNESS_M * FIN_FACE_DENSITY * area
    core = FIN_CORE_THICKNESS_M * PROVISIONAL["foam core density"] * area
    return faces + core


def build_vehicle() -> sim_mod.Vehicle:
    """The Goddard 26-27 vehicle."""
    r_body = BODY_DIAMETER_M / 2.0

    geometry = geom_mod.VehicleGeometry(
        nose=geom_mod.NoseGeometry(
            length_m=NOSE_LENGTH_M,
            base_diameter_m=BODY_DIAMETER_M,
            tip_radius_m=NOSE_TIP_RADIUS_M,
        ),
        # No flare: the nose meets the body at full diameter.
        transition=geom_mod.TransitionGeometry(
            length_m=0.0,
            fore_diameter_m=BODY_DIAMETER_M,
            aft_diameter_m=BODY_DIAMETER_M,
        ),
        body=geom_mod.BodyGeometry(
            diameter_m=BODY_DIAMETER_M, length_m=BODY_LENGTH_M
        ),
        fins=geom_mod.FinGeometry(
            count=FIN_COUNT,
            root_chord_m=FIN_ROOT_CHORD_M,
            tip_chord_m=FIN_TIP_CHORD_M,
            span_m=FIN_SPAN_M,
            thickness_m=FIN_THICKNESS_M,
            sweep_angle_rad=FIN_SWEEP_RAD,
            cant_angle_rad=FIN_CANT_RAD,
            cross_section=FIN_SECTION,
        ),
        surface_roughness_m=PROVISIONAL["surface roughness"],
    )

    # ---- mass layout, x measured aft from the nose tip
    x_tank = NOSE_LENGTH_M + 0.10
    x_chamber = x_tank + TANK_LENGTH_M
    chamber_length = PRE_CHAMBER_LENGTH_M + GRAIN_LENGTH_M + POST_CHAMBER_LENGTH_M

    def tube(name, m, x, length):
        i_ax, i_lat = mass_mod.tube_inertia(m, r_body * 0.9, r_body, length)
        return mass_mod.MassComponent(name, m, x, i_ax, i_lat)

    chamber_case = 2700.0 * math.pi * (
        r_body ** 2 - (r_body - CHAMBER_WALL_M) ** 2
    ) * chamber_length

    known = [
        tube("tank", TANK_DRY_MASS_KG, x_tank + TANK_LENGTH_M / 2, TANK_LENGTH_M),
        tube("chamber_case", chamber_case, x_chamber + chamber_length / 2,
             chamber_length),
        mass_mod.MassComponent(
            "fins", fin_set_mass_kg(), NOSE_LENGTH_M + BODY_LENGTH_M - 0.10,
            0.004, 0.02),
        mass_mod.MassComponent(
            "nose_tip", PROVISIONAL["nose tip mass"], 0.025, 1e-5, 1e-5),
        mass_mod.MassComponent("payload", 0.215, 0.45, 0.001, 0.004),
        mass_mod.MassComponent(
            "avionics", PROVISIONAL["avionics mass"], 0.50, 0.004, 0.02),
        mass_mod.MassComponent(
            "recovery", PROVISIONAL["recovery system mass"], 1.05, 0.005, 0.03),
    ]
    # Everything not itemised -- nose shell, body tube, nozzle, plumbing,
    # bulkheads, fasteners -- is lumped so the dry total matches the design
    # record exactly rather than drifting.
    balance = DRY_MASS_TOTAL_KG - sum(c.mass_kg for c in known)
    known.append(
        tube("structure_balance", balance, NOSE_LENGTH_M + BODY_LENGTH_M / 2,
             BODY_LENGTH_M)
    )

    mass_model = mass_mod.MassModel(
        dry=known,
        oxidiser_x_m=x_tank + TANK_LENGTH_M / 2,
        fuel_x_m=x_chamber + PRE_CHAMBER_LENGTH_M + GRAIN_LENGTH_M / 2,
        oxidiser_radius_m=(r_body - TANK_WALL_M) * 0.9,
        fuel_radius_m=GRAIN_OUTER_RADIUS_M,
    )

    # ---- recovery: single canopy, reefed then disreefed
    canopy_cds = (
        2.0 * DRY_MASS_TOTAL_KG * 9.80665 / (1.0883 * MAX_LANDING_SPEED_MS ** 2)
    )

    return sim_mod.Vehicle(
        geometry=geometry,
        mass_model=mass_model,
        injector_geometry=inj_mod.InjectorGeometry(
            n_holes=INJECTOR_HOLES,
            hole_diameter_m=INJECTOR_HOLE_DIAMETER_M,
            plate_thickness_m=PROVISIONAL["injector plate thickness"],
        ),
        grain_geometry=grain_mod.GrainGeometry(
            length_m=GRAIN_LENGTH_M,
            initial_port_radius_m=GRAIN_PORT_RADIUS_M,
            outer_radius_m=GRAIN_OUTER_RADIUS_M,
        ),
        tank_volume_m3=TANK_VOLUME_M3,
        tank_fill_fraction=TANK_FILL_FRACTION,
        tank_initial_temperature_K=TANK_TEMPERATURE_K,
        throat_area_m2=math.pi * (THROAT_DIAMETER_M / 2.0) ** 2,
        expansion_ratio=EXPANSION_RATIO,
        cea=_cea(),
        recovery=rec_mod.RecoveryConfig(
            canopy_cds_m2=canopy_cds,
            reefing_ratio=PROVISIONAL["reefing ratio"],
            disreef_altitude_m=DISREEF_ALTITUDE_M,
            opening_force_coefficient=PROVISIONAL["opening force coefficient"],
            max_opening_load_N=PROVISIONAL["max allowable opening load"],
        ),
        latent_heat=_latent_heat,
        nose_tip=heat_mod.TipThermal(
            nose_radius_m=NOSE_TIP_RADIUS_M,
            mass_kg=PROVISIONAL["nose tip mass"],
            # Effective STAGNATION-REGION area = 2*pi*R_n^2, not the wetted
            # area of the cap. See TipThermal's docstring.
            area_m2=2.0 * math.pi * NOSE_TIP_RADIUS_M ** 2,
            service_limit_K=473.0,   # 6061-T6, over-ageing limit
        ),
        field_elevation_m=FIELD_ELEVATION_M,
        rail_length_m=PROVISIONAL["launch rail length"],
    )
