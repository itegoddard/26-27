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

Planform **supersedes** `goddard1.0.ork` — the ORK fin was simultaneously
over-stable (4.3 cal) and flutter-critical (1.6 % thick). Dimensions now come
from `docs/reference/02_BUDGET_50KFT_DESIGN.md`.

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| B1 | Body outer diameter | 0.1524 | m (6 in) | CONFIRMED | Team spec |
| B2 | Body wall thickness | 2.4 | mm | CONFIRMED | Fibreglass, non-structural — only 0.45 m of tube. Pressure vessels carry the rest. docs/reference/02_BUDGET_50KFT_DESIGN.md |
| B3 | Body tube length | 3.60 | m | CONFIRMED | Master design variable. 3.247 m hits nominal; 3.60 m still hits target after every derate. docs/reference/02_BUDGET_50KFT_DESIGN.md |
| B4 | Nose shape | Von Kármán (Haack C=0) | — | CONFIRMED | ORK `haack`, shapeparameter 0.0 |
| B5 | Nose fineness ratio L/D | 5.0 | — | CONFIRMED | 762 mm. Stroick: fineness 5 critical for this regime. docs/reference/02_BUDGET_50KFT_DESIGN.md |
| B6 | Nose base diameter | 0.1524 | m (6 in) | CONFIRMED | Flare removed, so the nose meets the body at full diameter. This is now just B1. |
| B7 | Flare present? | **no** | — | CONFIRMED | Team decision: flare removed. It cost supersonic wave drag for no return. Constant-diameter nose-to-body joint. |
| B8 | Flare length | 0 | m | CONFIRMED | Zero by B7. Transition code retained and guarded, so reversing is a config change. |
| B9 | Nose tip radius | 3.81 | mm | CONFIRMED | 5 % bluffness × 152.4 mm ÷ 2. Bonded aluminium cap. docs/reference/02_BUDGET_50KFT_DESIGN.md |
| B10 | Fin count | 3 | — | CONFIRMED | ORK |
| B11 | Fin planform | clipped delta, flat tip | — | CONFIRMED | **Supersedes goddard1.0.ork** — the ORK fin was over-stable at 4.3 cal AND failed flutter. docs/reference/02_BUDGET_50KFT_DESIGN.md |
| B12 | Fin taper ratio | 0.425 | — | CONFIRMED | 85/200 mm. **Supersedes the ORK's 0.328** — team confirmed the ORK is wrong. |
| B13 | Fin LE sweep | 50 | deg | CONFIRMED | Band 45–70°. **Supersedes the ORK's 62°.** |
| B14 | Fin root chord | 200 | mm | CONFIRMED | docs/reference/02_BUDGET_50KFT_DESIGN.md |
| B15 | Fin span | 109.7 | mm | CONFIRMED | **Solved** from a 2.00-caliber stability target, not chosen. |
| B16 | Fin thickness | 6.35 | mm | CONFIRMED | 3.17 % of root, inside the 3–6 % rule. Source assumed solid G10; **we build CF skins over foam**, so the skin/core split (I2/I3) is open and the source's 2.22 flutter margin does NOT carry over. |
| B17 | Fin cross-section | hexagonal | — | CONFIRMED | Flat tip. Resolves the rounded-vs-wedge question. |
| B18 | Fin cant angle | 1.0 | deg | CONFIRMED | Team spec |
| B19 | Fin fillet radius | 0 | m | OPEN | ORK had none. Fillets help root stress and interference drag. |
| B20 | Surface roughness | — | µm | OPEN | Enters skin friction. **Expected finish quality?** |

## C. Mass properties

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| C1 | Total dry mass | — | kg | DERIVED | Built from geometry × material density, with override hooks |
| C2 | Airframe material | 6061-T6 aluminium + fibreglass | — | CONFIRMED | Stacked pressure vessels carry the airframe over their own length; only 0.45 m of non-structural fibreglass tube remains. |
| C3 | Avionics mass | — | kg | OPEN | |
| C4 | Payload mass | 0.215 | kg | ESTIMATED | CosmicWatch v3X. **The repo publishes no mass** — computed from its own drawings: PN2506 enclosure 136 g + endplates 19 g + scintillator 26 g + boards ~25 g + sundries ~10 g. Scintillator thickness assumed 10 mm (not dimensioned). Two detectors for coincidence ≈ 0.43 kg. **Weigh the real unit.** |
| C5 | Recovery system mass | — | kg | OPEN | |
| C6 | Tank dry mass | 10.61 | kg | DERIVED | From D6 geometry: 2700 × π(0.0762²−0.0727²) × 2.401. Not a guess. |
| C7 | Dry CG | derived | m | DERIVED | |
| C8 | Inertia I_xx, I_yy | derived | kg·m² | DERIVED | |
| C9 | Mass margin policy | +5 % | % | CONFIRMED | On structure, as used in the design record's derate ledger. |

