# CEA and CFD for a Paraffin/N₂O Hybrid Motor

**Propellant:** 89 wt% SasolWax 0907 / 10 wt% SEBS-g-MA / 1 wt% carbon black, with self-pressurised nitrous oxide.

One note before anything else: the `claude.ai/code/artifact/...` link you gave me is behind your account login, so I could not open it. Everything below is built from the PDFs in the project plus published literature. If that artifact contains oxidiser assumptions (tank temperature, supercharging, target Pc) that differ from what I assumed, tell me and I will re-run.

---

## 0. The most useful thing I found

Your formulation is not a guess — it is a published research fuel. Bisin, Paravan, Alberti and Galfetti at the Politecnico di Milano Space Propulsion Laboratory designate **89% SasolWax 0907 / 10% SEBS-MA / 1% carbon black as "S10W1"** and characterised it in EUCASS 2019-718. An earlier SPLab paper by Petrova, Prokopyev and Galfetti (6th EUCASS) calls the same mix "S10G".

That means you already have peer-reviewed property data for your exact fuel, which is unusual and very valuable:

| Property | S10W1 value | Source |
|---|---|---|
| Melt viscosity, 1000 s⁻¹, 150 °C | 0.040 Pa·s | Bisin 2019 |
| Melt viscosity, 1000 s⁻¹, 100 °C | 0.09 Pa·s | Petrova (S10G) |
| Young's modulus (compression) | 519 MPa | Bisin 2019 |
| Compressive yield stress | 4.8 MPa | Bisin 2019 |
| Yield strain | 1.8 % | Bisin 2019 |
| Solid–solid transition / melt peak | 64.1 °C / 81.1 °C | Bisin 2019 |
| Degradation onset / end | 373 °C / 462 °C | Bisin 2019 |

Two numbers matter most. The **0.040 Pa·s melt viscosity** is the input to any entrainment model — this is what makes paraffin regress fast, and it is the number your CFD would need. The **373 °C degradation onset** is your grain thermal limit, which is 44 °C higher than pure wax (329 °C) because of the SEBS. Cite Bisin rather than measuring these yourselves.

---

# PART 1 — CEA

## 1.1 What CEA actually computes

CEA (Chemical Equilibrium with Applications, Gordon & McBride, NASA RP-1311) solves one problem: **given a set of reactants, their elemental composition, their enthalpy, and a pressure, what product mixture minimises Gibbs free energy?**

It does this by iterating on species mole numbers subject to elemental mass conservation, using a Newton–Raphson scheme on the Lagrangian. Once it has the equilibrium chamber state it expands the gas isentropically to the throat and to whatever area ratio you ask for, re-equilibrating at each station (or not, if you request frozen flow).

What comes out: chamber temperature, product mole fractions, molecular weight, γ, c\*, thrust coefficient, Isp, and transport properties (viscosity, Prandtl number, cp) at chamber, throat and exit.

What CEA does **not** know about: geometry, mixing, time, turbulence, injectors, combustion efficiency, heat loss, or two-phase flow. It gives you the thermodynamic ceiling. Everything between that ceiling and your test stand is engineering.

## 1.2 Getting CEA running

Three options, in increasing order of usefulness to you:

1. **CEARUN** — NASA's web front end. Fine for one-off checks, useless for sweeping 130 O/F points.
2. **The original FCEA2 Fortran** from NASA Glenn. This is the reference implementation. You compile it with gfortran and drive it with `.inp` files. Worth having if you want to read the source.
3. **RocketCEA** — a Python package that wraps the *actual NASA Fortran* via f2py. Same code, same answers, scriptable. This is what I used.

```bash
# needs a Fortran compiler first
sudo apt-get install gfortran
pip install rocketcea
```

Verify your install before trusting it. LOX/LH2 at Pc = 1000 psia, O/F = 5.55, ε = 40 should give **Isp_vac ≈ 453.6 s**. Mine did. If yours doesn't, something is wrong with the thermo library path.

## 1.3 Anatomy of an input deck

A CEA rocket deck has four blocks:

