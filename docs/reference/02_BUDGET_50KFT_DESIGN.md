# Budget 50,000 Foot Design Point — Every Value, Evaluated and Referenced

**Vehicle:** 6.00 inch diameter, 14.31 foot single-stage sounding rocket
**Motor:** nitrous oxide / paraffin hybrid, impulse class O
**Fuel (fixed by requirement):** 89 wt% SasolWax 0907 paraffin, 10 wt% SEBS-g-MA, 1 wt% carbon black
**Oxidiser (fixed by requirement):** nitrous oxide, self-pressurising
**Objective:** 50,000 feet at the lowest achievable build cost

Companion documents: `00_HYBRID_ENGINE_REFERENCE.md`, `01_NOSECONE_AVIONICS_REFERENCE.md`, `CEA_and_CFD_guide.md`.
Working models: `analysis/budget_design_50kft.py`, `analysis/airframe_recovery_avionics.py`.

---

## 0. The headline

The previous baseline was published at a 3.20 m body tube and reached 50,932 ft.
Comparing against it directly would be unfair, because this design uses a longer
tube. **The honest comparison is both architectures at the same 3.60 m body tube:**

| At an equal 3.60 m body tube | Carbon fibre architecture | Aluminium architecture |
|---|---|---|
| Dry mass | 39.76 kg | **32.55 kg** |
| Liftoff mass | 71.30 kg | **61.14 kg** |
| Oxidiser carried | 27.74 kg | 25.04 kg |
| Tank fill fraction | 0.92 — **liquid-full at 27 °C** | 0.80 — safe to 33.6 °C |
| Nominal apogee | 62,209 ft | 61,962 ft |
| Estimated build cost | ~$10,600 | **~$5,740** |

**Read that table carefully, because the interesting result is the one that looks
like nothing happened.** The aluminium architecture is **7.2 kg lighter dry**, and
it gives back 2.7 kg of oxidiser to the safe fill fraction. Those two effects very
nearly cancel: apogee lands within 247 ft — four tenths of one percent — of the
composite design. So the trade is not "cheaper but slower". It is:

> **The same altitude, for 46 % of the cost, and it is the only one of the two
> that can be filled safely.**

**The single change that did the most:** deleting the inner wall. The previous
architecture paid for two structural walls over the same two metres — a carbon
fibre pressure vessel living inside a carbon fibre body tube. Making the
aluminium oxidiser tank and the aluminium combustion chamber case carry the
airframe loads over their own length removes 2.9 m of body tube entirely. This is
the stacked-pressure-vessel architecture flown by the Hybrid Experimental Rocket
Stuttgart (HEROS 3, 32.3 km, S30) and by Phoenix-1B (S26). Aluminium at the same
152.4 mm outer diameter gives a 145.4 mm bore against the 144 mm a composite tank
would have offered, so **the metal tank costs no internal volume at all** — it is
paid for entirely by the body tube it replaces.

### As-built figures for this design

| | Value |
|---|---|
| Nominal apogee | **61,962 ft (18.88 km)** |
| Apogee after every derate applied | **53,298 ft** — 6.6 % above target |
| Total impulse | 54,357 N·s (class O) |
| Liftoff mass | 61.14 kg |
| Total vehicle length | 4.362 m (14.31 ft) |
| Estimated build cost | ~$5,740 |

---

## 1. Values that were fixed and could not be traded

| Value | Setting | Source |
|---|---|---|
| Solid fuel composition | 89 % SasolWax 0907 / 10 % SEBS-g-MA / 1 % carbon black | Customer requirement. This exact blend is designated **S10W1** by Bisin, Paravan, Alberti and Galfetti at the Politecnico di Milano Space Propulsion Laboratory, EUCASS 2019-718 — so its viscosity, modulus and decomposition data are measured, not assumed |
| Oxidiser | Nitrous oxide, self-pressurising | Customer requirement |
| Airframe outer diameter | 152.4 mm (6.00 inch) | Carried over from the reference documents |
| Target apogee | 50,000 ft | Customer requirement |

