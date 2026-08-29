"""Mass, centre of gravity and inertia, varying through the burn.

Spec section 3, register section C.

Built up from components rather than hand-entered, so that changing a dimension
changes the mass without anyone remembering to update a second number. Each
component carries its own mass, axial position and local inertia; the vehicle
totals are assembled by the parallel-axis theorem.

Propellant is handled separately from dry structure because it moves: as the
oxidiser drains and the grain regresses, both the total mass and the CG shift,
and the CG shift is what changes the static margin during flight.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MassComponent:
    """A single mass item.

    Attributes
    ----------
    name       : identifier, used in the mass report
    mass_kg    : kg
    x_m        : axial centroid, m aft of the nose tip
    i_axial    : own moment of inertia about the roll axis, kg m^2
    i_lateral  : own moment of inertia about a lateral axis through its own
                 centroid, kg m^2
    """

    name: str
    mass_kg: float
    x_m: float
    i_axial: float = 0.0
    i_lateral: float = 0.0

    def __post_init__(self) -> None:
        if self.mass_kg < 0.0:
            raise ValueError(f"{self.name}: mass must be non-negative")


@dataclass(frozen=True)
class MassState:
    """Vehicle mass properties at one instant.

    Attributes
    ----------
    mass_kg   : total mass, kg
    x_cg_m    : centre of gravity, m aft of the nose tip
    i_roll    : moment of inertia about the roll axis, kg m^2
    i_pitch   : moment of inertia about a lateral axis through the CG, kg m^2
    """

    mass_kg: float
    x_cg_m: float
    i_roll: float
    i_pitch: float


def cylinder_inertia(
    mass_kg: float, radius_m: float, length_m: float
) -> tuple[float, float]:
    """``(i_axial, i_lateral)`` of a solid cylinder about its own centroid."""
    i_axial = 0.5 * mass_kg * radius_m ** 2
    i_lateral = mass_kg * (3.0 * radius_m ** 2 + length_m ** 2) / 12.0
    return i_axial, i_lateral


def tube_inertia(
    mass_kg: float, r_inner_m: float, r_outer_m: float, length_m: float
) -> tuple[float, float]:
    """``(i_axial, i_lateral)`` of a hollow tube about its own centroid."""
    if r_outer_m <= r_inner_m:
        raise ValueError("outer radius must exceed inner radius")
    rr = r_inner_m ** 2 + r_outer_m ** 2
    i_axial = 0.5 * mass_kg * rr
    i_lateral = mass_kg * (3.0 * rr + length_m ** 2) / 12.0
    return i_axial, i_lateral


def combine(components: list[MassComponent]) -> MassState:
    """Assemble total mass properties from components.

    Lateral inertia uses the parallel-axis theorem about the assembled CG.
    """
    if not components:
        raise ValueError("need at least one mass component")

    total = sum(c.mass_kg for c in components)
    if total <= 0.0:
        raise ValueError("total mass must be positive")

    x_cg = sum(c.mass_kg * c.x_m for c in components) / total
    i_roll = sum(c.i_axial for c in components)
    i_pitch = sum(
        c.i_lateral + c.mass_kg * (c.x_m - x_cg) ** 2 for c in components
    )
    return MassState(mass_kg=total, x_cg_m=x_cg, i_roll=i_roll, i_pitch=i_pitch)


@dataclass(frozen=True)
class MassModel:
    """Dry structure plus movable propellant.

    ``dry`` components never change. ``oxidiser_x_m`` and ``fuel_x_m`` are the
    centroids of the tank and grain, held fixed -- a simplification that ignores
    the liquid level dropping within the tank. For a short burn the resulting CG
    error is small, but it is a real approximation and is noted here rather than
    hidden.
    """

    dry: list[MassComponent] = field(default_factory=list)
    oxidiser_x_m: float = 0.0
    fuel_x_m: float = 0.0
    oxidiser_radius_m: float = 0.0
    fuel_radius_m: float = 0.0

    def at(self, oxidiser_mass_kg: float, fuel_mass_kg: float) -> MassState:
        """Mass properties with the given propellant remaining."""
        components = list(self.dry)

        if oxidiser_mass_kg > 0.0:
            i_ax, i_lat = cylinder_inertia(
                oxidiser_mass_kg, self.oxidiser_radius_m, 0.0
            )
            components.append(
                MassComponent(
                    "oxidiser", oxidiser_mass_kg, self.oxidiser_x_m, i_ax, i_lat
                )
            )
        if fuel_mass_kg > 0.0:
            i_ax, i_lat = cylinder_inertia(fuel_mass_kg, self.fuel_radius_m, 0.0)
            components.append(
                MassComponent("fuel", fuel_mass_kg, self.fuel_x_m, i_ax, i_lat)
            )
        return combine(components)

    @property
    def dry_mass_kg(self) -> float:
        return sum(c.mass_kg for c in self.dry)
