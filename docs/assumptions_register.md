# Goddard 26-27 — Assumptions Register

**Every number in the model that is not yet nailed down.**
Bring this to the NASA engineer meeting and fill in the right-hand columns.

**Date:** 2026-08-28 · **Model spec:** `docs/superpowers/specs/2026-08-28-goddard-math-model-design.md`
**Fillable version:** `docs/assumptions_register.csv`

---

## How to read the Status column

| Status | Meaning | Action needed |
|---|---|---|
| **CONFIRMED** | Team decision, locked. Not up for discussion unless something changes. | None |
| **DERIVED** | Computed from other entries. Changes automatically when its inputs change. | None — but check its inputs |
| **ESTIMATED** | Engineering estimate with a stated basis. Usable, but a better number improves confidence. | Ask if they have data |
| **BANDED** | Unmeasured. Swept across a range in band mode; the model reports an envelope, not a point. | Ask what would narrow the band |
| **OPEN** | No value yet. The model cannot run until this is set. | **Must be answered** |
| **ASSUMPTION** | A physical effect deliberately not modeled. | Ask whether it's safe to neglect |
| **PLACEHOLDER** | A value or dataset that must be replaced before any result is trusted. | **Must be replaced** |

**Priority for the meeting:** everything marked **OPEN** or **PLACEHOLDER** blocks
a trustworthy run. Everything marked **BANDED** is where test data would buy the
most confidence — those three are the dominant uncertainty in the whole model.

---

## A. Environment and launch site

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| A1 | Field elevation | 1216 | m MSL | CONFIRMED | Tularosa Basin floor, WSMR. Team-confirmed 2026-08-28. |
| A2 | Ground temperature | 303 | K | ESTIMATED | ~30 °C summer. **What launch window / season? Day-of temp swing matters for N₂O tank pressure.** |
| A3 | Ground pressure | derived | Pa | DERIVED | US Std 1976 at A1, unless a site measurement is supplied |
| A4 | Mean wind speed | — | m/s | OPEN | **What wind limits does the range impose? Needed for rail-exit and weathercocking.** |
| A5 | Wind profile model | uniform | — | ASSUMPTION | No shear layer modeled. **Is a WSMR sounding profile available?** |
| A6 | Launch rail length | — | m | OPEN | ORK had 1.0 m, far too short for this vehicle. **What rail/tower does WSMR provide?** |
| A7 | Launch rail angle | 0 | deg | ESTIMATED | Vertical. **Does the range require an off-vertical launch for safety?** |
| A8 | Humidity | ignored | — | ASSUMPTION | Dry-air atmosphere. Safe to neglect at these altitudes? |
| A9 | Latitude (Coriolis) | ignored | — | ASSUMPTION | Not modeled in 4-DOF. Negligible for a 50 kft flight? |

## B. Vehicle geometry

Shape is confirmed from `goddard1.0.ork`. **Dimensions below are all open.**

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| B1 | Body outer diameter | 0.1524 | m (6 in) | CONFIRMED | Team spec |
| B2 | Body wall thickness | — | m | OPEN | Drives dry mass and buckling |
| B3 | Body tube length | — | m | OPEN | |
| B4 | Nose shape | Von Kármán (Haack C=0) | — | CONFIRMED | ORK `haack`, shapeparameter 0.0 |
| B5 | Nose fineness ratio L/D | — | — | OPEN | ORK was ≈5.2. **Recommended fineness for Mach 2.5?** |
| B6 | Nose base diameter | 0.1524 | m (6 in) | CONFIRMED | Flare removed, so the nose meets the body at full diameter. This is now just B1. |
| B7 | Flare present? | **no** | — | CONFIRMED | Team decision: flare removed. It cost supersonic wave drag for no return. Constant-diameter nose-to-body joint. |
| B8 | Flare length | 0 | m | CONFIRMED | Zero by B7. Transition code retained and guarded, so reversing is a config change. |
| B9 | Nose tip radius | — | m | OPEN | **Directly drives stagnation heating (Fay–Riddell). Sharpest tip that survives Mach 2.5?** |
| B10 | Fin count | 3 | — | CONFIRMED | ORK |
| B11 | Fin planform | clipped delta | — | CONFIRMED | **Shape locked — not open for change** |
| B12 | Fin taper ratio | 0.328 | — | CONFIRMED | Shape ratio from ORK |
| B13 | Fin LE sweep | 62 | deg | CONFIRMED | Shape ratio from ORK |
| B14 | Fin root chord | — | m | OPEN | Absolute size open; ratios above fixed |
| B15 | Fin span | — | m | OPEN | |
| B16 | Fin thickness | — | m | OPEN | **Dominant flutter driver — enters as (t/c)³** |
| B17 | Fin cross-section | rounded | — | OPEN | ORK says rounded. **At Mach 2.5 a rounded LE gives a detached bow shock. Double-wedge instead?** Model prices both. |
| B18 | Fin cant angle | 1.0 | deg | CONFIRMED | Team spec |
| B19 | Fin fillet radius | 0 | m | OPEN | ORK had none. Fillets help root stress and interference drag. |
| B20 | Surface roughness | — | µm | OPEN | Enters skin friction. **Expected finish quality?** |

