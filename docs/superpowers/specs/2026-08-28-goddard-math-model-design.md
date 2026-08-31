# Goddard 26-27 Modular Math Model — Design Specification

**Date:** 2026-08-28
**Status:** Approved for implementation planning
**Supersedes:** `25-26 Math Model.xlsx` (single-sheet Excel time-march)

---

## 1. Purpose

A modular, testable flight-performance model for the Goddard 26-27 vehicle: a
6 in diameter, single-stage, paraffin/N₂O hybrid sounding rocket targeting
**50,000 ft AGL** from White Sands Missile Range.

The model must answer four questions:

1. Does this design reach 50,000 ft, and with what confidence interval?
2. What are the peak structural loads, and do the fins flutter?
3. Does the motor run stable, and does the grain survive the burn?
4. What are the recovery loads under a reefed deployment?

It replaces a spreadsheet whose known defects were a 10× mass-flow error, a
constant `C_D` = 0.5 held through Mach 1.65, an atmosphere table that returned
`#N/A` above 15,420 m, a hard-coded launch altitude inconsistent with its own
input, and summary cells that evaluated to `#NAME?`. Every one of those failure
classes is structurally impossible in this design, by construction rather than
by care.

### 1.1 Non-goals (explicit YAGNI)

Out of scope for this build. Listed so they are not re-litigated mid-implementation:

- Optimization / inverse sizing. Forward prediction only. Every entry point is a
  pure `config → results` function so a solver can wrap it later without refactoring.
- 6-DOF, Monte Carlo dispersion, landing ellipses. Reopened on request.
- CFD, FEA, or any meshed solver.
- Structural stress analysis beyond fin aeroelasticity and nose-tip temperature.
- Multi-port or non-circular grain geometry.
- Excel as an *input* surface. The workbook is a generated read-only report.

---

## 2. Vehicle definition

Geometry **shape** is taken from `goddard1.0.ork`; **dimensions** are set fresh
in config per direction from the team.

| Element | Shape (fixed) | Dimension source |
|---|---|---|
| Nose cone | Haack series, shape parameter C = 0 → **Von Kármán (LD-Haack)**, unclipped | config |
| Nose tip | Aluminum, for Mach 2+ stagnation heating | config |
| Transition | Haack, clipped, **fore radius < aft radius** (a flare up to the 6 in body) | config |
| Body tube | Single cylindrical section, 6 in (0.1524 m) OD | config |
| Fins | 3 × trapezoidal clipped delta. Taper ratio ≈ 0.33, LE sweep ≈ 62°, exposed-panel AR ≈ 0.54 | config |
| Fin construction | Carbon-fibre skins over foam core | config |
| Fin cant | **1.0°** | config |
| Recovery | Drogue → reefed main → disreefed main | config |
| Motor | Paraffin 89 % / SEBS-MA 10 % / carbon black 1 %, N₂O 99.9 %, showerhead injector | config |

**Fin planform is confirmed and not to be modified.** The ratios above are the
carried-over shape; absolute dimensions are config inputs.

**On the flare:** a nose section narrower than the body, flared up to 6 in, is a
real supersonic wave-drag source. It is implemented as a parameterized element
and may be collapsed to zero length (nose base diameter = body diameter) by
config if the team later drops it. The model prices it either way; it does not
argue about it.

**On the fin cross-section:** the ORK specifies `rounded`. At Mach 2+ a rounded
leading edge produces a detached bow shock and materially more drag than a
double-wedge or hex section. Cross-section is a config field, separate from the
confirmed planform. The model reports the delta; the team decides.

### 2.1 Environment

| Parameter | Value | Note |
|---|---|---|
| Launch site | White Sands Missile Range, Tularosa Basin | |
| Field elevation | **1,216 m MSL (3,990 ft)** | Basin-floor value. Confirm against the launch agreement for the specific complex; single config field. |
| Atmosphere | US Standard 1976, analytic, 0–86 km | Site ground `T₀`/`P₀` override available |
| Wind | Profile + gust, config | |

---

## 3. Architecture

