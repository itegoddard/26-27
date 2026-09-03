"""Trajectory simulation: wires every module together and runs to landing.

Spec section 9.

Runs to landing, not to a fixed row count. The 25-26 model spanned 50 s of a
flight that lasts around 250 s, so its "apogee" was the end of the table.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

from goddard import dynamics, mass as mass_mod, recovery as rec_mod
from goddard.aero import drag as drag_mod
from goddard.aero import geometry as geom_mod
from goddard.aero import normal_force as nf_mod
from goddard.aero import roll as roll_mod
from goddard.env import atmosphere
from goddard.events import Event, EventLog, EventRecord, interpolate_crossing
from goddard.motor import chamber as chamber_mod
from goddard.motor import grain as grain_mod
from goddard.motor import injector as inj_mod
from goddard.motor import tank as tank_mod
from goddard.props import n2o
from goddard.props.cea import CEATable
from goddard.structures import heating as heat_mod


@dataclass(frozen=True)
class Vehicle:
    """Everything the simulation needs, assembled from config."""

    geometry: geom_mod.VehicleGeometry
    mass_model: mass_mod.MassModel
    injector_geometry: inj_mod.InjectorGeometry
    grain_geometry: grain_mod.GrainGeometry
    tank_volume_m3: float
    tank_fill_fraction: float
    tank_initial_temperature_K: float
    throat_area_m2: float
    expansion_ratio: float
    cea: CEATable
    recovery: rec_mod.RecoveryConfig
    latent_heat: Callable[[float], float]
    nose_tip: heat_mod.TipThermal | None = None
    field_elevation_m: float = 1216.0
    rail_length_m: float = 9.0
    eta_cf: float = 0.97

    # Combustion extinguishes when the tank runs out of LIQUID, expressed as a
    # fraction of the initial liquid charge.
    #
    # This is the primary flame-out criterion and it is grounded in the tank
    # state the model already computes, rather than in a tuned number. The
    # regression law returns a non-zero rate for any non-zero oxidiser flux, so
    # without this the grain keeps pyrolysing right through the vapour
    # blowdown, in a phase where chamber pressure has collapsed and there is
    # not enough enthalpy arriving to sustain a flame. On the v1 config that
    # phantom tail burn consumed an 18 % web margin and reported a false
    # burnthrough.
    #
    # 0.02 matches the working model's cutoff. The flux floor in props.fuel is
    # retained as a SECONDARY guard for cases this misses.
    min_liquid_fraction: float = 0.02

    # Set True to keep combusting into the vapour-blowdown phase.
    #
    # Default False truncates at liquid depletion, which matches the working
    # model and is the conservative choice. But it IS a known omission: gaseous
    # N2O is still an oxidiser, and HEROS flew roughly 15 s of liquid plus 10 s
    # of gaseous blowdown that delivered real impulse -- low thrust, but at
    # altitude where it converts efficiently and drag is thin.
    #
    # Enabling it restores the tail, with the props.fuel flux floor as the
    # guard against the runaway regression that used to eat the whole web.
    # Provided so the tail's contribution can be differenced rather than
    # argued about.
    combust_vapour_phase: bool = False


@dataclass(frozen=True)
class Calibration:
    """The three unmeasured constants for one run."""

    regression: float = 0.85
    injector_cd: float = 0.70
    eta_cstar: float = 0.88


@dataclass
class Sample:
    """One row of the trajectory."""

    t: float
    x: float
    z: float
    vx: float
    vz: float
    speed: float
    mach: float
    altitude_agl: float
    theta: float
    alpha: float
    roll_rate: float
    mass: float
    thrust: float
    drag: float
    cd: float
    dynamic_pressure: float
    acceleration_g: float
    chamber_pressure: float
    of_ratio: float
    web_fraction: float
    chug_margin: float
    static_margin: float
    tip_temperature: float


@dataclass
class FlightResult:
    """Complete simulation output."""

    samples: list[Sample] = field(default_factory=list)
    events: EventLog = field(default_factory=EventLog)
    warnings: list[str] = field(default_factory=list)
    terminated_reason: str = ""

    @property
    def apogee_agl_m(self) -> float:
        return max((s.altitude_agl for s in self.samples), default=0.0)

    @property
    def apogee_ft(self) -> float:
        return self.apogee_agl_m / 0.3048

    @property
    def max_mach(self) -> float:
        return max((s.mach for s in self.samples), default=0.0)

    @property
    def max_speed_ms(self) -> float:
        return max((s.speed for s in self.samples), default=0.0)

    @property
    def max_dynamic_pressure_Pa(self) -> float:
        return max((s.dynamic_pressure for s in self.samples), default=0.0)

    @property
    def max_acceleration_g(self) -> float:
        return max((abs(s.acceleration_g) for s in self.samples), default=0.0)

    @property
    def min_web_fraction(self) -> float:
        return min((s.web_fraction for s in self.samples), default=1.0)

    @property
    def min_chug_margin(self) -> float:
        burning = [s.chug_margin for s in self.samples if s.thrust > 0.0]
        return min(burning, default=math.inf)

    @property
    def min_static_margin(self) -> float:
        powered = [s.static_margin for s in self.samples if s.speed > 20.0]
        return min(powered, default=0.0)

    @property
    def peak_tip_temperature_K(self) -> float:
        return max((s.tip_temperature for s in self.samples), default=0.0)

    @property
    def rail_exit_velocity_ms(self) -> float:
        record = self.events.get(Event.RAIL_EXIT)
        return record.velocity_ms if record else 0.0

    def summary(self) -> str:
        lines = [
            f"apogee              {self.apogee_agl_m:9.1f} m AGL "
            f"({self.apogee_ft:,.0f} ft)",
            f"max Mach            {self.max_mach:9.2f}",
            f"max speed           {self.max_speed_ms:9.1f} m/s",
            f"max dynamic press.  {self.max_dynamic_pressure_Pa / 1000:9.1f} kPa",
            f"max acceleration    {self.max_acceleration_g:9.1f} g",
            f"rail exit velocity  {self.rail_exit_velocity_ms:9.1f} m/s",
            f"min static margin   {self.min_static_margin:9.2f} cal",
            f"min web remaining   {self.min_web_fraction * 100:9.1f} %",
            f"min chug margin     {self.min_chug_margin:9.2f}",
        ]
        if self.peak_tip_temperature_K > 0.0:
            lines.append(f"peak tip temp       {self.peak_tip_temperature_K:9.1f} K")
        lines.append(f"events              {self.events}")
        if self.terminated_reason:
            lines.append(f"terminated          {self.terminated_reason}")
        for w in self.warnings:
            lines.append(f"WARNING             {w}")
        return "\n".join(lines)


def run(
    vehicle: Vehicle,
    calibration: Calibration | None = None,
    dt: float = 0.01,
    max_time_s: float = 600.0,
    raise_on_burnthrough: bool = False,
) -> FlightResult:
    """Simulate one flight from rail to landing."""
    cal = calibration or Calibration()
    result = FlightResult()
    result.warnings.append(
        "supersonic wave-drag terms are UNCALIBRATED -- cross-check total C_D "
        "against RASAero II or CFD before trusting absolute apogee "
        "(see goddard/aero/drag.py)"
    )

    geom = vehicle.geometry
    ground_z = vehicle.field_elevation_m

    tank_state = tank_mod.initial_state(
        vehicle.tank_volume_m3,
        vehicle.tank_fill_fraction,
        vehicle.tank_initial_temperature_K,
    )
    grain_state = grain_mod.GrainState(
        port_radius_m=vehicle.grain_geometry.initial_port_radius_m
    )
    initial_fuel = vehicle.grain_geometry.initial_fuel_mass()

    state = dynamics.State(x=0.0, z=ground_z)
    t = 0.0
    tip_T = vehicle.tank_initial_temperature_K
    initial_liquid_kg = tank_state.liquid_mass_kg
    liquid_cutoff = vehicle.min_liquid_fraction * initial_liquid_kg
    burning = True
    stage = rec_mod.Stage.STOWED
    stage_start_t = 0.0
    deploy_speed = 0.0
    prev_vz = 0.0

    result.events.record(EventRecord(Event.LAUNCH, 0.0, 0.0, 0.0))

    while t < max_time_s:
        atm = atmosphere.state(state.z)
        v = state.speed
        mach = v / atm.a if atm.a > 0.0 else 0.0
        agl = state.z - ground_z
        on_rail = agl < vehicle.rail_length_m and v >= 0.0

        # ---------------------------------------------------------- motor
        thrust = 0.0
        chamber = None

        # Primary flame-out criterion: the tank has gone vapour-only.
        if (
            burning
            and not vehicle.combust_vapour_phase
            and tank_state.liquid_mass_kg <= liquid_cutoff
        ):
            burning = False
            result.events.record(EventRecord(Event.BURNOUT, t, agl, v, mach))
            result.warnings.append(
                f"flame out at t={t:.2f}s: liquid oxidiser exhausted "
                f"({vehicle.min_liquid_fraction:.0%} residual cutoff). "
                "Vapour-phase impulse is discarded -- set "
                "combust_vapour_phase=True to retain it."
            )

        if burning and tank_state.total_mass_kg > 1e-6:
            try:
                chamber = chamber_mod.solve(
                    tank_pressure=tank_mod.pressure(tank_state),
                    vapour_pressure=n2o.vapour_pressure(tank_state.temperature_K),
                    rho_liquid=n2o.liquid_density(tank_state.temperature_K),
                    ambient_pressure=atm.P,
                    injector_geom=vehicle.injector_geometry,
                    injector_cd=cal.injector_cd,
                    grain_geom=vehicle.grain_geometry,
                    grain_state=grain_state,
                    calibration=cal.regression,
                    eta_cstar=cal.eta_cstar,
                    throat_area=vehicle.throat_area_m2,
                    expansion_ratio=vehicle.expansion_ratio,
                    cea=vehicle.cea,
                    eta_cf=vehicle.eta_cf,
                )
                thrust = chamber.thrust_N
            except (chamber_mod.ChamberSolveFailed, ValueError) as exc:
                burning = False
                result.events.record(EventRecord(Event.BURNOUT, t, agl, v, mach))
                result.warnings.append(f"motor stopped at t={t:.2f}s: {exc}")

        # ----------------------------------------------------------- mass
        fuel_left = grain_mod.fuel_mass_remaining(
            vehicle.grain_geometry, grain_state
        )
        mass_state = vehicle.mass_model.at(tank_state.total_mass_kg, fuel_left)

        # ------------------------------------------------------------ aero
        re = drag_mod.reynolds_number(v, geom.total_length_m, atm.rho, atm.mu)
        blockage = 0.8 if thrust > 0.0 else 0.0
        cd_build = drag_mod.buildup(geom, mach, re, blockage)
        alpha = 0.0 if on_rail else state.angle_of_attack
        nf = nf_mod.evaluate(geom, mach, alpha)
        q_dyn = dynamics.dynamic_pressure(atm.rho, v)

        cd_total = cd_build.total
        drag_force = q_dyn * geom.reference_area_m2 * cd_total
        normal_force = -q_dyn * geom.reference_area_m2 * nf.cn

        # Recovery drag replaces body drag once a canopy is out.
        if stage is not rec_mod.Stage.STOWED:
            cds = rec_mod.drag_area(
                vehicle.recovery, stage, t - stage_start_t, deploy_speed
            )
            drag_force = q_dyn * cds
            normal_force = 0.0

        pitch_moment = normal_force * (nf.x_cp_m - mass_state.x_cg_m)

        roll = roll_mod.evaluate(geom, v, state.p, atm.rho, mach)
        roll_moment = 0.0 if on_rail else roll.moment_Nm

        forces = dynamics.Forces(
            thrust_N=thrust,
            drag_N=drag_force,
            normal_N=normal_force,
            pitch_moment=pitch_moment,
            roll_moment=roll_moment,
            mass_kg=mass_state.mass_kg,
            i_pitch=mass_state.i_pitch,
            i_roll=mass_state.i_roll,
        )

        accel = (thrust - drag_force) / mass_state.mass_kg - dynamics.GRAVITY

        # ---------------------------------------------------------- heating
        if vehicle.nose_tip is not None:
            flux = heat_mod.stagnation_heat_flux(
                atm.rho, v, vehicle.nose_tip.nose_radius_m
            )
            tip_T = heat_mod.step_temperature(
                vehicle.nose_tip, tip_T, flux, atm.T, dt
            )

        result.samples.append(
            Sample(
                t=t,
                x=state.x,
                z=state.z,
                vx=state.vx,
                vz=state.vz,
                speed=v,
                mach=mach,
                altitude_agl=agl,
                theta=state.theta,
                alpha=alpha,
                roll_rate=state.p,
                mass=mass_state.mass_kg,
                thrust=thrust,
                drag=drag_force,
                cd=cd_total,
                dynamic_pressure=q_dyn,
                acceleration_g=accel / dynamics.GRAVITY,
                chamber_pressure=chamber.chamber_pressure_Pa if chamber else 0.0,
                of_ratio=chamber.of_ratio if chamber else 0.0,
                web_fraction=grain_mod.web_fraction(
                    vehicle.grain_geometry, grain_state
                ),
                chug_margin=chamber.chug_margin if chamber else math.inf,
                static_margin=nf_mod.static_margin(
                    nf.x_cp_m, mass_state.x_cg_m, geom.reference_length_m
                ),
                tip_temperature=tip_T,
            )
        )

        # ----------------------------------------------------------- events
        if not result.events.has(Event.RAIL_EXIT) and agl >= vehicle.rail_length_m:
            result.events.record(EventRecord(Event.RAIL_EXIT, t, agl, v, mach))

        if prev_vz > 0.0 and state.vz <= 0.0 and not result.events.has(Event.APOGEE):
            t_apo = interpolate_crossing(t - dt, prev_vz, t, state.vz)
            result.events.record(EventRecord(Event.APOGEE, t_apo, agl, v, mach))
            stage = rec_mod.Stage.REEFED
            stage_start_t = t
            deploy_speed = max(v, 1.0)
            result.events.record(EventRecord(Event.CHUTE_DEPLOY, t, agl, v, mach))

        if (
            stage is rec_mod.Stage.REEFED
            and result.events.has(Event.APOGEE)
            and agl <= vehicle.recovery.disreef_altitude_m
        ):
            stage = rec_mod.Stage.FULL
            stage_start_t = t
            deploy_speed = max(v, 1.0)
            result.events.record(EventRecord(Event.DISREEF, t, agl, v, mach))

        if agl <= 0.0 and t > 1.0:
            result.events.record(EventRecord(Event.LANDING, t, agl, v, mach))
            result.terminated_reason = "landed"
            break

        # ------------------------------------------------------- integrate
        prev_vz = state.vz
        state = dynamics.rk4_step(state, forces, dt, on_rail)

        if chamber is not None and burning:
            try:
                grain_state = grain_mod.step(
                    vehicle.grain_geometry,
                    grain_state,
                    chamber.regression_rate_ms,
                    dt,
                    raise_on_burnthrough=raise_on_burnthrough,
                )
            except grain_mod.PortBurnthrough as exc:
                result.terminated_reason = f"port burnthrough: {exc}"
                break

            try:
                tank_state = tank_mod.step(
                    tank_state,
                    vehicle.tank_volume_m3,
                    chamber.m_dot_ox,
                    dt,
                    latent_heat=vehicle.latent_heat,
                )
            except (tank_mod.TankDepleted, ValueError):
                burning = False
                result.events.record(EventRecord(Event.BURNOUT, t, agl, v, mach))

        t += dt
    else:
        result.terminated_reason = f"reached max_time_s = {max_time_s}"

    # Max-Q is a post-pass: it is a maximum, not a crossing.
    if result.samples:
        peak = max(result.samples, key=lambda s: s.dynamic_pressure)
        result.events.record(
            EventRecord(Event.MAX_Q, peak.t, peak.altitude_agl, peak.speed, peak.mach)
        )

    if vehicle.cea.was_clamped:
        result.warnings.append(
            "CEA table was queried outside its tabulated envelope and clamped "
            "to the edge -- widen the O/F or pressure range"
        )

    return result
