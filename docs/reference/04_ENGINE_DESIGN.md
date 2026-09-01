# Engine Design — Groundwork, Front to Back

**Motor:** nitrous oxide / paraffin hybrid, impulse class O
**Vehicle:** 6.00 inch (152.4 mm) airframe, 4.362 m long, 60.90 kg on the pad
**Mission:** 50,000 feet
**Fuel (fixed):** 89 wt% SasolWax 0907 paraffin, 10 wt% SEBS-g-MA, 1 wt% carbon black — the blend designated **S10W1** by Bisin, Paravan, Alberti and Galfetti (EUCASS 2019-718)
**Oxidiser (fixed):** nitrous oxide, self-pressurising

Companion documents: `00_HYBRID_ENGINE_REFERENCE.md` (sources S1–S35),
`01_NOSECONE_AVIONICS_REFERENCE.md` (sources N1–N24), `CEA_and_CFD_guide.md`,
`NOZZLE_DESIGN.md` (literature and method — its *dimensions* are superseded),
`02_BUDGET_50KFT_DESIGN.md`, `03_CHANGE_REGISTER.md`.

Working models: `analysis/budget_design_50kft.py`, `analysis/run_nozzle_50kft.py`,
`analysis/motorsim.py`, `analysis/nozzle_design.py`.

---

## 0. The engine on one page

Copy this block into the notebook first; everything after it is justification.

| Station | Value | Unit |
|---|---|---|
| **Oxidiser** | | |
| Nitrous oxide loaded | 24.89 | kg |
| Tank internal volume | 39.6 | litre |
| Tank fill fraction at 20 °C | 0.80 | — |
| Tank bore × wall | 145.4 × 3.5 | mm |
| Tank length | 2,387 | mm |
| Burst disc setting | 70 | bar |
| **Injector** | | |
| Pattern | showerhead, axial | — |
| Orifice count × diameter | 33 × 1.5 | mm |
| Geometric orifice area | 58.31 | mm² |
| Effective (discharge) area | 38.1 | mm² |
| Discharge coefficient | 0.653 | — |
| Injection velocity | 95.5 | m/s |
| **Igniter** | | |
| Method | electrical arc on printed ABS | — |
| Energy per start | 5–15 | J |
| **Chamber** | | |
| Case bore × wall | 144.4 × 4.0 | mm |
| Pre-combustion chamber length | 60 | mm |
| Fuel grain length | 348 | mm |
| Grain outer diameter | 136.8 | mm |
| Initial port diameter | 69.2 | mm |
| Final port diameter | 129.7 | mm |
| Post-combustion chamber length | 100 | mm |
| Characteristic length, start → end | 6.4 → 11.5 | m |
| **Nozzle** | | |
| Throat diameter | 28.87 | mm |
| Throat land length | 7.22 | mm |
| Exit diameter | 70.73 | mm |
| Expansion area ratio | 6.00 | — |
| Contraction area ratio | 25.01 | — |
| Convergence half angle | 45.0 | degrees |
| Initial divergence wall angle | 20.75 | degrees |
| Exit divergence wall angle | 7.50 | degrees |
| Overall wetted length | 161.6 | mm |
| **Performance** | | |
| Chamber pressure, start → end | 36.0 → 26.2 | bar |
| Oxidiser-to-fuel ratio, start → end | 6.75 → 8.00 | — |
| Total impulse | 54,037 | N·s |
| Burn time | 18.02 | s |
| Average thrust | 2,998 | N |
| Peak thrust | 3,435 | N |
| Delivered specific impulse | 225.4 | s |
| **Nominal apogee** | **61,471** | **ft** |
| **Apogee after every derate** | **51,784** | **ft** |

---

## 1. Oxidiser — nitrous oxide

| Value | Setting | Why |
|---|---|---|
| Grade | Medical USP, ≥ 99.0 %, **undenatured** | Automotive nitrous is denatured with ≈100 ppm sulphur dioxide to deter inhalation abuse (US Patent 5,579,636, written in exactly this hybrid rocket context). Sulphur dioxide does not hurt specific impulse but it is corrosive with any water present and it attacks aluminium — and this vehicle is now made of aluminium. Demand a certificate of analysis and check sulphur dioxide **and water** |
| Mass loaded | 24.89 kg | Solved so tank plus grain exactly fill the body tube |
| State at the injector | Saturated liquid, ≈50.5 bar at 20 °C | Self-pressurising: no helium bottle, no regulator, no pump. This is why nitrous is chosen over liquid oxygen for a student vehicle |
| Reactant enthalpy used in the chemistry | Saturated liquid at 293 K, 17,185 cal/mol | The chemistry code ships nitrous as an ideal gas at 298 K. Your tank does not contain that. Using the saturated-liquid enthalpy moves characteristic velocity from 1,617 to 1,598 m/s — a free 1.2 % of accuracy |