```
problem  rocket  equilibrium
   p,bar = 35
   o/f = 7.0
   sup,ae/at = 6
reac
   fuel = SasolWax0907  C 50 H 102  wt%=89.0
     h,cal=-343738.0  t(k)=298.15  rho=0.924
   oxid = NitrousOxide  N 2 O 1  wt%=100
     h,cal=17185.0  t(k)=293.15
output  siunits  transport
   plot p t isp cstar
end
```

- `problem rocket` selects the rocket-performance module. `equilibrium` vs `frozen` chooses whether composition re-equilibrates during expansion.
- `p,bar` is chamber stagnation pressure. `o/f` is oxidiser-to-fuel mass ratio.
- `sup,ae/at` is supersonic exit area ratio. You can also give `pi/p` (pressure ratio).
- Each reactant needs **four things**: elemental formula, heat of formation, reference temperature, and (optionally) density.
- `transport` is what gives you μ, Pr and cp — you need these for Bartz heat transfer and for CFD boundary conditions.

That heat-of-formation line is where nearly all student CEA errors live. Get it wrong and your flame temperature is wrong by hundreds of kelvin.

## 1.4 Building the propellant cards

This is the part that requires actual chemistry, so here is the full derivation for your fuel.

### SasolWax 0907

Sasol's own data, as reported by Bisin (2019) and Piscitelli (2018): **average composition C₅₀H₁₀₂, density 0.924 g/cm³, congealing point 83–94 °C**. Physically it is roughly 36% C34 n-paraffin and 64% C59 iso-paraffin, but for equilibrium chemistry only the C:H ratio and the enthalpy matter, so the C₅₀H₁₀₂ average is fine.

Heat of formation: **−1438.2 kJ/mol**. This is the value in the UKZN Phoenix-1B CEA deck (Balmogim 2017, Appendix B) — the same wax formula, the same oxidiser, in a peer-reviewed thesis.

Always sanity-check a ΔHf against a heat of combustion, because ΔHf values in the literature are frequently mis-transcribed:

```
C50H102 + 76.5 O2 -> 50 CO2 + 51 H2O(l)
ΔHc = [50(-393.5) + 51(-285.8)] - (-1438.2) = -32,813 kJ/mol
    = -32,813 / 0.7023 kg = -46.7 MJ/kg
```

Paraffin wax HHV is 46.5–47 MJ/kg. The value checks out.

### SEBS-g-MA (Sigma-Aldrich 432431)

The supplier page gives you what you need:

- maleic anhydride ≈ **2 wt%**
- polystyrene block = **30 wt%** (this is in the Q&A section, answered by Sigma technical support, not the spec table)
- density **0.910 g/cm³**
- Mw ≈ 100 kDa, melt index 21 g/10 min

The remaining 68 wt% is the hydrogenated poly(ethylene-*ran*-butylene) mid-block. That block is a saturated polyolefin, so treat it as (CH₂)ₙ.

Heats of formation per repeat unit:

| Block | Unit | MW | ΔHf | Basis |
|---|---|---|---|---|
| Styrene block | C₈H₈ | 104.15 | **+33.9 kJ/mol** | ΔHf(styrene, liq) = +103.8, heat of polymerisation = −69.9 |
| E/B mid-block | CH₂ | 14.027 | **−25.0 kJ/mol** | back-calculated from HDPE HHV ≈ 46.5 MJ/kg |
| Maleic anhydride | C₄H₂O₃ | 98.06 | **−469.8 kJ/mol** | standard, solid |

Per 100 g of SEBS-MA:

```
styrene:  30.0/104.15 = 0.28804 mol  ->  C 2.3043   H 2.3043
E/B:      68.0/14.027 = 4.84781 mol  ->  C 4.8478   H 9.6956
MA:        2.0/98.058 = 0.02040 mol  ->  C 0.0816   H 0.0408   O 0.0612
------------------------------------------------------------------
                                          C 7.2337   H 12.0407  O 0.0612
mass check: 7.2337(12.011) + 12.0407(1.008) + 0.0612(15.999) = 100.00 g ✓
ΔHf = 0.28804(+33.9) + 4.84781(-25.0) + 0.02040(-469.8) = -121.0 kJ per 100 g
```