**Buy the oxidiser correctly.** Automotive nitrous oxide is denatured with roughly
100 ppm sulphur dioxide to deter inhalation abuse (documented in US Patent
5,579,636, in exactly this hybrid rocket context). Sulphur dioxide will not hurt
specific impulse, but it is corrosive in the presence of water and attacks
aluminium — and this design is now full of aluminium. Specify **medical-grade
USP nitrous oxide, ≥ 99.0 %, undenatured**, and demand a certificate of analysis
showing sulphur dioxide and water content (`CEA_and_CFD_guide.md` §1.5).

---

## 2. Propellant and combustion values

| Value | Setting | Why, and where it comes from |
|---|---|---|
| Theoretical grain density | 927.8 kg/m³ | Rule of mixtures on the 89/10/1 blend. **Measure the cast density.** More than 2 % below this is void volume, and voids are how a paraffin grain burns through its case |
| Regression rate coefficient | 0.132 mm/s per (kg/m²·s)^0.5 | Pure paraffin with nitrous oxide is 0.155 (Karabeyoglu 2012, via Balmogim 2017 Table 3.1). 10 % SEBS-g-MA raises melt viscosity at 150 °C from ~0.005 to 0.040 Pa·s (Bisin 2019 Table 1), and droplet entrainment scales inversely with viscosity, so this is a 15 % derate. **The least certain number in the design** |
| Regression rate exponent | 0.500 | Classical turbulent boundary layer value (Marxman and Gilbert 1963). At exactly 0.5 the required grain length becomes independent of initial port diameter |
| Oxidiser-to-fuel mass ratio, end of burn | 8.00 | Peak characteristic velocity is at 7.00, peak vacuum specific impulse at 8.10 (`cea_S10W1_N2O_35bar.csv`). Setting the **end** point at 8.0 makes the burn sweep 6.75 → 8.00, crossing the 7.0 peak, rather than starting on the peak and walking away from it |
| Characteristic velocity efficiency | 0.90 | Zilliac et al. (AIAA 2020-3746) report single-port hybrids from 55 % to 97 %. Balmogim sized Phoenix-1B at 0.90; HEROS verified above 0.97 on the ground (S30). **This is the largest single risk in the design** |
| Thrust coefficient efficiency | 0.96 | 0.985 for friction on an 80 % bell contour, plus divergence loss and some throat erosion |
| Chamber pressure | 36 bar | Characteristic velocity is nearly flat with chamber pressure — 1592 m/s at 20 bar to 1602 m/s at 50 bar, a 0.6 % span. Higher pressure buys thrust coefficient, not chemistry. What it costs is injector isolation, because the tank only supplies ~50 bar and that decays. **The sweep fails the stability constraint at 40 bar and above** |
| Nozzle expansion ratio | 6.0 | Burnout near 6.6 km. Sweep is very flat (4.5 to 8.0 spans ~600 ft); 6.0 keeps margin against sea-level flow separation |

### Three findings from Chemical Equilibrium with Applications worth restating

1. **The SEBS-g-MA is thermochemically invisible.** Peak characteristic velocity
   for 89/10/1 is 1598.1 m/s; for 99 % wax plus 1 % carbon black it is 1598.5 m/s.
   Structural design and performance design are decoupled — nobody on the team
   should argue that the polymer "costs specific impulse". It does not. What it
   *does* cost is regression rate, through melt viscosity.
2. **There is a soot boundary at oxidiser-to-fuel ratio ≈ 3.1.** Below it, solid
   graphite condenses in the chamber. Steady state at 6.75–8.00 is nowhere near
   it, but ignition and shutdown transients pass straight through it — which is
   why hybrid startup is sooty and why nozzle erosion concentrates at the ends of
   a burn.
3. **Half the exhaust is nitrogen.** That is the price of nitrous oxide over
   liquid oxygen, and it is why this propellant tops out near 250 s rather than
   300 s.

