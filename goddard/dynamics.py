"""Four-degree-of-freedom equations of motion.

Spec section 9.

State: ``[x, z, vx, vz, theta, q, phi, p]``

    x, z        downrange and altitude, m (z is MSL)
    vx, vz      inertial velocity components, m/s
    theta       body pitch angle from vertical, rad
    q           pitch rate, rad/s
    phi         roll angle, rad
    p           roll rate, rad/s

Sign conventions
----------------
``theta`` is measured from vertical, positive nose-over toward +x. The flight
path angle ``gamma = atan2(vx, vz)`` uses the same convention, so the angle of
attack is simply ``alpha = theta - gamma``. Keeping both in one convention
avoids the sign errors that plague planar rocket models.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

GRAVITY = 9.80665


@dataclass(frozen=True)
class State:
    """Vehicle kinematic state."""

    x: float = 0.0
    z: float = 0.0
    vx: float = 0.0
    vz: float = 0.0
    theta: float = 0.0
    q: float = 0.0
    phi: float = 0.0
    p: float = 0.0

    def as_tuple(self) -> tuple[float, ...]:
        return (self.x, self.z, self.vx, self.vz, self.theta, self.q, self.phi, self.p)

    @staticmethod
    def from_tuple(t: tuple[float, ...]) -> "State":
        return State(*t)

    @property
    def speed(self) -> float:
        return math.hypot(self.vx, self.vz)

    @property
    def flight_path_angle(self) -> float:
        """Angle of the velocity vector from vertical, rad."""
        if self.speed < 1e-9:
            return self.theta
        return math.atan2(self.vx, self.vz)

    @property
    def angle_of_attack(self) -> float:
        """Body axis minus flight path, rad."""
        return self.theta - self.flight_path_angle


@dataclass(frozen=True)
class Forces:
    """Resolved forces and moments at one instant.

    Attributes
    ----------
    thrust_N     : along the body axis
    drag_N       : opposing the velocity vector, positive magnitude
    normal_N     : perpendicular to the body axis, signed
    pitch_moment : about the CG, N m
    roll_moment  : about the roll axis, N m
    mass_kg      : current total mass
    i_pitch      : pitch inertia about the CG
    i_roll       : roll inertia
    """

    thrust_N: float
    drag_N: float
    normal_N: float
    pitch_moment: float
    roll_moment: float
    mass_kg: float
    i_pitch: float
    i_roll: float


def derivatives(state: State, forces: Forces, on_rail: bool) -> tuple[float, ...]:
    """Time derivative of the state vector.

    While ``on_rail`` the vehicle is constrained: no rotation, and only the
    velocity-aligned forces act. That models the rail carrying the normal load,
    which is why rail exit velocity matters for stability.
    """
    if forces.mass_kg <= 0.0:
        raise ValueError("mass must be positive")

    sin_t, cos_t = math.sin(state.theta), math.cos(state.theta)

    # Thrust acts along the body axis.
    fx = forces.thrust_N * sin_t
    fz = forces.thrust_N * cos_t

    # Drag opposes the velocity vector.
    v = state.speed
    if v > 1e-9:
        fx -= forces.drag_N * state.vx / v
        fz -= forces.drag_N * state.vz / v

    if not on_rail:
        # Normal force is perpendicular to the body axis.
        fx += forces.normal_N * cos_t
        fz -= forces.normal_N * sin_t

    fz -= forces.mass_kg * GRAVITY

    ax = fx / forces.mass_kg
    az = fz / forces.mass_kg

    if on_rail:
        return (state.vx, state.vz, ax, az, 0.0, 0.0, state.p, 0.0)

    q_dot = forces.pitch_moment / forces.i_pitch if forces.i_pitch > 0.0 else 0.0
    p_dot = forces.roll_moment / forces.i_roll if forces.i_roll > 0.0 else 0.0

    return (state.vx, state.vz, ax, az, state.q, q_dot, state.p, p_dot)


def rk4_step(
    state: State,
    forces: Forces,
    dt: float,
    on_rail: bool,
) -> State:
    """One classical RK4 step.

    Forces are held frozen across the step. That is the standard quasi-steady
    treatment for a vehicle whose aerodynamic and propulsive state changes
    slowly relative to ``dt`` -- at dt = 0.01 s and a ~6 s burn the error is far
    below the uncertainty in the calibration constants. It also keeps the motor
    subsystem, whose tank and grain models are inherently discrete, consistent
    with the trajectory integration.
    """
    if dt <= 0.0:
        raise ValueError("time step must be positive")

    y0 = state.as_tuple()

    def f(y: tuple[float, ...]) -> tuple[float, ...]:
        return derivatives(State.from_tuple(y), forces, on_rail)

    k1 = f(y0)
    y1 = tuple(a + 0.5 * dt * b for a, b in zip(y0, k1))
    k2 = f(y1)
    y2 = tuple(a + 0.5 * dt * b for a, b in zip(y0, k2))
    k3 = f(y2)
    y3 = tuple(a + dt * b for a, b in zip(y0, k3))
    k4 = f(y3)

    y_new = tuple(
        a + dt / 6.0 * (b + 2.0 * c + 2.0 * d + e)
        for a, b, c, d, e in zip(y0, k1, k2, k3, k4)
    )
    return State.from_tuple(y_new)


def dynamic_pressure(density: float, velocity_ms: float) -> float:
    """``q = 0.5 rho V^2``, Pa."""
    return 0.5 * density * velocity_ms * velocity_ms