## C. Mass properties

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| C1 | Total dry mass | — | kg | DERIVED | Built from geometry × material density, with override hooks |
| C2 | Airframe material | — | — | OPEN | ORK said fiberglass (1850 kg/m³). **CF airframe or fiberglass?** |
| C3 | Avionics mass | — | kg | OPEN | |
| C4 | Payload mass | — | kg | OPEN | **Is there a required payload for the competition/agreement?** |
| C5 | Recovery system mass | — | kg | OPEN | |
| C6 | Tank dry mass | — | kg | OPEN | See D6 |
| C7 | Dry CG | derived | m | DERIVED | |
| C8 | Inertia I_xx, I_yy | derived | kg·m² | DERIVED | |
| C9 | Mass margin policy | — | % | OPEN | **What growth allowance do they recommend at this design stage?** |

## D. Oxidizer system

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| D1 | Oxidizer | N₂O, 99.9 % | — | CONFIRMED | Team spec |
| D2 | N₂O mass | — | kg | OPEN | **Primary performance driver. Sized against the 50 kft target.** |
| D3 | Tank internal volume | — | m³ | OPEN | |
| D4 | Initial fill fraction | — | — | OPEN | Typically 0.80–0.85 liquid by volume. **Recommended ullage for thermal safety?** |
| D5 | Initial tank temperature | = ambient (A2) | K | ESTIMATED | **Is pre-chill or pre-heat planned? Strongly affects tank pressure.** |
| D6 | Tank material / MEOP | — | — | OPEN | **Burst margin required? Aluminum or composite-overwrapped?** |
| D7 | Feed line ID and length | — | m | OPEN | |
| D8 | Feed line pressure drop | neglected | — | ASSUMPTION | Only injector ΔP modeled. **Safe to neglect, or does line loss matter for chug?** |
| D9 | Main valve type / open time | — | s | OPEN | Affects ignition transient |
| D10 | Ullage non-condensables | 0.0 | frac | CONFIRMED | Negligible at 99.9 % purity; knob exists for sensitivity only |
| D11 | Tank thermal environment | adiabatic | — | ASSUMPTION | No heat leak into tank during burn. Valid for a ~6 s burn? |

## E. Injector

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| E1 | Injector type | showerhead, straight-drilled | — | CONFIRMED | Team spec |
| E2 | Number of orifices | — | — | OPEN | |
| E3 | Orifice diameter | — | m | OPEN | |
| E4 | Plate thickness (sets L/d) | — | m | OPEN | L/d sets discharge coefficient regime |
| E5 | **`injector_Cd`** | **0.70** | — | **BANDED [0.61, 0.82]** | No cold-flow data. 0.61 = sharp-edge limit, 0.82 = straight-drilled L/d 2–5 upper. **Would they lend cold-flow facilities?** |
| E6 | Injector ΔP/P_c target | ≥ 0.20 | — | ESTIMATED | NASA SP-194 chug criterion. **Do they recommend a higher margin for a blowdown feed?** |

