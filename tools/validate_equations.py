"""Independently validate every equation stated in docs/equations.tex.

This does NOT simply re-run the model and check it agrees with itself. Each
check re-derives the result a *different* way -- analytically, by numerical
quadrature, by round-tripping an inverse, or against a published value -- and
compares that against what the code produces.

    python tools/validate_equations.py

Exit code 0 if every check passes, 1 otherwise.
"""

from __future__ import annotations

import math
import sys

# --------------------------------------------------------------- test harness

RESULTS: list[tuple[str, str, bool, str]] = []


def check(section: str, name: str, got: float, want: float, tol: float,
          note: str = "") -> None:
    """Relative-tolerance comparison."""
    if want == 0.0:
        ok = abs(got) <= tol
        rel = abs(got)
    else:
        rel = abs(got - want) / abs(want)
        ok = rel <= tol
    detail = f"got {got:.6g}, want {want:.6g}, rel {rel:.2e}"
    if note:
        detail += f"  ({note})"
    RESULTS.append((section, name, ok, detail))


def check_true(section: str, name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((section, name, bool(ok), detail))


# =============================================================================
# 1. ATMOSPHERE -- against published US Std 1976 table values
# =============================================================================
def validate_atmosphere() -> None:
    from goddard.env import atmosphere as atm

    S = "Atmosphere"
    # Published layer-base values, tabulated on GEOPOTENTIAL altitude.
    for h, T, P in [(0, 288.150, 101325.0), (11000, 216.650, 22632.1),
                    (20000, 216.650, 5474.89), (32000, 228.650, 868.019),
                    (47000, 270.650, 110.906)]:
        s = atm.state(atm.geometric(float(h)))
        check(S, f"T at {h} m'", s.T, T, 1e-5)
        check(S, f"P at {h} m'", s.P, P, 1e-4)

    # Ideal gas closure, independent of the layer formulas.
    s = atm.state(5000.0)
    check(S, "rho = P/(RT) closure", s.rho, s.P / (atm.R_AIR * s.T), 1e-12)
    check(S, "a = sqrt(gamma R T)", s.a,
          math.sqrt(atm.GAMMA * atm.R_AIR * s.T), 1e-12)

    # Sutherland viscosity at sea level, accepted 1.7894e-5 Pa s.
    check(S, "Sutherland mu at SL", atm.state(0.0).mu, 1.7894e-5, 1e-4)

    # Hydrostatic consistency, checked by finite difference.
    #
    # The relation is exact in GEOPOTENTIAL altitude, dP/dh = -rho*g0. In
    # GEOMETRIC altitude gravity falls off, so the correct comparison is
    #     dP/dz = -rho * g(z),   g(z) = g0 (rE/(rE+z))^2
    # Using g0 here instead would disagree by 0.25 % at 8 km -- and that
    # disagreement is precisely the geopotential correction, so this check
    # independently confirms the h(z) conversion rather than just the layer
    # formulas.
    z = 8000.0
    dz = 1.0
    dP = (atm.state(z + dz).P - atm.state(z - dz).P) / (2 * dz)
    st = atm.state(z)
    g_local = atm.G0 * (atm.R_EARTH / (atm.R_EARTH + z)) ** 2
    check(S, "hydrostatic dP/dz = -rho g(z)", dP, -st.rho * g_local, 1e-6,
          "confirms geopotential conversion")


# =============================================================================
# 2. NITROUS OXIDE -- against independently known property values
# =============================================================================
def validate_n2o() -> None:
    from goddard.props import n2o

    S = "N2O"
    T = 293.15
    check(S, "P_sat at 20 C", n2o.vapour_pressure(T), 5.07e6, 0.02,
          "accepted 5.05-5.09 MPa")
    check(S, "rho_liquid at 20 C", n2o.liquid_density(T), 786.0, 0.01)
    check(S, "rho_vapour at 20 C", n2o.vapour_density(T), 158.0, 0.02)

    # Critical-point limit: both branches must approach rho_c.
    Tn = n2o.T_CRIT - 1e-6
    check(S, "rho_l -> rho_c", n2o.liquid_density(Tn), n2o.RHO_CRIT, 5e-3)
    check(S, "rho_v -> rho_c", n2o.vapour_density(Tn), n2o.RHO_CRIT, 5e-3)
    check(S, "P_sat -> P_c", n2o.vapour_pressure(n2o.T_CRIT - 1e-3),
          n2o.P_CRIT, 1e-3)

    # Latent heat must still refuse rather than guess.
    try:
        n2o.enthalpy_vaporisation(T)
        check_true(S, "latent heat raises (unverified data)", False,
                   "returned a value -- it must not")
    except NotImplementedError:
        check_true(S, "latent heat raises (unverified data)", True,
                   "NotImplementedError as designed")


# =============================================================================
# 3. FUEL BLEND AND REGRESSION LAW
# =============================================================================
def validate_fuel() -> None:
    from goddard.props import fuel

    S = "Fuel"
    hand = 0.89 * 924.0 + 0.10 * 910.0 + 0.01 * 1900.0
    check(S, "blend density (mass-weighted)", fuel.blend_density(), hand, 1e-12)
    check(S, "composition sums to 1", fuel.FRAC_PARAFFIN + fuel.FRAC_SEBS_MA
          + fuel.FRAC_CARBON_BLACK, 1.0, 1e-12)

    # Power law: doubling flux must scale rdot by 2**n.
    r1 = fuel.regression_rate(100.0, 1.0)
    r2 = fuel.regression_rate(200.0, 1.0)
    check(S, "rdot ~ G^0.5 exponent", r2 / r1, 2.0 ** fuel.REGRESSION_N, 1e-12)

    # Magnitude: paraffin is ~1.5 mm/s at G_ox = 100, 3-4x HTPB.
    check(S, "rdot magnitude at G=100", r1, 1.55e-3, 0.02,
          "literature ~1.5 mm/s")

    # THE SIGN RELATIONSHIP the whole band-mode argument rests on:
    # lower regression -> less fuel -> HIGHER O/F.
    kw = dict(m_dot_ox=2.0, r_port=0.03, grain_length=0.7)
    lo = fuel.evaluate(**kw, calibration=0.75)
    hi = fuel.evaluate(**kw, calibration=1.00)
    check_true(S, "lower k_cal raises O/F (spec 6.1)",
               lo.of_ratio > hi.of_ratio and lo.m_dot_fuel < hi.m_dot_fuel,
               f"O/F {lo.of_ratio:.2f} > {hi.of_ratio:.2f}")

    # Closure: O/F * m_dot_fuel must return m_dot_ox.
    check(S, "O/F closure", lo.of_ratio * lo.m_dot_fuel, 2.0, 1e-12)


# =============================================================================
# 4. NOZZLE -- inverse round-trip and an independent C_F derivation
# =============================================================================
def validate_nozzle() -> None:
    from goddard.motor import nozzle as nz

    S = "Nozzle"
    g = 1.2

    # Area-Mach inversion: strongest available check, solver vs analytic form.
    for m in (1.5, 2.0, 2.5, 3.0, 4.0):
        check(S, f"exit_mach inverts area_ratio at M={m}",
              nz.exit_mach(nz.area_ratio(m, g), g), m, 1e-6)

    # Throat pressure ratio against the closed form.
    check(S, "P/Pt at M=1", nz.pressure_ratio(1.0, g),
          (2.0 / (g + 1.0)) ** (g / (g - 1.0)), 1e-12)

    # C_F recomputed here from scratch, independent of the module's code path.
    pc, pa, eps = 3.0e6, 101325.0, 4.0
    me = nz.exit_mach(eps, g)
    pe_pc = (1.0 + 0.5 * (g - 1.0) * me * me) ** (-g / (g - 1.0))
    momentum = math.sqrt((2 * g * g / (g - 1.0))
                         * (2.0 / (g + 1.0)) ** ((g + 1.0) / (g - 1.0))
                         * (1.0 - pe_pc ** ((g - 1.0) / g)))
    hand_cf = momentum + (pe_pc * pc - pa) / pc * eps
    got_cf, _, _ = nz.thrust_coefficient(pc, pa, eps, g)
    check(S, "C_F vs hand-derived", got_cf, hand_cf, 1e-12)
    check_true(S, "C_F physically sized (1.2-2.0)", 1.2 < got_cf < 2.0,
               f"C_F = {got_cf:.4f}")

    # Altitude compensation: thrust must rise as ambient falls.
    sl, _, _ = nz.thrust_coefficient(pc, 101325.0, eps, g)
    alt, _, _ = nz.thrust_coefficient(pc, 12000.0, eps, g)
    vac, _, _ = nz.thrust_coefficient(pc, 0.0, eps, g)
    check_true(S, "thrust rises with altitude", sl < alt < vac,
               f"{sl:.3f} < {alt:.3f} < {vac:.3f}")

    # At perfect expansion the pressure term must vanish exactly.
    pe = pe_pc * pc
    cf_opt, _, _ = nz.thrust_coefficient(pc, pe, eps, g)
    check(S, "optimum expansion = momentum only", cf_opt, momentum, 1e-12)


# =============================================================================
# 5. VON KARMAN NOSE -- the x_cp = L/2 claim, verified by quadrature
# =============================================================================
def validate_nose() -> None:
    from goddard.aero import geometry as geom
    from goddard.aero import normal_force as nf

    S = "Nose"
    R, L = 0.0762, 0.70

    # equations.tex claims V = A_base * L / 2 EXACTLY for Haack C=0.
    # Verify by integrating pi r(x)^2 dx numerically.
    n = 200000
    vol = 0.0
    for i in range(n):
        x = L * (i + 0.5) / n
        phi = math.acos(max(-1.0, min(1.0, 1.0 - 2.0 * x / L)))
        r2 = (R * R / math.pi) * (phi - 0.5 * math.sin(2.0 * phi))
        vol += math.pi * r2 * (L / n)
    analytic = math.pi * R * R * L / 2.0
    check(S, "Haack C=0 volume = A_base*L/2", vol, analytic, 1e-6,
          "numerical quadrature vs claimed closed form")

    # Therefore x_cp = L - V/A_base = L/2. Check the module agrees.
    g = geom.VehicleGeometry(
        nose=geom.NoseGeometry(length_m=L, base_diameter_m=2 * R,
                               tip_radius_m=0.006),
        transition=geom.TransitionGeometry(0.0, 2 * R, 2 * R),
        body=geom.BodyGeometry(diameter_m=2 * R, length_m=3.2),
        fins=geom.FinGeometry(3, 0.30, 0.0984, 0.13, 0.005, 1.0821,
                              math.radians(1.0)),
        surface_roughness_m=20e-6,
    )
    cna, xcp = nf.nose_contribution(g)
    check(S, "nose x_cp = L/2", xcp, L / 2.0, 1e-12)
    check(S, "nose CN_alpha = 2 on base area", cna, 2.0, 1e-12,
          "nose base = body dia here")


# =============================================================================
# 6. ROLL -- closed form vs direct strip summation
# =============================================================================
def validate_roll() -> None:
    from goddard.aero import geometry as geom
    from goddard.aero import roll as roll_mod

    S = "Roll"
    R = 0.0762
    cr, ct, b = 0.30, 0.0984, 0.13
    g = geom.VehicleGeometry(
        nose=geom.NoseGeometry(0.70, 2 * R, 0.006),
        transition=geom.TransitionGeometry(0.0, 2 * R, 2 * R),
        body=geom.BodyGeometry(2 * R, 3.2),
        fins=geom.FinGeometry(3, cr, ct, b, 0.005, 1.0821, math.radians(1.0)),
        surface_roughness_m=20e-6,
    )

    # Independent high-resolution strip integration of S, M1, M2.
    n = 200000
    S0 = M1 = M2 = 0.0
    dy = b / n
    for i in range(n):
        f = (i + 0.5) / n
        chord = cr + (ct - cr) * f
        y = R + f * b
        dS = chord * dy
        S0 += dS
        M1 += y * dS
        M2 += y * y * dS
    gs, gm1, gm2 = roll_mod.panel_moments(g)
    check(S, "panel area S", gs, S0, 1e-5)
    check(S, "first moment M1", gm1, M1, 1e-5)
    check(S, "second moment M2", gm2, M2, 1e-5)

    # S must also equal the trapezoidal planform area analytically.
    check(S, "S = (cr+ct)b/2", gs, 0.5 * (cr + ct) * b, 1e-5)

    # Equilibrium roll rate: closed form p_eq = delta*V*M1/M2.
    V, delta = 300.0, math.radians(1.0)
    check(S, "p_eq = delta V M1/M2",
          roll_mod.equilibrium_roll_rate(g, V), delta * V * M1 / M2, 1e-5)

    # At p = p_eq the net rolling moment must vanish -- the defining property.
    p_eq = roll_mod.equilibrium_roll_rate(g, V)
    st = roll_mod.evaluate(g, V, p_eq, 0.5, 0.9)
    check(S, "moment = 0 at p_eq", st.moment_Nm, 0.0, 1e-6,
          "absolute tolerance")

    # Independence claims: p_eq must not depend on density or Mach.
    a = roll_mod.equilibrium_roll_rate(g, V, 0.3)
    bb = roll_mod.equilibrium_roll_rate(g, V, 2.5)
    check_true(S, "p_eq independent of Mach/density", abs(a - bb) < 1e-12,
               f"{a:.6f} vs {bb:.6f}")


# =============================================================================
# 7. LAMINATE -- solid-plate recovery limit
# =============================================================================
def validate_laminate() -> None:
    from goddard.structures import laminate as lam

    S = "Laminate"
    # equations.tex claims GJ = 4 c D_xy recovers GJ = G c t^3 / 3 for a solid
    # isotropic plate. Drive the sandwich to that limit: no faces, pure core.
    G, c, t = 5.0e9, 0.20, 0.006
    sec = lam.SandwichSection(
        face_thickness_m=1e-9, core_thickness_m=t, chord_m=c,
        face_modulus_Pa=1.0, face_shear_Pa=1.0,
        core_modulus_Pa=G, core_shear_Pa=G,
    )
    check(S, "GJ -> G c t^3/3 (solid limit)", lam.torsional_stiffness(sec),
          G * c * t ** 3 / 3.0, 1e-6)

    check(S, "J_solid = c t^3/3", lam.torsion_constant_solid(c, t),
          c * t ** 3 / 3.0, 1e-12)

    # G_eff = GJ / J_solid must return G exactly in that same limit.
    check(S, "G_eff recovers G in solid limit",
          lam.effective_shear_modulus(sec), G, 1e-3)

    # Sandwich must be far stiffer than an equal-mass solid: that is the point
    # of the foam core.
    real = lam.SandwichSection(
        face_thickness_m=0.0005, core_thickness_m=0.005, chord_m=c,
        face_modulus_Pa=70e9, face_shear_Pa=5e9,
        core_modulus_Pa=60e6, core_shear_Pa=20e6,
    )
    solid_equiv = 5e9 * c * (2 * 0.0005) ** 3 / 3.0
    check_true(S, "sandwich GJ >> equal-face-material solid",
               lam.torsional_stiffness(real) > 10 * solid_equiv,
               f"GJ {lam.torsional_stiffness(real):.1f} vs {solid_equiv:.4f}")


# =============================================================================
# 8. FLUTTER AND DIVERGENCE -- dimensional and scaling behaviour
# =============================================================================
def validate_flutter() -> None:
    from goddard.structures import flutter as fl

    S = "Flutter"
    pf = fl.FinPlanform(root_chord_m=0.30, tip_chord_m=0.0984,
                        span_m=0.13, thickness_m=0.005)

    check(S, "panel area", pf.area_m2, 0.5 * (0.30 + 0.0984) * 0.13, 1e-12)
    check(S, "aspect ratio b^2/S", pf.aspect_ratio,
          0.13 ** 2 / pf.area_m2, 1e-12)

    # V_f ~ sqrt(G): quadrupling G must double flutter speed.
    v1 = fl.flutter_speed(pf, 5e9, 90000.0, 340.0)
    v2 = fl.flutter_speed(pf, 20e9, 90000.0, 340.0)
    check(S, "V_f ~ sqrt(G)", v2 / v1, 2.0, 1e-9)

    # V_f ~ 1/sqrt(P): flutter speed rises with altitude as pressure falls.
    v_lo = fl.flutter_speed(pf, 5e9, 90000.0, 340.0)
    v_hi = fl.flutter_speed(pf, 5e9, 22500.0, 340.0)
    check(S, "V_f ~ 1/sqrt(P)", v_hi / v_lo, 2.0, 1e-9)

    # V_f ~ (t/c)^{3/2}: from X ~ (t/c)^-3 under a square root.
    thick = fl.FinPlanform(0.30, 0.0984, 0.13, 0.010)
    ratio = fl.flutter_speed(thick, 5e9, 90000.0, 340.0) / v1
    check(S, "V_f ~ (t/c)^1.5", ratio,
          (thick.thickness_ratio / pf.thickness_ratio) ** 1.5, 1e-9)

    # Divergence: q_div ~ GJ, and ~ 1/s^2.
    q1 = fl.divergence_pressure(pf, 1000.0)
    q2 = fl.divergence_pressure(pf, 2000.0)
    check(S, "q_div ~ GJ", q2 / q1, 2.0, 1e-12)
    hand = math.pi ** 2 / 4.0 * 1000.0 / (
        pf.span_m ** 2 * 0.25 * pf.mean_chord_m ** 2 * 2 * math.pi)
    check(S, "q_div vs hand-derived", q1, hand, 1e-12)


# =============================================================================
# 9. HEATING -- Sutton-Graves scaling and radiation equilibrium
# =============================================================================
def validate_heating() -> None:
    from goddard.structures import heating as ht

    S = "Heating"
    # q ~ V^3 and q ~ sqrt(rho/Rn), checked by scaling.
    q1 = ht.stagnation_heat_flux(0.4, 700.0, 0.006)
    q2 = ht.stagnation_heat_flux(0.4, 1400.0, 0.006)
    check(S, "q ~ V^3", q2 / q1, 8.0, 1e-12)

    q3 = ht.stagnation_heat_flux(1.6, 700.0, 0.006)
    check(S, "q ~ sqrt(rho)", q3 / q1, 2.0, 1e-12)

    q4 = ht.stagnation_heat_flux(0.4, 700.0, 0.024)
    check(S, "q ~ 1/sqrt(Rn)", q4 / q1, 0.5, 1e-12)

    # Direct formula check.
    check(S, "Sutton-Graves closed form", q1,
          1.7415e-4 * math.sqrt(0.4 / 0.006) * 700.0 ** 3, 1e-12)

    # Radiation equilibrium: with q balanced by re-radiation dT must be 0.
    tip = ht.TipThermal(nose_radius_m=0.006, mass_kg=0.1, area_m2=2.3e-4)
    T = 800.0
    q_eq = tip.emissivity * ht.STEFAN_BOLTZMANN * (T ** 4 - 300.0 ** 4)
    T_new = ht.step_temperature(tip, T, q_eq, 300.0, 0.01)
    check(S, "radiative equilibrium is a fixed point", T_new, T, 1e-9)


# =============================================================================
# 10. RECOVERY -- reefing scaling and opening load
# =============================================================================
def validate_recovery() -> None:
    from goddard import recovery as rec

    S = "Recovery"
    cfg = rec.RecoveryConfig(drogue_cds_m2=0.6, main_cds_m2=14.0,
                             reefing_ratio=0.35, disreef_altitude_m=300.0,
                             opening_force_coefficient=1.7,
                             max_opening_load_N=12000.0)
    # Drag area scales with the SQUARE of the diameter ratio.
    check(S, "reefed CdS = full * ratio^2", cfg.main_reefed_cds_m2,
          14.0 * 0.35 ** 2, 1e-12)
    check_true(S, "reefed CdS < full CdS",
               cfg.main_reefed_cds_m2 < cfg.main_cds_m2,
               f"{cfg.main_reefed_cds_m2:.3f} < {cfg.main_cds_m2}")

    # Opening load F = Cx q CdS, per stage.
    q = 0.5 * 1.0 * 40.0 ** 2
    for stage, cds in ((rec.Stage.DROGUE, 0.6),
                       (rec.Stage.MAIN_REEFED, cfg.main_reefed_cds_m2),
                       (rec.Stage.MAIN_FULL, 14.0)):
        check(S, f"F = Cx q CdS ({stage.value})",
              rec.opening_load(cfg, stage, q), 1.7 * q * cds, 1e-9)

    # Reefing must actually reduce the opening load -- its entire purpose.
    check_true(S, "reefing cuts main opening load",
               rec.opening_load(cfg, rec.Stage.MAIN_REEFED, q)
               < rec.opening_load(cfg, rec.Stage.MAIN_FULL, q),
               f"ratio {cfg.reefing_ratio ** 2:.4f}")

    # Nominal diameter back-out: CdS = Cd * pi D^2/4  =>  D = sqrt(4 CdS/(pi Cd))
    check(S, "D0 = sqrt(4 CdS/(pi Cd))", rec.nominal_diameter(14.0, 1.5),
          math.sqrt(4.0 * 14.0 / (math.pi * 1.5)), 1e-12)

    # Filling time t_fill = n D0 / V.
    V = 40.0
    d0 = rec.nominal_diameter(14.0, 1.5)
    check(S, "t_fill = n D0 / V",
          rec.filling_time(cfg, rec.Stage.MAIN_FULL, V), 8.0 * d0 / V, 1e-12)

    # Inflation ramp: squared law, clamped at both ends.
    check(S, "inflation is squared in time", rec.inflation_fraction(0.5, 1.0),
          0.25, 1e-12)
    check(S, "inflation starts at 0", rec.inflation_fraction(0.0, 1.0), 0.0, 1e-12)
    check(S, "inflation saturates at 1", rec.inflation_fraction(5.0, 1.0),
          1.0, 1e-12)

    # Fully inflated drag area must equal the stage target.
    check(S, "drag_area -> target when inflated",
          rec.drag_area(cfg, rec.Stage.MAIN_FULL, 1e3, V), 14.0, 1e-12)


# =============================================================================
# 11. MASS -- parallel axis theorem
# =============================================================================
def validate_mass() -> None:
    from goddard import mass as mass_mod

    S = "Mass"
    comps = [
        mass_mod.MassComponent("a", 10.0, 1.0, 0.01, 0.5),
        mass_mod.MassComponent("b", 30.0, 3.0, 0.02, 1.5),
    ]
    st = mass_mod.combine(comps)
    check(S, "total mass", st.mass_kg, 40.0, 1e-12)
    check(S, "x_cg weighted mean", st.x_cg_m,
          (10.0 * 1.0 + 30.0 * 3.0) / 40.0, 1e-12)

    xcg = 2.5
    hand = (0.5 + 10.0 * (1.0 - xcg) ** 2) + (1.5 + 30.0 * (3.0 - xcg) ** 2)
    check(S, "I_pitch parallel-axis", st.i_pitch, hand, 1e-12)
    check(S, "I_roll is additive", st.i_roll, 0.03, 1e-12)


# =============================================================================
# 12. DYNAMICS -- angle conventions
# =============================================================================
def validate_dynamics() -> None:
    from goddard import dynamics as dyn

    S = "Dynamics"
    # Straight up: velocity purely +z, so flight path angle is 0.
    s = dyn.State(vx=0.0, vz=300.0, theta=0.0)
    check(S, "gamma = 0 flying straight up", s.flight_path_angle, 0.0, 1e-12)
    check(S, "alpha = 0 when aligned", s.angle_of_attack, 0.0, 1e-12)

    # alpha = theta - gamma, by construction.
    s2 = dyn.State(vx=30.0, vz=300.0, theta=math.radians(10.0))
    check(S, "alpha = theta - gamma", s2.angle_of_attack,
          s2.theta - math.atan2(30.0, 300.0), 1e-12)

    # Speed is the Euclidean norm.
    check(S, "speed = hypot(vx,vz)", s2.speed, math.hypot(30.0, 300.0), 1e-12)


# =============================================================================
# 13. CHAMBER BALANCE -- the solved root must satisfy the balance equation
# =============================================================================
def validate_chamber() -> None:
    from goddard.motor import chamber as ch
    from goddard.motor import grain as gr
    from goddard.motor import injector as inj
    from goddard.props import cea as cea_mod
    from goddard.props import n2o

    S = "Chamber"
    pts = []
    for i in range(25):
        of = 2.0 + 0.5 * i
        for j in range(9):
            pts.append(cea_mod.CEAPoint(of, (1.0 + 0.5 * j) * 1e6,
                                        1600.0 * math.exp(-((of - 7.0) ** 2) / 40.0),
                                        1.20, 3000.0))
    cea = cea_mod.CEATable(pts, source="<validation synthetic>")

    T = 293.15
    ig = inj.InjectorGeometry(n_holes=32, hole_diameter_m=0.0018,
                              plate_thickness_m=0.005)
    gg = gr.GrainGeometry(length_m=0.75, initial_port_radius_m=0.030,
                          outer_radius_m=0.062)
    gs = gr.GrainState(port_radius_m=0.040)
    At = math.pi * (0.030 / 2.0) ** 2

    st = ch.solve(
        tank_pressure=n2o.vapour_pressure(T),
        vapour_pressure=n2o.vapour_pressure(T),
        rho_liquid=n2o.liquid_density(T),
        ambient_pressure=87000.0,
        injector_geom=ig, injector_cd=0.70,
        grain_geom=gg, grain_state=gs,
        calibration=0.85, eta_cstar=0.88,
        throat_area=At, expansion_ratio=4.5, cea=cea,
    )

    # The defining balance: P_c must equal m_dot_total * eta * c* / A_t.
    predicted = st.m_dot_total * st.c_star_ms / At
    check(S, "P_c = mdot eta c*/A_t (root satisfies balance)",
          st.chamber_pressure_Pa, predicted, 2e-3,
          "c_star_ms already includes eta")

    # O/F closure.
    check(S, "O/F = mdot_ox/mdot_f", st.of_ratio,
          st.m_dot_ox / st.m_dot_fuel, 1e-9)

    # Chug margin definition.
    check(S, "chug margin = (dP/Pc)/0.20", st.chug_margin,
          st.injector_dp_ratio / 0.20, 1e-12)

    # Chamber pressure must sit between ambient and tank.
    check_true(S, "ambient < P_c < P_tank",
               87000.0 < st.chamber_pressure_Pa < n2o.vapour_pressure(T),
               f"P_c = {st.chamber_pressure_Pa/1e6:.3f} MPa")


# =============================================================================
# 14. DRAG -- scaling behaviour of each term
# =============================================================================
def validate_drag() -> None:
    from goddard.aero import drag as dg

    S = "Drag"
    # Base drag closed forms.
    check(S, "base drag subsonic 0.12+0.13M^2", dg.base_drag(0.5),
          0.12 + 0.13 * 0.25, 1e-12)
    check(S, "base drag supersonic 0.25/M", dg.base_drag(2.0),
          0.25 / 2.0, 1e-12)
    check(S, "jet blockage removes base drag", dg.base_drag(2.0, 1.0),
          0.0, 1e-12)

    # Nose wave drag must be zero subsonically for a min-wave-drag shape.
    check(S, "nose wave drag = 0 below M=0.9", dg.nose_wave_drag(5.0, 0.5),
          0.0, 1e-12)
    check_true(S, "nose wave drag > 0 supersonically",
               dg.nose_wave_drag(5.0, 2.0) > 0.0, "")

    # 1/f^2 slender-body scaling: doubling fineness must quarter wave drag.
    a = dg.nose_wave_drag(4.0, 2.0)
    b = dg.nose_wave_drag(8.0, 2.0)
    check(S, "nose wave drag ~ 1/f^2", a / b, 4.0, 1e-9)

    # Reynolds number definition.
    check(S, "Re = rho V L / mu", dg.reynolds_number(300.0, 4.0, 0.9, 1.8e-5),
          0.9 * 300.0 * 4.0 / 1.8e-5, 1e-12)

    # Skin friction must fall with Reynolds number.
    cf_lo = dg.skin_friction_coefficient(1e6, 0.0, 4.0, 0.3)
    cf_hi = dg.skin_friction_coefficient(1e8, 0.0, 4.0, 0.3)
    check_true(S, "C_f falls with Re", cf_hi < cf_lo,
               f"{cf_hi:.5f} < {cf_lo:.5f}")


# =============================================================================

def main() -> int:
    for fn in (validate_atmosphere, validate_n2o, validate_fuel,
               validate_nozzle, validate_nose, validate_roll,
               validate_laminate, validate_flutter, validate_heating,
               validate_recovery, validate_mass, validate_dynamics,
               validate_chamber, validate_drag):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            RESULTS.append((fn.__name__, "MODULE RAISED", False,
                            f"{type(exc).__name__}: {exc}"))

    width = 78
    print("=" * width)
    print("EQUATION VALIDATION -- docs/equations.tex vs independent derivation")
    print("=" * width)

    current = None
    passed = failed = 0
    for section, name, ok, detail in RESULTS:
        if section != current:
            print(f"\n[{section}]")
            current = section
        mark = "PASS" if ok else "FAIL"
        print(f"  {mark}  {name}")
        if not ok:
            print(f"        {detail}")
        passed += ok
        failed += not ok

    print("\n" + "=" * width)
    print(f"{passed} passed, {failed} failed, {passed + failed} total")
    print("=" * width)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
