"""Band mode: sweep the three unmeasured constants and report an envelope.

Spec section 6.2.

No static fire and no cold flow are planned, so ``regression_calibration``,
``injector_Cd`` and ``eta_cstar`` are all unmeasured. This module runs the
forward model over a full-factorial grid of the three and reports an envelope
per metric.

Why not one conservative point estimate
---------------------------------------
Oxidiser flow is set by the tank and injector, NOT by the grain. So a lower
regression rate produces less fuel and therefore a HIGHER O/F. Since c* peaks
near O/F 7-8, "conservative regression" does not reliably mean "conservative
apogee" -- the sign flips depending on which side of the peak the design sits.

The two directions also threaten different things:

    regression BELOW nominal  ->  apogee shortfall, lean O/F, chug margin
    regression ABOVE nominal  ->  port burnthrough

A single scalar biased for apogee leaves burnthrough unexamined. That is why
"conservative" is defined per metric here, and why this module exists.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

from goddard.sim import Calibration, FlightResult, Vehicle, run


@dataclass(frozen=True)
class BandRanges:
    """Sweep ranges for the three unmeasured constants."""

    regression: tuple[float, float] = (0.75, 1.00)
    injector_cd: tuple[float, float] = (0.61, 0.82)
    eta_cstar: tuple[float, float] = (0.82, 0.93)

    def levels(self, n: int) -> tuple[list[float], list[float], list[float]]:
        """``n`` evenly spaced levels across each range."""
        if n < 2:
            raise ValueError("need at least 2 levels per constant")

        def spread(lo: float, hi: float) -> list[float]:
            return [lo + (hi - lo) * i / (n - 1) for i in range(n)]

        return (
            spread(*self.regression),
            spread(*self.injector_cd),
            spread(*self.eta_cstar),
        )


@dataclass
class Corner:
    """One grid point and its result."""

    calibration: Calibration
    result: FlightResult | None
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.result is not None

    def label(self) -> str:
        c = self.calibration
        return (
            f"reg={c.regression:.3f} cd={c.injector_cd:.3f} "
            f"eta={c.eta_cstar:.3f}"
        )


@dataclass
class Envelope:
    """Worst-case value of one metric and the corner that produced it."""

    metric: str
    worst: float
    driving_corner: str
    best: float
    conservative_direction: str


@dataclass
class BandResult:
    """Full sweep output."""

    corners: list[Corner] = field(default_factory=list)
    envelopes: list[Envelope] = field(default_factory=list)

    @property
    def succeeded(self) -> list[Corner]:
        return [c for c in self.corners if c.ok]

    @property
    def failed(self) -> list[Corner]:
        return [c for c in self.corners if not c.ok]

    def envelope(self, metric: str) -> Envelope | None:
        for e in self.envelopes:
            if e.metric == metric:
                return e
        return None

    def summary(self) -> str:
        lines = [
            f"Band sweep: {len(self.succeeded)}/{len(self.corners)} corners "
            "completed",
            "",
        ]
        if self.failed:
            lines.append(f"{len(self.failed)} corner(s) failed:")
            for c in self.failed:
                lines.append(f"  {c.label()}  {c.error}")
            lines.append("")

        lines.append(
            f"{'metric':24s} {'worst':>12s} {'best':>12s}  driving corner"
        )
        for e in self.envelopes:
            lines.append(
                f"{e.metric:24s} {e.worst:12.2f} {e.best:12.2f}  "
                f"{e.driving_corner}"
            )
        return "\n".join(lines)


# Metric name -> (accessor, "min" if low values are the bad case else "max")
_METRICS = {
    "apogee_ft": (lambda r: r.apogee_ft, "min"),
    "max_mach": (lambda r: r.max_mach, "max"),
    "max_dynamic_pressure_kPa": (
        lambda r: r.max_dynamic_pressure_Pa / 1000.0,
        "max",
    ),
    "max_acceleration_g": (lambda r: r.max_acceleration_g, "max"),
    "min_web_fraction": (lambda r: r.min_web_fraction, "min"),
    "min_chug_margin": (lambda r: r.min_chug_margin, "min"),
    "min_static_margin_cal": (lambda r: r.min_static_margin, "min"),
    "rail_exit_velocity_ms": (lambda r: r.rail_exit_velocity_ms, "min"),
}


def run_band(
    vehicle: Vehicle,
    ranges: BandRanges | None = None,
    levels: int = 3,
    dt: float = 0.01,
    max_time_s: float = 600.0,
) -> BandResult:
    """Run the full-factorial sweep and build the envelopes.

    A corner that burns through or fails to solve is recorded as a *result*,
    not an abort -- that outcome is exactly what the sweep exists to surface.
    """
    ranges = ranges or BandRanges()
    reg_levels, cd_levels, eta_levels = ranges.levels(levels)

    out = BandResult()
    for reg, cd, eta in itertools.product(reg_levels, cd_levels, eta_levels):
        cal = Calibration(regression=reg, injector_cd=cd, eta_cstar=eta)
        try:
            result = run(
                vehicle,
                cal,
                dt=dt,
                max_time_s=max_time_s,
                raise_on_burnthrough=False,
            )
            out.corners.append(Corner(cal, result))
        except Exception as exc:  # noqa: BLE001 -- a failed corner is data
            out.corners.append(
                Corner(cal, None, error=f"{type(exc).__name__}: {exc}")
            )

    good = out.succeeded
    if not good:
        return out

    for name, (accessor, direction) in _METRICS.items():
        values = []
        for corner in good:
            try:
                value = accessor(corner.result)
            except Exception:  # noqa: BLE001
                continue
            if value is None or (isinstance(value, float) and math.isnan(value)):
                continue
            values.append((value, corner))
        if not values:
            continue

        if direction == "min":
            worst_value, worst_corner = min(values, key=lambda vc: vc[0])
            best_value = max(v for v, _ in values)
            note = "low is the bad case"
        else:
            worst_value, worst_corner = max(values, key=lambda vc: vc[0])
            best_value = min(v for v, _ in values)
            note = "high is the bad case"

        out.envelopes.append(
            Envelope(
                metric=name,
                worst=worst_value,
                driving_corner=worst_corner.label(),
                best=best_value,
                conservative_direction=note,
            )
        )

    return out