## F. Fuel grain

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| F1 | Composition | 89 % paraffin / 10 % SEBS-MA / 1 % carbon black | — | CONFIRMED | Team spec |
| F2 | Paraffin density | 924 | kg/m³ | ESTIMATED | **Which paraffin grade? Density varies with melting point.** |
| F3 | SEBS-MA density | 910 | kg/m³ | ESTIMATED | |
| F4 | Carbon black density | 1900 | kg/m³ | ESTIMATED | |
| F5 | Blend density ρ_f | 932 | kg/m³ | DERIVED | Mass-weighted from F2–F4 |
| F6 | Regression coefficient a | 1.55e-4 | m/s | ESTIMATED | Pure paraffin, Karabeyoglu 2004 (`10.2514/1.3340`) |
| F7 | Regression exponent n | 0.5 | — | ESTIMATED | Same source |
| F8 | **`regression_calibration`** | **0.85** | — | **BANDED [0.75, 1.00]** | No static fire. SEBS-MA stabilizes melt film → suppresses regression; carbon black opacifies → raises it. Net unresolved. **Do they have data on SEBS-MA-loaded paraffin?** |
| F9 | Grain length | — | m | OPEN | |
| F10 | Initial port diameter | — | m | OPEN | Sets initial G_ox and therefore initial O/F |
| F11 | Grain OD / web thickness | — | m | OPEN | **Sets the burnthrough margin — see spec §6.1** |
| F12 | Liner material and thickness | — | m | OPEN | |
| F13 | Port geometry | single circular | — | CONFIRMED | Multi-port out of scope |
| F14 | Grain casting defects | ignored | — | ASSUMPTION | Uniform density assumed. **Is void content a real risk for cast paraffin?** |

## G. Chamber and nozzle

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| G1 | Post-combustion chamber | none | — | CONFIRMED | Team spec |
| G2 | Mixing diaphragm | none | — | CONFIRMED | Team spec |
| G3 | Pre-combustion chamber volume | — | m³ | OPEN | |
| G4 | Throat diameter | — | m | OPEN | **Sets chamber pressure. Primary design variable.** |
| G5 | Expansion ratio ε | — | — | OPEN | **Optimize for what altitude? Sea-level-safe vs. altitude-optimized.** |
| G6 | Nozzle material | — | — | OPEN | Graphite? Phenolic? |
| G7 | Throat erosion | not modeled | — | ASSUMPTION | A_t held constant. **How much erosion is typical over a ~6 s N₂O burn? This could be significant.** |
| G8 | Nozzle divergence half-angle | — | deg | OPEN | Sets the divergence loss factor |
| G9 | **`eta_cstar`** | **0.88** | — | **BANDED [0.82, 0.93]** | Showerhead, no post-combustion chamber. **Engineering estimate — no published range found for this exact configuration. Do they have data?** |
| G10 | `eta_Cf` | 0.97 | — | ESTIMATED | Typical nozzle efficiency |
| G11 | **CEA c\*/γ/T_c table** | **not generated** | — | **PLACEHOLDER** | **Must be produced from NASA CEA (RP-1311) for this exact 89/10/1 blend vs N₂O. The model will refuse to run without it — it will not guess.** |

## H. Aerodynamics

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| H1 | Drag method | component build-up | — | CONFIRMED | Spec §5 |
| H2 | Boundary layer | fully turbulent | — | ASSUMPTION | No laminar run modeled. Conservative on drag. |
| H3 | Newtonian blend Mach | 1.3 | — | ESTIMATED | Where slender-body theory hands off |
| H4 | Base drag jet blockage | modeled | — | ASSUMPTION | Base drag reduced while motor burns |
| H5 | Fin-body interference | Hoerner correlation | — | ESTIMATED | |
| H6 | Angle of attack range | small-α linear | — | ASSUMPTION | Barrowman + Allen–Perkins cross-flow. Valid to ~10°. |
| H7 | Protuberances / launch lugs | not modeled | — | ASSUMPTION | **Rail buttons, camera housings, antennas — what's planned?** |