```
goddard/
  units.py                  in→m, lbm→kg, ft→m, psi→Pa
  config/
    schema.py               frozen dataclasses, validate on construction
    goddard_v2.py           THE design point — every number, in Python
  env/
    atmosphere.py           US Std 1976 analytic
    wind.py
  props/
    n2o.py                  saturated N₂O (ESDU 91022 form)
    fuel.py                 paraffin/SEBS-MA/CB blend properties
    cea.py                  c*, γ, T_c fitted vs (O/F, P_c)
  motor/
    tank.py                 self-pressurizing blowdown
    injector.py             showerhead, Dyer NHNE
    grain.py                regression
    nozzle.py               C_f, expansion, altitude compensation
    chamber.py              assembles the above → MotorState
  aero/
    geometry.py             derived areas, wetted, AR
    drag.py                 C_D(M, Re, α) component build-up
    normal_force.py         Barrowman C_Nα, X_cp(M)
    roll.py                 C_lδ, C_lp from the 1° cant
    damping.py              C_mq
  mass.py                   m(t), x_cg(t), I_xx(t), I_yy(t)
  structures/
    laminate.py             CF-skin / foam-core EI, GJ
    flutter.py              flutter + torsional divergence margins
    heating.py              Fay–Riddell nose-tip temperature
  recovery.py               staged reefed C_d·S(t), opening loads
  dynamics.py               4-DOF equations of motion
  events.py                 rail exit, burnout, apogee, deploy stages, landing
  sim.py                    RK4 + event detection → FlightResult
  band.py                   calibration-envelope driver
  report/
    excel.py                generated read-only workbook
    plots.py
  cli.py
tests/
```

**Config is a Python module, not YAML.** Derived quantities are written inline
(`A_port = pi * r_port**2`) rather than duplicated. `schema.py` holds frozen
dataclasses that validate physical bounds at construction.

### 3.1 Module contracts

Every module exposes one pure function with a typed return. No module reaches
across a boundary or mutates shared state.

| Module | Signature |
|---|---|
| `env.atmosphere` | `state(h) → AtmState(ρ, P, T, a, μ)` |
| `props.n2o` | `saturated(T) → N2OState(ρ_l, ρ_v, P_sat, h_l, h_v)` |
| `motor.chamber` | `derivatives(s, P_amb) → ds/dt`; `outputs(s, P_amb) → MotorOut(F, ṁ_ox, ṁ_f, OF, P_c, ΔP_inj, web_remaining)` |
| `aero` | `coefficients(M, Re, α, p) → AeroState(C_D, C_Nα, X_cp, C_lδ, C_lp, C_mq)` |
| `mass` | `at(m_ox, m_fuel) → MassState(m, x_cg, I_xx, I_yy)` |
| `structures.flutter` | `margins(q, M, a) → FlutterOut(V_f, q_div, margin_f, margin_d)` |
| `recovery` | `cds(t, h, v, stage) → float`; `opening_load(...) → float` |
| `sim` | `run(config) → FlightResult` |
| `band` | `run_band(config, grid) → BandResult` |

---

## 4. Motor — full internal ballistics

Motor state integrates in the same vector as the trajectory:

```
[ m_ox_liq, m_ox_vap, T_tank, r_port, P_c ]
```

### 4.1 Tank — self-pressurizing blowdown

Adiabatic quasi-equilibrium saturated model (Zilliac & Karabeyoglu,
`10.2514/6.2005-3549`; selected over alternatives per Zimmerman et al.,
AIAA 2013-4045). Liquid drains → vapour expands → liquid boils to hold
saturation → `T_tank` falls → `P_sat` falls. Handles the liquid→vapour
transition and the vapour-only tail as distinct regimes.

N₂O properties from ESDU 91022 reduced correlations:
`T_c` = 309.57 K, `P_c` = 7.251 MPa, `ρ_c` = 452 kg/m³.

**Purity.** At 99.9 % the pure-component correlations apply directly; no mixture
model. `ullage_noncondensable_fraction` exists, **defaults to 0.0**, and is
documented as a sensitivity knob only — the 0.1 % balance (N₂/air/water) would
contribute a non-condensing ullage partial pressure, which is inside the noise
at this purity.

Cross-check implementation against Whitmore & Chandler (`10.2514/1.47131`).

### 4.2 Injector — showerhead

```
A_inj = N_holes · π·d_hole² / 4
```

Config takes `N_holes`, `d_hole`, `plate_thickness`; `L/d` sets the discharge
coefficient regime.

Saturated N₂O flashes and cavitates in straight orifices, so single-phase
Bernoulli overpredicts and HEM underpredicts. Dyer non-equilibrium blend
(`10.2514/6.2007-5702`):