**Why nitrous costs you specific impulse, and why that is accepted.** Half the
exhaust is nitrogen (mole fraction 0.511 at the design mixture ratio). That is
why the mean molecular weight is a high 26.6 g/mol and why this propellant tops
out near 250 s rather than 300 s. The compensation is that it self-pressurises,
is storable, is handleable by students, and costs almost nothing.

**The safety item that is not optional.** Nitrous oxide is monopropellant-capable:
it decomposes exothermically given enough energy, and hydrocarbon contamination
lowers the activation barrier substantially. Keep hydrocarbons out of the
oxidiser side entirely — that includes assembly grease, thread sealant and
fingerprints. Adiabatic compression of nitrous vapour against a fast-opening
valve is how teams destroy feed systems (S34, S35).

---

## 2. Oxidiser tank

| Value | Setting | Why |
|---|---|---|
| Material | 6061-T6 aluminium tube | A filament-wound tank needs a winding machine, a mandrel, a liner and a cure oven. Drawn aluminium tube needs a lathe. Saves ≈$1,580 |
| Structural role | **It is the airframe over its own length** | Deletes 2.4 m of body tube. Stacked-pressure-vessel architecture, as flown by HEROS 3 to 32.3 km (S30) and Phoenix-1B (S26) |
| Outer diameter | 152.4 mm | Full airframe diameter |
| Wall thickness | 3.50 mm | Thin-wall hoop stress at 70 bar × safety factor 2.0 on ultimate (310 MPa) needs 3.29 mm. Rounded up for bulkhead threads and stock |
| Bore | 145.4 mm | Slightly *larger* than the 144 mm a composite tank would give — the metal tank costs no internal volume |
| Internal volume | 39.6 litre | |
| Length | 2,387 mm | The dominant single dimension in the vehicle |
| Maximum expected operating pressure | 70 bar | Set by the burst disc, not the weather. Above the 56.5 bar vapour pressure at 25 °C so it will not vent as a nuisance; below the 72.45 bar critical pressure |
| Burst safety factor | 2.0 on ultimate | Standard metallic value. Phoenix-1B Mk II used 2.25 on a *composite* vessel, where the extra covers fibre scatter |
| Proof test | Hydrostatic to 105 bar | 1.5 × the relief setting, with the real bulkheads and real threads |
| **Fill fraction** | **0.80 at 20 °C** | **Safety limit, not a packing choice — see below** |

### Fill fraction is the one number that can burst this tank

Nitrous filled to 92 % by volume at 20 °C becomes **liquid-full at about 27 °C**.
Liquid nitrous is nearly incompressible, so past that point tank pressure is set
by the thermal expansion of a trapped liquid rather than by the saturation curve,
and it rises almost without bound for a few degrees of sun on the tank.

| Fill fraction at 20 °C | Goes liquid-full at | Verdict |
|---|---|---|
| 0.92 | 27.0 °C | Not survivable |
| 0.88 | 29.4 °C | Not survivable |
| 0.84 | 31.6 °C | No margin |
| **0.80** | **33.6 °C** | **Selected** |
| 0.76 | 35.4 °C | Safe, costs length |

Nitrous saturation data (CoolProp), for the notebook:

| Temperature | Vapour pressure | Liquid density | Vapour density |
|---|---|---|---|
| 0 °C | 31.22 bar | 907.1 kg/m³ | 85.2 kg/m³ |
| 10 °C | 40.01 bar | 852.2 kg/m³ | 114.9 kg/m³ |
| 15 °C | 45.04 bar | 820.7 kg/m³ | 134.2 kg/m³ |
| **20 °C** | **50.53 bar** | **785.1 kg/m³** | **158.0 kg/m³** |
| 25 °C | 56.52 bar | 742.9 kg/m³ | 188.8 kg/m³ |
| 30 °C | 63.08 bar | 688.1 kg/m³ | 232.7 kg/m³ |
| 35 °C | 70.31 bar | 589.5 kg/m³ | 320.7 kg/m³ |
| 36.37 °C | 72.45 bar (critical) | 452.9 kg/m³ | 452.9 kg/m³ |

---

## 3. Feed system and main oxidiser valve

| Value | Setting | Why |
|---|---|---|
| Feed bay length | 100 mm | Tank aft bulkhead, main oxidiser valve, run to injector |
| Main oxidiser valve | Full-bore ball valve, pneumatically or servo actuated, remotely commanded | Must open in a controlled way — see the ignition sequence. Do **not** economise here |
| Relief | Burst disc at 70 bar, vented away from personnel and away from the airframe | Defines the maximum expected operating pressure |
| Fill and vent | Remote fill line with a remotely operated vent | Nobody stands next to a filled nitrous tank |
| Line material | Stainless steel, cleaned for oxidiser service | No hydrocarbons, no aluminium in contact with denatured product |

