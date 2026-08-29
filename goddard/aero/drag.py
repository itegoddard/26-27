"""Drag coefficient build-up, varying with Mach and Reynolds number.

Spec section 5.

This is the single largest correction over the 25-26 model, which held
``C_D = 0.5`` constant through Mach 1.65.

CALIBRATION WARNING
-------------------
The skin-friction and base-drag terms rest on well-established correlations.
The **supersonic wave-drag terms do not**: nose and fin wave drag here are
engineering approximations, not validated results. ``DragBuildup.validated`` is
``False`` for exactly this reason, and ``sim.run`` surfaces it.

Before trusting an apogee number, cross-check ``total`` against RASAero II or
CFD at Mach 0.5 / 1.2 / 2.0 / 2.5 and record the comparison. Until then treat
absolute drag as uncertain to tens of percent, while trends and sensitivities
remain useful.

References
----------
Hoerner, *Fluid-Dynamic Drag*, 1965 -- base drag, fin thickness drag,
leading-edge bluntness, interference.
Niskanen, *OpenRocket Technical Documentation* -- skin-friction form and the
compressibility corrections.
See ``docs/references.bib``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from goddard.aero.geometry import VehicleGeometry


@dataclass(frozen=True)
class DragBuildup:
    """Drag coefficients on the vehicle reference area.

    ``validated`` is False until the supersonic terms have been checked against
    RASAero or CFD. It is threaded through to the simulation report rather than
    quietly forgotten.
    """

    friction: float
    nose_wave: float
    transition_wave: float
    fin_wave: float
    base: float
    interference: float
    total: float
    validated: bool = False


def skin_friction_coefficient(
    reynolds: float, roughness_m: float, length_m: float, mach: float
) -> float:
    """Compressible turbulent flat-plate skin-friction coefficient.

    Fully turbulent is assumed throughout (register H2) -- conservative on drag
    for a vehicle of this size and speed.
    """
    if reynolds < 1.0e4:
        cf = 1.48e-2
    else:
        cf = 1.0 / (1.50 * math.log(reynolds) - 5.6) ** 2

    # Roughness-limited floor: below a critical Reynolds number the surface
    # finish, not the boundary layer, sets the friction.
    if roughness_m > 0.0 and length_m > 0.0:
        cf_rough = 0.032 * (roughness_m / length_m) ** 0.2
        cf = max(cf, cf_rough)

    # Compressibility.
    if mach < 1.0:
        cf *= 1.0 - 0.1 * mach * mach
    else:
        cf /= (1.0 + 0.15 * mach * mach) ** 0.58
    return cf


def friction_drag(
    geom: VehicleGeometry, reynolds: float, mach: float
) -> float:
    """Total skin-friction drag coefficient on the reference area."""
    cf = skin_friction_coefficient(
        reynolds, geom.surface_roughness_m, geom.total_length_m, mach
    )

    # Body form factor -- accounts for the pressure gradient over a slender
    # body of revolution of fineness ratio f.
    f = max(geom.total_length_m / geom.body.diameter_m, 1e-6)
    body_form = 1.0 + 60.0 / f ** 3 + 0.0025 * f
    body_wetted = (
        geom.nose.wetted_area_m2
        + geom.transition.wetted_area_m2
        + geom.body.wetted_area_m2
    )

    # Fin form factor from thickness ratio.
    fin_form = 1.0 + 2.0 * geom.fins.thickness_ratio

    return cf * (
        body_form * body_wetted + fin_form * geom.fins.wetted_area_m2
    ) / geom.reference_area_m2


def nose_wave_drag(fineness: float, mach: float) -> float:
    """Wave drag of a Von Karman nose, on the nose base area.

    APPROXIMATE -- see the module-level calibration warning.

    Subsonic: zero (a Von Karman nose is a minimum-wave-drag shape and carries
    no wave drag below the critical Mach number).

    Transonic 0.9 < M < 1.1: blended in smoothly rather than stepped, so the
    integrator does not see a discontinuity.

    Supersonic: slender-body form ``C_Dw ~ k / f**2`` with the Mach dependence
    of linearised theory. The ``1/f**2`` scaling is the correct slender-body
    result for the Haack family (Ward 1949; Sears 1947); the leading constant
    is calibrated to typical measured ogive data rather than derived.
    """
    if fineness <= 0.0:
        raise ValueError(f"fineness ratio must be positive, got {fineness}")
    if mach <= 0.9:
        return 0.0

    supersonic = 6.0 / fineness ** 2
    if mach > 1.1:
        beta = math.sqrt(max(mach * mach - 1.0, 1e-9))
        return supersonic * (1.0 / max(beta, 0.5)) * 1.2

    # Transonic blend across 0.9 -> 1.1.
    peak = supersonic * 1.2 / 0.5
    return peak * (mach - 0.9) / 0.2


def transition_wave_drag(
    geom: VehicleGeometry, mach: float, reference_area_m2: float
) -> float:
    """Wave drag of the Haack flare, on the reference area.

    APPROXIMATE. Zero when no flare is present -- set the transition length to
    zero in config and this term vanishes, which is how the model prices the
    open question in register B7.
    """
    t = geom.transition
    if not t.present or mach <= 0.9:
        return 0.0

    area_ratio = t.area_change_m2 / reference_area_m2
    if area_ratio <= 0.0:
        return 0.0

    # Flare half-angle drives the shock strength.
    half_angle = math.atan2(
        (t.aft_diameter_m - t.fore_diameter_m) / 2.0, max(t.length_m, 1e-9)
    )
    beta = math.sqrt(max(mach * mach - 1.0, 0.25))
    return 2.0 * area_ratio * math.sin(half_angle) ** 2 / beta * 4.0


def fin_wave_drag(geom: VehicleGeometry, mach: float) -> float:
    """Fin thickness and leading-edge wave drag, on the reference area.

    APPROXIMATE.

    The double-wedge branch is Ackeret linearised theory,
    ``C_D = 4 (t/c)**2 / sqrt(M**2 - 1)``, which is a genuine analytic result.
    The rounded branch adds a leading-edge bluntness penalty, which is where the
    real uncertainty sits.

    A rounded leading edge at Mach 2+ carries a detached bow shock and costs
    materially more than a wedge. This function is what prices register B17 --
    the ORK specifies ``rounded``, and the team can compare.
    """
    if mach <= 0.9:
        return 0.0

    tc = geom.fins.thickness_ratio
    beta = math.sqrt(max(mach * mach - 1.0, 0.25))
    wedge = 4.0 * tc * tc / beta

    if geom.fins.cross_section == "rounded":
        # Blunt leading edge behaves like a 2D cylinder in the normal flow
        # component. Coefficient is Hoerner-scaled, not derived.
        bluntness = 0.5 * tc
        cd_panel = wedge + bluntness
    else:
        cd_panel = wedge

    return cd_panel * geom.fins.total_area_m2 / geom.reference_area_m2


def base_drag(mach: float, jet_blockage: float = 0.0) -> float:
    """Base drag on the reference area (Hoerner).

    Parameters
    ----------
    jet_blockage : fraction of the base area covered by the exhaust plume,
        0 to 1. While the motor burns the plume fills the base and base drag
        falls; after burnout it returns in full.
    """
    if mach < 1.0:
        cd = 0.12 + 0.13 * mach * mach
    else:
        cd = 0.25 / mach
    return cd * max(0.0, 1.0 - jet_blockage)


def interference_drag(geom: VehicleGeometry) -> float:
    """Fin-body junction interference, on the reference area."""
    return (
        0.02
        * geom.fins.count
        * geom.fins.root_chord_m
        * geom.fins.thickness_m
        / geom.reference_area_m2
    )


def buildup(
    geom: VehicleGeometry,
    mach: float,
    reynolds: float,
    jet_blockage: float = 0.0,
) -> DragBuildup:
    """Full component drag build-up at one flight condition."""
    if mach < 0.0:
        raise ValueError(f"Mach number must be non-negative, got {mach}")

    friction = friction_drag(geom, reynolds, mach)
    nose = nose_wave_drag(geom.nose.fineness, mach) * (
        geom.nose.base_area_m2 / geom.reference_area_m2
    )
    trans = transition_wave_drag(geom, mach, geom.reference_area_m2)
    fins = fin_wave_drag(geom, mach)
    base = base_drag(mach, jet_blockage)
    interf = interference_drag(geom)

    return DragBuildup(
        friction=friction,
        nose_wave=nose,
        transition_wave=trans,
        fin_wave=fins,
        base=base,
        interference=interf,
        total=friction + nose + trans + fins + base + interf,
        validated=False,
    )


def reynolds_number(
    velocity_ms: float, length_m: float, density: float, viscosity: float
) -> float:
    """Reynolds number on vehicle length."""
    if viscosity <= 0.0:
        raise ValueError("viscosity must be positive")
    return density * abs(velocity_ms) * length_m / viscosity