So SEBS-MA enters CEA as a pseudo-species with formula **C 7.2337 H 12.0407 O 0.0612**, MW = 100, ΔHf = −121.0 kJ/mol. This is exactly the trick NASA uses for HTPB, which appears in CEA libraries as `C 7.3165 H 10.3360 O 0.1063`.

### Carbon black

Graphitic carbon: **C, ΔHf = 0, ρ = 2.1 g/cm³**. Carbon black is very slightly above graphite in enthalpy (~10 kJ/mol) but at 1 wt% it makes no measurable difference.

### The assembled fuel card

```
fuel SasolWax0907  C 50.0000 H 102.0000        wt%=89.00
h,cal=-343738.0  t(k)=298.15  rho=0.924
fuel SEBSgMA  C 7.2337 H 12.0407 O 0.0612      wt%=10.00
h,cal=-28922.6   t(k)=298.15  rho=0.910
fuel CarbonBlack  C 1.0                        wt%=1.00
h,cal=0.0        t(k)=298.15  rho=2.100
```

(`h,cal` is cal/mol — CEA's default. Divide joules by 4.184.)

**Theoretical grain density:**
```
1/ρ = 0.89/0.924 + 0.10/0.910 + 0.01/2.100  ->  ρ = 0.9278 g/cm³
```
Measure your actual cast density and compare. If you are more than ~2% below 0.928 you have voids, and voids in a paraffin grain are how you get a burn-through. Bisin notes wax shrinks 15–25% on cooling and that you must hold pressure during solidification.

## 1.5 The oxidiser — three decisions people get wrong

**Decision 1: what state is the N₂O in?**

RocketCEA ships `N2O` as ideal gas at 298.15 K (h = +19467 cal/mol). Your tank does not contain gas at 298 K — it contains **saturated liquid at ambient**, around 293 K and 50 bar. The correct reactant enthalpy is the saturated-liquid enthalpy:

```
h(184.4 K, sat. liq)  = 61.0 kJ/mol     [CEA's N2O_nbp card]
+ ∫cp,liq dT (184->293) ≈ 10.9 kJ/mol
------------------------------------------
h(293 K, sat. liq)     ≈ 71.9 kJ/mol  = 17,185 cal/mol
```

The effect: **c\* drops from 1617 to 1598 m/s (−1.2%) and Tc from 3306 to 3265 K.** Small, but it is a free 1.2% of accuracy and it is the physically defensible choice. Note this penalty is much smaller than it would be for LOX, because at 293 K nitrous is at Tr = 0.95 and its latent heat has nearly collapsed.

**Decision 2: how pure is "as pure as we can purchase"?**

I ran 99.0% N₂O with 1% N₂ as a conservative bound. Result: **c\* falls 4 m/s, 0.26%.** Purity is essentially irrelevant to your thermochemistry. Buy on the basis of the next point instead.

**Decision 3 — this is the one that matters:**

Automotive nitrous ("NOS" bottles) is **denatured with ~100 ppm sulphur dioxide** to deter inhalation abuse. This is documented in US Patent 5,579,636 in exactly the hybrid-rocket context. SO₂ will not hurt your Isp but it is corrosive in the presence of any water, and it attacks aluminium and some elastomers over time. Food-grade whipped-cream chargers also carry additives.

What you want is **medical-grade USP N₂O (≥99.0%) or aerospace-grade**, undenatured. Get a certificate of analysis and check specifically for SO₂ and for water content. Water is the bigger enemy — it drives corrosion in the tank and feed system.

One safety note that is not a CEA issue but belongs here: nitrous oxide is monopropellant-capable. It will decompose exothermically if given enough energy, and hydrocarbon contamination in the feed system lowers the activation barrier substantially. Keep hydrocarbons out of the oxidiser side, and read the Waxman paper in your project folder before you design the injector.

## 1.6 Results for your propellant

Full data is in `cea_S10W1_N2O_35bar.csv` (O/F from 1.0 to 14.0 in steps of 0.1). Plots are in `cea_S10W1_N2O_performance.png`.

**Design point, Pc = 35 bar, ε = 6, equilibrium:**

| Quantity | Value |
|---|---|
| O/F at peak c\* | **7.00** |
| c\* (ideal) | **1598 m/s** |
| Chamber temperature | **3265 K** |
| Isp, vacuum, ε=6 | 271.9 s |
| Isp, sea level, ε=6 | 243.6 s |
| γ (chamber) | 1.159 |
| Mean molecular weight | 25.87 g/mol |
| cp (chamber) | 0.83 kJ/kg·K |
| Viscosity | 0.983 millipoise |
| Prandtl number | 0.492 |

**Peak locations differ, and this matters:**

| Optimised for | Occurs at O/F | Value |
|---|---|---|
| c\* | 7.00 | 1598 m/s |
| Vacuum Isp (ε=6) | 8.10 | 273.5 s |
| Sea-level Isp (ε=6) | 8.20 | 245.4 s |
| Density Isp | 8.00 | 187 s·g/cc |

The c\* peak sits below the Isp peak because c\* only sees chamber conditions, while Isp also sees the expansion, and richer-in-oxidiser mixtures give slightly better γ and expansion behaviour. **Design to peak c\* (O/F ≈ 7), not peak Isp.** The Isp curve is very flat between 7 and 9 (less than 1 s of difference), whereas going leaner in oxidiser costs you real c\*, and a hybrid's O/F drifts upward during the burn anyway. Peak c\* puts you in the middle of that drift rather than at one end.

**Chamber species at the design point (O/F = 7, 35 bar):**

```
N2   0.511    H2O  0.169    CO   0.155    CO2  0.076
H2   0.044    OH   0.020    H    0.012    NO   0.008
```

Half the exhaust is nitrogen — that is the price of using N₂O instead of LOX. It is also why your molecular weight is a fairly high 25.9 g/mol, and why paraffin/N₂O tops out near 250 s rather than 300.

**Three findings you should act on:**

**1. The SEBS-MA is thermochemically invisible.** Peak c\* for 89/10/1 is 1598.1 m/s; for 99% wax + 1% CB it is 1598.5 m/s. A 0.03% difference. This is genuinely good news: you can tune the polymer fraction purely for mechanical properties and grain integrity without ever having to re-do performance analysis. Structural design and performance design are decoupled. Do not let anyone on the team argue that adding polymer "costs Isp" — it does not.

**2. There is a soot boundary at O/F ≈ 3.1.** Below that, CEA starts condensing solid graphite in the chamber: 1.0 mol% at O/F = 3.0, 6.9% at 2.5, 13.5% at 2.0. That is the kink you can see in the c\* curve. Two-phase flow through the throat causes real losses that CEA's equilibrium model handles only crudely, and solid carbon fouls nozzles. Your steady-state O/F of 7 is nowhere near this — but **ignition and shutdown transients pass right through it**, which is one reason hybrid start-up is sooty and why nozzle erosion tends to happen at the ends of a burn rather than the middle.

**3. Chamber pressure barely affects c\*.** From 20 to 50 bar, c\* moves 1592 → 1602 m/s, about 0.6%. Pressure buys you Isp through the *expansion* (243.6 s at 35 bar vs 252.6 s at 50 bar at sea level), not through the chemistry. So the argument for higher Pc is nozzle performance and combustion stability, not thermochemistry. Weigh that against tank and case mass.

## 1.7 Turning CEA output into a motor

CEA gives you the ceiling. Three things stand between it and your test stand.

**The O/F is an outcome, not a choice.** You set the oxidiser flow with the injector; the fuel flow is whatever the grain gives you. For paraffin/N₂O the published correlation (Karabeyoglu 2012, via Balmogim 2017 Table 3.1) is:

```
ṙ = 0.155 · G_ox^0.5        [ṙ in mm/s, G_ox in kg/m²·s]
```

with fuel flow ṁ_f = ρ_f · A_burn · ṙ = ρ_f · (π D_port L) · ṙ. As the port opens up, G_ox falls, ṙ falls, and **O/F climbs through the burn**. Your job in preliminary design is to pick an initial port diameter such that the O/F *sweeps across* 7 rather than starting there. A common approach is to start around O/F ≈ 5.5–6 and finish around 8–8.5, which keeps the burn-averaged c\* close to peak. Use the CSV as a lookup table for this — that is exactly what the Phoenix-1B code does.

Note that 0.155 is for *pure* paraffin. Adding 10% SEBS raises melt viscosity from ~0.005 to ~0.040 Pa·s at 150 °C (Bisin, Table 1), and entrainment scales inversely with viscosity. Expect your `a` coefficient to be **lower than 0.155** — this is a real trade, and it is the one place the polymer does cost you. You will have to measure it. That is what a slab burner or a series of small motors is for.

**Combustion efficiency.** Hybrids mix badly because the flame is diffusion-limited in a boundary layer. Real delivered c\* is η_c\* × ideal, with **η_c\* typically 0.90–0.95** for a well-designed paraffin motor. Dyer et al. (your Peregrine paper) report "well in excess of 90%". Balmogim uses 0.90 for design. Use **0.90 for sizing and treat anything above that as margin.**

```
η = 1.00 -> c* = 1598 m/s
η = 0.95 -> c* = 1518 m/s
η = 0.90 -> c* = 1438 m/s
```

A pre-combustion chamber and a post-combustion chamber (roughly 0.5–1 port diameter each) are the cheapest way to buy efficiency. The post-chamber is the more important of the two.

**Worked sizing**, at O/F = 7, Pc = 35 bar, ε = 6, η_c\* = 0.90, sea level (Cf = 1.495):

| Thrust | Throat dia. | Total ṁ | ṁ_ox | ṁ_fuel |
|---|---|---|---|---|
| 1000 N | 15.6 mm | 0.465 kg/s | 0.407 | 0.058 |
| 2000 N | 22.1 mm | 0.930 kg/s | 0.814 | 0.116 |
| 3000 N | 27.0 mm | 1.395 kg/s | 1.221 | 0.174 |
| 5000 N | 34.9 mm | 2.326 kg/s | 2.035 | 0.291 |

For reference, Phoenix-1B — a paraffin/N₂O motor of exactly this class — ran 5000 N at 40 bar with a 60 mm initial port, 148 mm OD and 404 mm grain length.

## 1.8 What CEA cannot tell you

Be explicit about this in your design reviews:

- Combustion efficiency, mixing quality, or whether your flame is even attached
- The regression rate (and therefore the O/F, and therefore which point on the CEA curve you are actually on)
- Anything about the injector, two-phase nitrous flow, or feed-system coupling
- Combustion instability (hybrids have a characteristic low-frequency chuffing mode)
- Heat flux to the wall — CEA gives you the *properties* to compute it, not the flux
- Nozzle erosion or throat area growth
- Transients: ignition, shutdown, blowdown tail-off

---

# PART 2 — CFD

## 2.1 Scope this honestly

The biggest failure mode I see with student teams and CFD is attempting the hardest problem first, spending six months, and getting a colourful picture nobody can validate. Hybrid combustion CFD is a genuinely open research area — entrainment of liquid droplets from a melting wall into a turbulent reacting boundary layer, with a moving boundary and significant radiation, is a PhD topic and not a settled one.

So split it into tiers and be deliberate about which you attempt:

| Tier | Problem | Difficulty | Value to you | Verdict |
|---|---|---|---|---|
| 1 | Nozzle flow + wall heat flux | Moderate | High | **Do this** |
| 1b | Cold-flow port aerodynamics (non-reacting) | Moderate | High | **Do this** |
| 2 | Reacting port flow, prescribed wall mass flux | Hard | Medium | Optional, later |
| 3 | Entrainment-coupled combustion, moving boundary | Research | Low for you | Do not attempt |
| 3b | Two-phase N₂O injector | Research | Low | Use Waxman's data instead |

Tiers 1 and 1b will give you results you can actually defend and that will change your hardware. Tier 3 will give you a picture.

## 2.2 Tier 1 — nozzle flow and throat heat flux

This is the highest-value CFD you can do, because throat heat flux sizes your nozzle material and your nozzle is the part most likely to fail.

**Setup:**

- **Axisymmetric**, 2D. A full 3D nozzle run buys you nothing unless you are studying a specific asymmetry.
- **Domain**: from the aft end of the post-combustion chamber, through convergent, throat, divergent, and out to at least 2–3 exit diameters of ambient plume so the exit boundary is not sitting on a shock.
- **Solver**: density-based, compressible, steady RANS to start.

**Inlet boundary conditions — this is the CEA→CFD link you asked about.** At the chamber inlet use a pressure-inlet with:

```
Total pressure     P0 = 35 bar
Total temperature  T0 = 3265 K            <- from CEA
Gas composition    from the CEA species table
```

You then have a choice for gas properties:

- **Simplest and recommended first pass:** treat the exhaust as a single calorically-imperfect ideal gas with **MW = 25.87 g/mol, γ = 1.159, cp = 830 J/kg·K, μ = 9.83e-5 Pa·s, Pr = 0.492** — all straight out of the CEA `transport` output. This is the *frozen* assumption.
- **Better:** import the CEA mole fractions as a fixed mixture and let the solver compute mixture properties from NASA polynomials with temperature. Still frozen chemistry, but variable cp.
- **Best and rarely necessary:** equilibrium chemistry through the nozzle, either via a lookup table generated from CEA at a range of (P, T) or via an equilibrium solver.

Frozen flow will **under-predict** Isp by roughly 1–3% relative to equilibrium, because it does not let recombination release energy during expansion. CEA gives you both, so you can bound your CFD result: your simulation should land between the frozen and equilibrium CEA values. If it lands outside that band, you have a bug.

**Turbulence:** k-ω SST. It is the standard choice for wall-bounded compressible flow with pressure gradients, which is exactly a nozzle. Resolve the boundary layer properly — **target y⁺ < 1 at the throat**, with at least 20–30 cells across the boundary layer and a growth ratio ≤ 1.2. Wall functions will give you a heat flux that is wrong by a factor you cannot predict. Heat transfer is far more sensitive to near-wall resolution than pressure is, so a mesh that gives a converged thrust may still give a badly wrong heat flux.

**Validate against Bartz before you believe anything.** The Bartz correlation is the standard semi-empirical throat heat transfer coefficient and it is what Balmogim used for the Phoenix-1B nozzle:

```
        0.026   μ^0.2 cp    P0  ^0.8   D_t ^0.1        A_t ^0.9
h_g =  ------- ( -------- )( ---- )   ( --- )    σ    ( --- )
       D_t^0.2    Pr^0.6     c*         R_c              A
```

where σ is a correction for property variation across the boundary layer. If your CFD throat heat flux is within ~20–30% of Bartz you are in reasonable shape; Bartz itself is only good to about that. If you are off by 3×, fix the mesh.

**What to extract:** wall heat flux distribution (peaks just upstream of the throat, not at it), wall temperature, and the pressure/Mach distribution. Feed the heat flux into a transient thermal FEA of the graphite or phenolic to size the throat insert. This is exactly the workflow in Chapter 5 of the Balmogim thesis, and it is worth reading — he passes CEA transport properties into Bartz, then into ANSYS for a coupled thermo-structural analysis.

**Do not forget the transient.** A 10-second burn never reaches steady state in the nozzle wall. A steady CFD gives you the gas-side boundary condition; the wall problem must be transient.

## 2.3 Tier 1b — cold-flow port and injector aerodynamics

Non-reacting, single-phase, and therefore tractable. Useful questions you can genuinely answer:

- Does the oxidiser jet from your injector impinge on the grain face and cause local erosion?
- Is the pre-combustion chamber long enough to let the jet spread before it enters the port?
- What is the recirculation structure in the post-combustion chamber, and is the residence time enough to finish combustion?
- What is the pressure drop across the grain?

Run this with N₂ or with your CEA-derived gas properties as a passive fluid. It will change your injector plate and pre-chamber geometry, which is a real hardware outcome for modest effort.

## 2.4 Tier 2 — reacting port flow

If you want to attempt this, the tractable formulation is:

- Treat the fuel surface as a **mass-flux inlet**, not a melting solid. Compute the mass flux from ṙ = 0.155·G_ox^0.5 (or your measured correlation), inject gaseous fuel at the wall temperature (~700 K surface for paraffin), and let the solver handle the diffusion flame.
- **Species transport** with a reduced mechanism. Do not attempt detailed chemistry for C₅₀H₁₀₂ — nobody has a validated mechanism for it. Use a surrogate: a one- or two-step global mechanism for a C₁₂–C₁₆ alkane plus N₂O decomposition, or an eddy-dissipation model where mixing rather than kinetics limits the rate. In a hybrid, mixing genuinely is the limiter, so EDM is defensible.
- **Include radiation.** In a sooty hybrid flame radiation is a first-order contributor to the surface heat flux, which is precisely why you have 1% carbon black in the grain. A discrete-ordinates model with a weighted-sum-of-grey-gases property model is the usual choice. Omitting radiation is a common and serious error.

What this will *not* capture is entrainment — the roll-wave instability that strips liquid droplets off the melt layer and is responsible for most of paraffin's regression rate advantage. Karabeyoglu, Altman and Cantwell's two-part 2002 JPP papers are the theory. Modelling it in CFD means a coupled VOF liquid layer with a moving interface, and it is not something to take on for a first vehicle.

## 2.5 Tools

- **OpenFOAM** — free, scriptable, good compressible solvers (`rhoCentralFoam`, `sonicFoam`) and `reactingFoam` for Tier 2. Steepest learning curve, best long-term investment, and no cell limit.
- **SU2** — free, built for compressible aerodynamics, cleaner to set up than OpenFOAM for a nozzle. Weaker on combustion.
- **ANSYS Fluent, student licence** — easiest to learn, best documentation, capable of everything above. The student version caps at 512k cells, which is enough for a 2D axisymmetric nozzle but not for 3D reacting flow.

For Tier 1 I would use Fluent student or SU2. Do not start with OpenFOAM and combustion simultaneously.

## 2.6 Validation discipline

Three things, non-negotiable:

1. **Grid convergence.** Run three meshes at roughly 1.5–2× refinement and report a Grid Convergence Index (Roache). A single-mesh CFD result is an opinion.
2. **Compare against something analytical.** 1D isentropic for the nozzle pressure and Mach distribution, Bartz for the heat flux, CEA frozen/equilibrium for the Isp bracket. If CFD disagrees with 1D isentropic in the divergent section, the CFD is wrong.
3. **Compare against your own hot-fire data.** Instrument for chamber pressure at minimum, and thrust if you can. Back out delivered c\* from Pc, throat area and total mass flow, and compare to CEA × η. That single number tells you more about your motor than any simulation.

---

## Suggested order of work

1. Reproduce my CEA numbers yourself with the deck provided. Change one thing — the wax ΔHf, say — and watch what happens. That is how you learn what the code is sensitive to.
2. Build the O/F-vs-time model using the CSV as a lookup table and the regression correlation. This tells you your initial port diameter.
3. Fix your grain and nozzle geometry from that.
4. Tier 1 nozzle CFD and Bartz cross-check. Size the throat insert.
5. Tier 1b cold-flow on the injector and pre-chamber.
6. Static fire. Measure Pc, back out η_c\*, and measure your actual regression coefficient.
7. Only then consider Tier 2.

Step 6 will teach you more than steps 4 and 5 combined. CFD is worth doing, but a hybrid motor is an empirical machine and the test stand is the real instrument.

---

## References

**In your project folder:**

- Balmogim, U. (2017). *Design and Development of the Phoenix-1B Hybrid Rocket*. MSc thesis, University of KwaZulu-Natal. — Closest analogue to your project. Chapter 3 for the CEA/HRPC methodology, Chapter 5 for nozzle thermo-structural analysis, Appendix B for a working CEA input deck and MATLAB driver.
- Dyer, J. et al. (2008). *Status Update Report for the Peregrine 100 km Sounding Rocket Project*. AIAA. — Paraffin/N₂O at flight scale, Stanford/NASA Ames/SPG.
- Waxman, B. S., Zimmerman, J. E., Cantwell, B. J., Zilliac, G. G. *Mass Flow Rate and Isolation Characteristics of Injectors for Use with Self-Pressurizing Oxidizers in Hybrid Rockets*. — Read before designing the injector. Critical-flow criterion and supercharging.
- Judson, M. I. (2015). *Direct Electrical Arc Ignition of Hybrid Rocket Motors*. MSc thesis, Utah State University.
- Crowell, G. A. (1996). *The Descriptive Geometry of Nose Cones*. — Airframe, not propulsion.

**Fuel formulation (your exact blend):**

- Bisin, R., Paravan, C., Alberti, S., Galfetti, L. (2019). *An Innovative Strategy for Paraffin-based Fuels Reinforcement: Part I, Mechanical and Pre-Burning Characterization*. EUCASS 2019-718. — S10W1 = your 89/10/1 formulation. Viscosity, TGA/DSC, compression data.
- Bisin, R., Paravan, C., Verga, A., Galfetti, L. (2019). *…Part II, Ballistic Characterization*. EUCASS 2019-728. — Regression rate data. Get this one.
- Petrova, A., Prokopyev, D., Galfetti, L. *Paraffin-based Solid Fuels Characterization and Effect of their Properties on Entrainment Phenomena*. 6th EUCASS. — Same blend as "S10G", rheology and mechanical properties.
- Piscitelli, F. et al. (2018). *Characterization and manufacturing of a paraffin wax as fuel for hybrid rockets*. Propulsion and Power Research 7(3), 218–230. — SasolWax 0907 specifically: molecular weight distribution, casting defects, shrinkage.
- Kobald, M. et al. (2014). *Evaluation of Paraffin-based Fuels for Hybrid Rocket Engines*. AIAA 2014-3646. — Comparative testing of several Sasol waxes including 0907.
- DeSain, J. et al. (2009). *Tensile Tests of Paraffin Wax for Hybrid Rocket Fuel Grains*. AIAA 2009-5115.

**Theory:**

- Gordon, S., McBride, B. J. (1994/1996). *Computer Program for Calculation of Complex Chemical Equilibrium Compositions and Applications*. NASA RP-1311 Parts I and II. — The CEA manual. Part II is the user guide; read it.
- Karabeyoglu, M. A., Altman, D., Cantwell, B. J. (2002). *Combustion of Liquefying Hybrid Propellants: Part 1, General Theory*. J. Propulsion and Power 18(3).
- Karabeyoglu, M. A., Cantwell, B. J. (2002). *…Part 2, Stability of Liquid Films*. J. Propulsion and Power 18(3). — Parts 1 and 2 are the entrainment theory that explains why paraffin works.
- Karabeyoglu, M. A., Zilliac, G., Cantwell, B. J., DeZilwa, S., Castellucci, P. (2004). *Scale-up Tests of High Regression Rate Paraffin-Based Hybrid Rocket Fuels*. J. Propulsion and Power 20(6), 1037–1045.
- Marxman, G. A., Gilbert, M. (1963). *Turbulent Boundary Layer Combustion in the Hybrid Rocket*. 9th Symposium (International) on Combustion. — The original regression rate theory.
- Chiaverini, M. J., Kuo, K. K. (eds.) (2007). *Fundamentals of Hybrid Rocket Combustion and Propulsion*. AIAA Progress in Astronautics and Aeronautics vol. 218. — The reference text. Chapter 2 for regression rate behaviour.

---

## Files

| File | What it is |
|---|---|
| `cea_S10W1_deck.py` | The propellant card definitions with full derivation in comments. Import this. |
| `cea_sweep_and_plots.py` | Runs the O/F sweeps, writes the CSV and the figure. |
| `cea_S10W1_N2O_35bar.csv` | O/F 1.0–14.0 at 0.1 steps: c\*, Tc, Isp, γ, MW, cp, μ, Pr, ρIsp. Use as a lookup table. |
| `cea_S10W1_N2O_performance.png` | Four-panel summary. |
