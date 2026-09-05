# Model Status

Where the model stands, what it is standing on, and what is failing.
Regenerate the numbers with `run.bat sim`.

---

## Two constraints are failing

```
FAIL  rail exit velocity (m/s)      24.01  vs 25.00
FAIL  min chug margin                0.73  vs  1.00
PASS  min static margin (cal)        1.96  vs  1.50
PASS  min web remaining (%)         18.34  vs  5.00
PASS  min flutter margin             4.78  vs  1.50
PASS  min divergence margin          4.52  vs  1.50
```

These are **design** problems, not missing data. Every register parameter is
answered.

### Rail departure velocity — 24.01 m/s against 25.0 required

**Worse than the headline.** 24.01 assumes the full 5.2 m rail is effective.
Effective length ends where the vehicle first becomes free in pitch, so it is
shorter by the rail-button spacing:

| Button spacing | Effective | Exit velocity |
|---|---|---|
| 0.3 m | 4.9 m | 23.3 m/s |
| 0.5 m | 4.7 m | **22.8 m/s** |
| 0.8 m | 4.4 m | 22.1 m/s |

Realistically **9–12 % under**, not 4 %.

**Compliance.** An IREC requirement, not a guideline. A design that misses it
does not pass review, independently of whether the vehicle would fly acceptably.

**Physics.** At 24 m/s in the 5 m/s design wind the vehicle leaves the rail at
**11.8° angle of attack**; in the 10 m/s limit gust, **22.6°**. The second is
outside the small-angle range the Barrowman model is valid in. That is the
moment the vehicle has least authority and most disturbance, which is why the
requirement exists. Consequences run from weathercocking — apogee loss and
downrange dispersion — to an unsafe departure angle in a gust.

**Note the failure mode that hid this.** The model was checking thrust-to-weight
≥ 5.0, which is a *proxy*. The real requirement is on velocity. The proxy passed
while the requirement failed, and nothing was looking.

### Chug margin — 0.73, and the shape matters more than the number

Not one marginal instant. **Below the criterion for 5.3 s of a 14.9 s burn —
36 % of it** — from t = 9.6 s, worsening monotonically to 0.146 at 27.5 bar.

Chug is feed-system/chamber coupling: the injector is not stiff enough to
decouple them, so chamber pressure and feed flow oscillate together at low
frequency, typically 10–100 Hz. Outcomes span:

- **Mild** — rough burn, degraded c\*, apogee loss
- **Moderate** — pressure oscillation fatiguing feed-line and tank joints
- **Severe** — structural failure of the feed system or chamber

A margin number cannot tell you which. That is why the criterion is a floor.

**The timing is the dangerous part.** It fails at the *end* of the burn as tank
pressure decays, so everything looks healthy at ignition. The design record says
the same: *"Worst at the END of the burn, when tank pressure has decayed — that
is where teams get chug."*

Feed-line loss is included: 1 in OD × 0.065 wall stainless at K ≈ 3 costs
0.11 bar at end-of-burn flow, moving ΔP/P_c from 0.152 to **0.146**, through the
0.15 floor. Small in absolute terms, decisive because the margin sits on its
limit.

### They want opposite fixes

Rail wants **more initial thrust**. Chug wants **more injector stiffness at the
end of the burn**. Larger injector area helps the first and hurts the second.
Higher tank pressure helps both but costs fill fraction — and 0.80 is a *safety*
limit, not a packing choice, so there is no room there.

The lever that might serve both is a **smaller throat**: it raises chamber
pressure and thrust, but also raises the chug denominator, so the net needs
computing rather than arguing. Two constraints, two-plus variables, opposed
gradients — this is what `size` mode is for.

---

## Behind the numbers

Every register parameter is answered, but *filled* and *measured* are not the
same thing. What the model actually rests on:

| Count | Status | Meaning |
|---|---|---|
| 71 | **CONFIRMED** | Sourced or team-decided |
| 8 | **DERIVED** | Computed from confirmed values |
| 16 | **ESTIMATED** | Engineering judgement with a stated basis |
| 13 | **ASSUMPTION** | Physics deliberately not modelled |
| 3 | **CONVENTION** | Tabulated default, not fetched for this vehicle |
| 3 | **BANDED** | Never measured. Swept, not trusted. |
| **1** | **PLACEHOLDER** | **D12 — see below** |

### D12 — the N₂O latent heat

**The only placeholder left, and it was not tracked here until the register was
audited against the code.** This document previously claimed zero placeholders
while the model stood on a substitute.