## D. Oxidizer system

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| D1 | Oxidizer | N₂O, 99.9 % | — | CONFIRMED | Team spec |
| D2 | N₂O mass | 25.04 | kg | CONFIRMED | Solved so tank + grain exactly fill the body tube. docs/reference/02_BUDGET_50KFT_DESIGN.md |
| D3 | Tank internal volume | 0.0399 | m³ (39.9 L) | CONFIRMED | 6061-T6, 152.4 mm OD × 3.50 mm wall, 145.4 mm bore. |
| D4 | Initial fill fraction | 0.80 | — | CONFIRMED | **Safety limit, not packing.** 0.92 goes liquid-full at 27 °C; 0.80 clears 33.6 °C. |
| D5 | Initial tank temperature | = ambient (A2) | K | ESTIMATED | **Is pre-chill or pre-heat planned? Strongly affects tank pressure.** |
| D6 | Tank material / MEOP | 6061-T6, 70 bar | — | CONFIRMED | Burst SF 2.0 on ultimate. Above 56.5 bar vapour pressure at 25 °C, below 72.45 bar critical. |
| D7 | Feed line ID and length | — | m | OPEN | |
| D8 | Feed line pressure drop | neglected | — | ASSUMPTION | Only injector ΔP modeled. **Safe to neglect, or does line loss matter for chug?** |
| D9 | Main valve type / open time | — | s | OPEN | Affects ignition transient |
| D10 | Ullage non-condensables | 0.0 | frac | CONFIRMED | Negligible at 99.9 % purity; knob exists for sensitivity only |
| D11 | Tank thermal environment | adiabatic | — | ASSUMPTION | No heat leak into tank during burn. Valid for a ~6 s burn? |

## E. Injector

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| E1 | Injector type | showerhead, straight-drilled | — | CONFIRMED | Team spec |
| E2 | Number of orifices | 33 | — | CONFIRMED | Many small holes decouple the motor from the feed system. |
| E3 | Orifice diameter | 1.5 | mm | CONFIRMED | Effective flow area 38.3 mm². |
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
| F9 | Grain length | 349 | mm | CONFIRMED | docs/reference/02_BUDGET_50KFT_DESIGN.md |
| F10 | Initial port diameter | 69.2 | mm | CONFIRMED | 0.50 of grain OD. At n=0.5 this does not trade against apogee. |
| F11 | Grain OD / web thickness | 137.0 | mm (33.9 mm web) | CONFIRMED | 3.6 mm web left at burnout against a 3.0 mm threshold. **Burns through at a=0.150.** |
| F12 | Liner material and thickness | 3.0 mm under grain, 12.7 mm pre/post | m | CONFIRMED | Ablative. docs/reference/02_BUDGET_50KFT_DESIGN.md |
| F13 | Port geometry | single circular | — | CONFIRMED | Multi-port out of scope |
| F14 | Grain casting defects | ignored | — | ASSUMPTION | Uniform density assumed. **Is void content a real risk for cast paraffin?** |

## G. Chamber and nozzle