---

## 3. Oxidiser tank — the largest change, and one safety correction

| Value | Setting | Why |
|---|---|---|
| Material and role | 6061-T6 aluminium tube, **structural airframe section** | Deletes 2.4 m of body tube. A filament-wound tank needs a winder, a mandrel, a uPVC liner and a cure oven; drawn aluminium tube needs a lathe |
| Outer diameter | 152.4 mm — full airframe diameter | |
| Wall thickness | 3.50 mm | Thin-wall hoop stress at a burst safety factor of 2.0 on the 70 bar relief setting needs 3.29 mm; rounded up for bulkhead threads and stock availability |
| Bore | 145.4 mm | Essentially identical to the 144 mm the composite tank would have given. **The aluminium tank costs no internal volume at all** |
| Maximum expected operating pressure | 70 bar | Set by the burst disc, not by the weather. Above the 56.5 bar vapour pressure at 25 °C so it will not vent as a nuisance; below the 72.45 bar critical pressure |
| Burst safety factor | 2.0 on ultimate | Standard metallic value. Phoenix-1B Mk II used 2.25 on a *composite* vessel (S12), where the higher factor covers composite scatter. Balmogim proof-tested to 80 bar (S26) |
| Fill fraction | **0.80** | See below |
| Tank length | 2401 mm | |
| Internal volume | 39.9 L | |
| Oxidiser load | 25.04 kg | Solved so tank plus grain exactly fill the body tube |

### The fill fraction is a safety limit, not a packing choice

The previous baseline used 92 % fill. **That is not survivable.** Nitrous oxide
filled to 92 % by volume at 20 °C becomes liquid-full at about 27 °C. Liquid
nitrous is nearly incompressible, so past that point tank pressure is set by the
thermal expansion of a trapped liquid rather than by the saturation curve, and it
rises almost without bound for a few degrees of sun on a black tank.

Computed liquid-full temperatures, filling at 20 °C:

| Fill fraction | Liquid-full at |
|---|---|
| 0.92 | 27.0 °C |
| 0.88 | 29.4 °C |
| 0.84 | 31.6 °C |
| **0.80** | **33.6 °C** |
| 0.76 | 35.4 °C |

0.80 is the least conservative value that still clears a 32 °C soak with margin.
HEROS 3 flew at about 70 % and its team explicitly recorded that the conservatism
cost them apogee (S30) — so this is not free, it is just necessary. Going from
92 % to 80 % lengthened the tank by about 300 mm.

Nitrous oxide saturation data underlying the table (CoolProp):

| Temperature | Vapour pressure | Liquid density |
|---|---|---|
| 15 °C | 45.04 bar | 820.7 kg/m³ |
| 20 °C | 50.53 bar | 785.1 kg/m³ |
| 25 °C | 56.52 bar | 742.9 kg/m³ |
| 30 °C | 63.08 bar | 688.1 kg/m³ |
| 35 °C | 70.31 bar | 589.5 kg/m³ |
| 36.37 °C | 72.45 bar (critical) | 452.9 kg/m³ |

---

## 4. Injector — the highest-leverage part

| Value | Setting | Why |
|---|---|---|
| Pattern | Showerhead, axial | Simplest and most stable. The University of Brasília comparison ran a showerhead at 19.1 bar drop with very stable combustion while a single-hole axial injector in the same motor oscillated severely (S20). Phoenix-1A had high-frequency instability with a conical injector and **switched to axial for the flight test** (S26) — learn from that rather than repeating it. Chase regression rate with swirl on version two |
| Orifice count | 33 | Many small holes act as a flow isolation element that decouples the motor from the feed system (S20) |
| Orifice diameter | 1.5 mm | |
| Orifice geometry | Sharp entrance, short tube | The geometry Dyer's non-homogeneous non-equilibrium model was validated on (S15). Match it or the correlation does not apply |
| Effective flow area | 38.3 mm² | From the non-homogeneous non-equilibrium two-phase model at a full tank |
| Pressure drop / chamber pressure, worst point | 0.228 | Floor is 0.15, design target 0.20–0.25 (S20, S22). **Worst at the END of the burn**, when tank pressure has decayed — that is where teams get chug |

