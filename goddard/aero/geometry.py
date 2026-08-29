"""Derived aerodynamic geometry.

Spec section 5. Pure geometry -- areas, wetted areas, aspect ratios -- computed
once from the config and handed to the coefficient modules.
"""

from __future__ import annotations

import functools
import math
from dataclasses import dataclass


@functools.lru_cache(maxsize=64)
def _haack_wetted_area(radius_m: float, length_m: float, panels: int = 2000) -> float:
    """Surface area of a Haack C=0 body of revolution, m^2.

    Cached: this runs once per unique nose geometry rather than once per
    integration step. The simulation queries it tens of thousands of times.
    """
    total = 0.0
    prev_x, prev_r = 0.0, 0.0
    for i in range(1, panels + 1):
        x = length_m * i / panels
        theta = math.acos(max(-1.0, min(1.0, 1.0 - 2.0 * x / length_m)))
        r = (radius_m / math.sqrt(math.pi)) * math.sqrt(
            max(0.0, theta - math.sin(2.0 * theta) / 2.0)
        )
        slant = math.hypot(x - prev_x, r - prev_r)
        total += math.pi * (r + prev_r) * slant
        prev_x, prev_r = x, r
    return total


@dataclass(frozen=True)
class NoseGeometry:
    """Von Karman (Haack C=0) nose."""

    length_m: float
    base_diameter_m: float
    tip_radius_m: float

    @property
    def fineness(self) -> float:
        return self.length_m / self.base_diameter_m

    @property
    def base_area_m2(self) -> float:
        return math.pi * (self.base_diameter_m / 2.0) ** 2

    @property
    def wetted_area_m2(self) -> float:
        """Surface area of the Haack C=0 body of revolution.

        Integrated numerically from the Haack radius distribution

            theta = arccos(1 - 2x/L)
            r(x)  = (R/sqrt(pi)) * sqrt(theta - sin(2 theta)/2)

        using the surface-of-revolution integral. 2000 panels puts the
        discretisation error well below any other uncertainty in the drag
        build-up. Result is cached per geometry.
        """
        return _haack_wetted_area(self.base_diameter_m / 2.0, self.length_m)


@dataclass(frozen=True)
class TransitionGeometry:
    """Haack flare. ``length_m == 0`` means no flare."""

    length_m: float
    fore_diameter_m: float
    aft_diameter_m: float

    @property
    def present(self) -> bool:
        return self.length_m > 0.0 and self.aft_diameter_m != self.fore_diameter_m

    @property
    def area_change_m2(self) -> float:
        """Frontal area added by the flare, m^2. Positive for a flare."""
        return math.pi / 4.0 * (self.aft_diameter_m ** 2 - self.fore_diameter_m ** 2)

    @property
    def wetted_area_m2(self) -> float:
        """Frustum lateral area -- adequate for a short transition."""
        r1 = self.fore_diameter_m / 2.0
        r2 = self.aft_diameter_m / 2.0
        slant = math.hypot(self.length_m, r2 - r1)
        return math.pi * (r1 + r2) * slant


@dataclass(frozen=True)
class BodyGeometry:
    diameter_m: float
    length_m: float

    @property
    def reference_area_m2(self) -> float:
        """Maximum cross-section -- the reference area for every coefficient."""
        return math.pi * (self.diameter_m / 2.0) ** 2

    @property
    def wetted_area_m2(self) -> float:
        return math.pi * self.diameter_m * self.length_m


@dataclass(frozen=True)
class FinGeometry:
    """One fin panel, times ``count``."""

    count: int
    root_chord_m: float
    tip_chord_m: float
    span_m: float
    thickness_m: float
    sweep_angle_rad: float
    cant_angle_rad: float
    cross_section: str = "rounded"

    @property
    def panel_area_m2(self) -> float:
        return 0.5 * (self.root_chord_m + self.tip_chord_m) * self.span_m

    @property
    def total_area_m2(self) -> float:
        return self.count * self.panel_area_m2

    @property
    def aspect_ratio(self) -> float:
        return self.span_m ** 2 / self.panel_area_m2

    @property
    def taper_ratio(self) -> float:
        return self.tip_chord_m / self.root_chord_m

    @property
    def mean_chord_m(self) -> float:
        return self.panel_area_m2 / self.span_m

    @property
    def thickness_ratio(self) -> float:
        return self.thickness_m / self.mean_chord_m

    @property
    def wetted_area_m2(self) -> float:
        """Both faces of every panel."""
        return 2.0 * self.total_area_m2

    @property
    def mid_chord_sweep_rad(self) -> float:
        """Sweep of the mid-chord line, used by lift-curve-slope corrections."""
        dx = (
            self.span_m * math.tan(self.sweep_angle_rad)
            + self.tip_chord_m / 2.0
            - self.root_chord_m / 2.0
        )
        return math.atan2(dx, self.span_m)


@dataclass(frozen=True)
class VehicleGeometry:
    """Everything the aerodynamic modules need, derived once."""

    nose: NoseGeometry
    transition: TransitionGeometry
    body: BodyGeometry
    fins: FinGeometry
    surface_roughness_m: float

    @property
    def reference_area_m2(self) -> float:
        return self.body.reference_area_m2

    @property
    def reference_length_m(self) -> float:
        """Body diameter -- the caliber, used for static margin."""
        return self.body.diameter_m

    @property
    def total_length_m(self) -> float:
        return self.nose.length_m + self.transition.length_m + self.body.length_m

    @property
    def wetted_area_m2(self) -> float:
        return (
            self.nose.wetted_area_m2
            + self.transition.wetted_area_m2
            + self.body.wetted_area_m2
            + self.fins.wetted_area_m2
        )
