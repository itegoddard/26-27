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
from goddard.structures import flutter as fl_mod
from goddard.structures import heating as heat_mod
from goddard.structures import laminate as lam_mod

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
TANK_LENGTH_M = 2.3866            # tank length
TANK_WALL_M = 0.0035              # tank wall thickness, 6061-T6
TANK_DRY_MASS_KG = 10.61          # tank dry mass, derived from the above

INJECTOR_HOLES = 33               # injector orifice count
INJECTOR_HOLE_DIAMETER_M = 0.0015  # injector orifice diameter

GRAIN_LENGTH_M = 0.3484           # grain length
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
    # -- foam core RESOLVED: Divinycell H100, manufacturer datasheet.
    #    Kept in this dict only so the whole material set reads together;
    #    these are confirmed values, not placeholders.
    "foam core shear modulus": 3.5e7,
    "foam core Young's modulus": 1.35e8,
    "foam core density": 100.0,
    "nose tip mass": 0.028,              # solid 6061-T6 cap, 40-50 mm
    # --- recovery: bounded, not open. 3.5 kN is ~11 g on 32.9 kg, sized on
    #     the binding element in the load path -- the nose cone bulkhead bond,
    #     not the hardware. A 3/8-16 forged eyebolt carries several kN working
    #     and Dyneema far more; a bonded 1/2 in plywood or G10 bulkhead fails
    #     in the bondline first. PENDING A PULL TEST on the real assembly.
    "max allowable opening load": 3500.0,
    # Solved from that limit, not chosen: 0.396 puts the disreef load exactly
    # at 3.5 kN. Rounded up to 0.40 for margin.
    #
    # Note the direction, which is counterintuitive: a LARGER reefing ratio
    # LOWERS the disreef load, because the reefed canopy slows the vehicle more
    # before the line is cut. And the binding case is the DISREEF, not the
    # apogee deployment -- at apogee the vehicle is nearly stationary so
    # dynamic pressure is negligible.
    "reefing ratio": 0.40,
    "opening force coefficient": 1.7,    # Knacke, solid cloth
    # --- hardware: all sourced now
    # Counterbored plate: 3.5 mm orifice LAND (L/d 2.3, the stable short-tube
    # band) with 12.5 mm of structure behind it. Flat-drilling 12.5 mm would
    # give L/d 8.3, outside the band the correlations cover.
    "injector plate thickness": 0.0035,
    # ESRA 1515 extrusion, 5.2 m. A specification, not a choice. EFFECTIVE
    # length is shorter by the rail-button spacing, so this is optimistic.
    "launch rail length": 5.2,
    "mean wind speed": 5.0,              # convention; site stats would be better
    "surface roughness": 7.5e-6,         # well-finished student airframe
    # --- mass breakdown: the 32.55 kg dry total is CONFIRMED, the split is not
    # -- masses RESOLVED from the register; kept here for one-place visibility
    "avionics mass": 1.200,              # sled, two flight computers, batteries
    "recovery system mass": 4.400,       # chutes 2.600 + cords 1.400 + ejection 0.400
    "nozzle assembly mass": 2.000,       # graphite throat and retainer
}

DRY_MASS_TOTAL_KG = 32.916        # total dry mass

# ---------------------------------------------------------------------------
# STATION TABLE -- x measured aft from the nose tip, metres.
#
# This is the length budget, and getting it wrong dominates everything else.
# An earlier version placed the tank with an arbitrary 0.10 m gap behind the
# nose and NO recovery bay, putting its midpoint at 2.062 m instead of 2.305 m.
# That single 250 mm error moved the centre of gravity forward by more than the
# entire mass-allocation error combined, and pushed static margin from 2.0 to
# 5.2 calibers. Reconcile stations before touching masses.
# ---------------------------------------------------------------------------
STATIONS = {                      # (start, end) in metres
    "nose_cone":       (0.0000, 0.7620),
    "recovery_bay":    (0.7620, 1.1120),
    "oxidiser_tank":   (1.1120, 3.4986),
    "feed_bay":        (3.4986, 3.5986),
    "injector":        (3.5986, 3.6586),
    "pre_chamber":     (3.6586, 3.7186),
    "fuel_grain":      (3.7186, 4.0670),
    "post_chamber":    (4.0670, 4.1670),
    "nozzle":          (4.1670, 4.3320),
}
TOTAL_LENGTH_M = 4.362

