# What We Need — Goddard 26-27

**13 values block a trustworthy run.** This document sorts every one of them by
*how you get it*, so work can start in parallel instead of waiting on a meeting.

Coverage is verified: 13 blocking entries in the register, 13 assigned below,
no duplicates, none dropped. Regenerate the underlying list with
`run.bat check`.

> **Updated after the design-record intake.** 26 of the original 51 were
> answered by `docs/reference/02_BUDGET_50KFT_DESIGN.md` — see
> [`DESIGN_POINT.md`](DESIGN_POINT.md). **G11, the CEA table, is resolved**, so
> the model has no PLACEHOLDER left.
>
> Of the 25 remaining, the **7 material properties (I1–I7) are now the single
> largest block** and they gate the entire flutter and divergence calculation.

| # | Route | Count | Blocked on |
|---|---|---|---|
| ① | Team decides | **9** | nobody |
| ② | Motor sizing | **~~11~~ 1** | mostly solved by the design record |
| ③ | **Vendor datasheets** | **5** | **the foam core (I3–I5) and tip alloy (I6/I7)** |
| ④ | Run a tool | **~~1~~ 0** | ✅ CEA table delivered |
| ⑤ | Ask NASA / the range | **4** | the meeting |
| ⑥ | Recovery sizing | **5** | Knacke + a load limit from ⑤ |

---

## ① Team decides — 21 items, needs nobody

Design calls, not research. **Start here.** Every one of these unblocks
something downstream, and none require anyone outside the team.

| ID | Parameter | Units | Note |
|---|---|---|---|
| B2 | Body wall thickness | m | drives dry mass and buckling |
| B3 | Body tube length | m | 25-26 used 2.5 m overall |
| B5 | Nose fineness ratio L/D | — | ORK was ≈5.2 |
| B9 | Nose tip radius | m | drives stagnation heating directly |
| B14 | Fin root chord | m | planform *ratios* are locked; size is not |
| B15 | Fin span | m | |
| B16 | Fin thickness | m | **dominant flutter driver — enters as (t/c)³** |
| B17 | Fin cross-section | — | rounded vs double-wedge; model prices both |
| B19 | Fin fillet radius | m | helps root stress and interference drag |
| B20 | Surface roughness | µm | enters skin friction |
| C2 | Airframe material | — | CF or fiberglass |
| C3 | Avionics mass | kg | |
| C4 | Payload mass | kg | |
| C5 | Recovery system mass | kg | |
| D4 | Initial fill fraction | — | typically 0.80–0.85 liquid by volume |
| D7 | Feed line ID and length | m | |
| D9 | Main valve type / open time | s | affects ignition transient |
| F12 | Liner material and thickness | m | |
| G3 | Pre-combustion chamber volume | m³ | |
| G6 | Nozzle material | — | graphite? phenolic? |
| G8 | Nozzle divergence half-angle | deg | sets divergence loss |

**Suggested order:** B5/B9 (nose done — flare already removed), then B14/B15/B16/B17
(fins done, flutter becomes computable), then C2–C5 (mass model closes).

---

## ② Motor sizing — 11 items, and they do NOT decompose

| ID | Parameter | Units |
|---|---|---|
| D2 | N₂O mass | kg |
| D3 | Tank internal volume | m³ |
| C6 | Tank dry mass | kg |
| E2 | Number of orifices | — |
| E3 | Orifice diameter | m |
| E4 | Plate thickness (sets L/d) | m |
| F9 | Grain length | m |
| F10 | Initial port diameter | m |
| F11 | Grain OD / web thickness | m |
| G4 | Throat diameter | m |
| G5 | Expansion ratio ε | — |

**These are one coupled problem, not eleven decisions.** The loop:

```
throat area  ->  chamber pressure  ->  injector dP  ->  m_dot_ox
     ^                                                      |
     |                                                      v
  c*(O/F)  <-  O/F  <-  regression rate  <-  oxidiser flux
```

Change the throat and every other number moves. Picking them one at a time and
checking afterwards means dozens of manual iterations.

> ### Recommendation: reopen `size` mode
>
> We built forward-prediction-only by choice, and this is where that decision
> costs us. The architecture deliberately kept every entry point a pure
> `config → results` function so a solver wraps it **without a rewrite**.
>
> A `size` mode would drive chosen free variables until apogee = 50,000 ft
> subject to constraints (max Q, max g, flutter margin, rail exit, web
> remaining, chug margin). Roughly a day's work, and it turns 11 unknowns into
> a handful of stated constraints.
>
> **Ballpark from last year:** 82,000 N·s at 41% propellant fraction, 68.3 kg
> wet. Our frontal area is **44% smaller** (6″ vs 8″), so we should need
> meaningfully less impulse for the same altitude.

---

## ③ Vendor datasheets — 7 items

Pick suppliers, pull the TDS. No analysis required.