`props.n2o.enthalpy_vaporisation` raises: the ESDU 91022 latent-heat
coefficients could not be verified. `goddard_v1._latent_heat` supplies a
physically-shaped stand-in — latent heat falling to zero at the critical point —
so the tank blowdown can run at all.

**It is not cosmetic.** It sets the tank chilling rate, hence the thrust taper,
hence burn time. That propagates into apogee, into where the chug margin bottoms
out, and into web remaining.

**To clear it:** take the coefficients from ESDU 91022 and verify against
~376 kJ/kg at the normal boiling point (184.65 K) and ~145–150 kJ/kg at 293.15 K
*before* trusting any result. `tests/test_n2o.py` asserts the function keeps
raising until that is done.

### The three BANDED constants

No static fire and no cold flow are planned, so these are swept rather than
trusted. Sensitivity measured on this vehicle:

| Constant | Nominal | Band | Apogee across the band |
|---|---|---|---|
| `eta_cstar` | 0.88 | 0.82–0.93 | 49,256 → 67,178 ft — **17,922 ft** |
| `regression_calibration` | 0.85 | 0.75–1.00 | 54,859 → 61,256 ft — 6,397 ft |
| `injector_Cd` | 0.70 | 0.61–0.82 | swept in band mode |

c\* efficiency is the single largest uncertainty in the model. A static fire
collapses it faster than any amount of further modelling.

### The three CONVENTION values

Standard tabulated defaults, not fetched for this vehicle. Usable; verify.

- **surface roughness** 7.5 µm — well-finished student airframe is 5–10 µm
- **mean wind** 5 m/s with a 10 m/s limit case — Spaceport America publishes
  real site statistics, use those
- **main valve opening time** 0.15 s — pneumatic ball valve range is 0.05–0.3 s

---

## The largest remaining model error: supersonic drag

Not a missing input — a **systematic bias** silently in every number.

`DragBuildup.validated` is `False` and every run warns, but nothing quantified
it until now. Against the working model's lumped curve at actual flight
conditions:

| Mach | theirs | mine | ratio |
|---|---|---|---|
| 0.50 | 0.42 | 0.36 | 0.85 |
| 0.95 | 0.58 | 0.75 | 1.29 |
| **1.05** | 0.68 | **1.03** | **1.51** |
| 1.20 | 0.63 | 0.81 | 1.28 |
| 2.00 | 0.44 | 0.46 | 1.04 |

At Mach 2 we agree to 4 %. Through the transonic mine runs **29–51 % high**.

**Swapping only the drag model, everything else identical:**

| | Apogee |
|---|---|
| my component build-up | 58,265 ft |
| their lumped curve | 62,753 ft (**+4,488**) |
| their published run | 60,829 ft |

Substituting their curve lands within **1,924 ft (3.2 %)** of their number. That
is strong evidence the drag model is the dominant remaining error and the rest
of the model is sound.

**Neither curve is validated.** Theirs is a hand-fit high-power-rocketry curve
by their own description; mine is an unvalidated component build-up. A RASAero II
cross-check at Mach 0.5 / 1.2 / 2.0 / 2.5 settles it in an afternoon and is
worth more than any other single analysis task.

### Why drag before c\* efficiency

c\* efficiency spans a wider range (17,922 ft against drag's ~4,500 ft per 10 %),
but the two are different kinds of problem:

- c\* efficiency is a **measurement** gap. It is honestly represented — band mode
  reports the envelope — and closing it needs a static fire.
- Drag is an **error**, of known sign and roughly known size, presenting itself
  as a value. It biases every single run and nothing reports it.

An honest wide band is safer than a confident wrong number.

---

## Sensitivities, measured

For sizing decisions, from the current design point (58,265 ft):

| Change | Apogee |
|---|---|
| C_D × 0.70 | +18,775 ft |
| C_D × 0.90 | +5,285 ft |
| C_D × 1.10 | −4,499 ft |
| C_D × 1.30 | −11,614 ft |
| `eta_cstar` 0.82 | −9,009 ft |
| `eta_cstar` 0.93 | +8,913 ft |
| `regression_calibration` 0.75 | −3,406 ft (web 26.5 %) |
| `regression_calibration` 1.00 | +2,991 ft (web 6.9 %) |

Note the last line: at the top of the regression band the web margin drops to
6.9 %, approaching the burnthrough case that spec §6.1 exists to keep visible.