## I. Structures and materials

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| I1 | CF skin E₁ / E₂ / G₁₂ | — | GPa | OPEN | **Which prepreg/layup? Needed for laminate theory.** |
| I2 | CF ply thickness and layup | — | — | OPEN | |
| I3 | Foam core type | — | — | OPEN | **Which foam? Divinycell, Rohacell, other?** |
| I4 | Foam core shear modulus | — | MPa | OPEN | **Dominates fin GJ — the single most important structural unknown** |
| I5 | Foam core density | — | kg/m³ | OPEN | |
| I6 | Aluminum tip alloy | — | — | OPEN | 6061? 7075? **Which has the service temperature margin at Mach 2.5?** |
| I7 | Al service temperature limit | — | K | OPEN | Checked against Fay–Riddell tip temperature |
| I8 | Fin root attachment | rigid | — | ASSUMPTION | Root fixity assumed perfect. **Real root compliance lowers flutter speed — how much margin to carry?** |
| I9 | Required flutter margin | — | — | OPEN | **What flutter margin do they require? 1.5×? 2×?** |

## J. Recovery

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| J1 | Architecture | single canopy: reefed → full | — | CONFIRMED | Team spec. No drogue — the reefed stage does that job. |
| J3 | Canopy C_d·S (full open) | — | m² | OPEN | Single canopy; reefed area is this × ratio² |
| J4 | Reefing ratio | — | — | OPEN | **Sets the reefed-stage load. Typical starting value?** |
| J5 | Disreef trigger | — | m or s | OPEN | Altitude-triggered or timer? |
| J6 | Filling constant n | 8 | — | ESTIMATED | Knacke, solid cloth. Range 8–10. |
| J7 | Opening force coefficient C_x | — | — | OPEN | Knacke, canopy-type dependent |
| J8 | Canopy deploy | at apogee, no delay | — | ASSUMPTION | **Should there be a delay past apogee to reduce deployment velocity?** Reefed deployment at apogee is the high-load case. |
| J9 | Max allowable opening load | — | N | OPEN | **What g-limit does the airframe/payload impose? This is what reefing is sized against.** |
| J10 | Max allowable landing speed | — | m/s | OPEN | **Range safety requirement?** |

## K. Simulation settings

| ID | Parameter | Value | Units | Status | Basis |
|---|---|---|---|---|---|
| K1 | Integrator | RK4, fixed step | — | CONFIRMED | Spec §9 |
| K2 | Time step | 0.01 | s | CONFIRMED | |
| K3 | Degrees of freedom | 4 (x, z, θ, φ) | — | CONFIRMED | 6-DOF reopened on request |
| K4 | Atmosphere | US Std 1976, analytic | — | CONFIRMED | |
| K5 | Band grid | 3³ full factorial | — | CONFIRMED | {low, nominal, high} on E5, F8, G9 |
| K6 | Event detection | bisection on sign change | — | CONFIRMED | |

---

## Summary — what blocks a trustworthy run

**111 parameters tracked.** Counts below are generated from this file, not
hand-tallied — regenerate with the script in `docs/README.md` after editing.

| Count | Status | Meaning |
|---|---|---|
| **50** | OPEN | No value yet. Model cannot run. |
| **1** | PLACEHOLDER | G11, the CEA table. Model will refuse to run rather than guess. |
| **3** | BANDED | E5, F8, G9. The dominant uncertainty. Band mode reports an envelope. |
| **13** | ASSUMPTION | Effects deliberately not modeled — worth a sanity check with them |
| **13** | ESTIMATED | Usable now; better data improves confidence |
| **26** | CONFIRMED | Locked by team decision |
| **5** | DERIVED | Computed from other entries |

### The five questions most worth their time

1. **G11 / G7** — Can they help generate CEA data for the 89/10/1 blend, and how much throat erosion should we expect over a ~6 s N₂O burn? Erosion is currently unmodeled and could be significant.
2. **F8** — Any data on regression rate for SEBS-MA-loaded paraffin? This is the single largest performance unknown, and we are not doing a static fire.
3. **I4 / I9** — Foam core shear modulus dominates fin GJ, and we have no value. What flutter margin do they require?
4. **E5** — Access to cold-flow facilities would convert `injector_Cd` from a banded guess to a measurement.
5. **J9** — What opening-load limit should reefing be sized against?

### The honest framing for the meeting

We have no static fire and no cold flow planned. Three constants
(`injector_Cd`, `regression_calibration`, `eta_cstar`) are therefore unmeasured,
and the model sweeps them rather than pretending to a single answer. **Any test
data they can offer against those three collapses the uncertainty band faster
than any amount of additional modeling.** That is the ask.
