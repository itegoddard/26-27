"""Fin flutter and torsional divergence.

Spec section 7.1.

Two independent checks, because they are different instabilities and either can
be the binding one:

* **Flutter** -- the dynamic bending/torsion coupling of NACA TN 4197.
* **Divergence** -- the static aeroelastic instability. For low-``GJ`` composite
  fins divergence frequently arrives *first*, and flutter-only screening misses
  it entirely.

Both are evaluated against the actual trajectory, not a single worst-case guess.

References
----------
Martin, D. J., NACA TN 4197 (1958). NTRS 19930085030.
Bisplinghoff, Ashley & Halfman, *Aeroelasticity*, 1955.
See ``docs/references.bib``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FinPlanform:
    """Exposed planform of one fin panel.

    Attributes
    ----------
    root_chord_m : root chord, m
    tip_chord_m  : tip chord, m
    span_m       : exposed semi-span of one panel, m
    thickness_m  : maximum section thickness, m
    """

    root_chord_m: float
    tip_chord_m: float
    span_m: float
    thickness_m: float

    def __post_init__(self) -> None:
        if self.root_chord_m <= 0.0 or self.span_m <= 0.0:
            raise ValueError("root chord and span must be positive")
        if self.tip_chord_m < 0.0:
            raise ValueError("tip chord must be non-negative")
        if self.thickness_m <= 0.0:
            raise ValueError("thickness must be positive")

    @property
    def area_m2(self) -> float:
        """Exposed panel area, m^2."""
        return 0.5 * (self.root_chord_m + self.tip_chord_m) * self.span_m

    @property
    def aspect_ratio(self) -> float:
        """Panel aspect ratio ``b^2 / S``."""
        return self.span_m ** 2 / self.area_m2

    @property
    def taper_ratio(self) -> float:
        """Tip chord over root chord."""
        return self.tip_chord_m / self.root_chord_m

    @property
    def mean_chord_m(self) -> float:
        """Mean geometric chord, m."""
        return self.area_m2 / self.span_m

    @property
    def thickness_ratio(self) -> float:
        """``t/c`` on the mean chord."""
        return self.thickness_m / self.mean_chord_m


@dataclass(frozen=True)
class AeroelasticMargins:
    """Flutter and divergence results at one flight condition.

    Margins are ``critical / actual``: greater than 1 is safe, and the margin is
    how much faster (or how much more dynamic pressure) the vehicle could take
    before the instability onsets.
    """

    flutter_speed_ms: float
    divergence_pressure_Pa: float
    flutter_margin: float
    divergence_margin: float
    critical: bool


def flutter_speed(
    planform: FinPlanform,
    shear_modulus_Pa: float,
    ambient_pressure_Pa: float,
    speed_of_sound_ms: float,
) -> float:
    """Flutter onset velocity, m/s. NACA TN 4197.

        V_f = a * sqrt( G / X )
        X   = 1.337 * AR**3 * P * (lambda + 1) / (2 * (AR + 2) * (t/c)**3)

    ``G`` and ``P`` need only share units, since the criterion depends on their
    ratio -- so this is evaluated in SI directly, with no psi conversion.

    Pass ``shear_modulus_Pa`` from ``laminate.effective_shear_modulus`` rather
    than the raw fibre modulus, or the foam core does nothing in the answer.

    TN 4197's own author describes these criteria as "crude". Treat the result
    as a screening number, and see ``laminate.py`` for why it is additionally an
    upper bound.
    """
    if shear_modulus_Pa <= 0.0:
        raise ValueError(f"shear modulus must be positive, got {shear_modulus_Pa}")
    if ambient_pressure_Pa <= 0.0:
        raise ValueError("ambient pressure must be positive")
    if speed_of_sound_ms <= 0.0:
        raise ValueError("speed of sound must be positive")

    ar = planform.aspect_ratio
    tc = planform.thickness_ratio
    lam = planform.taper_ratio

    denom = (
        1.337
        * ar ** 3
        * ambient_pressure_Pa
        * (lam + 1.0)
        / (2.0 * (ar + 2.0) * tc ** 3)
    )
    return speed_of_sound_ms * math.sqrt(shear_modulus_Pa / denom)


def divergence_pressure(
    planform: FinPlanform,
    torsional_stiffness_Nm2: float,
    lift_curve_slope: float = 2.0 * math.pi,
    eccentricity: float = 0.25,
) -> float:
    """Torsional divergence dynamic pressure, Pa.

    Uniform-cantilever result:

        q_div = (pi**2 / 4) * GJ / (s**2 * e * c**2 * CL_alpha)

    Parameters
    ----------
    torsional_stiffness_Nm2 : effective ``GJ`` from ``laminate.py``
    lift_curve_slope        : ``dCL/dalpha`` per radian
    eccentricity            : distance from elastic axis to aerodynamic centre,
                              as a fraction of chord. The 0.25 default assumes
                              the elastic axis sits at mid-chord and the
                              aerodynamic centre at the quarter-chord -- check
                              against the real layup before relying on it.
    """
    if torsional_stiffness_Nm2 <= 0.0:
        raise ValueError("GJ must be positive")
    if eccentricity <= 0.0:
        raise ValueError(
            "eccentricity must be positive; a zero or negative value means the "
            "aerodynamic centre is at or behind the elastic axis, in which case "
            "the fin does not diverge and this function should not be called"
        )

    s = planform.span_m
    c = planform.mean_chord_m
    return (
        math.pi ** 2
        / 4.0
        * torsional_stiffness_Nm2
        / (s ** 2 * eccentricity * c ** 2 * lift_curve_slope)
    )


def margins(
    planform: FinPlanform,
    shear_modulus_Pa: float,
    torsional_stiffness_Nm2: float,
    velocity_ms: float,
    dynamic_pressure_Pa: float,
    ambient_pressure_Pa: float,
    speed_of_sound_ms: float,
    lift_curve_slope: float = 2.0 * math.pi,
    eccentricity: float = 0.25,
) -> AeroelasticMargins:
    """Both aeroelastic margins at a single flight condition."""
    v_f = flutter_speed(
        planform, shear_modulus_Pa, ambient_pressure_Pa, speed_of_sound_ms
    )
    q_div = divergence_pressure(
        planform, torsional_stiffness_Nm2, lift_curve_slope, eccentricity
    )

    flutter_margin = math.inf if velocity_ms <= 0.0 else v_f / velocity_ms
    divergence_margin = (
        math.inf if dynamic_pressure_Pa <= 0.0 else q_div / dynamic_pressure_Pa
    )

    return AeroelasticMargins(
        flutter_speed_ms=v_f,
        divergence_pressure_Pa=q_div,
        flutter_margin=flutter_margin,
        divergence_margin=divergence_margin,
        critical=min(flutter_margin, divergence_margin) < 1.0,
    )
