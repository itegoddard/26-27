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
    8.  Equations  - validate every equation, open the PDF
    9.  Exit
```

**First time?** Run **6 (Setup)** once, then **2 (Simulate)**.

The menu **stays open after each action**, so you can run 6 and then 2 in the
same window without relaunching. Only **8 (Exit)** closes it.

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
run.bat test                                    :: 257 tests
run.bat equations                               :: validate equations, open PDF
run.bat doctor                                  :: diagnose the environment
run.bat sim goddard.config.demo_placeholder     :: override the config
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
python -m pytest                    # 257 tests
python -m goddard.cli check         # what still needs filling in
python -m goddard.cli run  --config goddard.config.goddard_v1 --out out
python -m goddard.cli band --config goddard.config.goddard_v1 --out out
```

**`run.bat` now runs the real vehicle** — `goddard/config/goddard_v1.py` —
and prints which values are still provisional before every run.

> `goddard/config/demo_placeholder.py` is still there for format previews, but
> every number in it is invented. You have to ask for it explicitly now.

---

## Status

**All modules implemented. 257 tests, all green.**

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

A full flight — launch, rail exit, max-Q, burnout, apogee, chute deploy, disreef,
landing — runs in about 1.5 s. Band mode's 27 corners take under a minute.

### Where it stands — see [`docs/STATUS.md`](docs/STATUS.md)

**Every register parameter is answered.** `run.bat check` reports *"All
parameters filled."* What remains is not missing inputs:

**Two constraints failing** — design problems, printed after every run and
written to the workbook's Constraints sheet:

```
FAIL  rail exit velocity (m/s)      24.01  vs 25.00
FAIL  min chug margin                0.73  vs  1.00
```

They want opposite fixes: rail wants more initial thrust, chug wants more
injector stiffness at the end of the burn.

**One placeholder** — the N₂O latent heat (register D12) is an unverified
stand-in, because the ESDU 91022 coefficients could not be checked. It sets tank
chilling, hence thrust taper and burn time, so it touches everything downstream.
Every run says so.

**The largest model error is supersonic drag.** Mine runs 29–51 % high through
the transonic against the working model. Substituting their curve — nothing else
changed — moves apogee +4,488 ft and lands within 3.2 % of their published
number. A RASAero II cross-check is worth more than any other single analysis
task.

---

## The equations

**[`docs/equations.pdf`](docs/equations.pdf)** states every governing equation in
the model, so the physics can be reviewed without reading Python. Each equation
names the module implementing it and carries a confidence tag:

| Tag | Meaning |
|---|---|
| **[E]** | Established — analytic, or a long-standing published correlation |
| **[A]** | Engineering approximation — right form and magnitude, calibrated constants |
| **[U]** | **Not validated** — used because something is needed, not yet checked against data |

`run.bat equations` runs **95 independent checks** against that document and then
opens it. These don't re-run the model and check it agrees with itself — each one
re-derives the result a different way: against published tables, by inverting an
analytic relation, by high-resolution quadrature, by limiting case, or by a
defining property (net rolling moment must be *exactly* zero at the equilibrium
roll rate; the chamber root must satisfy its own balance equation).

They confirm each equation is implemented as written. They **cannot** confirm an
approximate correlation is the *right* correlation — that's what the [U] tags are
for, and supersonic wave drag is the one that matters.

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
data/
  cea_S10W1_N2O_35bar.csv      NASA CEA sweep -- resolves register G11
payload/                       CosmicWatch muon detector (CC BY-NC, see its README)
docs/
  STATUS.md                    failing constraints, what the model rests on
  DESIGN_POINT.md              values from the reference docs, conflicts flagged
  reference/                   design record and literature (sources, not model)
  WHAT_WE_NEED.md              8 blocking values, sorted by how to get them
  equations.pdf                every governing equation  <- start here
  equations.tex                its source
  superpowers/specs/2026-08-28-goddard-math-model-design.md   approved design
  assumptions_register.md      113 parameters, 8 OPEN  <- the meeting artifact
  assumptions_register.csv     fillable; regenerate with tools/
  references.bib               31 sources, grouped by module
  references_dois.txt          13 DOIs, 11 publisher-verified
tools/build_register_csv.py    regenerates the CSV and status counts
tools/validate_equations.py    95 independent equation checks
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

Note `check` reports **55** blocking fields against the register's **51** OPEN /
PLACEHOLDER entries. Not a discrepancy — a few register entries map to more than one schema
field. 51 is the number of distinct questions to answer; 55 is the number of
slots to fill.