**Supercharging was considered and rejected.** Peregrine supercharged slightly
above vapour pressure specifically to stop cavitation in the feed system (S32),
and Phoenix-1B Mk II supercharged to 65 bar with helium. Both flatten the thrust
curve. Both also add a gas bottle, a regulator and a second pressurised system.
For a cost-driven first vehicle the blowdown penalty is affordable — the injector
pressure drop ratio holds above the 0.15 floor for the whole burn without it (see
§4) — so the complexity is not bought.

---

## 4. Injector — the highest-leverage part in the engine

| Value | Setting | Why |
|---|---|---|
| Pattern | **Showerhead, axial** | Simplest and most stable. In the University of Brasília comparison a showerhead at 19.1 bar drop gave very stable combustion while a single-hole axial injector in the *same motor* oscillated severely (S20). Phoenix-1A had high-frequency instability with a conical injector and switched to axial for the flight test (S26) |
| Orifice count | 33 | Many small orifices act as a flow isolation element, decoupling the chamber from the feed system (S20). Never one large hole |
| Orifice diameter | 1.5 mm | |
| Orifice geometry | **Sharp entrance, short tube** | This is the geometry Dyer's non-homogeneous non-equilibrium model was validated on (S15). Match it or the correlation does not apply to your plate |
| Geometric orifice area | 58.31 mm² | 33 × π/4 × 1.5² |
| Effective flow area | 38.1 mm² | From the two-phase model at a full tank |
| Discharge coefficient | 0.653 | Falls out of the two above — consistent with the 0.65 assumed |
| Injection velocity | 95.5 m/s | At two-phase quality 0.5, effective density 263 kg/m³ (the modelling assumption used in S20) |
| Pressure drop, start of burn | 14.5 bar → ratio **0.403** | |
| Pressure drop, end of burn | 6.0 bar → ratio **0.229** | **This is the number that matters.** Floor 0.15, design band 0.20–0.25 |

### Why the *end* of the burn is the design case

The stability parameter is injector pressure drop divided by chamber pressure
(S22). A high-drop injector chokes, so chamber pressure oscillations cannot
propagate upstream and modulate the oxidiser flow. In a blowdown system that
ratio **collapses through the burn** as tank pressure decays — 0.403 at ignition,
0.229 at burnout. Check stability at the end, not the start. This is where most
teams get chug.

It is also why chamber pressure is capped at 36 bar. The sweep **fails this
constraint at 40 bar and above**, because the tank only supplies about 50 bar
falling to 32.

### Sanity check against published hardware

A tested plate on a 1 kN paraffin/nitrous motor was 11 orifices of 1.4 mm
delivering ≈400 g/s of liquid nitrous (S17). This motor flows 1,464 g/s; scaling
that plate linearly gives 38 orifices. This design has 33 of slightly larger
diameter. Same family, right order of magnitude.

### The one thing no model can replace

Waxman's dissertation reviews every available two-phase injector model and
concludes **none is reliable enough to replace experimental injector flow
studies** (S16). Build the cold-flow rig. Water first, then nitrous. It is $450.

---

## 5. Igniter

| Value | Setting | Why |
|---|---|---|
| Method | Direct electrical arc across a 3D-printed acrylonitrile butadiene styrene section cast into the head end of the grain | High voltage, low wattage. The arc runs along the printed layer lines, pyrolysing a little plastic that seeds combustion along the whole port as oxidiser arrives |
| Energy per start | 5–15 J | Demonstrated repeatedly at Utah State University with nitrous oxide, including a low-voltage variant that held flame on **40 V direct current for one second** (S24) |
| Restarts | Unlimited, no consumables | |
| Energetics paperwork | None | |
| Printed section | ≈25 mm long ring at the port entrance, two electrodes | Sits in the pre-combustion chamber, upstream of the wax |

**What an igniter must do** (S23): deliver enough energy to *pyrolyse the solid
fuel*, **and** retain enough residual energy to *initiate combustion*. Both, not
either.

**Why not pyrotechnic.** The saving is not hardware cost, which is small either
way. It is that pyrotechnic igniters are consumed on every test, must be stored
and transported under regulation, and their pressure spike is a genuine hazard to
a mechanically weak cast paraffin grain — a properly designed pyrotechnic avoids
a shockwave, but a poorly designed one cracks the grain and changes the burning
area (S25).

### Ignition sequence — as important as the igniter

Phoenix-1A suffered **three consecutive failed hot fires from igniter quenching**
before its team adopted the partial-open step (S26):

1. Arc igniter energised — confirm current draw
2. Main oxidiser valve cracked to ≈25 %
3. Confirm chamber pressure rise — flame is holding
4. Main oxidiser valve to full open

Instrument every stage. Chamber pressure is the confirmation signal, so it must
be live on the ground station before the valve is touched.

---

## 6. Pre-combustion chamber