```
k       = √( (P₁ − P₂) / (P_v − P₂) )
ṁ_SPI   = C_d·A·√( 2·ρ_l·(P₁ − P₂) )
ṁ_HEM   = C_d·A·ρ₂·√( 2·(h₁ − h₂) )
ṁ_ox    = ( k·ṁ_SPI + ṁ_HEM ) / (1 + k)
```

**Chug margin is a required output.** Feed/chamber coupling is the governing
instability for a showerhead on a blowdown feed system. Criterion
`ΔP_inj / P_c ≥ 0.20` (NASA SP-194). This is *not* a single check: as the tank
blows down, `ΔP_inj` collapses faster than `P_c`, so the ratio degrades through
the burn and the risk peaks at the tail. Reported as a time history with the
crossing flagged.

### 4.3 Grain — paraffin blend regression

```
G_ox = ṁ_ox / (π · r_port²)
ṙ    = calib · a · G_ox^n              a ≈ 1.55e-4 m/s, n ≈ 0.5   [10.2514/1.3340]
ṁ_f  = ρ_f · 2π · r_port · L_grain · ṙ
O/F  = ṁ_ox / ṁ_f
```

Fuel density, mass-weighted:
`0.89·924 + 0.10·910 + 0.01·1900` ≈ **932 kg/m³**.

`a` and `n` are published for *pure* paraffin. The blend perturbs both
directions: 10 % SEBS-MA raises melt viscosity and stabilizes the liquid film,
suppressing entrainment and **lowering** ṙ (`10.2514/2.5976`); 1 % carbon black
opacifies and raises surface absorption, **raising** ṙ. Net effect is not
resolvable from literature. It is carried entirely in `regression_calibration`
(§6) — there are no other hidden factors.

**Web-remaining is a required output.** `r_port` growing to the liner radius is
burnthrough, raised as `PortBurnthrough`.

### 4.4 Chamber and nozzle

```
V_c · dρ_c/dt = ṁ_in − ṁ_out           filling transient
P_c           = ṁ_tot · η_c* · c*(O/F, P_c) / A_t
F             = η_Cf · C_f · P_c · A_t + (P_e − P_a)·A_e
```

`c*(O/F, P_c)` from a CEA fit (NASA RP-1311), peak near O/F ≈ 7–8.

The `(P_e − P_a)·A_e` term means **thrust rises with altitude** — a first-order
effect over a 50,000 ft climb that the 25-26 model could not represent at all.

---

## 5. Aerodynamics

`C_D` is built up by component and varies with Mach. This is the single largest
correction over the previous model, which held `C_D` = 0.5 through Mach 1.65.

| Contribution | Method | Source |
|---|---|---|
| Skin friction | Compressible turbulent flat plate, roughness floor, per-component wetted area | Hoerner; Niskanen |
| Nose wave drag | Slender-body (Ward) blended to modified-Newtonian above M ≈ 1.3 | `10.1093/qjmam/2.1.75`; Sears `10.1090/qam/20394` |
| Flare wave drag | Same treatment, applied to the Haack transition | Ward |
| Fin wave drag | Leading-edge + thickness; cross-section-dependent | Hoerner |
| Base drag | Hoerner correlation, scaled by jet blockage during burn | Hoerner |
| Interference | Fin-body junction | Hoerner |

The Von Kármán nose is the C = 0 member of the minimum-wave-drag Haack family;
the nose model must recover that analytic result as a validation check.

**Normal force and stability:** Barrowman component build-up with Mach
correction (NTRS 20010047838), plus the Allen & Perkins body cross-flow term
(NACA Report 1048) — required because α is a live state in 4-DOF. Static margin
reported in calibers vs. time.

**Roll from the 1° cant:**

```
p_eq = −( C_lδ · δ / C_lp ) · (2V / d)
```

`C_lδ` from fin geometry, `C_lp` from strip theory. Roll is integrated as a real
state, not assumed at equilibrium, and the roll-induced `ΔC_D` from the fins'
effective incidence feeds back into drag.

---

## 6. Calibration constants and band mode

**Three constants are unmeasured.** No static fire and no cold-flow test are
planned. This is the dominant uncertainty in the model and is handled explicitly
rather than buried.

| Constant | Nominal | Band | Why unmeasured |
|---|---|---|---|
| `regression_calibration` | 0.85 | [0.75, 1.00] | No static fire; SEBS-MA/CB net effect unresolved in literature |
| `injector_Cd` | 0.70 | [0.61, 0.82] | No cold flow; 0.61 = sharp-edge limit, 0.82 = straight-drilled L/d 2–5 upper |
| `eta_cstar` | 0.88 | [0.82, 0.93] | No static fire; showerhead with no post-combustion chamber or mixing diaphragm. **Engineering estimate, not a literature citation** — no published range for this exact configuration was found. |