**Sanity check against published hardware.** The tested SH1 plate on a 1 kN
paraffin/nitrous motor was 11 orifices of 1.4 mm delivering ~400 g/s of liquid
nitrous (S17). This motor flows 1,390 g/s; scaling SH1 linearly gives 38 orifices.
This design has 33 of slightly larger diameter. Same family, right order.

**Budget for a cold-flow rig anyway.** Waxman's dissertation reviews every
available two-phase model and concludes none is reliable enough to replace
experimental injector flow studies (S16). That is the most important sentence in
the entire injector development plan. It is $450 on the cost list.

---

## 5. Fuel grain and combustion chamber

| Value | Setting | Why |
|---|---|---|
| Port geometry | Single circular port | Paraffin regresses fast enough that a single port works — that is paraffin's whole advantage. Multi-port and wagon-wheel cores buy burn area at the cost of slivers, structural weakness and casting complexity |
| Grain length | 349 mm | |
| Grain outer diameter | 137.0 mm | |
| Initial port diameter | 69.2 mm (0.50 of grain outer diameter) | Because the regression exponent is 0.5, this does **not** trade against apogee — the sweep is flat from 0.45 to 0.60. It buys fuel web instead |
| Final port diameter | 129.8 mm | |
| Fuel web remaining at burnout | 3.6 mm | Against a 3.0 mm warning threshold |
| Peak oxidiser mass flux | 392 kg/m²·s | Ceiling is 650. No single-port paraffin/nitrous laboratory motor has shown stable combustion above that, and Peregrine's 1300 kg/m²·s design point **failed to achieve flame holding with any injector tested** (S32) |
| Fuel utilisation | 0.863 | Floor 0.85 |
| Chamber case | 6061-T6 aluminium, 4.00 mm wall, structural | Hoop stress needs 2.35 mm at 55 bar and a burst factor of 2.0; 4.00 mm is a handling, thread and bending-load floor |
| Ablative liner, under the grain | 3.0 mm | The wax insulates the case wherever it is present |
| Ablative liner, pre- and post-chamber | 12.7 mm | Hot gas touches the case there for the whole burn. This is what the Illinois Space Society used |
| Pre-combustion chamber length | 60 mm | Length-to-diameter 0.43, inside the 0.26–0.66 band from droplet vaporisation stability. Pre-chamber length and injection velocity are the two parameters that set the oscillation period in feed-coupled instability (S20) |
| Post-combustion chamber length | 100 mm | The main lever on characteristic velocity efficiency (S27), and it is empty space — the cheapest performance in the vehicle |

### Burn-through exposure — the risk that must be retired by test

The grain is cut for a regression coefficient of 0.132. Flown at other values:

| Coefficient | Final port | Web left | Verdict |
|---|---|---|---|
| 0.115 | 123.4 mm | 6.8 mm | ok |
| 0.125 | 127.2 mm | 4.9 mm | ok |
| **0.132** | **129.8 mm** | **3.6 mm** | **ok — design point** |
| 0.140 | 132.7 mm | 2.1 mm | thin |
| 0.150 | 136.2 mm | 0.4 mm | **burn-through** |
| 0.165 | 137.0 mm | 0.0 mm | **burn-through** |

Pure paraffin is 0.155. The derate to 0.132 is an *estimate* from a viscosity
argument, not a measurement. **Measure the regression coefficient in a slab
burner or a series of small motors before cutting the flight grain.** This is the
single highest-priority item in the test campaign.

### Casting

