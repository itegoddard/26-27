"""Unit conversions.

The model is SI internally, everywhere, without exception. These helpers exist
so that config files can be written in whatever units the source data came in
(drawings in inches, tank pressures in psi, altitudes in feet) while the solver
only ever sees SI.

Rule: convert at the config boundary, never inside a physics module.
"""

from __future__ import annotations

# ---------------------------------------------------------------- length

M_PER_INCH = 0.0254
M_PER_FOOT = 0.3048


def inches(x: float) -> float:
    """Inches to metres."""
    return x * M_PER_INCH


def feet(x: float) -> float:
    """Feet to metres."""
    return x * M_PER_FOOT


def to_inches(x: float) -> float:
    """Metres to inches."""
    return x / M_PER_INCH


def to_feet(x: float) -> float:
    """Metres to feet."""
    return x / M_PER_FOOT


# ------------------------------------------------------------------ mass

KG_PER_LBM = 0.45359237


def lbm(x: float) -> float:
    """Pounds-mass to kilograms."""
    return x * KG_PER_LBM


def to_lbm(x: float) -> float:
    """Kilograms to pounds-mass."""
    return x / KG_PER_LBM


# -------------------------------------------------------------- pressure

PA_PER_PSI = 6894.757293168361
PA_PER_BAR = 1.0e5


def psi(x: float) -> float:
    """Pounds per square inch to pascals."""
    return x * PA_PER_PSI


def to_psi(x: float) -> float:
    """Pascals to pounds per square inch."""
    return x / PA_PER_PSI


def bar(x: float) -> float:
    """Bar to pascals."""
    return x * PA_PER_BAR


# ----------------------------------------------------------- temperature

def celsius(x: float) -> float:
    """Degrees Celsius to kelvin."""
    return x + 273.15


def to_celsius(x: float) -> float:
    """Kelvin to degrees Celsius."""
    return x - 273.15


def fahrenheit(x: float) -> float:
    """Degrees Fahrenheit to kelvin."""
    return (x - 32.0) * 5.0 / 9.0 + 273.15


# ------------------------------------------------------------- angle

def degrees(x: float) -> float:
    """Degrees to radians."""
    from math import pi
    return x * pi / 180.0


def to_degrees(x: float) -> float:
    """Radians to degrees."""
    from math import pi
    return x * 180.0 / pi


# -------------------------------------------------------------- force

N_PER_LBF = 4.4482216152605


def lbf(x: float) -> float:
    """Pounds-force to newtons."""
    return x * N_PER_LBF


def to_lbf(x: float) -> float:
    """Newtons to pounds-force."""
    return x / N_PER_LBF