Nominals are biased conservative. **No other value in the model is tunable** —
everything else is geometry or published physics.

### 6.1 Why a single conservative point estimate is insufficient

> **Team-reviewed 2026-08-28 — accepted.** The two-sided conservatism argument
> below is the approved basis for band mode. The key consequence to carry into
> implementation: **"conservative" has no single direction here.** Any future
> change that collapses the band back to a single point estimate must
> independently re-examine the port-burnthrough case, because a scalar biased
> for apogee will not cover it. Do not simplify this away.

Oxidizer mass flow is set by the tank and injector, **not** by the grain.
Therefore lower regression → less fuel → **higher** O/F. Paraffin/N₂O peaks in
c\* near O/F ≈ 7–8, so:

- If the design sits **at** the peak, error in either direction costs c\*.
- If the design sits **fuel-rich** of the peak, low regression moves *toward*
  peak and **raises** thrust.

"Conservative regression" therefore does **not** reliably mean "conservative
apogee" — the sign flips depending on which side of the c\* peak the design lands.

The two directions also threaten different things:

| Direction | Endangers |
|---|---|
| Regression **below** nominal | Apogee shortfall, lean O/F, chug margin |
| Regression **above** nominal | **Port burnthrough into liner/case** |

A single scalar tuned for apogee leaves the burnthrough case unexamined. That is
unacceptable without test data.

### 6.2 Band mode

`band.py` runs the forward model over a **3³ = 27-corner full-factorial grid**
at {low, nominal, high} for the three constants, treated as independent (no
correlation data exists). Grid density is configurable.

"Conservative" is defined **per metric**, because the metrics do not share a
direction:

| Metric | Reported as |
|---|---|
| Apogee | **Minimum** across band — do we still clear 50,000 ft? |
| Max Q, max g | **Maximum** across band |
| Flutter / divergence margin | **Minimum** across band |
| Chug margin `ΔP_inj/P_c` | **Minimum** across band |
| Web remaining at burnout | **Minimum** across band — the burnthrough check |
| O/F | **Full excursion** |

Each envelope value reports the **driving corner**, so the output states which
unmeasured constant controls each risk. That directly identifies which single
test would buy the most margin.

27 forward runs is computationally free. Band mode is the primary deliverable;
the single nominal run is a convenience.

---

## 7. Structures

### 7.1 Fin flutter and divergence

The foam core exists to raise torsional stiffness, so the model must represent
the sandwich rather than plug an isotropic shear modulus into an amateur formula.

1. **`laminate.py`** — classical laminate theory for the CF skins (Jones 1999)
   plus core shear compliance (Allen 1969), which dominates `GJ` for thin skins
   over a low-modulus foam core. Yields effective `EI` and `GJ`.
   *(Note: Allen 1969 — H. G. Allen, sandwich panels — is a different author
   from Allen & Perkins, NACA Report 1048, cited in §5 for body cross-flow.)*

2. **`flutter.py`** — NACA TN 4197 flutter velocity:

   ```
   V_f = a · √[ G_eff / ( (39.3·AR³) / ((t/c)³·(AR+2)) · ((λ+1)/2) · (P/P₀) ) ]
   ```

   driven by `G_eff = GJ / J_solid`, the shear modulus of the equivalent solid
   section — the defensible way to map a sandwich into an isotropic-plate
   criterion. TN 4197's author calls the criteria "crude"; this is why they are
   not used alone.

3. **Torsional divergence**, uniform-cantilever result:

   ```
   q_div = (π²/4) · GJ / ( s²·e·c²·C_Lα )
   ```

   (Bisplinghoff, Ashley & Halfman). Checked independently, because for
   low-`GJ` composite fins divergence frequently precedes flutter and is missed
   by flutter-only screening.

Both margins are evaluated against the actual `V(t)`, `q(t)`, `P(t)` along the
trajectory — not a single worst-case guess.

### 7.2 Nose-tip heating

Fay–Riddell stagnation-point heat flux (`10.2514/8.7517`) integrated along the
trajectory → aluminum tip temperature vs. time, checked against the alloy
service limit. The metal tip exists because of this load; the model produces the
number rather than assuming the result.

---

## 8. Recovery — reefed

`C_d·S` is a staged function with real inflation dynamics:

