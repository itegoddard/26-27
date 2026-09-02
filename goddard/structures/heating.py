"""Stagnation-point heating of the aluminium nose tip.

Spec section 7.2.

The aluminium tip exists because of this load, so the model should produce the
number rather than assume the answer.

Method
------
Stagnation heat flux from the Sutton-Graves correlation

    q = k * sqrt(rho / R_n) * V**3        k = 1.7415e-4  (SI)

which is the standard engineering reduction of Fay & Riddell's dissociated-air
solution. Full Fay-Riddell needs boundary-layer edge properties and a Lewis
number; Sutton-Graves collapses those into one constant and is accurate to
roughly 10 % over the relevant range -- well inside the other uncertainties
here.

Tip temperature follows from a lumped-capacitance balance with re-radiation:

    m c dT/dt = q A - eps sigma (T**4 - T_inf**4) A

Lumped capacitance assumes the tip is thermally thin (small Biot number), which
holds for a small aluminium tip precisely because aluminium conducts well. It
gives the BULK temperature and therefore **under-predicts the peak surface
temperature**; treat the margin accordingly.

References
----------
Fay, J. A. and Riddell, F. R., J. Aerospace Sciences 25(2), 1958,
doi:10.2514/8.7517. See ``docs/references.bib``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

SUTTON_GRAVES_K = 1.7415e-4  # SI
STEFAN_BOLTZMANN = 5.670374419e-8


@dataclass(frozen=True)
class TipThermal:
    """Aluminium nose tip thermal properties and geometry.

    Attributes
    ----------
    nose_radius_m : tip radius of curvature, m
    mass_kg       : mass of the metal cap, m
    area_m2       : **effective area over which the STAGNATION-POINT flux
        acts** -- roughly the hemispherical tip, ``2*pi*R_n**2``.

        This is NOT the wetted area of the cap, and the distinction is not
        pedantic. Sutton-Graves returns the flux at the stagnation point, which
        is the maximum; it falls off steeply within a few nose radii. Passing
        the wetted area of a 50 mm cap here instead of the tip hemisphere
        over-stated the heated area by 30x and produced a peak tip temperature
        of 1156 K against a true figure nearer 400 K. ``__post_init__``
        rejects that mistake now.
    """

    nose_radius_m: float
    mass_kg: float
    area_m2: float
    specific_heat: float = 900.0        # J/(kg K), typical aluminium
    emissivity: float = 0.15            # bare aluminium; rises when oxidised
    service_limit_K: float = 473.0      # 6061-T6 over-ageing limit, 200 C

    def __post_init__(self) -> None:
        if self.nose_radius_m <= 0.0:
            raise ValueError("nose radius must be positive")
        if self.mass_kg <= 0.0 or self.area_m2 <= 0.0:
            raise ValueError("tip mass and area must be positive")
        if not 0.0 <= self.emissivity <= 1.0:
            raise ValueError("emissivity must be between 0 and 1")

        # Guard against the wetted-area mistake described above. The stagnation
        # region cannot be much larger than the tip hemisphere; anything beyond
        # a few times that is a units or definition error, not a design.
        hemisphere = 2.0 * math.pi * self.nose_radius_m ** 2
        if self.area_m2 > 5.0 * hemisphere:
            raise ValueError(
                f"area_m2 = {self.area_m2 * 1e4:.2f} cm^2 is more than 5x the "
                f"tip hemisphere {hemisphere * 1e4:.2f} cm^2. This field is the "
                "effective STAGNATION-REGION area, not the wetted area of the "
                "cap -- Sutton-Graves gives the peak flux at the tip, and "
                "applying it over the whole cap over-predicts heating badly. "
                f"Use about {hemisphere * 1e4:.2f} cm^2."
            )


def stagnation_heat_flux(
    density: float, velocity_ms: float, nose_radius_m: float
) -> float:
    """Stagnation-point convective heat flux, W/m^2 (Sutton-Graves)."""
    if nose_radius_m <= 0.0:
        raise ValueError("nose radius must be positive")
    if density < 0.0:
        raise ValueError("density must be non-negative")
    if velocity_ms <= 0.0:
        return 0.0
    return SUTTON_GRAVES_K * (density / nose_radius_m) ** 0.5 * velocity_ms ** 3


def step_temperature(
    tip: TipThermal,
    temperature_K: float,
    heat_flux: float,
    ambient_K: float,
    dt: float,
) -> float:
    """Advance the tip bulk temperature one step, W/m^2 in, radiation out."""
    if dt <= 0.0:
        raise ValueError("time step must be positive")

    absorbed = heat_flux * tip.area_m2
    radiated = (
        tip.emissivity
        * STEFAN_BOLTZMANN
        * (temperature_K ** 4 - ambient_K ** 4)
        * tip.area_m2
    )
    dT = (absorbed - radiated) * dt / (tip.mass_kg * tip.specific_heat)
    return temperature_K + dT


def margin(tip: TipThermal, peak_temperature_K: float) -> float:
    """Service-limit margin. Below 1.0 the tip exceeds its allowable."""
    if peak_temperature_K <= 0.0:
        raise ValueError("temperature must be positive")
    return tip.service_limit_K / peak_temperature_K