| ID | Parameter | Value | Units | Status | Basis / question for NASA |
|---|---|---|---|---|---|
| G1 | Post-combustion chamber | none | — | CONFIRMED | Team spec |
| G2 | Mixing diaphragm | none | — | CONFIRMED | Team spec |
| G3 | Pre-combustion chamber volume | 60 mm length (L/D 0.43) | m³ | CONFIRMED | Inside the 0.26–0.66 droplet-vaporisation stability band. |
| G4 | Throat diameter | 28.87 | mm (654.6 mm²) | CONFIRMED | Team value, supersedes the 28.96 mm in the design record. Falls out of the chamber mass balance at 36 bar. |
| G5 | Expansion ratio ε | 6.0 | — | CONFIRMED | Exit 70.9 mm. Sweep flat 4.5–8.0; 6.0 keeps margin against sea-level separation. |
| G6 | Nozzle material | graphite throat, silica-phenolic con/div | — | CONFIRMED | docs/reference/02_BUDGET_50KFT_DESIGN.md |
| G7 | Throat erosion | not modeled | — | ASSUMPTION | A_t held constant. **How much erosion is typical over a ~6 s N₂O burn? This could be significant.** |
| G8 | Nozzle contour / angles | 80 % bell, 45° convergence | deg | CONFIRMED | NASA SP-8115 standard convergence. |
| G9 | **`eta_cstar`** | **0.88** | — | **BANDED [0.82, 0.93]** | Showerhead, no post-combustion chamber. **Engineering estimate — no published range found for this exact configuration. Do they have data?** |
| G10 | `eta_Cf` | 0.96 | — | ESTIMATED | Adopted from the design record: 0.985 bell friction, less divergence loss and throat erosion. |
| G11 | CEA c\*/γ/T_c table | `data/cea_S10W1_N2O_35bar.csv` | — | CONFIRMED | Real NASA CEA O/F sweep at 35 bar for the S10W1 blend. Peak c\* 1598.1 m/s at O/F 7.00. Load with `cea.load_of_sweep(path, 35e5)`. Pinned by `tests/test_cea_real_table.py`. |

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
| I1 | CF skin E / G | 17.3 / 31.0 | GPa | CONFIRMED | E_x and G_xy at 45°, derived by CLT. Density 1570 kg/m³. **G > E is correct for ±45**, not an error — fibres lie along the principal shear directions, which is exactly what a flutter-critical fin wants. |
| I2 | CF ply thickness and layup | 1.981e-4 m, [(±45)₃/core/(±45)₃] | m | CONFIRMED | 3 fabric plies per side → 0.594 mm faces, leaving 5.161 mm of core. Woven fabric at 45° gives ±45 in one ply, so the stack is balanced and symmetric with no hand-orientation of tows. |
| I3 | Foam core type | — | — | OPEN | **Which foam? Divinycell, Rohacell, other?** |
| I4 | Foam core shear modulus | — | MPa | OPEN | **Dominates fin GJ — the single most important structural unknown** |
| I5 | Foam core density | — | kg/m³ | OPEN | |
| I6 | Aluminum tip alloy | 6061-T6 | — | CONFIRMED | Team decision. Tip mass still needs weighing once the cap is machined. |
| I7 | Al service temperature limit | 473 | K (200 °C) | CONFIRMED | Set by **over-ageing of the T6 temper**, not melting — the strengthening precipitates coarsen above ~200 °C and do not recover on cooling. Short-duration value, right for a ~40 s ascent. **Lower than the old 550 K default, so heating margin is tighter than it looked.** |
| I8 | Nose tip mass | — | kg | OPEN | Solid bonded aluminium cap. Drives the lumped-capacitance thermal response: a heavier tip heats more slowly. **Weigh it once machined.** |
| I8 | Fin root attachment | rigid | — | ASSUMPTION | Root fixity assumed perfect. **Real root compliance lowers flutter speed — how much margin to carry?** |
| I9 | Required flutter margin | ≥ 1.5 | — | CONFIRMED | Stated requirement. **Must be recomputed for CF/foam** — the source's 2.22 was for solid G10. |

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
| J10 | Max allowable landing speed | 7 | m/s | CONFIRMED | Design target achieved in the source. |

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

**112 parameters tracked.** Counts below are generated from this file, not
hand-tallied — regenerate with the script in `docs/README.md` after editing.

| Count | Status | Meaning |
|---|---|---|
| **18** | OPEN | No value yet. Model cannot run. |
| **0** | PLACEHOLDER | G11 resolved — the CEA table is in `data/`. |
| **3** | BANDED | E5, F8, G9. The dominant uncertainty. Band mode reports an envelope. |
| **13** | ASSUMPTION | Effects deliberately not modeled — worth a sanity check with them |
| **14** | ESTIMATED | Usable now; better data improves confidence |
| **59** | CONFIRMED | Locked by team decision |
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