Paraffin shrinks 17–19 % on solidification, and voids come from both entrained
air during pouring and shrinkage on cooling (S8). Only two methods are documented
as avoiding critical defects: a **heated mould-piston applying ~1.0 MPa during
cooling**, or **centrifugal casting**. The mould-piston is the budget option — it
is a machined cylinder, a plunger and a press. Section your test grains and
measure void content before any of them fly.

---

## 6. Nozzle

| Value | Setting | Why |
|---|---|---|
| Throat diameter | 28.96 mm | Falls out of the chamber mass balance at 36 bar |
| Exit diameter | 70.9 mm | |
| Expansion ratio | 6.0 | |
| Contour | 80 % bell | Higher efficiency than a conical nozzle of similar parameters |
| Throat material | Monolithic graphite | Widely used in hybrids for low cost and availability. Machining generates fine conductive dust — keep it away from avionics |
| Convergent/divergent | Silica phenolic | The Phoenix-1B solution, arrived at through iterative transient thermo-structural analysis after the Phoenix-1A nozzle failed in flight |
| Sea-level exit pressure ratio | 0.97 of ambient | Against a Summerfield separation threshold of 0.35 — flow stays attached |

**Design the retention as carefully as the contour.** Phoenix-1A's nozzle
physically departed the motor in flight and cost the vehicle 75 % of its apogee
(S26). That is the worst single outcome available to this design.

---

## 7. Airframe

| Value | Setting | Why |
|---|---|---|
| Nose cone profile | Von Karman (Haack series), 5 % blunted | Minimum wave drag for a given volume; rated superior in the transonic. The blunt tip is also structurally and practically necessary |
| Nose cone length | 762 mm (30 inch), fineness ratio 5.0 | Ajuwon's study found maximum apogee at a 30 inch, 6.15 inch diameter fibreglass ogive. Stroick calls fineness ratio 5 critical for this regime. **Changed from the 26 inch / fineness 4.33 in the reference document**, which the computational fluid dynamics study places in a measurable drag penalty zone |
| Nose cone material | Fibreglass, 4 plies of 6 oz E-glass (1.32 mm) | **Not negotiable.** Carbon fibre is conductive and opaque to radio frequency; the antennas live inside this cone. Four plies is the converged student-team answer, validated by Hyak-1 against ~20 g flight loads. NASA Marshall's absolute floor is 0.030 inch (0.76 mm) — this clears it |
| Nose cone tip | Bonded aluminium cap, solid | Highest pressure and temperature point on the vehicle |
| Body tube, non-structural | Commercial fibreglass, 2.4 mm, **0.45 m only** | The pressure vessels carry the airframe over the other 2.9 m |
| Body tube length | 3.60 m (11.81 ft) | Master design variable. **Not** sized so the nominal prediction hits 50,000 ft — that takes only 3.247 m. Sized so the prediction still hits 50,000 ft after every derate |
| Total vehicle length | 4.362 m (14.31 ft) | |
| Maximum dynamic pressure | 139 kPa (2,900 pounds per square foot) | From the flown trajectory, not an assumed profile |

### Fins — both original values were wrong

A first pass using 150 mm semi-span on a 300 mm root chord produced **4.3 calibers
of stability** (badly over-stable — the vehicle weathercocks into the wind and
loses apogee) and simultaneously **failed fin flutter**, because a 4.8 mm fin on a
300 mm root chord is only 1.6 % thick against a design rule of 3–6 %. Shrinking
the fin fixes both at once. The semi-span is now **solved** from the stability
target rather than chosen.

| Value | Setting |
|---|---|
| Count | 3 |
| Material | G10 fibreglass laminate, 6.35 mm (1/4 inch) sheet |
| Planform | Clipped delta, hexagonal section, flat tip |
| Root chord | 200 mm |
| Tip chord | 85 mm |
| Semi-span (solved) | 109.7 mm |
| Leading edge sweep | 50° (band 45–70°) |
| Thickness ratio | 3.2 % of root chord (band 3–6 %) |
| Fin set mass | 1.09 kg |
| Centre of pressure | 2.793 m from the nose tip |
| Static stability margin, loaded | **2.00 calibers** |
| Static stability margin, burnout | **2.13 calibers** |
| Worst flutter margin | **2.22** at 6,606 m (want ≥ 1.5) |

