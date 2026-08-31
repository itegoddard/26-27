# Goddard 26-27 — Flight Performance Model

Modular flight-performance model for the Goddard 26-27 vehicle: a 6 in
diameter, single-stage, paraffin/N₂O hybrid sounding rocket targeting
**50,000 ft AGL** from White Sands Missile Range.

Replaces the `25-26 Math Model.xlsx` single-sheet time-march.

---

## Quick start

### Step 1 — get the code onto your computer

> ⚠️ **Clicking `run.bat` here on GitHub will not run it.** GitHub only shows
> you the file's text. You must download the project first.

Pick one:

**Git** (recommended — makes updates a one-liner later):
```bat
git clone https://github.com/itegoddard/26-27.git
cd 26-27
```

**No git?** On this repo's GitHub page click the green **Code** button →
**Download ZIP**, then **right-click the ZIP → Extract All**. Open the extracted
folder.

> Windows will let you look inside a ZIP without extracting, and `run.bat` will
> fail if you launch it from there. Extract it properly first.

### Step 2 — double-click `run.bat`

**You do not need to touch a terminal.** In the folder you just downloaded,
double-click **`run.bat`** and pick a number:

```
  ========================================================
    Goddard 26-27 Flight Model
  ========================================================

    [ First run? Choose 6 to set up. ]

    1.  Check      - what still needs filling in
    2.  Simulate   - one flight, writes Excel + plots
    3.  Band       - 27-corner calibration sweep
    4.  Show       - open the last results
    5.  Test       - run the test suite
    6.  Setup      - create .venv and install dependencies
    7.  Doctor     - diagnose the environment
    8.  Exit
```

**First time?** Run **6 (Setup)** once, then **2 (Simulate)**.

Setup builds a project-local `.venv`, so it works on locked-down machines where
global `site-packages` is not writable, and it cannot collide with other Python
projects. If anything misbehaves, **7 (Doctor)** prints what it found.

### If something goes wrong

| Symptom | Cause and fix |
|---|---|
| *"Windows protected your PC"* | Windows flags files downloaded from the internet. Click **More info → Run anyway**, or right-click `run.bat` → **Properties** → tick **Unblock** → **OK**. |
| Window flashes and vanishes | You are running it from inside the ZIP preview. Extract the folder first. |
| *"run.bat is not inside the project folder"* | Only `run.bat` was downloaded. Get the whole repo — the script prints the clone command. |
| *"Python was not found"* | Install Python 3.10+ from [python.org](https://python.org/downloads) and tick **Add python.exe to PATH**. |
| Anything else | Run **7 (Doctor)** — it reports interpreter, venv and package state. |

Option **2** runs a flight and then opens the Excel workbook and the plots
folder for you automatically. Results land in `out/`:

| Output | Contents |
|---|---|
| `out\goddard_results.xlsx` | Summary · Events · Trajectory (~2,700 rows × 13) · Motor |
| `out\plots\` | altitude · mach · acceleration · dynamic_pressure · drag_coefficient · static_margin · roll_rate · chug_margin · motor |

### Or from a terminal

`run.bat` also takes an argument, so nothing has to be typed twice:

```bat
run.bat setup                                   :: create .venv, install deps
run.bat check                                   :: unfilled parameters
run.bat sim                                     :: one flight + open results
run.bat band                                    :: 27-corner sweep
run.bat show                                    :: reopen last results
run.bat test                                    :: 227 tests
run.bat doctor                                  :: diagnose the environment
run.bat sim goddard.config.goddard_v2           :: use a specific config
```

**Portability.** It `cd`s to its own folder first, so spaces in the path never
cause trouble and it works from any working directory. It finds Python via `py`,
`python`, or `python3` — whichever the machine has — and installs into `.venv`
rather than global site-packages. `.gitattributes` forces `*.bat` to CRLF on
checkout, because cmd.exe mis-parses `goto` in an LF-only batch file and the
menu silently never appears.

### Python directly

```bash
pip install -e ".[dev,report]"
python -m pytest                    # 227 tests
python -m goddard.cli check         # what still needs filling in
python -m goddard.cli run  --config goddard.config.demo_placeholder --out out
python -m goddard.cli band --config goddard.config.demo_placeholder --out out
```

> ⚠️ **The demo config produces meaningless numbers.**
> `goddard/config/demo_placeholder.py` exists only so you can *see the report
> format* before the real parameters are known. Every value in it is invented —
> it is the apogee of a rocket nobody is building. `run.bat` prints a warning
> box before every demo run. Delete that file once a real
> `goddard/config/goddard_v2.py` exists.

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
run.bat                        <- double-click this
goddard/                       model package
  config/demo_placeholder.py   invented numbers, for previewing the report only
tests/                         227 tests
out/                           generated results (gitignored)
docs/
  superpowers/specs/2026-08-28-goddard-math-model-design.md   approved design
  assumptions_register.md      112 parameters, 54 OPEN  <- the meeting artifact
  assumptions_register.csv     fillable; regenerate with tools/
  references.bib               31 sources, grouped by module
  references_dois.txt          13 DOIs, 11 publisher-verified
tools/build_register_csv.py    regenerates the CSV and status counts
goddard1.0.ork                 OpenRocket source of the confirmed shape
```

The predecessor `25-26 Math Model.xlsx` has been removed. It remains in git
history at commit `648e0b8` if it is ever needed:

```bat
git show 648e0b8:"25-26 Math Model.xlsx" > old_model.xlsx
```

---

## Writing a real config

A config module defines `build_vehicle()` returning a `sim.Vehicle`. Copy
`goddard/config/demo_placeholder.py` to `goddard/config/goddard_v2.py`, replace
every invented number with a register value, then:

```bat
run.bat sim goddard.config.goddard_v2
```

`run.bat check` lists what is still missing, by register ID, so the register and
the config can be filled in together.

Note `check` reports **60** blocking fields against the register's **54** OPEN
entries. Not a discrepancy — a few register entries map to more than one schema
field (B6 is both the nose base diameter and the flare fore diameter). 54 is the
number of distinct questions to answer; 60 is the number of slots to fill.
