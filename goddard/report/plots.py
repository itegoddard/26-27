"""Trajectory plots. Optional -- requires matplotlib.

Spec section 9. Generated output; regenerated on every run.
"""

from __future__ import annotations

import math
from pathlib import Path

from goddard.sim import FlightResult

_M_TO_FT = 1.0 / 0.3048


def available() -> bool:
    """True if matplotlib is importable."""
    try:
        import matplotlib  # noqa: F401
        return True
    except ImportError:
        return False


def write(result: FlightResult, directory: str | Path) -> list[Path]:
    """Write the standard plot set. Returns the paths written."""
    if not available():
        raise ImportError(
            "matplotlib is required for plots. Install with: "
            "pip install -e '.[report]'  (the Excel report works without it)"
        )

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    t = [s.t for s in result.samples]

    panels = [
        ("altitude", "Altitude (ft AGL)",
         [s.altitude_agl * _M_TO_FT for s in result.samples]),
        ("mach", "Mach", [s.mach for s in result.samples]),
        ("acceleration", "Acceleration (g)",
         [s.acceleration_g for s in result.samples]),
        ("dynamic_pressure", "Dynamic pressure (kPa)",
         [s.dynamic_pressure / 1000.0 for s in result.samples]),
        ("drag_coefficient", "C_D", [s.cd for s in result.samples]),
        ("static_margin", "Static margin (calibers)",
         [s.static_margin for s in result.samples]),
        ("roll_rate", "Roll rate (rad/s)",
         [s.roll_rate for s in result.samples]),
    ]

    for name, label, series in panels:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(t, series, linewidth=1.2)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.3)
        ax.set_title(f"Goddard 26-27 -- {label}")
        fig.tight_layout()
        path = directory / f"{name}.png"
        fig.savefig(path, dpi=130)
        plt.close(fig)
        written.append(path)

    # Motor panel: thrust and chamber pressure share a time axis.
    burning = [s for s in result.samples if s.thrust > 0.0]
    if burning:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot([s.t for s in burning], [s.thrust for s in burning],
                label="Thrust (N)", linewidth=1.2)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Thrust (N)")
        ax.grid(True, alpha=0.3)
        ax2 = ax.twinx()
        ax2.plot([s.t for s in burning],
                 [s.chamber_pressure / 1e6 for s in burning],
                 color="tab:orange", linestyle="--", label="P_c (MPa)")
        ax2.set_ylabel("Chamber pressure (MPa)")
        ax.set_title("Goddard 26-27 -- Motor")
        fig.tight_layout()
        path = directory / "motor.png"
        fig.savefig(path, dpi=130)
        plt.close(fig)
        written.append(path)

        # Chug margin against its criterion -- the risk grows toward the tail.
        fig, ax = plt.subplots(figsize=(8, 4.5))
        margins = [
            s.chug_margin for s in burning if math.isfinite(s.chug_margin)
        ]
        times = [s.t for s in burning if math.isfinite(s.chug_margin)]
        if margins:
            ax.plot(times, margins, linewidth=1.2)
            ax.axhline(1.0, color="red", linestyle=":",
                       label="stability criterion")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Chug margin (x criterion)")
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_title("Goddard 26-27 -- Injector chug margin")
            fig.tight_layout()
            path = directory / "chug_margin.png"
            fig.savefig(path, dpi=130)
            written.append(path)
        plt.close(fig)

    return written