| ID | Parameter | Units | Source |
|---|---|---|---|
| ~~I1~~ | ~~CF skin E / G~~ | ✅ | **17.3 / 31.0 GPa**, density 1570 |
| ~~I2~~ | ~~ply thickness and layup~~ | ✅ | **1.981e-4 m, [(±45)₃/core/(±45)₃]** |
| I3 | Foam core type | — | Rohacell / Divinycell / other |
| I4 | **Foam core shear modulus** | MPa | **dominates fin GJ — the one that moves the flutter answer** |
| I5 | Foam core density | kg/m³ | foam datasheet |
| I6 | Aluminum tip alloy | — | 6061 vs 7075 |
| I7 | Al service temperature limit | K | MMPDS or vendor |

Until I1–I5 land, the flutter and divergence margins cannot be computed at all.

---

## ④ Run a tool — 1 item

| ID | Parameter | How |
|---|---|---|
| G11 | **CEA c\*/γ/T_c table** | Run **NASA CEA** (RP-1311, free) for the 89/10/1 paraffin blend vs N₂O across O/F 2–14 and P_c 1–5 MPa |

This is the only **PLACEHOLDER**. `props/cea.py` raises `PlaceholderData` rather
than guessing thermochemistry, so **the motor model cannot run at all without
it.** Highest value-per-hour item on the list.

**Not blocking but same category:** cross-check total C_D against **RASAero II**
at Mach 0.5 / 1.2 / 2.0 / 2.5. Supersonic wave drag is tagged `[U]` in
`equations.pdf` and every run emits a warning until this is done.

---

## ⑤ Ask NASA / the range — 7 items

**The actual meeting agenda.** Everything else above we can do ourselves.

| ID | Question | Why it matters |
|---|---|---|
| A6 | What rail/tower does the range provide? | Sets rail-exit velocity, hence minimum stable speed |
| A4 | What wind limits does the range impose? | Rail exit and weathercocking |
| C9 | What mass growth allowance at this design stage? | Standard practice question |
| D6 | Tank burst margin required? Al or COPV? | Safety-critical, drives C6 |
| I9 | **What flutter margin do you require?** | 1.5×? 2×? Changes fin thickness |
| J9 | **What opening-load limit should reefing be sized against?** | This is what J4 is solved for |
| J10 | Max allowable landing speed? | Range safety requirement |

### Also worth their time — not register entries, but higher-value

1. **Any regression-rate data for SEBS-MA-loaded paraffin?** (`F8`) Our largest
   performance unknown, and no static fire is planned.
2. **Access to cold-flow facilities?** (`E5`) Would convert `injector_Cd` from a
   banded guess into a measurement.
3. **How much throat erosion over a ~6 s N₂O burn?** Currently not modelled at
   all — could be significant.
4. **Any c\* efficiency data for a showerhead with no post-combustion chamber?**
   (`G9`) Our 0.88 is an engineering estimate, not a citation.

> **The honest framing.** No static fire and no cold flow are planned, so three
> constants are unmeasured and are *swept* rather than trusted. **Any test data
> against `regression_calibration`, `injector_Cd` or `eta_cstar` collapses the
> uncertainty band faster than any amount of additional modelling.** That is the
> ask.

---

## ⑥ Recovery sizing — 4 items

Single canopy, reefed → full. **No drogue** — the reefed stage does that job.

| ID | Parameter | Units | How |
|---|---|---|---|
| J3 | Canopy C_d·S (full open) | m² | sized for J10 landing speed |
| J4 | Reefing ratio | — | solved so reefed opening load ≤ J9 |
| J5 | Disreef trigger | m or s | altitude or timer — decide |
| J7 | Opening force coefficient C_x | — | Knacke, by canopy type |

Reefed drag area is `J3 × J4²`, so a 0.35 ratio gives ~12% of full area. **J4
is not a free choice — it is what you solve once J9 is known.**

---

## Usable right now from last year's repo

`itegoddard/Math-Model-25-26-` contains values we can adopt or anchor to today:

| Item | 25-26 value | Use as |
|---|---|---|
| `A4` wind | 5.0 m/s ground, shear α=0.15, ref 10 m, capped >5000 m | **adopt directly** |
| `J6` filling | measured inflation curve: 50% at 1.20 s, full at 2.30 s | **better than our n=8 estimate** |
| `C1` mass | 40.5 kg dry / 68.3 kg wet | anchor (theirs was 8″) |
| `B3` length | 2.5 m overall | anchor |
| `J3` chute | Cd 1.3, A = 4.15 m² **or** 8.3 m² | ⚠️ their own files disagree 2× — pick deliberately |
| Impulse | 82,000 N·s, 41% propellant fraction | sizing anchor for ② |

⚠️ **Do not inherit their atmosphere table.** `atmosphere.csv` spans 500–15,420 m
and `np.interp` *clamps* past the end — so a 50,000 ft flight from 1,231 m spends
its last ~1,050 m on frozen density with no error raised. Ours is analytic to
86 km specifically to avoid this.

---

## Critical path

```
1. Fin dimensions B14-B17     -> flutter becomes computable once (3) lands
2. Run NASA CEA (G11)         -> unblocks the entire motor model
3. Vendor datasheets I1-I5    -> unblocks flutter and divergence
4. NASA meeting (5)           -> J9 unblocks J4, I9 sizes the fins
5. Motor sizing (2)           -> needs G11 first; wants a solver
```

**Fastest single action:** run NASA CEA. It is one person, one afternoon, free,
needs no external input, and it is the only thing standing between us and a
motor model that runs at all.
