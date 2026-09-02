"""Configuration schema and the OPEN-parameter sentinel.

Spec section 3. Companion to ``docs/assumptions_register.md``.

The register lists 112 parameters, 54 of which have no value yet. This module
makes that fact *executable*: an unfilled parameter is not a zero, not a
plausible default, and not a ``None`` that turns into a confusing ``TypeError``
three call frames later. It is an ``Open`` object that raises the moment
anything tries to compute with it, naming the register entry that must be
filled in.

    >>> cfg.fins.root_chord_m
    Open(B14, 'fin root chord')
    >>> cfg.fins.root_chord_m * 2.0
    OpenParameter: parameter B14 (fin root chord) is OPEN ...

This is the same principle as ``n2o.enthalpy_vaporisation`` raising rather than
guessing: the model must never return a plausible-looking wrong answer. A
spreadsheet cell containing a placeholder 0.5 is indistinguishable from a
measured 0.5, and that is how the 25-26 model shipped a constant drag
coefficient through Mach 1.65 without anyone noticing.

Coverage
--------
``RocketConfig().report_missing()`` enumerates every OPEN parameter across all
register sections A through K. Keep this schema and
``docs/assumptions_register.md`` in step: adding a register entry without a
field here means the model can run while silently missing it, which is the
whole failure class this module exists to prevent.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Iterator


class OpenParameter(ValueError):
    """An OPEN register parameter was used in a computation.

    Fill the value in ``goddard/config/`` and record the source in
    ``docs/assumptions_register.md``.
    """


class PlaceholderData(ValueError):
    """A dataset marked PLACEHOLDER was requested but has not been supplied.

    Currently only register item G11, the CEA c*/gamma/Tc table.
    """


class Open:
    """Sentinel for a parameter that has no value yet.

    Deliberately not a float subclass. Any arithmetic raises immediately with
    the register ID, so a missing value surfaces at the point of use rather
    than propagating as a silently wrong number.
    """

    __slots__ = ("register_id", "description", "units")

    def __init__(self, register_id: str, description: str, units: str = "") -> None:
        self.register_id = register_id
        self.description = description
        self.units = units

    def _raise(self, *_args: Any) -> Any:
        unit_note = f" [{self.units}]" if self.units else ""
        raise OpenParameter(
            f"parameter {self.register_id} ({self.description}){unit_note} is "
            f"OPEN -- it has no value yet. Fill it in under goddard/config/ and "
            f"record the source in docs/assumptions_register.md "
            f"(entry {self.register_id})."
        )

    # Any attempt to compute with an OPEN value is an error, in either operand
    # position, including in-place and unary forms.
    __add__ = __radd__ = __sub__ = __rsub__ = _raise
    __mul__ = __rmul__ = __truediv__ = __rtruediv__ = _raise
    __pow__ = __rpow__ = __neg__ = __abs__ = _raise
    __float__ = __int__ = __index__ = _raise
    __lt__ = __le__ = __gt__ = __ge__ = _raise

    def __repr__(self) -> str:
        return f"Open({self.register_id}, {self.description!r})"

    def __bool__(self) -> bool:
        # Truthiness is safe and useful: `if isinstance(x, Open)` reads better,
        # but `if not x` should not silently treat an OPEN value as absent.
        return True


Number = float | Open


def open_parameters(node: Any, _path: str = "") -> Iterator[tuple[str, Open]]:
    """Walk a config tree and yield every ``(dotted_path, Open)`` still unfilled."""
    if isinstance(node, Open):
        yield _path, node
        return
    if is_dataclass(node) and not isinstance(node, type):
        for f in fields(node):
            child = getattr(node, f.name)
            child_path = f"{_path}.{f.name}" if _path else f.name
            yield from open_parameters(child, child_path)
    elif isinstance(node, (list, tuple)):
        for i, child in enumerate(node):
            yield from open_parameters(child, f"{_path}[{i}]")


def assert_complete(config: Any) -> None:
    """Raise if any parameter in ``config`` is still OPEN.

    Call this before running a simulation. The error lists every unfilled
    parameter at once rather than failing on the first one, so a single run
    tells you the whole remaining gap.
    """
    missing = list(open_parameters(config))
    if not missing:
        return
    lines = "\n".join(
        f"  {o.register_id:5s} {path:44s} {o.description}" for path, o in missing
    )
    raise OpenParameter(
        f"{len(missing)} parameter(s) are still OPEN:\n{lines}\n\n"
        "Fill these in under goddard/config/ and record sources in "
        "docs/assumptions_register.md."
    )


# ---------------------------------------------------------------- environment


@dataclass(frozen=True)
class Environment:
    """Launch site and atmospheric conditions. Register section A."""

    field_elevation_m: Number = 1216.0          # A1 CONFIRMED, Tularosa Basin
    ground_temperature_K: Number = 303.15       # A2 ESTIMATED
    mean_wind_speed_ms: Number = Open("A4", "mean wind speed", "m/s")
    rail_length_m: Number = Open("A6", "launch rail length", "m")
    rail_angle_rad: Number = 0.0                # A7 ESTIMATED, vertical


# ------------------------------------------------------------------- geometry


@dataclass(frozen=True)
class NoseCone:
    """Von Karman (Haack C=0) nose. Register section B."""

    length_m: Number = 0.762                    # B5 CONFIRMED, fineness 5.0
    # B6 CONFIRMED -- the flare was removed, so the nose meets the body at full
    # diameter. This is no longer an independent parameter: it IS B1.
    base_diameter_m: Number = 0.1524
    tip_radius_m: Number = 0.00381              # B9 CONFIRMED, 5 % bluffness
    haack_c: float = 0.0                        # B4 CONFIRMED, Von Karman


@dataclass(frozen=True)
class Transition:
    """Flare between the nose section and the body. REMOVED by team decision.

    The ORK carried a sub-body-diameter nose flaring out to the body tube. That
    costs supersonic wave drag for no aerodynamic return, and the team removed
    it (register B7). A constant-diameter nose-to-body joint is the design.

    The transition machinery is kept rather than deleted: it is implemented and
    tested, it contributes exactly zero at zero length, and keeping it means
    reversing the decision is a config change rather than a rewrite. Everything
    downstream is guarded on ``present``.
    """

    present: bool = False            # B7 CONFIRMED -- flare removed
    length_m: float = 0.0            # B8 CONFIRMED -- zero length, no flare
    fore_diameter_m: float = 0.1524  # B6 CONFIRMED -- equals the body diameter
    aft_diameter_m: float = 0.1524   # B1 CONFIRMED


@dataclass(frozen=True)
class BodyTube:
    """Register section B."""

    diameter_m: Number = 0.1524                 # B1 CONFIRMED, 6 in
    length_m: Number = 3.60                     # B3 CONFIRMED, master variable
    wall_thickness_m: Number = 0.0024           # B2 CONFIRMED, fibreglass tube


@dataclass(frozen=True)
class FinSet:
    """Three clipped-delta fins. Register section B.

    Planform SUPERSEDES goddard1.0.ork. The ORK fin was found to be wrong on
    two counts at once (docs/reference/02_BUDGET_50KFT_DESIGN.md): it produced
    4.3 calibers of static margin -- badly over-stable, so the vehicle
    weathercocks into wind and loses apogee -- and it failed fin flutter,
    because a thin fin on a 300 mm root chord is only 1.6 % thick against a
    3-6 % design rule. Shrinking the fin fixes both simultaneously.

    The semi-span is therefore SOLVED from a 2.0-caliber stability target
    rather than chosen, which is why it carries an odd value.

    Construction is carbon-fibre skins over a foam core (team spec), NOT the
    solid G10 the source document assumed. See ``thickness_m``.
    """

    count: int = 3                              # B10 CONFIRMED
    taper_ratio: float = 0.425                  # B12 CONFIRMED, 85/200 mm
    sweep_angle_rad: float = 0.872665           # B13 CONFIRMED, 50 deg
    cant_angle_rad: float = 0.017453            # B18 CONFIRMED, 1.0 deg
    root_chord_m: Number = 0.200                # B14 CONFIRMED
    span_m: Number = 0.1097                     # B15 CONFIRMED, solved for 2.0 cal
    # B16 CONFIRMED as a total section thickness -- 3.17 % of root chord, inside
    # the 3-6 % rule. NOTE: the source sized this as 1/4 in solid G10 sheet. We
    # are building carbon-fibre skins over a foam core, so the skin/core split
    # (I2, I3) is still open and the source's flutter margin of 2.22 does NOT
    # carry over -- a sandwich has a different GJ entirely. Recompute once
    # I1-I5 land.
    thickness_m: Number = 0.00635
    cross_section: str = "hexagonal"            # B17 CONFIRMED, flat tip
    fillet_radius_m: Number = Open("B19", "fin fillet radius", "m")

    @property
    def tip_chord_m(self) -> Number:
        """Derived from the confirmed taper ratio."""
        return self.root_chord_m * self.taper_ratio


@dataclass(frozen=True)
class Geometry:
    nose: NoseCone = field(default_factory=NoseCone)
    transition: Transition = field(default_factory=Transition)
    body: BodyTube = field(default_factory=BodyTube)
    fins: FinSet = field(default_factory=FinSet)
    surface_roughness_m: Number = Open("B20", "surface roughness", "m")
    # H7 is an ASSUMPTION in the register, not an OPEN parameter: rail buttons,
    # camera housings and antennas are simply not modelled. Zero means "none
    # accounted for", which is the documented state -- not a missing value.
    protuberance_drag_area_m2: float = 0.0


# ---------------------------------------------------------------------- motor


@dataclass(frozen=True)
class Tank:
    """Self-pressurizing N2O tank. Register section D."""

    oxidiser_mass_kg: Number = 25.04            # D2 CONFIRMED
    volume_m3: Number = 0.0399                  # D3 CONFIRMED, 39.9 L
    fill_fraction: Number = 0.80                # D4 CONFIRMED -- SAFETY limit,
    # not a packing choice. 0.92 goes liquid-full at 27 C; 0.80 clears 33.6 C.
    initial_temperature_K: Number = 303.15      # D5 ESTIMATED, = ambient
    ullage_noncondensable_fraction: float = 0.0  # D10 CONFIRMED


@dataclass(frozen=True)
class Injector:
    """Straight-drilled showerhead plate. Register section E."""

    n_holes: Number = 33                        # E2 CONFIRMED
    hole_diameter_m: Number = 0.0015            # E3 CONFIRMED, 1.5 mm
    plate_thickness_m: Number = Open("E4", "plate thickness, sets L/d", "m")
    min_dp_ratio: float = 0.20                  # E6 ESTIMATED, chug criterion


@dataclass(frozen=True)
class Grain:
    """Single circular port, paraffin blend. Register section F."""

    length_m: Number = 0.349                    # F9 CONFIRMED
    initial_port_diameter_m: Number = 0.0692    # F10 CONFIRMED, 0.50 of grain OD
    outer_diameter_m: Number = 0.1370           # F11 CONFIRMED, 33.9 mm web
    liner_thickness_m: float = 0.003            # F12 CONFIRMED, ablative under
    # the grain; 12.7 mm in the pre- and post-chambers where gas touches the case


@dataclass(frozen=True)
class Nozzle:
    """Register section G."""

    throat_diameter_m: Number = 0.02887         # G4 CONFIRMED, 654.6 mm^2
    expansion_ratio: Number = 6.0               # G5 CONFIRMED, exit 70.9 mm
    convergence_half_angle_rad: float = 0.785398  # G8 CONFIRMED, 45 deg, SP-8115
    contour: str = "80% bell"                     # G8 CONFIRMED
    eta_cf: float = 0.96                        # G10 -- adopted from the design
    # record: 0.985 bell friction, less divergence loss and throat erosion.


@dataclass(frozen=True)
class Motor:
    tank: Tank = field(default_factory=Tank)
    injector: Injector = field(default_factory=Injector)
    grain: Grain = field(default_factory=Grain)
    nozzle: Nozzle = field(default_factory=Nozzle)
    pre_chamber_length_m: float = 0.060         # G3 CONFIRMED, L/D 0.43
    nozzle_material: str = "graphite throat, silica-phenolic con/div"  # G6
    feed_line_diameter_m: Number = Open("D7", "feed line inner diameter", "m")
    feed_line_length_m: Number = Open("D7", "feed line length", "m")
    main_valve_open_time_s: Number = Open("D9", "main valve opening time", "s")
    tank_material: str = "6061-T6"              # D6 CONFIRMED
    tank_meop_Pa: float = 70e5                  # D6 CONFIRMED, burst SF 2.0


# ------------------------------------------------------------ mass properties


@dataclass(frozen=True)
class MassBudget:
    """Register section C.

    Structural masses are DERIVED from geometry and material density in
    ``mass.py``; the entries here are the discrete items that geometry cannot
    predict.
    """

    # C2 CONFIRMED. Stacked-pressure-vessel architecture: the 6061-T6 tank and
    # chamber case ARE the airframe over their own length; only 0.45 m of
    # non-structural fibreglass tube remains. Density here is the aluminium.
    airframe_material_density: Number = 2700.0
    airframe_material: str = "6061-T6 aluminium (pressure vessels), fibreglass tube"
    avionics_mass_kg: Number = 1.200         # C3 CONFIRMED, at 0.594 m
    # C4 ESTIMATED, not measured. CosmicWatch Desktop Muon Detector v3X.
    # The repository publishes no mass, so this is built from its own drawings:
    #   enclosure PN2506 aluminium extrusion, 66.4 x 39.9 mm, 73.7 mm long,
    #     1.88 mm wall -> 50.3 cm^3 -> 136 g
    #   2 acrylic endplates, 3 mm                                    ->  19 g
    #   plastic scintillator 50 x 50 x 10 mm at 1.03 g/cc            ->  26 g
    #   PCBs, Pico, OLED, connectors                                 -> ~25 g
    #   microSD, screws, foil, tape                                  -> ~10 g
    # Scintillator THICKNESS is not given in the drawing (only 50 x 50);
    # 10 mm is assumed. At 20 mm the total rises to ~241 g.
    # Coincidence mode needs TWO detectors: ~0.43 kg plus the CAT5 cable.
    # WEIGH THE ACTUAL UNIT before this is treated as confirmed.
    payload_mass_kg: Number = 0.215
    recovery_mass_kg: Number = 4.400         # C5 CONFIRMED, at 0.937 m
    # C6 DERIVED from D6 geometry, not guessed:
    #   rho_Al * pi * (R^2 - (R-t)^2) * L
    #   = 2700 * pi * (0.0762^2 - 0.0727^2) * 2.401 = 10.61 kg
    tank_dry_mass_kg: Number = 10.61
    growth_allowance: Number = 0.05          # C9 CONFIRMED, +5 % on structure


# --------------------------------------------------------- materials


@dataclass(frozen=True)
class FinMaterials:
    """CF skins over a foam core. Register section I.

    ``core_shear_Pa`` is the single most important structural unknown: it
    dominates the fin's effective GJ, which sets the flutter speed. See
    ``structures/laminate.py``.
    """

    # ---- I1/I2 CONFIRMED: carbon-fibre skins, +/-45 woven fabric
    #
    # Note G_xy (31.0 GPa) EXCEEDS E_x (17.3 GPa). For an isotropic material
    # that would be impossible -- G = E/2(1+nu) is roughly 0.4E. For a +/-45
    # laminate it is exactly right and it is the whole point: the fibres lie
    # along the principal shear directions, so the layup is optimised for
    # torsional stiffness. On a flutter-critical fin, where GJ is what sets the
    # flutter speed, that is the correct choice rather than an anomaly.
    #
    # Woven fabric rotated 45 deg to the fin axis puts +45 and -45 fibres in a
    # single ply, so the stack is balanced and symmetric without anyone having
    # to orient individual tows by hand.
    face_modulus_Pa: Number = 1.733e10          # I1, E_x at 45 deg by CLT
    face_shear_Pa: Number = 3.10e10             # I1, G_xy at 45 deg by CLT
    face_density: Number = 1570.0               # I1, 1.57 g/cc
    ply_thickness_m: Number = 1.981e-4          # I2, normalisation CPT
    plies_per_side: int = 3                     # I2
    layup: str = "[(+/-45)3 / core / (+/-45)3]"  # I2

    core_type: str = "Divinycell H100"       # I3 CONFIRMED
    # I4 CONFIRMED. Note this did NOT turn out to dominate GJ as first assumed:
    # once core shear compliance is modelled the fin clears the 1.5 flutter
    # margin at every plausible core. The core couples the faces; it does not
    # supply the stiffness.
    core_shear_Pa: Number = 3.5e7
    core_modulus_Pa: Number = 1.35e8         # I4 CONFIRMED
    core_density: Number = 100.0             # I5 CONFIRMED
    # I9 CONFIRMED. NOTE: the design record achieved 2.22, but that was for a
    # SOLID G10 fin. We build CF skins over a foam core, so GJ differs and the
    # margin must be recomputed once I1-I5 land.
    required_flutter_margin: float = 1.5


@dataclass(frozen=True)
class NoseTipMaterial:
    """Aluminium tip. Register I6, I7."""

    alloy: str = "6061-T6"                  # I6 CONFIRMED
    # I7. 6061-T6 is limited by OVER-AGEING of the T6 temper, not by melting:
    # the precipitate structure that gives T6 its strength coarsens above
    # roughly 200 C, and the alloy does not recover on cooling. 473 K is the
    # short-duration limit, appropriate for a ~40 s ascent; sustained exposure
    # should use ~423 K.
    #
    # NOTE this is LOWER than the 550 K that TipThermal defaulted to, so the
    # heating margin is now tighter than it looked. That is the correct
    # direction -- the old default was not tied to any alloy.
    service_limit_K: Number = 473.0         # I7 CONFIRMED, 200 C
    mass_kg: Number = Open("I8", "nose tip mass -- weigh the machined cap", "kg")
    emissivity: float = 0.15


@dataclass(frozen=True)
class Materials:
    fins: FinMaterials = field(default_factory=FinMaterials)
    nose_tip: NoseTipMaterial = field(default_factory=NoseTipMaterial)


# ---------------------------------------------------------------- calibration


@dataclass(frozen=True)
class Calibration:
    """The three unmeasured constants. Spec section 6, register E5/F8/G9.

    No static fire and no cold flow are planned, so none of these is measured.
    They are swept in band mode rather than trusted as point values.

    Read spec section 6.1 before changing any of this. "Conservative" has no
    single direction here: oxidiser flow is set by the tank and injector, not
    the grain, so lower regression means HIGHER O/F. A scalar biased for apogee
    leaves port burnthrough unexamined.
    """

    regression_calibration: float = 0.85        # F8 BANDED
    injector_cd: float = 0.70                   # E5 BANDED
    eta_cstar: float = 0.88                     # G9 BANDED

    # Band-mode sweep ranges, (low, high).
    regression_band: tuple[float, float] = (0.75, 1.00)
    injector_cd_band: tuple[float, float] = (0.61, 0.82)
    eta_cstar_band: tuple[float, float] = (0.82, 0.93)


# ------------------------------------------------------------------ recovery


@dataclass(frozen=True)
class Recovery:
    """Drogue then reefed main then full main. Register section J."""

    canopy_cds_m2: Number = Open("J3", "canopy Cd*S, full open", "m^2")
    reefing_ratio: Number = Open("J4", "reefing ratio")
    disreef_altitude_m: Number = Open("J5", "disreef trigger altitude", "m")
    filling_constant: float = 8.0               # J6 ESTIMATED, Knacke
    opening_force_coefficient: Number = Open("J7", "opening force coefficient Cx")
    max_opening_load_N: Number = Open("J9", "max allowable opening load", "N")
    max_landing_speed_ms: float = 7.0           # J10 CONFIRMED


# ------------------------------------------------------------------ settings


@dataclass(frozen=True)
class SimSettings:
    """Register section K -- all CONFIRMED."""

    dt_s: float = 0.01
    max_time_s: float = 600.0
    band_grid_levels: int = 3


@dataclass(frozen=True)
class RocketConfig:
    """Root configuration object."""

    name: str = "goddard-v2"
    environment: Environment = field(default_factory=Environment)
    geometry: Geometry = field(default_factory=Geometry)
    mass: MassBudget = field(default_factory=MassBudget)
    materials: Materials = field(default_factory=Materials)
    motor: Motor = field(default_factory=Motor)
    calibration: Calibration = field(default_factory=Calibration)
    recovery: Recovery = field(default_factory=Recovery)
    sim: SimSettings = field(default_factory=SimSettings)

    def missing(self) -> list[tuple[str, Open]]:
        """Every parameter still OPEN, as ``(dotted_path, Open)`` pairs."""
        return list(open_parameters(self))

    def report_missing(self) -> str:
        """Human-readable list of everything still unfilled."""
        missing = self.missing()
        if not missing:
            return "All parameters filled."
        lines = [f"{len(missing)} parameter(s) still OPEN:"]
        lines += [
            f"  {o.register_id:5s} {path:44s} {o.description}"
            for path, o in missing
        ]
        return "\n".join(lines)
