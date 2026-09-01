# Design Point — extracted from the new reference documents

Source: `02_BUDGET_50KFT_DESIGN.md` (+ `04_ENGINE_DESIGN.md`, `NOZZLE_DESIGN.md`,
`01_NOSECONE_AVIONICS_REFERENCE.md`, `cea_S10W1_N2O_35bar.csv`).

Every value below is mapped to its register ID. **All three conflicts in §C are
resolved and everything here is now applied** — the register went from 51
blocking entries to 25, and the model has no PLACEHOLDER left.

Section A is retained as the audit trail: what came from where.

**Headline:** 61,962 ft nominal, **53,298 ft after every derate** — 6.6 % above
the 50,000 ft target. 54,357 N·s (class O), 61.14 kg liftoff, 4.362 m long,
aluminium stacked-pressure-vessel architecture, ~$5,740.

The document is internally consistent — I re-derived the exit diameter
(√6 × 28.96 = 70.9 mm ✓), the tank volume (25.04 kg ÷ 785.1 ÷ 0.80 = 39.9 L ✓)
and the fin thickness ratio (6.35/200 = 3.17 % ✓) and they all close.

---

## A. Applied — was OPEN, now CONFIRMED

### Geometry

| ID | Parameter | Value | Note |
|---|---|---|---|
| B2 | Body wall thickness | 2.4 mm fibreglass | non-structural, only 0.45 m of it |
| B3 | Body tube length | **3.60 m** | master design variable; 3.247 m would hit nominal, 3.60 m survives the derates |
| B5 | Nose fineness ratio | **5.0** (762 mm) | changed up from 4.33 in the earlier reference |
| B9 | Nose tip radius | **3.81 mm** | derived: 5 % bluffness × 152.4 mm ÷ 2 |
| B14 | Fin root chord | **200 mm** | |
| B15 | Fin span | **109.7 mm** | *solved* from the 2.0-caliber stability target, not chosen |
| B16 | Fin thickness | **6.35 mm** | 3.17 % of root, inside the 3–6 % rule |
| B17 | Fin cross-section | **hexagonal**, flat tip | resolves the rounded-vs-wedge question |
| B20 | Surface roughness | — | still missing |

### Mass and structure

| ID | Parameter | Value |
|---|---|---|
| C2 | Airframe material | 6061-T6 aluminium pressure vessels carry the airframe; fibreglass tube elsewhere; fibreglass nose (RF-transparent, antennas inside) |
| C9 | Mass margin policy | +5 % on structure (used in the derate ledger) |

### Oxidiser system

| ID | Parameter | Value |
|---|---|---|
| D2 | N₂O mass | **25.04 kg** |
| D3 | Tank internal volume | **39.9 L** (0.0399 m³) |
| D4 | Initial fill fraction | **0.80** — a *safety* limit, not packing. 0.92 goes liquid-full at 27 °C |
| D6 | Tank material / MEOP | 6061-T6, 152.4 mm OD × 3.50 mm wall, 145.4 mm bore, MEOP 70 bar, burst SF 2.0 |

### Injector

| ID | Parameter | Value |
|---|---|---|
| E2 | Orifice count | **33** |
| E3 | Orifice diameter | **1.5 mm** |
| E4 | Orifice geometry | sharp entrance, short tube — *the geometry Dyer's NHNE model was validated on* |

### Grain

| ID | Parameter | Value |
|---|---|---|
| F9 | Grain length | **349 mm** |
| F10 | Initial port diameter | **69.2 mm** (0.50 of grain OD) |
| F11 | Grain OD | **137.0 mm** → 33.9 mm web, 3.6 mm left at burnout |
| F12 | Liner | 3.0 mm under the grain, 12.7 mm pre/post chamber |

### Nozzle — and the CEA table

| ID | Parameter | Value |
|---|---|---|
| G3 | Pre-combustion chamber | 60 mm length (L/D 0.43) |
| G4 | Throat diameter | **28.96 mm** (658.7 mm²) |
| G5 | Expansion ratio | **6.0** (exit 70.9 mm) |
| G6 | Nozzle material | graphite throat, silica-phenolic convergent/divergent |
| G8 | Contour | 80 % bell; **45° convergence half-angle** (NASA SP-8115) |
| **G11** | **CEA table** | **`cea_S10W1_N2O_35bar.csv` — the PLACEHOLDER is resolved** |

### Requirements we'd been meaning to ask NASA for

| ID | Value |
|---|---|
| I9 | Flutter margin **≥ 1.5** (design achieves 2.22 worst-case at 6,606 m) |
| J9 | Main opening load ~1.3 kN |
| J10 | 7 m/s at touchdown |

---

## B. Changes a current default

| Our value | Theirs | Verdict |
|---|---|---|
| `regression_calibration` **0.85** | 0.132/0.155 = **0.8516** | **Independent agreement.** We derated on a melt-viscosity argument; they did the same from Bisin 2019 Table 1 and landed within 0.2 %. |
| `eta_cstar` **0.88** | **0.90** | Adopt 0.90 as nominal? Their band (Zilliac: 0.55–0.97) is wider than ours. Note their own derate ledger *drops it back to 0.88* — so 0.88 is the derated case, 0.90 the nominal. |
| `eta_cf` **0.97** | **0.96** | Adopt 0.96 — theirs accounts for divergence loss and throat erosion. |
| Fuel density **932.4** kg/m³ | **927.8** kg/m³ | Adopt 927.8 — SasolWax 0907 specific, not generic paraffin. |
| CEA γ placeholder **1.20** | **1.1594** at peak c\* | Comes free with G11. |
| Synthetic c\* peak 1600 @ O/F 7.0 | **1598.1 @ O/F 7.00** | My invented table was accidentally almost exact. |

