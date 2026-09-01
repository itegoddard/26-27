"""Combustion thermochemistry lookup: c*, gamma and chamber temperature.

Spec section 4.4. Register item G11.

This module does NOT ship data. The 89 % paraffin / 10 % SEBS-MA / 1 % carbon
black blend burning N2O has no published c* table, and inventing one would
produce a model that runs, returns numbers, and is wrong -- exactly the failure
this rewrite exists to prevent. ``load`` raises ``PlaceholderData`` until a real
table is supplied.

Generating the table
--------------------
Run NASA CEA (RP-1311) for the blend across the operating envelope and write a
CSV with a header row and these columns:

    of_ratio,pressure_Pa,c_star_ms,gamma,temperature_K

Cover O/F from about 2 to 14 and chamber pressure from 1 to 5 MPa. Grid spacing
of 0.5 in O/F and 0.5 MPa is ample -- the interpolation error is far below the
uncertainty in ``eta_cstar``.

Then::

    from goddard.props import cea
    table = cea.load("data/cea_paraffin_n2o.csv")
    table.c_star(of_ratio=7.0, pressure_Pa=3.0e6)
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from goddard.config.schema import PlaceholderData


@dataclass(frozen=True)
class CEAPoint:
    of_ratio: float
    pressure_Pa: float
    c_star_ms: float
    gamma: float
    temperature_K: float


class CEATable:
    """Bilinear interpolation over a scattered CEA grid.

    Queries outside the tabulated envelope are clamped to the nearest edge
    rather than extrapolated, and ``was_clamped`` records whether any query in
    this table's lifetime hit an edge -- so a run that silently pinned itself to
    the table boundary is visible in the report rather than invisible.
    """

    def __init__(self, points: list[CEAPoint], source: str = "<memory>") -> None:
        if not points:
            raise ValueError("CEA table must contain at least one point")
        self.points = points
        self.source = source
        self.was_clamped = False

        self._of = sorted({p.of_ratio for p in points})
        self._p = sorted({p.pressure_Pa for p in points})
        self._by_key = {(p.of_ratio, p.pressure_Pa): p for p in points}

    @property
    def of_range(self) -> tuple[float, float]:
        return self._of[0], self._of[-1]

    @property
    def pressure_range(self) -> tuple[float, float]:
        return self._p[0], self._p[-1]

    def _bracket(self, values: list[float], x: float) -> tuple[float, float, float]:
        """Return ``(lo, hi, weight)`` bracketing ``x``, clamping at the edges."""
        if x <= values[0]:
            if x < values[0]:
                self.was_clamped = True
            return values[0], values[0], 0.0
        if x >= values[-1]:
            if x > values[-1]:
                self.was_clamped = True
            return values[-1], values[-1], 0.0
        for lo, hi in zip(values, values[1:]):
            if lo <= x <= hi:
                return lo, hi, (x - lo) / (hi - lo) if hi > lo else 0.0
        return values[-1], values[-1], 0.0

    def _interpolate(self, of_ratio: float, pressure_Pa: float, field: str) -> float:
        o0, o1, wo = self._bracket(self._of, of_ratio)
        p0, p1, wp = self._bracket(self._p, pressure_Pa)

        def at(o: float, p: float) -> float:
            point = self._by_key.get((o, p))
            if point is None:
                # Sparse grid: fall back to the nearest tabulated point.
                point = min(
                    self.points,
                    key=lambda q: (q.of_ratio - o) ** 2
                    + ((q.pressure_Pa - p) / 1e6) ** 2,
                )
            return getattr(point, field)

        bottom = at(o0, p0) * (1.0 - wo) + at(o1, p0) * wo
        top = at(o0, p1) * (1.0 - wo) + at(o1, p1) * wo
        return bottom * (1.0 - wp) + top * wp

    def c_star(self, of_ratio: float, pressure_Pa: float) -> float:
        """Characteristic velocity, m/s."""
        return self._interpolate(of_ratio, pressure_Pa, "c_star_ms")

    def gamma(self, of_ratio: float, pressure_Pa: float) -> float:
        """Ratio of specific heats of the combustion products."""
        return self._interpolate(of_ratio, pressure_Pa, "gamma")

    def temperature(self, of_ratio: float, pressure_Pa: float) -> float:
        """Chamber temperature, K."""
        return self._interpolate(of_ratio, pressure_Pa, "temperature_K")

    def peak_of_ratio(self, pressure_Pa: float) -> float:
        """O/F giving maximum c* at a given pressure.

        Useful context for spec section 6.1: which side of this peak the design
        sits determines whether a low regression rate helps or hurts.
        """
        return max(self._of, key=lambda o: self.c_star(o, pressure_Pa))


def load(path: str | Path) -> CEATable:
    """Load a CEA table from CSV.

    Raises
    ------
    PlaceholderData
        If the file does not exist. The message explains how to generate it --
        the model refuses to guess thermochemistry.
    """
    p = Path(path)
    if not p.exists():
        raise PlaceholderData(
            f"No CEA table at {p}. This is register item G11, the one "
            "PLACEHOLDER in the model.\n\n"
            "The 89/10/1 paraffin blend with N2O has no published c* data, and "
            "the model will not invent it. Generate a table with NASA CEA "
            "(RP-1311) and save CSV columns:\n"
            "    of_ratio,pressure_Pa,c_star_ms,gamma,temperature_K\n"
            "covering O/F 2-14 and chamber pressure 1-5 MPa.\n\n"
            "See goddard/props/cea.py for details."
        )

    points: list[CEAPoint] = []
    with p.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            points.append(
                CEAPoint(
                    of_ratio=float(row["of_ratio"]),
                    pressure_Pa=float(row["pressure_Pa"]),
                    c_star_ms=float(row["c_star_ms"]),
                    gamma=float(row["gamma"]),
                    temperature_K=float(row["temperature_K"]),
                )
            )
    if not points:
        raise PlaceholderData(f"CEA table at {p} is empty.")
    return CEATable(points, source=str(p))


def load_of_sweep(path: str | Path, pressure_Pa: float) -> CEATable:
    """Load a single-chamber-pressure CEA export (an O/F sweep).

    This reads the column layout NASA CEA actually emits from an O/F sweep run
    at one chamber pressure:

        O/F, c*_m/s, Tc_K, ..., gamma_chamber, ...

    rather than the (O/F, pressure) grid ``load`` expects. Extra columns are
    ignored.

    Parameters
    ----------
    path        : CSV from a CEA O/F sweep
    pressure_Pa : the chamber pressure the sweep was run at. It is NOT in the
                  file, so it must be supplied and must be correct.

    Single-pressure caveat
    ----------------------
    The resulting table is constant in pressure, so ``c_star(of, P)`` returns
    the same value at every ``P``. That is acceptable here because c* is very
    nearly flat in chamber pressure for this propellant -- 1592 m/s at 20 bar
    against 1602 m/s at 50 bar, a 0.6 % span across the whole usable range,
    while O/F moves it by tens of percent.

    It is still an approximation, and it is the reason this is a separate
    function rather than a silent branch inside ``load``: a caller choosing
    this has to say so. If pressure dependence ever matters, run CEA at several
    pressures and use ``load`` instead.
    """
    p = Path(path)
    if not p.exists():
        raise PlaceholderData(
            f"No CEA O/F sweep at {p}. See load() for how to generate one."
        )
    if pressure_Pa <= 0.0:
        raise ValueError(f"chamber pressure must be positive, got {pressure_Pa}")

    points: list[CEAPoint] = []
    with p.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            points.append(
                CEAPoint(
                    of_ratio=float(row["O/F"]),
                    pressure_Pa=pressure_Pa,
                    c_star_ms=float(row["c*_m/s"]),
                    gamma=float(row["gamma_chamber"]),
                    temperature_K=float(row["Tc_K"]),
                )
            )
    if not points:
        raise PlaceholderData(f"CEA O/F sweep at {p} is empty.")
    return CEATable(points, source=f"{p} (single pressure {pressure_Pa/1e5:.0f} bar)")
