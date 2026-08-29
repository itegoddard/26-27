"""Effective stiffness of a carbon-fibre-skinned, foam-cored fin.

Spec section 7.1.

The foam core exists to raise torsional stiffness, so the flutter calculation
must see the sandwich rather than an isotropic plate. This module produces the
effective ``EI`` and ``GJ`` that ``flutter.py`` consumes.

Method
------
Thin-face sandwich approximation (Allen 1969). The faces are treated as
membranes separated by a distance ``d`` between their centroids; the core
contributes its own (small) direct stiffness. For a plate of chord ``c``:

    twisting rigidity per unit width   D_xy = G_face * t_face * d**2 / 2
    plate torsional rigidity           GJ   = 4 * c * D_xy

The ``GJ = 4 * c * D_xy`` relation is the standard thin-plate result: for a
solid isotropic plate ``D_xy = G t**3 / 12``, which recovers the familiar
``GJ = G c t**3 / 3``. ``tests/test_laminate.py`` pins that recovery.

Limitations -- read before trusting a flutter margin
----------------------------------------------------
1. Thin-face approximation. Valid while ``t_face << t_core``; degrades as the
   faces thicken.
2. Quasi-isotropic faces assumed, characterised by a single ``G_face``. A real
   layup is orthotropic and direction matters. For a fin whose flutter mode is
   torsional this is the largest modelling simplification here.
3. Core shear compliance reduces effective torsional stiffness beyond what the
   direct core term captures. Not modelled.

All three push in the SAME direction: this module **over-predicts** ``GJ``, and
therefore over-predicts flutter speed. Treat its output as an upper bound and
carry margin accordingly (register I9 asks NASA what margin they require).

Reference
---------
Allen, H. G., *Analysis and Design of Structural Sandwich Panels*, Pergamon,
1969. See ``docs/references.bib`` (key ``allen1969sandwich``).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SandwichSection:
    """Geometry and material properties of a symmetric sandwich fin section.

    Attributes
    ----------
    face_thickness_m : thickness of ONE face sheet, m
    core_thickness_m : core thickness, m
    chord_m          : section chord (plate width in torsion), m
    face_modulus_Pa  : face in-plane Young's modulus, Pa
    face_shear_Pa    : face in-plane shear modulus, Pa
    core_modulus_Pa  : core Young's modulus, Pa
    core_shear_Pa    : core shear modulus, Pa
    """

    face_thickness_m: float
    core_thickness_m: float
    chord_m: float
    face_modulus_Pa: float
    face_shear_Pa: float
    core_modulus_Pa: float
    core_shear_Pa: float

    def __post_init__(self) -> None:
        for name in (
            "face_thickness_m",
            "core_thickness_m",
            "chord_m",
            "face_modulus_Pa",
            "face_shear_Pa",
        ):
            if getattr(self, name) <= 0.0:
                raise ValueError(f"{name} must be positive, got {getattr(self, name)}")
        if self.core_modulus_Pa < 0.0 or self.core_shear_Pa < 0.0:
            raise ValueError("core properties must be non-negative")

    @property
    def total_thickness_m(self) -> float:
        """Overall section thickness, ``2 * t_face + t_core``."""
        return 2.0 * self.face_thickness_m + self.core_thickness_m

    @property
    def face_separation_m(self) -> float:
        """Distance ``d`` between the centroids of the two face sheets."""
        return self.core_thickness_m + self.face_thickness_m


def bending_stiffness(section: SandwichSection) -> float:
    """Effective ``EI`` of the section about its neutral axis, N m^2."""
    t_f = section.face_thickness_m
    d = section.face_separation_m
    c = section.chord_m

    faces = section.face_modulus_Pa * t_f * d * d / 2.0 * c
    core = section.core_modulus_Pa * c * section.core_thickness_m ** 3 / 12.0
    return faces + core


def torsional_stiffness(section: SandwichSection) -> float:
    """Effective ``GJ`` of the section, N m^2.

    See the module docstring: this is an upper bound.
    """
    t_f = section.face_thickness_m
    d = section.face_separation_m
    c = section.chord_m

    d_xy = section.face_shear_Pa * t_f * d * d / 2.0
    faces = 4.0 * c * d_xy
    core = section.core_shear_Pa * c * section.core_thickness_m ** 3 / 3.0
    return faces + core


def torsion_constant_solid(chord_m: float, thickness_m: float) -> float:
    """Torsion constant ``J`` of an equivalent solid plate, m^4.

    Thin-plate result ``J = c * t**3 / 3``.
    """
    if chord_m <= 0.0 or thickness_m <= 0.0:
        raise ValueError("chord and thickness must be positive")
    return chord_m * thickness_m ** 3 / 3.0


def effective_shear_modulus(section: SandwichSection) -> float:
    """Shear modulus of a solid plate of the same outer dimensions, Pa.

    This is the bridge into NACA TN 4197, which is written for an isotropic
    plate. Rather than plugging in the raw carbon-fibre shear modulus -- which
    would ignore the whole point of the foam core -- the sandwich ``GJ`` is
    mapped onto the equivalent solid section:

        G_eff = GJ_sandwich / J_solid

    so the flutter criterion sees a plate that twists like the real fin.
    """
    gj = torsional_stiffness(section)
    j = torsion_constant_solid(section.chord_m, section.total_thickness_m)
    return gj / j