Flutter speed rises with ambient pressure, so the danger is low and fast, not high
and fast. If it ever fails, the fix is a thicker fin or a shorter root chord —
never more span.

---

## 8. Recovery

| Value | Setting | Why |
|---|---|---|
| Architecture | Dual deployment — drogue at apogee, main low | |
| Mass at apogee | 32.5 kg | |
| Drogue diameter | 0.58 m | 30 m/s at sea level; 77 m/s at apogee, because the air is seven times thinner there — the drogue barely works until the vehicle is low |
| Main diameter | 2.48 m | 7 m/s at touchdown |
| Main deployment altitude | 450 m above ground (1,476 ft) | Community standard; comparable competition vehicles use 1,200–1,500 ft. A 15 km descent is a long drift, so deploy the main low |
| Estimated descent time | ~7 minutes | |
| Main opening load | ~1.3 kN | |
| Anti-rotation stops | **Mandatory** | An ESRA team documented their nose cone payload unthreading itself under parachute descent. The fix is physical stops bonded inside the coupler, designed in from the start (S/N7) |

---

## 9. Avionics — where the second big cost saving sits

| Value | Setting | Why |
|---|---|---|
| Architecture | Two independent flight computers, each with its own battery and its own arming switch, each able to sense apogee and fire its own charge | The pattern the community has converged on, and what the competition design guide requires |
| Primary | Industrial-band flight computer with positioning and telemetry, 915 MHz long-range chirp spread spectrum | |
| Backup | Barometric-only deployment altimeter, separate battery, separate charges | |
| Licence required | **None** | The 902–928 MHz industrial, scientific and medical band is licence-free. The 70 cm amateur-band alternative costs more than twice as much **and** is illegal to operate in the United States without a licensed amateur radio operator on the team |
| Static pressure ports | Four holes of 0.172 inch (4.37 mm), 90° apart | Community rule: each hole area = bore in inches × 0.004 in². Nearest drill #19 (0.166 inch). Four rather than one averages the pressure around the circumference so a crosswind gradient does not bias the altitude that fires the charges |
| State estimation | Kalman filter fusing barometer and inertial data | Non-negotiable. Barometric altitude is unreliable through the transonic region and positioning receivers routinely lose lock accelerating through Mach 0.8–1.2. Buy a computer that already does this |

### Telemetry link budget at apogee

| Term | Value |
|---|---|
| Transmit power | +20.0 dBm (100 mW) |
| Onboard antenna gain | −2.0 dBi (whip inside the fibreglass cone) |
| Free space path loss | −119.6 dB (25 km slant range, 915 MHz) |
| Ground antenna gain | +12.0 dBi (nine-element Yagi) |
| **Received power** | **−89.6 dBm** |
| Receiver sensitivity | −120.0 dBm |
| **Link margin** | **+30.4 dB — ample** |

For comparison, the University of Arizona telemetry work calculated useful margin
to 50 km on a 440 MHz downlink and verified an industrial-band system with a
15 dBi receiving antenna at 9 km. This vehicle needs 15–19 km.

**Ground-test the radio.** Power the complete stack, leave it stationary for
30–45 minutes, confirm satellite lock and confirm the ground station receives,
before the vehicle leaves the bench.

---

## 10. Ignition

| Value | Setting |
|---|---|
| Method | Direct electrical arc ignition across a 3D-printed acrylonitrile butadiene styrene section cast into the head end of the grain |
| Energy per start | ~5–15 J |
| Restart capability | Unlimited, no consumables |
| Energetics paperwork | None |