| Value | Setting | Why |
|---|---|---|
| Length | 60 mm | |
| Diameter | 138.4 mm | |
| Length-to-diameter ratio | **0.43** | Inside the 0.26–0.66 band from droplet-vaporisation stability analysis |
| Volume | 0.90 litre | |
| Axial gas velocity | ≈28 m/s | |
| Residence time | ≈2.2 ms | |

**Its job** is to let injected nitrous droplets vaporise and begin reacting before
they reach the grain, and to establish a recirculation zone that anchors the
flame. Balmogim documents using hot-gas recirculation downstream of the injector
to heat the expanding nitrous and promote vaporisation (S26).

**It is also a stability driver.** Pre-combustion chamber length and oxidiser
injection velocity are the two parameters that set the pressure oscillation
period in feed-system-coupled instability (S20). Too long and you have built a
resonator; too short and you get incomplete vaporisation and a long combustion
time lag. Do not change this length casually to solve a packaging problem.

---

## 7. Fuel grain

| Value | Setting | Why |
|---|---|---|
| Composition | 89 % SasolWax 0907 / 10 % SEBS-g-MA / 1 % carbon black | Fixed by requirement. Also a published research fuel, so viscosity, modulus and decomposition data are measured, not assumed |
| Theoretical density | 927.8 kg/m³ | Rule of mixtures. **Measure the cast density** — more than 2 % low is void volume |
| Mass | 3.54 kg | |
| Port geometry | Single circular port | Paraffin regresses fast enough that one port works — that is paraffin's whole advantage. Multi-port and wagon-wheel cores buy burn area at the cost of slivers, structural weakness and casting complexity |
| Length | 348 mm | |
| Outer diameter | 136.8 mm | |
| Initial port diameter | 69.2 mm | |
| Final port diameter | 129.7 mm | |
| Web remaining at burnout | 3.6 mm | Against a 3.0 mm warning threshold |
| Regression rate coefficient | 0.132 mm/s per (kg/m²·s)^0.5 | Pure paraffin is 0.155 (Karabeyoglu 2012 via Balmogim Table 3.1). 10 % SEBS-g-MA raises melt viscosity at 150 °C from ≈0.005 to 0.040 Pa·s (Bisin 2019 Table 1), and droplet entrainment scales inversely with viscosity, so this is a 15 % derate |
| Regression rate exponent | 0.500 | Marxman and Gilbert 1963. At exactly 0.5 the required grain length is independent of port diameter |
| Regression rate, start → end | 2.60 → 1.17 mm/s | |
| Peak oxidiser mass flux | 389 kg/m²·s | **Ceiling 650.** No single-port paraffin/nitrous laboratory motor has been stable above it, and Peregrine's 1,300 kg/m²·s design point failed to hold flame with *any* injector tested (S32) |

### Why paraffin at all

A hybrid burns diffusion-limited: a flame sheet sits in a turbulent boundary layer
above the fuel and the fuel burns only as fast as heat reaches the solid. That is
why classical hybrid regression rates are 3–5× below solid propellant burn rates.
Paraffin breaks this. It melts into a thin, low-viscosity, hydrodynamically
unstable liquid layer; the oxidiser shears droplets off that layer and entrains
them into the core flow, where they burn. Entrainment is a *mass transfer*
mechanism that bypasses the heat-transfer bottleneck (Karabeyoglu, Altman and
Cantwell 2002). That is worth roughly 3–4× over HTPB, and it is what makes a
single-port grain viable.

### The 10 % SEBS-g-MA is free in performance and expensive in regression rate

Peak characteristic velocity for 89/10/1 is 1,598.1 m/s; for 99 % wax plus 1 %
carbon black it is 1,598.5 m/s — a 0.03 % difference. **Nobody on the team should
argue the polymer costs specific impulse. It does not.** What it costs is
regression rate, through melt viscosity, and that is the whole reason the
coefficient is derated from 0.155 to 0.132.

### Burn-through exposure — the single highest-priority test

The grain is cut for a regression coefficient of 0.132. That number is an
estimate from a viscosity argument, not a measurement, and pure paraffin is 0.155.

| Coefficient | Final port | Web left | Verdict |
|---|---|---|---|
| 0.115 | 123.4 mm | 6.8 mm | ok |
| 0.125 | 127.2 mm | 4.9 mm | ok |
| **0.132** | **129.7 mm** | **3.6 mm** | **design point** |
| 0.140 | 132.7 mm | 2.1 mm | thin |
| 0.150 | 136.2 mm | 0.4 mm | **burn-through** |
| 0.165 | 136.8 mm | 0.0 mm | **burn-through** |

**Measure the regression coefficient in a slab burner or a series of small motors
before cutting the flight grain.**

### Casting

Paraffin shrinks 17–19 % on solidification, and voids come from both entrained
air during pouring and shrinkage on cooling (S8). Two methods are documented as
avoiding critical defects: a **heated mould-piston applying ≈1.0 MPa during
cooling**, or **centrifugal casting**. The mould-piston is the budget option — a
machined cylinder, a plunger and a press. Section your test grains and measure
void content before any of them fly. Grain thermal limit is **373 °C**
(degradation onset, Bisin 2019), 44 °C above pure wax thanks to the SEBS.

