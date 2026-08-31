"""Flight event detection by bisection on sign change.

Spec section 9.

Events are located by root-finding on a scalar condition, not by noticing after
the fact that a step went past them. The 25-26 model detected apogee by taking
the maximum of a column, which meant its apogee was quantised to the time step
and -- because the table ran out before apogee -- was in fact the last row.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class Event(Enum):
    """Discrete flight events, in nominal order."""

    LAUNCH = "launch"
    RAIL_EXIT = "rail_exit"
    BURNOUT = "burnout"
    MAX_Q = "max_q"
    APOGEE = "apogee"
    CHUTE_DEPLOY = "chute_deploy"
    DISREEF = "disreef"
    LANDING = "landing"


@dataclass(frozen=True)
class EventRecord:
    """A detected event."""

    event: Event
    time_s: float
    altitude_m: float
    velocity_ms: float
    mach: float = 0.0


def bisect_crossing(
    condition: Callable[[float], float],
    t_lo: float,
    t_hi: float,
    tolerance_s: float = 1e-6,
    max_iterations: int = 100,
) -> float:
    """Time at which ``condition`` crosses zero between ``t_lo`` and ``t_hi``.

    ``condition`` must have opposite signs at the two ends. Returns the crossing
    time to within ``tolerance_s``.
    """
    f_lo = condition(t_lo)
    f_hi = condition(t_hi)
    if f_lo == 0.0:
        return t_lo
    if f_hi == 0.0:
        return t_hi
    if f_lo * f_hi > 0.0:
        raise ValueError(
            "condition does not change sign across the interval; there is no "
            "crossing to bisect"
        )

    for _ in range(max_iterations):
        if t_hi - t_lo < tolerance_s:
            break
        mid = 0.5 * (t_lo + t_hi)
        f_mid = condition(mid)
        if f_mid == 0.0:
            return mid
        if f_lo * f_mid < 0.0:
            t_hi = mid
            f_hi = f_mid
        else:
            t_lo = mid
            f_lo = f_mid
    return 0.5 * (t_lo + t_hi)


def interpolate_crossing(
    t0: float, v0: float, t1: float, v1: float
) -> float:
    """Linear interpolation to a zero crossing between two samples.

    Used where the underlying quantity is only known at step boundaries -- the
    step is small enough that linear interpolation is well inside the
    integration error.
    """
    if v1 == v0:
        return t1
    return t0 + (t1 - t0) * (-v0) / (v1 - v0)


class EventLog:
    """Ordered record of detected events, one entry per event type."""

    def __init__(self) -> None:
        self._records: dict[Event, EventRecord] = {}

    def record(self, record: EventRecord) -> None:
        """Record an event, keeping the first occurrence of each type."""
        self._records.setdefault(record.event, record)

    def has(self, event: Event) -> bool:
        return event in self._records

    def get(self, event: Event) -> EventRecord | None:
        return self._records.get(event)

    def time_of(self, event: Event) -> float | None:
        record = self._records.get(event)
        return record.time_s if record else None

    def all(self) -> list[EventRecord]:
        """Every recorded event, in chronological order."""
        return sorted(self._records.values(), key=lambda r: r.time_s)

    def __len__(self) -> int:
        return len(self._records)

    def __repr__(self) -> str:
        parts = [f"{r.event.value}@{r.time_s:.2f}s" for r in self.all()]
        return f"EventLog({', '.join(parts)})"