```
apogee            → canopy reefed, C_d·S₁ = (reefing ratio)² · C_d·S₂
h_disreef         → canopy full,   C_d·S₂

Single canopy, two states. No drogue -- the reefed stage does that job.
```

Each stage ramps over filling time `t_fill ≈ n·D₀/V` and reports a **peak
opening load** `F = C_x · q · (C_d·S)`. All per Knacke (NWC TP 6575) and the
AFFDL Recovery Systems Design Guide.

Bounding opening load is the entire purpose of reefing, so peak load per stage is
a primary output, not a diagnostic. OpenRocket already flags the current
single-chute-at-apogee configuration with *"deployment at high speed (151 ft/s)"*
— this module is the fix.

---

## 9. Integration, events, outputs

**Integrator:** RK4, fixed `dt` = 0.01 s, motor states in the same vector.

**Events** — rail exit, burnout, apogee, each recovery stage, landing — located
by **bisection on sign change**, never by stepping past them. The simulation runs
to landing, not to a fixed row count. (The 25-26 model spanned 50 s against a
~250–380 s flight.)

**Outputs:** `FlightResult` → CSV, plots, and a generated
`goddard_results.xlsx`.

The workbook is **read-only display**: Summary, Trajectory, Motor, Aero, Margins,
Band Envelope, with charts. It is regenerated on every run. Editing it has no
effect on anything. All inputs are edited in `config/goddard_v2.py`.

Internal units are SI throughout; the report renders both SI and US customary.

---

## 10. Error handling

No `#N/A`, no silent `NaN`, no value that is wrong without being loud.

- Config validated at construction against physical bounds.
- Named exceptions: `PortBurnthrough`, `TankDepleted`, `SubTriplePoint`,
  `UnchokedNozzle`, `ChuteOverload`, `DivergenceExceeded`.
- Atmosphere is analytic to 86 km — there is no table edge to fall off, which is
  how the previous model produced `#N/A` above 15,420 m.
- Band mode records per-corner failures rather than aborting the sweep; a corner
  that burns through is a *result*, not a crash.

---

## 11. Validation and testing

**Unit tests** per module against published references:

| Module | Validated against |
|---|---|
| `env.atmosphere` | US Std 1976 published tables |
| `props.n2o` | ESDU 91022 saturation data |
| `aero.normal_force` | Hand-worked Barrowman case |
| `structures.flutter` | Hand-worked TN 4197 case |
| `motor.injector` | Dyer et al. published NHNE results |
| `recovery` | Knacke worked example |

**End-to-end validation test.** Substitute a thrust-curve motor, run the
`goddard1.0.ork` geometry with the AeroTech O6000W, and compare apogee and max
Mach against OpenRocket's **15,300 m / Mach 2.47**.

This validates atmosphere + aero + mass + integrator *independently of the hybrid
physics*. When hybrid numbers later look strange, this test localizes the fault.
It is the single most valuable test in the suite and is written first.

---

## 12. Assumptions and open items

**Assumptions carried into implementation:**

1. Field elevation **1,216 m MSL** (Tularosa Basin floor).
   > **Team-confirmed 2026-08-28 — good as-is.** Tularosa Basin floor value
   > accepted; no further confirmation against the launch agreement required.
   > Remains a single config field (`environment.field_elevation_m`) if a
   > specific complex later needs a different value.
2. Mass, CG and inertia are built from geometry and material densities, with
   per-component override hooks — not a hand-entered total.
3. The three calibration constants are treated as **independent** in the band
   grid. No correlation data exists to justify otherwise.
4. Excel report layout is Summary / Trajectory / Motor / Aero / Margins / Band
   Envelope. If a competition or design-review template exists, sheet structure
   should be matched to it instead.

**Deferred by decision:**

- 6-DOF and Monte Carlo dispersion — reopened on request.
- Inverse sizing / optimization — the pure-function architecture keeps this a
  wrapper, not a rewrite.

**Outputs, not decisions** — the model produces these and the team decides after:

- Rounded vs. double-wedge fin cross-section at Mach 2+.
- Whether to retain the sub-body-diameter nose with flare.
- Whether chug margin holds through the blowdown tail.

---

## 13. References

See `docs/references.bib` (31 entries, grouped by the module each one backs) and
`docs/references_dois.txt` (13 DOIs — 11 publisher-verified, 2 constructed from
confirmed AIAA paper numbers; 18 sources with no DOI carry authoritative
identifiers instead).