---

## 8. Combustion chamber and post-combustion chamber

| Value | Setting | Why |
|---|---|---|
| Case material | 6061-T6 aluminium, structural | Also the airframe over its length |
| Case bore × wall | 144.4 × 4.00 mm | Hoop stress needs only 2.35 mm at 55 bar with a 2.0 burst factor; 4.00 mm is a handling, thread and bending-load floor, because this section carries flight bending too |
| Case design pressure | 55 bar | 36 bar steady plus ignition transient and partial throat blockage |
| Ablative liner under the grain | 3.0 mm | The wax insulates the case wherever it is present |
| Ablative liner, pre- and post-chamber | 12.7 mm phenolic | Hot gas touches the case directly there for the whole burn |
| **Post-combustion chamber length** | **100 mm** | Length-to-diameter 0.72 |
| Post-chamber volume | 1.50 litre | |
| Post-chamber residence time | ≈3.2 ms | Plus a further ≈0.5 litre and ≈1 ms in the convergent section |
| Characteristic length, start → end | 6.4 → 11.5 m | Chamber volume ÷ throat area. High compared with a liquid engine (0.8–3 m) because in a hybrid the port *is* the chamber |

### This is the cheapest performance in the whole vehicle

Hybrid combustion is stratified — oxidiser-rich core, fuel-rich near-wall — so
unmixed propellant leaves the grain. The post-combustion chamber is where you
recover it, and it is a primary driver of the **55 % to 97 % spread in
single-port characteristic velocity efficiency** reported by Zilliac et al.
(S27). It is empty space. It costs 100 mm of tube and about 0.5 kg.

Look at the margin ledger in §11: characteristic velocity efficiency is worth
roughly ten times more apogee per point than anything else in the design. **If
you have length to spare anywhere, spend it here.** A passive mixing device or
diaphragm between grain and post-chamber is demonstrated on paraffin/nitrous and
recovers several percent, with the caveat that exceeding the identified limit
produces oscillations above 20 % of mean chamber pressure (S28).

---

## 9. Nozzle

> Superseding the dimensions in `NOZZLE_DESIGN.md`, which were sized for a
> five inch, 8.42 second, 5 kN motor with a 38.70 mm throat. That nozzle on this
> motor would choke at ≈19 bar instead of 36.

### 9.1 Dimensions

| Dimension | Value | Unit |
|---|---|---|
| **Throat diameter** | **28.87** | mm |
| Throat radius | 14.44 | mm |
| Throat area | 654.84 | mm² |
| **Cylindrical throat land length** | **7.22** | mm |
| **Exit diameter** | **70.73** | mm |
| Exit radius | 35.36 | mm |
| **Expansion area ratio** | **6.00** | — |
| Chamber diameter at nozzle entrance | 144.40 | mm |
| Contraction area ratio | 25.01 | — |
| **Convergence half angle** | **45.0** | degrees |
| Chamber blend arc radius | 21.66 | mm |
| Upstream throat arc radius | 21.66 | mm |
| Downstream throat arc radius | 5.52 | mm |
| **Initial divergence wall angle** | **20.75** | degrees |
| **Exit divergence wall angle** | **7.50** | degrees |
| Fractional length of bell | 1.00 (full length) | — |
| Reference conical divergent length | 78.83 | mm |
| Actual divergent length | 78.83 | mm |
| Convergent length | 75.70 | mm |
| **Overall wetted length** | **161.63** | mm |

Full wall coordinate table: `analysis/outputs/nozzle_contour_50kft.csv`
(≈900 points, millimetres, ready to import as a computer-aided-design sketch and
revolve). Drawing: `analysis/outputs/nozzle_design_50kft.png`.

### 9.2 Where each number comes from

**Throat diameter** falls out of the definition of characteristic velocity:

> throat area = total mass flow rate × **delivered** characteristic velocity ÷ chamber pressure
> = 1.647 × 1,431.2 ÷ 3,600,000 = 654.8 mm² → **28.87 mm**

Use the *delivered* characteristic velocity (ideal 1,590.3 m/s × efficiency 0.90),
not the ideal one. Size on the ideal number and the real chamber pressure comes
out ten percent low, and every downstream number is wrong.

**Expansion area ratio 6.00** was confirmed by two independent methods that
agreed. The nozzle sweep shows sea-level thrust coefficient peaking exactly at
6.0; the trajectory sweep shows apogee flat from 4.5 to 8.0 and peaking near 6.5.