Utah State University has demonstrated this repeatedly with nitrous oxide,
including a low-voltage variant that achieved flame holding on **40 V direct
current for one second** (S24). The budget argument is not hardware cost — it is
that pyrotechnic igniters are consumed on every test, must be stored and
transported under regulation, and their pressure spike is a genuine hazard to a
soft cast paraffin grain.

**The sequence matters as much as the igniter.** Phoenix-1A suffered three
consecutive failed hot fires from igniter quenching before its team adopted a
partial-open step (S26):

1. Arc igniter energised — confirm current draw
2. Main oxidiser valve cracked to ~25 %
3. Confirm chamber pressure rise — flame is holding
4. Main oxidiser valve to full open

Instrument every stage.

---

## 11. Performance and margin

| Quantity | Value |
|---|---|
| Total impulse | 54,357 N·s (class O) |
| Delivered specific impulse | 225.4 s |
| Burn time | 18.0 s |
| Average thrust | 3,016 N |
| Peak thrust | 3,455 N |
| Chamber pressure | 36.0 → 26.2 bar |
| Tank pressure | 50.5 → 32.2 bar |
| Oxidiser-to-fuel ratio | 6.75 → 8.00 |
| Regression rate | 2.61 → 1.17 mm/s |
| Burnout | 6,607 m at 672 m/s |
| Maximum Mach number | 2.14 |
| Liftoff mass | 61.14 kg |
| Propellant mass fraction | 46.8 % |
| **Nominal apogee** | **61,962 ft (18.88 km)** |

### The margin ledger — why the design is aimed above the target

A nominal prediction is not a delivered altitude. Applied cumulatively:

| Step | Apogee | Change |
|---|---|---|
| Nominal design point | 61,962 ft | |
| Characteristic velocity efficiency 0.90 → 0.88 | 59,139 ft | −2,823 |
| Structure mass +5 % | 57,926 ft | −1,213 |
| Drag coefficient +10 % | 53,706 ft | −4,219 |
| Launch rail 5° off vertical | 53,298 ft | −408 |
| **Target** | **50,000 ft** | |
| **Delivered with every derate applied** | **53,298 ft** | **margin is real** |

Note what dominates: characteristic velocity efficiency is worth roughly ten times
more apogee per point than anything else on the list, and it is bought with
post-combustion chamber length and injector quality — not with money.

### Constraints, all passing

| Constraint | Value | Limit |
|---|---|---|
| Body tube length | 3.570 m | ≤ 3.600 m |
| Rail exit thrust-to-weight | 5.76 | ≥ 5.0 |
| Injector isolation | 0.228 | ≥ 0.15 |
| Flame holding, oxidiser flux | 392 kg/m²·s | ≤ 650 |
| Fuel utilisation | 0.863 | ≥ 0.85 |
| Nozzle flow attached at sea level | 0.97 | ≥ 0.35 |
| Tank liquid-full temperature | 33.6 °C | ≥ 32 °C |

---

## 12. Sensitivity — what actually moves apogee

Apogee in feet; "×" marks a constraint violation.

| Value | Sweep |
|---|---|
| Body tube length [m] | 3.20: 48,735 · 3.35: 52,884 · 3.45: 55,782 · 3.60: 60,334 · 3.75: 65,169 |
| Burn time [s] | 13: 53,565 · 15: 55,108 · 16: 55,782 · 18: 57,157 · **20: 58,406 ×** |
| Chamber pressure [bar] | 30: 53,726 · 33: 54,814 · 36: 55,782 · **40: 56,835 ×** · **44: 57,780 ×** |
| Oxidiser-to-fuel ratio | 7.0: 54,195 · 7.5: 55,139 · 8.0: 55,782 · 8.5: 56,131 · 9.0: 56,236 |
| Nozzle expansion ratio | 4.5: 55,253 · 5.5: 55,782 · 6.5: 55,856 · 8.0: 55,272 |
| Initial port fraction | 0.45: 55,782 · 0.55: 55,782 · 0.60: 56,055 · 0.65: 53,793 |
| Tank fill fraction | 0.72: 48,500 · 0.80: 55,782 · **0.84: 59,703 ×** · **0.88: 63,878 ×** |
| Regression coefficient | 0.115: 53,986 · 0.132: 55,782 · 0.155: 57,525 |
| Fixed structure mass [kg] | 20.6: 53,382 · 18.6: 55,782 · 16.6: 58,340 · 12.6: 63,992 |
| **Characteristic velocity efficiency** | **0.86: 51,082 · 0.90: 55,782 · 0.96: 63,625** |

