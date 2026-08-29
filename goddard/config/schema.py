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

    length_m: Number = Open("B5", "nose length (sets fineness ratio)", "m")
    base_diameter_m: Number = Open("B6", "nose base diameter", "m")
    tip_radius_m: Number = Open("B9", "nose tip radius", "m")
    haack_c: float = 0.0                        # B4 CONFIRMED, Von Karman


@dataclass(frozen=True)
class Transition:
    """Haack flare from the nose section up to the body. Register section B.

    Set ``length_m = 0.0`` to remove the flare entirely (nose base diameter
    equal to body diameter). See register B7 -- whether the flare is intended
    is an open question, and it costs supersonic wave drag.
    """

    present: Number = Open("B7", "is the sub-body-diameter nose + flare intended?")
    length_m: Number = Open("B8", "flare length", "m")
    fore_diameter_m: Number = Open("B6", "flare fore diameter", "m")
    aft_diameter_m: float = 0.1524   # B1 CONFIRMED -- the flare meets the body


@dataclass(frozen=True)
class BodyTube:
    """Register section B."""

    diameter_m: Number = 0.1524                 # B1 CONFIRMED, 6 in
    length_m: Number = Open("B3", "body tube length", "m")
    wall_thickness_m: Number = Open("B2", "body wall thickness", "m")


@dataclass(frozen=True)
class FinSet:
    """Three clipped-delta fins. Planform shape is CONFIRMED and locked.

    Register section B. The taper ratio and sweep are shape ratios carried over
    from goddard1.0.ork and are not open for change; the absolute size is.
    """

    count: int = 3                              # B10 CONFIRMED
    taper_ratio: float = 0.328                  # B12 CONFIRMED
    sweep_angle_rad: float = 1.0821             # B13 CONFIRMED, 62 deg
    cant_angle_rad: float = 0.017453            # B18 CONFIRMED, 1.0 deg
    root_chord_m: Number = Open("B14", "fin root chord", "m")
    span_m: Number = Open("B15", "fin span", "m")
    thickness_m: Number = Open("B16", "fin thickness", "m")
    cross_section: Number = Open(
        "B17", "fin cross-section: rounded (per ORK) or double-wedge"
    )
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

    oxidiser_mass_kg: Number = Open("D2", "N2O mass", "kg")
    volume_m3: Number = Open("D3", "tank internal volume", "m^3")
    fill_fraction: Number = Open("D4", "initial liquid fill fraction")
    initial_temperature_K: Number = 303.15      # D5 ESTIMATED, = ambient
    ullage_noncondensable_fraction: float = 0.0  # D10 CONFIRMED


@dataclass(frozen=True)
class Injector:
    """Straight-drilled showerhead plate. Register section E."""

    n_holes: Number = Open("E2", "number of orifices")
    hole_diameter_m: Number = Open("E3", "orifice diameter", "m")
    plate_thickness_m: Number = Open("E4", "plate thickness, sets L/d", "m")
    min_dp_ratio: float = 0.20                  # E6 ESTIMATED, chug criterion


@dataclass(frozen=True)
class Grain:
    """Single circular port, paraffin blend. Register section F."""

    length_m: Number = Open("F9", "grain length", "m")
    initial_port_diameter_m: Number = Open("F10", "initial port diameter", "m")
    outer_diameter_m: Number = Open("F11", "grain OD, sets burnthrough margin", "m")
    liner_material: Number = Open("F12", "liner material and thickness")


@dataclass(frozen=True)
class Nozzle:
    """Register section G."""

    throat_diameter_m: Number = Open("G4", "throat diameter", "m")
    expansion_ratio: Number = Open("G5", "expansion ratio")
    divergence_half_angle_rad: Number = Open("G8", "divergence half angle", "rad")
    eta_cf: float = 0.97                        # G10 ESTIMATED


@dataclass(frozen=True)
class Motor:
    tank: Tank = field(default_factory=Tank)
    injector: Injector = field(default_factory=Injector)
    grain: Grain = field(default_factory=Grain)
    nozzle: Nozzle = field(default_factory=Nozzle)
    chamber_volume_m3: Number = Open("G3", "pre-combustion chamber volume", "m^3")
    nozzle_material: Number = Open("G6", "nozzle material")
    feed_line_diameter_m: Number = Open("D7", "feed line inner diameter", "m")
    feed_line_length_m: Number = Open("D7", "feed line length", "m")
    main_valve_open_time_s: Number = Open("D9", "main valve opening time", "s")
    tank_material: Number = Open("D6", "tank material / MEOP")


# ------------------------------------------------------------ mass properties


@dataclass(frozen=True)
class MassBudget:
    """Register section C.

    Structural masses are DERIVED from geometry and material density in
    ``mass.py``; the entries here are the discrete items that geometry cannot
    predict.
    """

    airframe_material_density: Number = Open("C2", "airframe material density", "kg/m^3")
    avionics_mass_kg: Number = Open("C3", "avionics mass", "kg")
    payload_mass_kg: Number = Open("C4", "payload mass", "kg")
    recovery_mass_kg: Number = Open("C5", "recovery system mass", "kg")
    tank_dry_mass_kg: Number = Open("C6", "tank dry mass", "kg")
    growth_allowance: Number = Open("C9", "mass growth allowance", "fraction")


# --------------------------------------------------------- materials


@dataclass(frozen=True)
class FinMaterials:
    """CF skins over a foam core. Register section I.

    ``core_shear_Pa`` is the single most important structural unknown: it
    dominates the fin's effective GJ, which sets the flutter speed. See
    ``structures/laminate.py``.
    """

    face_modulus_Pa: Number = Open("I1", "CF skin Young's modulus", "Pa")
    face_shear_Pa: Number = Open("I1", "CF skin shear modulus", "Pa")
    ply_thickness_m: Number = Open("I2", "CF ply thickness", "m")
    layup: Number = Open("I2", "CF layup schedule")
    core_type: Number = Open("I3", "foam core type")
    core_shear_Pa: Number = Open("I4", "foam core shear modulus -- dominates GJ", "Pa")
    core_modulus_Pa: Number = Open("I4", "foam core Young's modulus", "Pa")
    core_density: Number = Open("I5", "foam core density", "kg/m^3")
    required_flutter_margin: Number = Open("I9", "required flutter margin")


@dataclass(frozen=True)
class NoseTipMaterial:
    """Aluminium tip. Register I6, I7."""

    alloy: Number = Open("I6", "aluminium alloy")
    service_limit_K: Number = Open("I7", "alloy service temperature limit", "K")
    mass_kg: Number = Open("I6", "tip mass", "kg")
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

    drogue_cds_m2: Number = Open("J2", "drogue Cd*S", "m^2")
    main_cds_m2: Number = Open("J3", "main Cd*S, full open", "m^2")
    reefing_ratio: Number = Open("J4", "reefing ratio")
    disreef_altitude_m: Number = Open("J5", "disreef trigger altitude", "m")
    filling_constant: float = 8.0               # J6 ESTIMATED, Knacke
    opening_force_coefficient: Number = Open("J7", "opening force coefficient Cx")
    max_opening_load_N: Number = Open("J9", "max allowable opening load", "N")
    max_landing_speed_ms: Number = Open("J10", "max allowable landing speed", "m/s")


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