| Ratio | Exit dia. | Exit pressure | Sea-level thrust coeff. | Vacuum thrust coeff. |
|---|---|---|---|---|
| 4.0 | 57.9 mm | 1.731 bar | 1.5100 | 1.6225 |
| 5.0 | 64.8 mm | 1.283 bar | 1.5231 | 1.6638 |
| 5.5 | 67.9 mm | 1.130 bar | 1.5258 | 1.6806 |
| **6.0** | **70.7 mm** | **1.008 bar** | **1.5265** ← peak | 1.6954 |
| 6.5 | 73.8 mm | 0.907 bar | 1.5257 | 1.7086 |
| 7.0 | 76.6 mm | 0.824 bar | 1.5236 | 1.7206 |
| 8.0 | 81.9 mm | 0.693 bar | 1.5164 | 1.7416 |
| 10.0 | 91.6 mm | 0.520 bar | 1.4934 | 1.7749 |

At ratio 6.0 the exit static pressure is **1.008 bar against a sea-level ambient
of 1.013 bar** — very nearly perfectly expanded at liftoff, and progressively
underexpanded as the vehicle climbs, which is the right compromise for a flight
that spends its whole burn climbing.

**Convergence half angle 45 degrees** is the NASA SP-8115 standard. The document
permits 1 to 75 degrees but warns that steeper inlets increase insulation
erosion, especially at higher chamber pressure — and this motor already runs
oxidiser-rich. A steeper inlet would have saved ≈15 mm; it was not taken.

**Cylindrical throat land 7.22 mm** = 0.5 × throat radius, the SP-8115 minimum.
A parallel land makes the throat far easier to machine and to measure with a bore
gauge, helps alignment, and means the first fraction of a millimetre of erosion
does not immediately change the throat area.

**Upstream throat arc 1.5 × throat radius, downstream arc 0.382 × throat radius.**
The 1.5 is standard and also sets the radius of curvature used in the Bartz
correlation; the 0.382 comes from Rao and is essentially universal.

**Full-length bell (fractional length 1.00).** The wall angles come from the Rao
charts as a *pair* — change the fractional length and you must change both.

| Fractional length | Initial angle | Exit angle | Divergent length | Divergence factor | Loss vs full |
|---|---|---|---|---|---|
| 0.60 | 25.0° | 20.0° | 47.4 mm | 0.96985 | −2.60 % |
| 0.70 | 24.0° | 17.0° | 55.3 mm | 0.97815 | −1.76 % |
| 0.80 | 22.5° | 14.0° | 63.3 mm | 0.98515 | −1.06 % |
| 0.90 | 21.5° | 10.5° | 71.2 mm | 0.99163 | −0.41 % |
| **1.00** | **20.75°** | **7.50°** | **78.8 mm** | **0.99572** | **0** |
| *15° cone* | — | 15.0° | — | 0.98296 | −1.28 % |

The full bell was chosen over an 80 % bell because the 1.06 % of axial thrust it
recovers is worth roughly 900 feet, against 15.8 mm of extra length and ≈0.15 kg.
The extra length came out of the vehicle's assembly slack.

### 9.3 Efficiencies

| Efficiency | Value | What it is |
|---|---|---|
| Divergence loss factor, this bell | **0.99572** | Fraction of exhaust momentum acting along the axis, (1 + cos 7.50°)/2 |
| Divergence loss factor, 15° cone | 0.98296 | For comparison — the bell is worth **+1.30 %** |
| Friction and boundary layer factor | 0.985 | Standard practice; the UKZN blowdown study used the same |
| **Combined nozzle efficiency** | **0.9808** | Divergence × friction |
| Characteristic velocity efficiency | 0.900 | **Combustion, not nozzle.** Sizing value |
| **Overall specific impulse efficiency** | **0.8827** | The product |
| Thrust coefficient, sea level | 1.5265 | |
| Thrust coefficient, vacuum | 1.6954 | |

Note the trajectory model assumes a thrust coefficient efficiency of **0.960**
while the contour actually delivers **0.981**. That 2 % is unclaimed margin, left
in deliberately.

### 9.4 Heat transfer — Bartz correlation

| Quantity | Value |
|---|---|
| Assumed wall temperature | 2,500 K |
| Adiabatic wall temperature at throat | 3,248 K |
| Heat transfer coefficient at throat | 7,157 W/m²·K |
| Heat flux at throat | 5.36 MW/m² |
| **Peak heat flux** | **5.40 MW/m²** |
| **Location of peak** | **1.59 mm UPSTREAM of the throat** |
| Integrated heat rate into the wall | 54.6 kW |
| Total heat load over the burn | 0.93 MJ |

**The peak is upstream of the throat, not at it.** This is a standard and
slightly counterintuitive result, and it is why throat inserts must extend into
the convergent section. Size the insert to cover only the geometric throat and
the hottest part of the nozzle will be sitting on your insulation.

**5.4 megawatts per square metre is a serious flux** — comparable to the throat of
a small liquid engine. Nothing you can make survives it indefinitely. The
strategy is not to resist it but to absorb it for 18 seconds and then stop, which
is what a thick graphite insert with a phenolic backing does.