(Sweep run at the 3.45 m intermediate design point; the ranking of sensitivities
is what matters, not the absolute values.)

Reading of this table:
- **Chamber pressure cannot go above 36 bar.** Injector isolation collapses.
- **Tank fill cannot go above 0.80.** The tank goes liquid-full.
- **Burn time cannot go to 20 s.** Rail exit thrust-to-weight breaks.
- **Characteristic velocity efficiency is the whole game.** A 10-point swing is
  12,500 ft — more than every other value on the list combined.

---

## 13. Cost

Budgetary order-of-magnitude estimates in US dollars, for **comparing
architectures**. Not quotations. Student labour and machine shop time assumed free.
Get real quotes before committing.

| Item | Cost |
|---|---|
| 6061-T6 aluminium tube, oxidiser tank and chamber case | 520 |
| Machining stock, bulkheads, injector plate, retainers | 700 |
| Commercial fibreglass airframe tube and couplers | 260 |
| Fibreglass nose cone, 30 inch ogive | 220 |
| G10 fin stock and fin can hardware | 150 |
| Graphite throat billet and silica-phenolic sections | 240 |
| Ablative phenolic liner stock | 120 |
| Main oxidiser valve, actuator, burst disc, fittings | 850 |
| Arc ignition system | 90 |
| Avionics, two flight computers, ground station | 480 |
| Recovery: parachutes, shock cord, hardware | 620 |
| Propellant for one flight | 260 |
| Cold-flow test rig for the injector | 450 |
| Static fire consumables, three qualification burns | 780 |
| **Total** | **5,740** |

Against the carbon fibre baseline:

| Baseline item | Baseline cost | Replaced by | Saving |
|---|---|---|---|
| Filament-wound carbon fibre airframe, 3.2 m | 3,200 | 260 of fibreglass tube | 2,940 |
| Filament-wound carbon fibre oxidiser tank | 2,100 | 520 of aluminium tube | 1,580 |
| Foam-core carbon fibre fins | 380 | 150 of G10 | 230 |
| Amateur-band telemetry plus redundant unit | 620 | 480 industrial-band | 140 |
| | | **Total saved** | **4,890** |

**Do not economise on the main oxidiser valve, the burst disc, or the cold-flow
rig.** Those three are the difference between a test campaign and an incident.

---

## 14. What must be measured before this design is trusted

In priority order:

1. **The regression rate coefficient.** Slab burner or a series of small motors.
   The design assumes 0.132; at 0.150 the grain burns through. Everything else on
   this list is secondary to this.
2. **Injector discharge behaviour, by cold flow.** No two-phase model is reliable
   enough to skip it (S16). Water first, then nitrous oxide.
3. **Characteristic velocity efficiency, by static fire.** Back it out from
   chamber pressure, throat area and total mass flow. It is worth more apogee than
   any other number in the design.
4. **Cast grain density and void content.** Section test grains.
5. **Tank proof test.** Hydrostatic to 1.5 × the 70 bar relief setting, with the
   real bulkheads and the real threads.
6. **Radio link, on the ground, for 30–45 minutes** with the complete stack
   powered and assembled.

---

*Design record generated by `analysis/budget_design_50kft.py` and
`analysis/airframe_recovery_avionics.py`. Source references keyed S1–S35 to
`00_HYBRID_ENGINE_REFERENCE.md` and N1–N24 to `01_NOSECONE_AVIONICS_REFERENCE.md`.*