**A finding worth keeping:** peak c\* for 89/10/1 is 1598.1 m/s; for 99 % wax + 1 %
carbon black it is 1598.5. **The SEBS-g-MA is thermochemically invisible** — it
costs regression rate, not specific impulse. Nobody should argue it costs Isp.

---

## C. Conflicts — RESOLVED by team decision

All three were put to the team and decided. Applied as noted.

### C1. Fin planform — contradicts B12 and B13

| | Locked (from the ORK) | New document |
|---|---|---|
| Taper ratio | **0.328** | **0.425** (85/200) |
| LE sweep | **62°** | **50°** |

You told me *"Fin shape is 100% confirmed"* from `goddard1.0.ork`, and B12/B13 are
marked CONFIRMED on that basis. The new document **solves** the semi-span from a
2.0-caliber stability target and reports that the earlier fin *"failed fin
flutter"* and was *"badly over-stable at 4.3 calibers"*.

> ### ✅ RESOLVED: the OpenRocket file is wrong. New planform adopted.
>
> B12 → **0.425**, B13 → **50°**, B14 → **200 mm**, B15 → **109.7 mm**,
> B16 → **6.35 mm**, B17 → **hexagonal**. The ORK planform is superseded and
> the register records why: it was simultaneously over-stable and
> flutter-critical.

### C2. Fin construction — contradicts your original spec

| | Original spec | New document |
|---|---|---|
| Material | **Carbon fibre skins, foam core** | **G10 fibreglass, 6.35 mm solid sheet** |

You specified *"carbon fibre fins with foam interior to minimize fin flutter."*
The document specifies solid G10.

> ### ✅ RESOLVED: carbon fibre with foam core is correct. G10 rejected.
>
> `structures/laminate.py` stays and earns its place — the sandwich `GJ`
> calculation is exactly what this construction needs. **I1–I5 remain OPEN**
> and are now the largest single block of missing values.
>
> **Carries an important caveat.** The source sized the fin as solid G10 and
> reports a worst-case flutter margin of **2.22**. That number does **not**
> transfer: a CF/foam sandwich has a completely different `GJ`. The *planform*
> is adopted; the *aeroelastic result* must be recomputed once I1–I5 land. This
> is recorded in the schema, the register (B16, I9) and here, because it is
> exactly the kind of inherited number that silently becomes wrong.

### C3. Recovery architecture — contradicts what you told me an hour ago

| | You said | New document |
|---|---|---|
| Architecture | **Single canopy, reefed → full** | **Dual deployment: drogue 0.58 m at apogee + main 2.48 m at 450 m** |

I rewrote `recovery.py` for single-stage reefed this session (commit `4e004fd`),
removing the drogue and register J2. The document describes two separate canopies
and no reefing at all.

> ### ✅ RESOLVED: single canopy, reefed → full. The document is wrong here.
>
> `recovery.py` is unchanged. The dual-deployment numbers in the source
> (0.58 m drogue, 2.48 m main at 450 m) do **not** apply, so J3/J4/J5/J7/J9
> stay OPEN and must be sized for the reefed architecture.
>
> J10 (7 m/s touchdown) **does** carry over — it is a requirement, not an
> artefact of the architecture.

---

## D. Still missing after all this

| ID | Parameter | Note |
|---|---|---|
| A4 | Mean wind speed | last year's repo has 5.0 m/s, α=0.15 — adoptable |
| A6 | Launch rail length | only "rail exit T/W 5.76" is given, not the length |
| B20 | Surface roughness | |
| C3 | Avionics mass | architecture is specified, mass is not |
| C4 | Payload mass | |
| C5 | Recovery system mass | |
| C6 | Tank dry mass | derivable from D6 geometry |
| D7 | Feed line ID and length | |
| D9 | Main valve type / open time | |
| E4 | Plate thickness | qualitative only ("short tube"); need the number for L/d |
| I6 | Aluminium tip alloy | |
| I7 | Al service temperature limit | |
| J4/J5/J7 | Reefing parameters | moot if C3 resolves to dual-deploy |

Plus **I1–I5** (CF/foam properties) — which vanish if C2 resolves to G10.

---

## E. What their own document says must be measured

Their priority order, which matches ours almost exactly:

1. **Regression rate coefficient** — slab burner. *"At 0.150 the grain burns
   through."* Their own burn-through table shows the design at 0.132 leaves
   3.6 mm of web and 0.150 leaves 0.4 mm. **This is spec §6.1's high-regression
   corner, independently arrived at.**
2. **Injector discharge by cold flow** — *"no two-phase model is reliable enough
   to skip it."* $450 on their cost list.
3. **c\* efficiency by static fire** — *worth ~10× more apogee per point than
   anything else in the derate ledger.*
4. Cast grain density and void content.
5. Tank proof test.
6. Radio link, 30–45 min on the ground.

Their derate ledger is worth internalising:

```
Nominal                          61,962 ft
c* efficiency 0.90 -> 0.88       59,139 ft   -2,823   <- dominates
Structure mass +5 %              57,926 ft   -1,213
Drag coefficient +10 %           53,706 ft   -4,219   <- our [U] wave-drag tag
Launch rail 5 deg off vertical   53,298 ft     -408
```

Note the **−4,219 ft** for a 10 % drag error. That is precisely the uncertainty
our unvalidated supersonic wave-drag terms carry, and it is the second-largest
line in their ledger. The RASAero cross-check is worth more than it looked.