**One trade worth knowing.** Running at an oxidiser-to-fuel ratio of 8.0 rather
than 6.5 raises the exhaust specific heat capacity from 735 to 950 J/kg·K and the
chamber temperature from 3,222 to 3,294 K. That is most of why this throat sees
5.4 MW/m² where the earlier five-inch design saw 3.5. Running lean in oxidiser
buys apogee and costs thermal margin at the throat.

### 9.5 Throat erosion and slag

Model used by internal-ballistics codes, including openMotor:

> d(throat radius)/dt = erosion coefficient × chamber pressure − slag coefficient ÷ chamber pressure

Check which convention your code uses — some work in diameter, and the value
halves.

| Recession rate | **Throat erosion coefficient** | Radial recession over burn | Final throat | Area growth | Chamber pressure at burnout | Effective expansion ratio |
|---|---|---|---|---|---|---|
| 0.050 mm/s | 1.389 × 10⁻¹¹ m/(s·Pa) | 0.85 mm | 30.66 mm | +12.1 % | 32.1 bar | 5.35 |
| **0.075 mm/s (design)** | **2.083 × 10⁻¹¹ m/(s·Pa)** | **1.27 mm** | **31.51 mm** | **+18.4 %** | **30.4 bar** | **5.07** |
| 0.100 mm/s | 2.778 × 10⁻¹¹ m/(s·Pa) | 1.70 mm | 32.36 mm | +24.9 % | 28.8 bar | 4.81 |

**Slag buildup coefficient: 0.000 (metre pascals per second).**

Slag in the solid rocket sense is condensed aluminium oxide, and this propellant
carries no metal. Chemical equilibrium shows condensed graphite only below an
oxidiser-to-fuel ratio of about 3.1; the burn runs 6.75 to 8.00 and never
approaches that in steady state. Ignition and shutdown transients do sweep
through it, so expect soot — but soot is not slag, and it does not accumulate at
the throat against a 2,900 K wall. Use zero, and revisit only if a post-fire bore
gauge reads *smaller* than nominal rather than larger.

**What erosion actually costs you: 1,127 feet.** Less than intuition suggests,
and the reason is worth understanding. In a hybrid the mass flow rate is set by
the injector and the tank, **not** by the throat. So as the throat grows, chamber
pressure falls but thrust barely moves — thrust is the thrust coefficient times
chamber pressure times throat area, and the last two move in opposite directions.
What you actually lose is thrust coefficient, because the effective expansion
ratio walks from 6.0 down to about 5.1 while exit area stays fixed.

| Recession rate | Total impulse | Apogee | Loss |
|---|---|---|---|
| 0.000 mm/s | 54,360 N·s | 61,962 ft | — |
| 0.025 mm/s | 54,192 N·s | 61,467 ft | −495 ft |
| 0.050 mm/s | 54,023 N·s | 60,983 ft | −979 ft |
| **0.075 mm/s** | **53,867 N·s** | **60,540 ft** | **−1,422 ft** |
| 0.100 mm/s | 53,720 N·s | 60,127 ft | −1,835 ft |
| 0.150 mm/s | 53,442 N·s | 59,369 ft | −2,593 ft |

A useful side effect: erosion *helps* injector stability, because falling chamber
pressure raises the pressure drop ratio.

**Optional: pre-shrink the throat.** Sizing the throat 4 % under nominal in area
(28.3 mm instead of 28.87 mm) centres the burn-averaged throat area nearer the
design value and recovers ≈450 feet. It costs injector isolation margin (worst
case falls from 0.228 to 0.208, floor 0.15). **Recommendation: fly the
qualification motors at nominal 28.87 mm so you measure erosion against a known
baseline, then decide.** 450 feet is not worth optimising against a number you
have not measured.

**Measure the throat before and after every static fire.** A bore gauge and five
minutes. That single measurement is worth more than any published correlation.

### 9.6 Materials and construction

| Component | Material | Function |
|---|---|---|
| Throat insert | Polycrystalline graphite, fine grain | Takes the peak heat flux and the erosion |
| Convergent liner | Silica phenolic | Insulates the structure through the convergent section |
| Divergent liner | Silica phenolic | Forms the bell contour, insulates, ablates slowly |
| Structural shell | Aluminium | Carries pressure and thrust loads, bolts to the case |
| Retaining ring | Steel | Holds the insert in **axial compression** |
| Sealing | O-rings at the case interface | Prevents hot gas leakage past the joint |

> **The rule the Phoenix team learned the hard way: graphite is much stronger in
> compression than in tension, so the retention scheme must load the insert in
> compression at all times.** Phoenix-1A left an intentional expansion gap between
> the graphite and the steel retainer. A stress concentration developed at that
> interface, the graphite went into tension, and the divergent section was
> **ejected from the motor shortly after ignition**. The boat tail went with it,
> and the vehicle reached 2.5 km instead of 10 km — it lost 75 % of its apogee to
> a retention detail (S26).

