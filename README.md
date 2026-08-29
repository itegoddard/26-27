# Goddard 26-27 — Flight Performance Model

Modular flight-performance model for the Goddard 26-27 vehicle: a 6 in
diameter, single-stage, paraffin/N₂O hybrid sounding rocket targeting
**50,000 ft AGL** from White Sands Missile Range.

Replaces the `25-26 Math Model.xlsx` single-sheet time-march.

```bash
pip install -e ".[dev,report]"
python -m pytest                    # 227 tests
python -m goddard.cli check         # what still needs filling in
```

---

## Status

**All modules implemented. 227 tests, all green.**

| Package | Modules |
|---|---|
| `goddard/` | `units` · `dynamics` · `events` · `mass` · `recovery` · `sim` · `band` · `cli` |
| `goddard/env/` | `atmosphere` (US Std 1976, analytic 0–86 km) |
| `goddard/props/` | `n2o` (ESDU 91022) · `fuel` (89/10/1 blend) · `cea` |
| `goddard/config/` | `schema` + the `Open` sentinel |
| `goddard/motor/` | `tank` · `injector` · `grain` · `nozzle` · `chamber` |
| `goddard/aero/` | `geometry` · `drag` · `normal_force` · `roll` |
| `goddard/structures/` | `laminate` · `flutter` · `heating` |
| `goddard/report/` | `excel` · `plots` |

A full flight — launch, rail exit, max-Q, burnout, apogee, drogue, disreef,
landing — runs in about 1.5 s. Band mode's 27 corners take under a minute.

### What it still needs to produce a *trustworthy* number

The code is done; the inputs are not. Three things, in order of impact:

1. **Fill in `docs/assumptions_register.md`** — 54 OPEN parameters. This is the
   meeting artifact. `python -m goddard.cli check` lists them by register ID.
2. **Generate the CEA table** (register G11) for the 89/10/1 blend vs N₂O.
   `props/cea.py` raises `PlaceholderData` rather than guessing thermochemistry.
3. **Supply the ESDU 91022 latent-heat coefficients.** Needed by the tank
   blowdown and the Dyer HEM term. Both take it as an injected callable, so the
   physics is complete and tested — only the data is outstanding.

And one calibration task: **the supersonic wave-drag terms are unvalidated.**
`DragBuildup.validated` is `False`, every run emits a warning, and the warning
is carried into the Excel report. Cross-check total `C_D` against RASAero II or
CFD at Mach 0.5 / 1.2 / 2.0 / 2.5 before trusting an absolute apogee.

---

## Design principle

Every failure mode of the 25-26 spreadsheet is structurally impossible here, by
construction rather than by care:

| 25-26 defect | Structural fix |
|---|---|
| Mass flow 10× too large (`Mdot/10` against `dt = 0.01`) | Δt never appears as a literal; regression is unit-tested |
| `C_D` fixed at 0.5 through Mach 1.65 | Component build-up varying with Mach and Reynolds |
| Atmosphere table returned `#N/A` above 15,420 m | Analytic to 86 km — no table edge to fall off |
| Launch altitude hard-coded 524 m against a stated 1255 m | Single config field, referenced everywhere |
| Summary cells evaluated to `#NAME?` | Named exceptions; nothing returns a wrong number quietly |
| Sim spanned 50 s of a ~250 s flight | Runs to landing via bisection event detection |
| Spreadsheet was input, solver and report at once | Excel is a generated, read-only report |

**Nothing returns a plausible-looking wrong answer.** Where a value is
unverified the code raises:

```python
>>> RocketConfig().geometry.fins.root_chord_m * 2.0
OpenParameter: parameter B14 (fin root chord) [m] is OPEN -- it has no value yet.

>>> n2o.enthalpy_vaporisation(293.15)
NotImplementedError: requires the ESDU 91022 coefficient set, which has not
been verified. This raises on purpose rather than guessing.
```

Tests assert both keep raising, and `tests/test_register_sync.py` fails if the
schema and the assumptions register ever drift apart.

---

## The three unmeasured constants

No static fire and no cold flow are planned, so three constants are unmeasured:

| Constant | Nominal | Band | Register |
|---|---|---|---|
| `regression_calibration` | 0.85 | [0.75, 1.00] | F8 |
| `injector_Cd` | 0.70 | [0.61, 0.82] | E5 |
| `eta_cstar` | 0.88 | [0.82, 0.93] | G9 |

These are **swept**, not trusted. `band.py` runs a 3³ grid and reports an
envelope per metric, naming the corner that drives each worst case.

That matters because **"conservative" has no single direction here.** Oxidiser
flow is set by the tank and injector, not the grain, so *lower* regression means
*less fuel* and therefore a **higher** O/F. Since c\* peaks near O/F 7–8, the
sign of the apogee effect flips depending on which side of that peak the design
sits. And the two directions threaten different things:

```
regression BELOW nominal  ->  apogee shortfall, lean O/F, chug margin
regression ABOVE nominal  ->  port burnthrough
```

A single scalar biased for apogee would leave burnthrough unexamined. See spec
§6.1 — that section is signed off and marked not to be simplified away.

---

## Layout

```
goddard/            model package
tests/              227 tests
docs/
  superpowers/specs/2026-08-28-goddard-math-model-design.md   approved design
  assumptions_register.md      112 parameters, 54 OPEN  <- the meeting artifact
  assumptions_register.csv     fillable; regenerate with tools/
  references.bib               31 sources, grouped by module
  references_dois.txt          13 DOIs, 11 publisher-verified
tools/build_register_csv.py    regenerates the CSV and status counts
25-26 Math Model.xlsx          predecessor, kept for reference
goddard1.0.ork                 OpenRocket source of the confirmed shape
```

## Running it

```bash
python -m goddard.cli check                              # unfilled parameters
python -m goddard.cli run  --config myconfig --out out/  # single flight
python -m goddard.cli band --config myconfig --out out/  # 27-corner sweep
```

A config module must define `build_vehicle()` returning a `sim.Vehicle`. None
exists yet — that is what the register unblocks. `tests/conftest.py` shows the
shape of one, with placeholder numbers that are **not** design values.
