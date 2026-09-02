"""Normal force and centre of pressure -- Barrowman with corrections.

Spec section 5.

Coefficients are per radian, referenced to the body maximum cross-section area.
``x_cp`` is measured aft from the nose tip.

References
----------
Barrowman, J. S., M.S. thesis, 1967. NTRS 20010047838.
Allen & Perkins, NACA Report 1048, 1951 -- body cross-flow at angle of attack.
See ``docs/references.bib``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from goddard.aero.geometry import VehicleGeometry


@dataclass(frozen=True)
class NormalForce:
    """Static aerodynamic stability at one flight condition.

    Attributes
    ----------
    cn_alpha    : normal-force curve slope, per radian
    x_cp_m      : centre of pressure aft of the nose tip, m
    cn          : normal-force coefficient at the current angle of attack
    """

    cn_alpha: float
    x_cp_m: float
    cn: float


def compressibility_factor(mach: float) -> float:
    """Prandtl-Glauert / Ackeret divisor, clamped through the transonic band.

    The singularity at M = 1 is real in linearised theory and unphysical in
    fact, so beta is floored at 0.5. Coefficients through the transonic region
    are approximate -- a known limitation, and the same one OpenRocket warns
    about.
    """
    if mach < 0.9:
        return max(math.sqrt(1.0 - mach * mach), 0.5)
    if mach > 1.1:
        return max(math.sqrt(mach * mach - 1.0), 0.5)
    return 0.5


def nose_contribution(geom: VehicleGeometry) -> tuple[float, float]:
    """Von Karman nose. Returns ``(cn_alpha, x_cp_m)``.

    Slender-body theory gives ``CN_alpha = 2`` on the base area for any pointed
    body of revolution, and ``x_cp = L - V / A_base``.

    For the Haack C=0 (Von Karman) profile the nose volume integrates exactly to
    ``V = A_base * L / 2``, so ``x_cp = L / 2``. That is a derived result, not a
    tabulated approximation -- ``tests/test_normal_force.py`` pins it.
    """
    ratio = geom.nose.base_area_m2 / geom.reference_area_m2
    return 2.0 * ratio, geom.nose.length_m / 2.0


def transition_contribution(geom: VehicleGeometry) -> tuple[float, float]:
    """Haack flare. Returns ``(cn_alpha, x_cp_m)``.

    Zero when no flare is present.
    """
    t = geom.transition
    if not t.present:
        return 0.0, 0.0

    d_ref = geom.body.diameter_m
    fore = (t.fore_diameter_m / d_ref) ** 2
    aft = (t.aft_diameter_m / d_ref) ** 2
    cn_alpha = 2.0 * (aft - fore)

    x_start = geom.nose.length_m
    ratio = t.fore_diameter_m / t.aft_diameter_m
    if abs(1.0 - ratio * ratio) < 1e-12:
        x_cp = x_start + t.length_m / 2.0
    else:
        x_cp = x_start + (t.length_m / 3.0) * (
            1.0 + (1.0 - ratio) / (1.0 - ratio * ratio)
        )
    return cn_alpha, x_cp


def fin_contribution(geom: VehicleGeometry) -> tuple[float, float]:
    """Fin set with body interference. Returns ``(cn_alpha, x_cp_m)``."""
    f = geom.fins
    R = geom.body.diameter_m / 2.0
    s = f.span_m

    # Mid-chord line length.
    dx = (
        s * math.tan(f.sweep_angle_rad)
        + f.tip_chord_m / 2.0
        - f.root_chord_m / 2.0
    )
    l_mid = math.hypot(s, dx)

    denom = 1.0 + math.sqrt(
        1.0 + (2.0 * l_mid / (f.root_chord_m + f.tip_chord_m)) ** 2
    )
    cn_alpha = (4.0 * f.count * (s / geom.body.diameter_m) ** 2) / denom

    # Body-to-fin interference (Barrowman K_fb).
    cn_alpha *= 1.0 + R / (s + R)

    sweep_len = s * math.tan(f.sweep_angle_rad)
    # Fin root leading-edge station. Falls back to flush with the tail only if
    # the layout does not say otherwise -- see FinGeometry.root_station_m.
    x_root = (
        f.root_station_m
        if f.root_station_m is not None
        else geom.total_length_m - f.root_chord_m
    )
    x_cp = (
        x_root
        + sweep_len * (f.root_chord_m + 2.0 * f.tip_chord_m)
        / (3.0 * (f.root_chord_m + f.tip_chord_m))
        + (1.0 / 6.0)
        * (
            f.root_chord_m
            + f.tip_chord_m
            - f.root_chord_m * f.tip_chord_m / (f.root_chord_m + f.tip_chord_m)
        )
    )
    return cn_alpha, x_cp


def body_crossflow(geom: VehicleGeometry, alpha_rad: float) -> tuple[float, float]:
    """Allen & Perkins viscous cross-flow on the body. Returns ``(cn, x_cp_m)``.

    Nonlinear in alpha, so it contributes to ``cn`` directly rather than to
    ``cn_alpha``. Negligible at small angles, significant past a few degrees --
    which is why it is here at all: alpha is a live state in the 4-DOF model.
    """
    if abs(alpha_rad) < 1e-9:
        return 0.0, 0.0

    k = 1.1  # cross-flow drag proportionality, Allen & Perkins
    planform = geom.body.diameter_m * geom.total_length_m
    cn = k * (planform / geom.reference_area_m2) * math.sin(alpha_rad) ** 2
    cn = math.copysign(cn, alpha_rad)
    return cn, 0.5 * geom.total_length_m


def evaluate(
    geom: VehicleGeometry, mach: float, alpha_rad: float = 0.0
) -> NormalForce:
    """Total normal-force slope, centre of pressure and normal force."""
    beta = compressibility_factor(mach)

    contributions = [
        nose_contribution(geom),
        transition_contribution(geom),
        fin_contribution(geom),
    ]

    cn_alpha = sum(c for c, _ in contributions) / beta
    slope_moment = sum(c * x for c, x in contributions) / beta

    # Linear (potential-flow) part.
    cn_linear = cn_alpha * alpha_rad
    moment_linear = slope_moment * alpha_rad

    # Nonlinear viscous cross-flow part.
    cn_cross, x_cross = body_crossflow(geom, alpha_rad)

    cn_total = cn_linear + cn_cross
    moment_total = moment_linear + cn_cross * x_cross

    # Centre of pressure is the force-weighted moment arm. At vanishing alpha
    # both numerator and denominator go to zero, so fall back to the linear
    # limit -- which is the quantity static margin is defined against anyway.
    if abs(cn_total) > 1e-12:
        x_cp = moment_total / cn_total
    elif cn_alpha > 1e-12:
        x_cp = slope_moment / cn_alpha
    else:
        x_cp = 0.0

    return NormalForce(cn_alpha=cn_alpha, x_cp_m=x_cp, cn=cn_total)


def static_margin(x_cp_m: float, x_cg_m: float, caliber_m: float) -> float:
    """Static margin in calibers. Positive is stable."""
    if caliber_m <= 0.0:
        raise ValueError("caliber must be positive")
    return (x_cp_m - x_cg_m) / caliber_m