Graphite has a low coefficient of thermal expansion and steel has a high one, so
a steel ring around a graphite insert **loosens as it heats**. Design the
retention so thermal expansion *increases* compressive preload rather than opening
a gap.

Two further points from SP-8115: differential erosion at material interfaces is a
recurring failure mode, so put material joints where the heat flux is low, never
near the throat; and adhesive bonding is a persistent source of uncertainty, so
never let a bond line be the only thing holding a component in place.

Machining graphite generates fine conductive dust — keep it away from avionics.

---

## 10. What this design does not yet include

State these plainly in reviews.

- **No transient thermal analysis of the solid.** The Bartz flux is the gas-side
  boundary condition. You still need transient conduction through the graphite
  and phenolic to confirm the aluminium shell stays below its temperature limit
  for 18 seconds. That is a finite-element problem.
- **No structural analysis of the nozzle.** Pressure loads, thrust loads, bolt
  pattern and thermal stress in the graphite are all outstanding.
- **No radiation in the heat flux.** In a sooty paraffin flame — and there is 1 %
  carbon black in this grain deliberately — radiation is a first-order
  contributor. Bartz is convection only, so **5.4 MW/m² is a lower bound.**
- **The 2,500 K wall temperature is assumed, not solved.** Heat flux is sensitive
  to it. Iterate once the conduction solution exists.
- **No allowance for a non-uniform nozzle inlet.** Incomplete mixing produces a
  radially non-uniform flow entering the nozzle and changes the erosion
  distribution (Migliorino et al.). A good post-combustion chamber reduces this.

---

## 11. Performance and margin

| Quantity | Value |
|---|---|
| Total impulse | 54,037 N·s (class O) |
| Delivered specific impulse | 225.4 s |
| Burn time | 18.02 s |
| Average thrust | 2,998 N |
| Peak thrust | 3,435 N |
| Chamber pressure | 36.0 → 26.2 bar |
| Tank pressure | 50.5 → 32.2 bar |
| Oxidiser-to-fuel ratio | 6.75 → 8.00 |
| Burnout | 6,586 m at 669 m/s |
| Maximum Mach number | 2.13 |
| Liftoff mass | 60.90 kg |
| **Nominal apogee** | **61,471 ft (18.74 km)** |

### The margin ledger

A nominal prediction is not a delivered altitude. Applied cumulatively:

| Step | Apogee | Change |
|---|---|---|
| Nominal design point | 61,487 ft | |
| Characteristic velocity efficiency 0.90 → 0.88 | 58,695 ft | −2,792 |
| Structure mass +5 % | 57,492 ft | −1,203 |
| Drag coefficient +10 % | 53,316 ft | −4,176 |
| Launch rail 5° off vertical | 52,911 ft | −405 |
| **Graphite throat erosion at 0.075 mm/s** | **51,784 ft** | **−1,127** |
| **Target** | **50,000 ft** | |
| **Delivered with every derate applied** | **51,784 ft** | **+3.6 %** |

### Constraints, all passing

| Constraint | Value | Limit |
|---|---|---|
| Body tube length | 3.570 m | ≤ 3.600 m |
| Rail exit thrust-to-weight | 5.75 | ≥ 5.0 |
| Injector isolation, worst point | 0.228 | ≥ 0.15 |
| Flame holding, oxidiser flux | 389 kg/m²·s | ≤ 650 |
| Fuel utilisation | 0.86 | ≥ 0.85 |
| Nozzle flow attached at sea level | 0.99 | ≥ 0.35 |
| Tank liquid-full temperature | 33.6 °C | ≥ 32 °C |
| Nozzle wetted length | 161.6 mm | ≤ 165 mm |

---

## 12. Test campaign, in priority order

1. **Regression rate coefficient.** Slab burner or a series of small motors. The
   design assumes 0.132; at 0.150 the grain burns through to the case.
   Everything below is secondary to this.
2. **Injector cold flow.** Water first, then nitrous. No two-phase model is
   reliable enough to skip it.
3. **Characteristic velocity efficiency, by static fire.** Back it out from
   chamber pressure, throat area and total mass flow. Worth ten times more apogee
   per point than anything else in the design.
4. **Throat recession rate.** Bore gauge before and after every fire.
5. **Cast grain density and void content.** Section test grains.
6. **Tank proof test.** Hydrostatic to 105 bar with real bulkheads and threads.
7. **Ignition sequence**, instrumented at every stage.

---

*Values generated by `analysis/budget_design_50kft.py` and
`analysis/run_nozzle_50kft.py`. Thermochemistry from a NASA Chemical Equilibrium
with Applications sweep of the S10W1 / nitrous oxide propellant cards
(`cea_S10W1_N2O_35bar.csv`); nitrous properties from CoolProp; nozzle contour by
the Rao parabolic approximation with NASA SP-8115 convergent practice; heat
transfer by the Bartz correlation.*