FIN_CG_STATION_M = 4.112          # fin set centre of gravity


def mid(name: str) -> float:
    """Midpoint of a station, m aft of the nose tip."""
    a, b = STATIONS[name]
    return 0.5 * (a + b)


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
            # Root LE from the station table, NOT flush with the tail:
            # the nozzle occupies 4.167-4.332 m.
            root_station_m=FIN_CG_STATION_M - FIN_ROOT_CHORD_M / 2.0,
        ),
        surface_roughness_m=PROVISIONAL["surface roughness"],
    )

    # ---- mass layout, every station taken from STATIONS above
    def tube(name, m, x, length):
        i_ax, i_lat = mass_mod.tube_inertia(m, r_body * 0.9, r_body, length)
        return mass_mod.MassComponent(name, m, x, i_ax, i_lat)

    def point(name, m, x, i_ax=0.004, i_lat=0.02):
        return mass_mod.MassComponent(name, m, x, i_ax, i_lat)

    known = [
        point("nose_tip", PROVISIONAL["nose tip mass"], 0.025, 1e-5, 1e-5),
        point("payload", 0.215, 0.450, 0.001, 0.004),
        point("avionics", PROVISIONAL["avionics mass"], 0.594),
        point("recovery", PROVISIONAL["recovery system mass"], mid("recovery_bay")),
        # Tank REGION, not just the tube: wall 10.55 + bulkheads 1.80 +
        # couplers 1.00. The bulkheads and couplers are part of the tank
        # section and belong at its station, not lumped elsewhere.
        tube("tank_region", 13.35, mid("oxidiser_tank"), TANK_LENGTH_M),
        point("feed_and_valve", 1.50, mid("feed_bay")),
        point("injector", 1.00, mid("injector")),
        tube("chamber_case", 2.862, mid("fuel_grain"), 0.5084),
        point("liners", 3.05, mid("fuel_grain")),
        point("nozzle", PROVISIONAL["nozzle assembly mass"], mid("nozzle")),
        # Fin set INCLUDING tabs, fillets and the retainer ring. The exposed
        # panels alone are only ~0.10 kg (see fin_set_mass_kg); the attachment
        # hardware is 0.55 kg of it. Using panels-only put nearly a kilogram
        # in the wrong place at the worst possible station.
        point("fins", 1.087, FIN_CG_STATION_M, 0.004, 0.02),
    ]
    # Nose shell and the non-structural body tube. Balanced to the dry total so
    # it cannot drift, and placed forward where that structure actually is.
    balance = DRY_MASS_TOTAL_KG - sum(c.mass_kg for c in known)
    known.append(tube("shell_and_tube", balance, 0.60, 1.112))

    mass_model = mass_mod.MassModel(
        dry=known,
        oxidiser_x_m=mid("oxidiser_tank"),
        fuel_x_m=mid("fuel_grain"),
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
        min_rail_exit_velocity_ms=25.0,     # 2026 IREC DTEG
        feed_line_diameter_m=0.0221,        # 1 in OD x 0.065 wall stainless
        feed_line_length_m=0.50,
        feed_line_loss_coefficient=3.0,     # ball valve + entrance + one bend
        # Aeroelastics evaluated along the trajectory, not computed once.
        flutter_planform=fl_mod.FinPlanform(
            root_chord_m=FIN_ROOT_CHORD_M,
            tip_chord_m=FIN_TIP_CHORD_M,
            span_m=FIN_SPAN_M,
            thickness_m=FIN_THICKNESS_M,
        ),
        flutter_section=lam_mod.SandwichSection(
            face_thickness_m=FIN_FACE_THICKNESS_M,
            core_thickness_m=FIN_CORE_THICKNESS_M,
            chord_m=0.5 * (FIN_ROOT_CHORD_M + FIN_TIP_CHORD_M) * FIN_SPAN_M
                    / FIN_SPAN_M,
            face_modulus_Pa=1.733e10,
            face_shear_Pa=3.10e10,
            core_modulus_Pa=PROVISIONAL["foam core Young's modulus"],
            core_shear_Pa=PROVISIONAL["foam core shear modulus"],
        ),
    )
