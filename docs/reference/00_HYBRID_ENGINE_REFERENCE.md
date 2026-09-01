# N2O / Cast-Fuel Hybrid Rocket Engine — Annotated Source Library & Design Handbook

**Scope:** the engine only — oxidizer tank, injector plate, igniter, fuel grain, combustion chamber, nozzle.
**Target vehicle:** 6 in (152 mm) filament-wound CF airframe, ~10 ft (3.05 m) body tube, foam-core CF fins, apogee 50,000 ft (15.2 km), impulse class O (~40 kN·s), nitrous oxide oxidizer, in-house cast fuel grain.

---

## 0. How to use this in VS Code

```
your-workspace/
├── 00_HYBRID_ENGINE_REFERENCE.md   <- this file
├── references.bib                  <- BibTeX for all sources
└── papers/                         <- drop the PDFs here
```

Recommended extensions:
- **Markdown All in One** — TOC, preview, math rendering
- **vscode-pdf** (tomoki1207) — opens PDFs in a VS Code tab
- **LaTeX Workshop** or **Citation Picker for Zotero** — if you cite from `references.bib`
- **Jupyter + Python** — for the internal-ballistics code you will end up writing

Quick bulk download of the open-access set (run in `papers/`):

```bash
# Direct-PDF sources, no login needed
curl -LO "https://ntrs.nasa.gov/api/citations/20190001326/downloads/20190001326.pdf"      # Waxman injectors
curl -LO "https://ntrs.nasa.gov/api/citations/20090029211/downloads/20090029211.pdf"      # Peregrine status
curl -LO "https://arxiv.org/pdf/2302.06725"                                               # McGill design model
curl -LO "https://par.nsf.gov/servlets/purl/10274228"                                     # Regression rate primer
curl -LO "https://www.eucass.eu/doi/EUCASS2019-0538.pdf"                                  # Instability study
curl -LO "https://shura.shu.ac.uk/27601/2/JPPjournal_Jungpyo_final.pdf"                   # Pre-chamber instability
curl -LO "https://core.ac.uk/download/pdf/144150075.pdf"                                  # N2O tank state estimation
```

A `.bib` file is included so you can cite everything in a report or a NASA-style paper.

---

## 1. Reading order (do not read these alphabetically)

| Stage | What you're trying to answer | Read |
|---|---|---|
| 1. Orientation | What *is* a hybrid, why is regression rate the whole ballgame | S1, S2 |
| 2. First sizing pass | How do I turn "40 kN·s to 50 kft" into a grain, throat, and tank | S3, S4, S16 |
| 3. Fuel grain | What fuel, what geometry, how do I cast it without voids | S5, S6, S7, S8, S9 |
| 4. Oxidizer tank | Self-pressurizing blowdown, ullage, COPV vs metal | S10, S11, S12, S13 |
| 5. Injector plate | The single highest-leverage part you will design | S14, S15, S17, S18, S19 |
| 6. Stability | Why your motor will chug and how to stop it | S17, S20, S21, S22 |
| 7. Igniter | Getting from cold hardware to flame-holding, reliably | S23, S24, S25 |
| 8. Nozzle & chamber | Throat sizing, erosion, ablatives, pre/post chamber | S26, S27, S28, S29 |
| 9. Flight proof | Someone who actually flew this and wrote it down | S30, S31, S32, S33 |
| 10. Safety | N2O decomposition, adiabatic compression, test-stand practice | S34, S35 |

---

## 2. Annotated source library

> **Note on these summaries.** Each entry describes *only* what that specific source contains. Where I could only access the abstract and bibliographic record rather than the full text, the entry is marked **[abstract-level]** so you know to verify details against the PDF before you quote it in a presentation.

---

### FOUNDATIONS

#### S1 — Cantwell, *Aircraft and Rocket Propulsion*, Chapter 11: Hybrid Rockets (Stanford AA283 course notes, 2024)
**Access:** Free PDF, direct download
`https://web.stanford.edu/~cantwell/AA283_Course_Material/AA283_Lectures/AA283_Chapter_11__Hybrid_Rockets_Brian_J_Cantwell_2024.pdf`
Full chapter index: `https://web.stanford.edu/~cantwell/AA283_Course_Material/AA283_Lectures`

**What this source contains:** A full textbook chapter on hybrid rocket propulsion by Brian Cantwell, who co-led the Stanford/NASA-Ames paraffin hybrid program. It is course material for AA283 (Aircraft and Rocket Propulsion) and sits in a directory alongside Chapter 7 (Rocket Performance), Chapter 9 (Thermodynamics of Reacting Mixtures) and Chapter 10 (Solid Rockets), all of which are also free PDFs and all of which you need. This is the single best starting point because it derives the hybrid combustion problem from first principles rather than presenting empirical correlations as given.

**Why you need it:** This is your NASA-presentation backbone. If you can reproduce the derivations here, you can defend any number in your design.

---

#### S2 — Karabeyoglu, *AA284a Advanced Rocket Propulsion* lecture series (Stanford / Koç University, Fall 2019)
**Access:** Free PDFs, direct download
`https://web.stanford.edu/~cantwell/AA284A_Course_Material/Karabeyoglu%20AA%20284A%20Lectures/AA284a_Lecture3.pdf` (browse the parent directory for the full set)

**What this source contains:** A complete graduate rocket propulsion lecture series by Arif Karabeyoglu — the person who discovered and characterized paraffin as a liquefying hybrid fuel. Lecture 1 covers propulsion fundamentals, the rocket equation, and a taxonomy placing hybrids alongside liquid and solid systems. Lecture 3 covers thermodynamics and chemistry review (open/closed/adiabatic systems, heat and work transfer). Lecture 4 covers thermochemistry and propellants — specifically how to get from reactants, O/F ratio, chamber pressure and reactant temperature to flame temperature, product composition, c\* and Isp using equilibrium thermodynamics, and it explicitly notes the limits of equilibrium methods (it cannot tell you reaction rates or whether reactions complete — that needs kinetics).

**Why you need it:** The thermochemistry lectures are exactly the theory behind running NASA CEA, which is the tool you will use to pick your O/F ratio.

---

### FIRST-PASS SIZING & INTERNAL BALLISTICS

#### S3 — *A computational model for the design of a nitrous oxide–paraffin wax hybrid rocket engine* (McGill Rocket Team, arXiv 2302.06725)
**Access:** Free PDF — `https://arxiv.org/pdf/2302.06725`

**What this source contains:** A complete, transparent, control-volume design model for exactly your propellant combination, written for a student team. It breaks the engine into control volumes: CV1 the oxidizer tank, CV2 the equilibrium combustion chamber, and downstream the nozzle. For the combustion chamber it models a hollow cylindrical fuel grain and applies the semi-empirical regression rate law

  dr_f/dt = a · G_o^n = a · (ṁ_o / (π r_f²))^n

and states its assumptions explicitly: constant oxidizer mass flow from tank to chamber, chamber pressure constant in both time and axial position, axially uniform grain regression, ideal-gas combustion products, and adiabatic chamber walls. The acknowledgements document that this model was developed to support the McGill Rocket Team's first hybrid engine ("Maelström"), its permanent hybrid engine test facility, and the team's first hybrid-powered launch vehicle ("Athos").

**Why you need it:** This is your template. It is a real student team's engine model, published openly, with every assumption stated. Port it to Python, then start relaxing the assumptions.

---

#### S4 — *A Primer on Classical Regression Rate Modeling in Hybrid Rockets*
**Access:** Free PDF — `https://par.nsf.gov/servlets/purl/10274228`

**What this source contains:** A tutorial paper on classical hybrid regression rate theory. Its reference list is effectively a curated map of the field and includes Zilliac & Karabeyoglu's regression rate data compilation (AIAA 2006-4504); Karabeyoglu et al.'s scale-up tests of high-regression-rate paraffin-based fuels (JPP Vol. 20 No. 6, 2004, and AIAA 2003-1162); Marxman-lineage turbulent boundary layer combustion work; Mickley & Davis on momentum transfer over a flat plate with blowing (the NACA report that underpins the blowing-correction term); Knuth et al. on vortex hybrid regression behavior; Yuasa et al. and Sakurai et al. on swirling-oxidizer-flow hybrid engines including a 5 kN class motor; and Bellomo et al. on unidirectional vortex injection.

**Why you need it:** It teaches you *why* the ṙ = aG^n law has the form it does, and where it breaks — which is what a NASA reviewer will ask you.

---

### FUEL GRAIN

#### S5 — Doran, Dyer, Lohner, Dunn, Cantwell, Zilliac, *Nitrous Oxide Hybrid Rocket Motor Fuel Regression Rate Characterization* (AIAA 2007-5344 / 43rd JPC)
**Access:** ResearchGate — `https://www.researchgate.net/publication/268482626`

**What this source contains:** The Stanford lab-scale N2O regression-rate test campaign. Reports that adding 10% paraffin to sorbitol markedly increased regression rate, approaching the SP1A paraffin baseline, with stable combustion. Notes that SP1A data showed significant scatter, making direct comparison difficult with a small number of tests. Reports that aluminized grains generally regressed at or above the baseline fuel rate, but that long-duration burns were not possible in these tests because the fast regression rate combined with the small grain diameter burned through the web — which is what motivated fabricating a larger-diameter test article. Discusses the advantage of cast grains: additives can be blended in during fabrication. States that aluminum is a typical additive because it increases fuel density and peak Isp and *decreases* the optimum O/F, which means the vehicle carries less oxidizer — but warns these gains can be outweighed by reduced combustion efficiency and increased nozzle erosion. Aluminum loadings tested ranged from 5% to 20% by mass, primarily using 2 μm aluminum powder.

**Why you need it:** This is the direct experimental basis for your fuel formulation decision, including the honest downsides of aluminizing.

---

#### S6 — *Fuel Regression Rate in a Paraffin-HTPB Nitrous Oxide Hybrid Rocket* **[abstract-level]**
**Access:** ResearchGate — `https://www.researchgate.net/publication/268343388`

**What this source contains:** Characterization of regression rates for three traditional hybrid fuels plus one novel fuel using nitrous oxide as oxidizer. Reports that a robust test facility was developed at Stanford for this study and for future hybrid programs, allowing rapid successive hot fires and testing of multiple fuel grain configurations. Related results reported alongside it: paraffin regresses roughly five times faster than PMMA; mixed paraffin-polymer fuels regress slower than pure paraffin but still 2–3× faster than PMMA. A companion study cast plain HTPB, plain paraffin, and HTPB loaded with 10–75% molten paraffin, evaluated them by thermogravimetric analysis, and burned cylindrical grains in gaseous oxygen at oxidizer mass fluxes of 10–130 kg/m²·s and pressures below 0.9 MPa; plain paraffin showed a 300% regression rate increase over plain HTPB, but none of the *mixed* formulations showed notable enhancement at those conditions.

**Why you need it:** It quantifies the paraffin-vs-HTPB trade and warns you that blending does not linearly buy you paraffin's regression rate.

---

#### S7 — Liu et al., *Regression rate of paraffin-based fuels in hybrid rocket motor* (Aerospace Science & Technology, 2020) **[abstract-level]**
**Access:** ScienceDirect (paywalled) — `https://www.sciencedirect.com/science/article/abs/pii/S1270963820309512`

**What this source contains:** Static-fire characterization of paraffin-based fuel regression rate with both N2O and GOX, evaluating the effect of combustion catalyst, injector type, and chamber pressure. Key findings stated: average regression rates with GOX and N2O are *similar* at the optimal O/F ratio, but the exponent *n* is larger with GOX, indicating higher sensitivity to oxidizer mass flux. Average regression rate increased with swirl number Sg, and a tangential injector with Sg = 6.83 improved regression rate significantly. With a jet (axial) injector the local regression rate was constant along the grain axis; with swirl injection a complex local regression rate profile appeared over the first half of the grain.

**Why you need it:** This is the paper that tells you N2O and GOX test data are cross-comparable at optimum O/F — which lets you use the much larger GOX literature to inform your N2O design.

---

#### S8 — *Microcrystalline paraffin wax as fuel for Hybrid Rocket Engine* and *Characterization and manufacturing of a paraffin wax as fuel for hybrid rockets*
**Access:** ResearchGate `.../290095691` and `.../327340831`; the latter is also on ScienceDirect as `S2212540X18300452`

**What this source contains:** Direct treatment of the casting problem. States that paraffin exhibits high shrinkage during solidification, producing cavities, cracks and internal rips that damage mechanical properties and structural integrity; quantifies liquid-to-solid shrinkage at **17–19%**, and identifies two void sources — entrapped air bubbles during pouring, and shrinkage on cooling. Presents calorimetric, thermo-mechanical and physical characterization of the selected wax. Reports that of the manufacturing methods investigated, only lab-scale processes using a **heated circular mould-piston apparatus applying both high temperature and pressure** avoided critical defects. Reports that pressure of approximately 1.0 MPa was applied to fuel samples during cooling and solidification to counteract shrinkage. Notes that centrifugal (spin) casting is used at higher scale but requires an expensive machine and non-trivial optimization of spinning rate, melt temperature and flow rate; a companion effort optimized centrifugal casting at 2.5 kg scale and successfully scaled to 25 kg grains meeting mechanical design specifications. Also notes paraffin transitions to a different solid phase after cooling.

**Why you need it:** This is your fuel-grain manufacturing SOP. Void content is the #1 cause of student hybrid grain failure and this tells you the two fixes: pressure during cure, or spin casting.

---

#### S9 — Veale, Adali, Pitot, Brooks, *A review of the performance and structural considerations of paraffin wax hybrid rocket fuels with additives* (Acta Astronautica 141, 2017) **[abstract-level]**
**Access:** ScienceDirect (paywalled) — `https://www.sciencedirect.com/science/article/abs/pii/S0094576517311384`; copy on Academia.edu

**What this source contains:** A review linking regression-rate test results for various additives against the available *structural* characterization data for those same fuel mixtures, specifically to assess launch-application feasibility. Explains hybrid vs solid combustion (oxidizer separated from grain; port count set by regression rate and required thrust). States that paraffin has high regression rate but poor mechanical properties, and that additives including EVA (ethylene vinyl acetate) and SEBS (styrene-ethylene-butylene-styrene) are used as strengthening agents with significant effect on mechanical properties. Notes that metal additives (metal hydrides, aluminum, boron) generally improve regression rate, but that very little attention has been paid to their structural effects on the wax grain, and that adding metal particles both promotes combustion instabilities and creates obvious casting difficulties.

**Why you need it:** It is the only source I found that treats grain *structural* integrity as a first-class design variable rather than an afterthought. For a 50 kft flight with high acceleration loads, this matters.

---

### OXIDIZER TANK

#### S10 — Zimmerman, Waxman, Cantwell, Zilliac, *Review and Evaluation of Models for Self-Pressurizing Propellant Tank Dynamics* (AIAA 2013-4045)
**Access:** Free PDF — `https://www.ibb.ch/publication/N2O/AIAA%202013-4045%20.pdf`

**What this source contains:** A side-by-side evaluation of the candidate models for how a self-pressurizing N2O tank actually empties. States directly that the equilibrium model does not capture the initial transient behaviour and often over-predicts pressure, but is the simplest model and requires only saturation properties. Situates itself against the Dyer et al. injector flow model, Solomon's two-phase saturated-fluid orifice model (Utah State PhD, 2011), the Hesson & Peck two-phase CO2 orifice work (AIChE 1958), and Zimmerman's own N2O-vs-CO2 comparison for tank expulsion dynamics.

**Why you need it:** Your entire thrust curve is set by tank blowdown. Pick the wrong model and your 50 kft prediction is fiction. This paper tells you which model to pick and what it will get wrong.

---

#### S11 — *Nitrous Oxide State Estimation in Hybrid Rocket Oxidizer Tanks*
**Access:** Free PDF — `https://core.ac.uk/download/pdf/144150075.pdf`

**What this source contains:** A modelling and estimation study of N2O tank state during a burn, validated against test data. States its modelling assumptions explicitly: the injector requires a finite time to fully open, modelled as a delay with time constant τ; a mixture of liquid oxidizer and oxidizer gas exits through the injector; oxidizer gas density is modelled with the ideal gas law; helium (if present as a supercharge gas) remains in the initial ullage region and does not exit the tank while liquid oxidizer remains; and the gas leaving the tank is nitrous bubbles forming within the primarily-liquid phase near the injector port, at the same pressure as the surrounding liquid. Notes the physical implication that to reduce simulated oxidizer pressure, simulated system temperature must be lower.

**Why you need it:** This is the practical, instrumented version of S10 — it tells you what actually comes out of the tank, including two-phase quality at the injector inlet, which is what sets your injector sizing.

---

#### S12 — Williams, *Development of a composite oxidiser tank for the Phoenix-1B Mk. II hybrid rocket* (MSc, University of KwaZulu-Natal, 2020)
**Access:** Free PDF — `https://researchspace.ukzn.ac.za/items/c126df97-fe02-40bc-ba69-6d3cfa406604/full` (file: `Williams_Dylan_Roy_2020.pdf`, 5.69 MB)
Project page: `https://aerospace.ukzn.ac.za/rocket-projects/phoenix/phoenix-1b-mk-ii/`

**What this source contains:** A full masters thesis on designing and building a filament-wound composite N2O tank for a flight vehicle — which is precisely your airframe technology. Per the associated project documentation: the tank was designed to reduce vehicle inert mass relative to the Mk I's aluminium tank; it was manufactured on a **4-axis filament winding machine using T800 carbon/epoxy**; the liner was formed from **uPVC pipe with aluminium bulkheads**, chosen specifically because of nitrous oxide material-compatibility constraints and material availability; and the tank was designed for a **maximum expected operating pressure of 80 bar with a minimum safety factor of 2.25 across all loading conditions**, with bulkheads fixed using stainless fasteners. The parent vehicle (Phoenix-1B Mk II) is a 4.92 m single-stage unguided sounding rocket, 0.17 m diameter at the tank and 0.164 m at the motor, 47 kg inert / 41 kg propellant / 88 kg total, carrying 34 kg N2O and 7.05 kg of paraffin with 20% aluminium, targeting 35 km apogee.

**Why you need it:** You are filament-winding carbon fibre. This is a documented, flight-intent composite N2O tank with a stated liner strategy, MEOP and safety factor. Read the liner section carefully — N2O compatibility with epoxy is a real hazard.

---

#### S13 — *On the Multidisciplinary Design of a Hybrid Rocket Launcher with a Composite Overwrapped Pressure Vessel* (J. Composites Science 8(3), 2024)
**Access:** Free (MDPI open access) — `https://www.mdpi.com/2504-477X/8/3/109`

**What this source contains:** A multidisciplinary design optimization study quantifying the impact of using composite overwrapped pressure vessels as the oxidizer tank on a paraffin/NOx hybrid launcher, versus conventional metallic vessels. Describes the COPV type classification, noting Type III and Type IV vessels use composites to reduce weight and increase compressed-gas storage efficiency in aerospace, and that Type V has potential to increase storage efficiency further. Uses NIST thermophysical fluid property data (Lemmon, Bell, Huber, McLinden) for the oxidizer.

**Why you need it:** It gives you the *systems-level* argument for why the composite tank is worth the manufacturing pain — i.e. how many feet of apogee you buy per kg of inert mass removed.

---

### INJECTOR — the highest-leverage part you will design

#### S14 — Waxman, Cantwell, Zilliac, Zimmerman, *Mass Flow Rate and Isolation Characteristics of Injectors for Use with Self-Pressurizing Oxidizers in Hybrid Rockets* (AIAA 2013-3636)
**Access:** Free PDF via NASA NTRS — `https://ntrs.nasa.gov/api/citations/20190001326/downloads/20190001326.pdf`

**What this source contains:** The core injector paper for N2O hybrids, and the one that reframes the injector as a *stability* device, not just a metering device. It notes there is limited open literature on N2O feed systems covering tanks, feed lines, valves and injectors, and states that injector design has a dramatic effect on overall engine efficiency and stability. It defines the job of a properly designed injector as delivering the required oxidizer mass flow rate to the chamber *while sufficiently atomizing the liquid to allow rapid droplet vaporization*. Its central finding: the existence of **two-phase flow at the injector can attenuate pressure fluctuations travelling upstream**, providing a degree of isolation between chamber and feed system — this is the mechanism governing feed-system-coupled combustion instabilities in N2O hybrids. Builds on the Dyer et al. 2007 feed system model, Hesson & Peck (1958), Henry & Fauske's two-phase critical flow through nozzles/orifices/short tubes (J. Heat Transfer, 1971), and Leung's generalized correlation for one-component homogeneous-equilibrium flashing choked flow (AIChE).

**Why you need it:** If you read one injector paper, read this one. Free, from NASA, and it explains the failure mode that kills most student N2O hybrids.

---

#### S15 — Dyer, Doran, Dunn, Lohner, Zilliac, Cantwell, *Modeling Feed System Flow Physics for Self-Pressurizing Propellants* (AIAA 2007-5702) **[abstract-level]**
**Access:** ResearchGate `.../268482381`; Semantic Scholar record; AIAA `10.2514/6.2007-5702`

**What this source contains:** The origin of the **NHNE (non-homogeneous, non-equilibrium) injector model** that essentially the entire N2O community now uses. States the problem: self-pressurizing propellants like N2O have high vapor pressure at low temperature and can be expelled without an external pressurant, saving mass and complexity — but performance prediction is much harder because of two-phase thermodynamics and mass transfer kinetics, and because at useful propulsion pressures the liquid is not incompressible and the vapor is not ideal. Presents the Dyer correlation as a weighted trade-off between the Homogeneous Equilibrium Model mass flow and the Single-Phase Incompressible model mass flow. Figures listed include: calculated density errors for N2O using Peng-Robinson vs Span-Wagner equations of state; a T-s diagram for N2O with vapor dome, isobars and isenthalps; a conceptual injector element pressure history; the metastable extension of an N2O isotherm and isentrope from Span-Wagner; and measured vs predicted flow rates for a range of **sharp-entrance short-tube injectors** used on the Stanford subscale hybrid test stand.

**Why you need it:** This is the equation you will actually code to size your orifices. Note "sharp-entrance, short tube" — that geometry is not accidental.

---

#### S16 — Waxman, *An investigation of injectors for use with high vapor pressure propellants with applications to hybrid rockets* (PhD dissertation, Stanford University)
**Access:** Stanford Digital Repository — `https://purl.stanford.edu/ng346xh6244`

**What this source contains:** The full-length dissertation behind S14. States that N2O exhibits ≈730 psia (5.03 MPa) vapor pressure at room temperature, which is why it self-expels without pumps or a pressurization system — giving weight savings and design simplicity, plus storability, ease of handling and relative safety versus traditional liquid oxidizers. States the core design difficulty: feed system pressures often drop below vapor pressure, *especially inside the injector*, so injectors are likely to cavitate, forming vapor and choking mass flow. Reviews the available two-phase flow models and concludes **none is reliable enough to replace experimental injector flow studies** — which is why a small-scale N2O cold-flow rig was designed and a test campaign run across a broad range of operating conditions. Reports that the Peregrine program had been hampered for years by combustion instability, and that the small-scale injector results produced a "powerful, yet simple" solution to feed-system-coupled instability, plus a new class of injector designed specifically to reduce the likelihood of that instability.

**Why you need it:** The explicit statement that no model replaces cold-flow testing is the most important sentence in your entire injector development plan. Budget for a cold-flow rig.

---

#### S17 — Bertoldi et al., *Performance comparison of oxidizer injectors in a 1-kN paraffin-fueled hybrid rocket motor* (Acta Astronautica / Aerospace Science & Technology) **[abstract-level]**
**Access:** ScienceDirect (paywalled) — `https://www.sciencedirect.com/science/article/abs/pii/S1270963818320157`; a related open version exists as *Experimental investigation of the axial oxidizer injectors geometry on a 1-kN paraffin-fueled hybrid rocket motor* at `https://www.sciencedirect.com/science/article/pii/S2667134421000584`

**What this source contains:** Four injector types designed, manufactured and tested **in the same motor**, which is what makes it uniquely useful: showerhead (SH), hollow-cone (HC), pressure-swirl (PSW) and vortex (VOR). The authors explicitly motivate the work by noting that experimental N2O/paraffin firing data is poorly represented in the open literature. Method: cold tests first with liquid water and liquid nitrous oxide to observe spray profiles, then hot fires. Analyzes injector influence on fuel regression rate, specific impulse and combustion efficiency, and determines the influence of fuel port diameter on motor efficiency plus the regression rate law for N2O.

The companion axial-injector paper gives concrete plate geometry: **SH1 has 11 orifices of 1.4 mm diameter, distributed on two radii plus one central hole** to spread oxidizer evenly, delivering ~400 g/s of liquid N2O. Three further plates (SH2, SH3, SH4) were designed from the SH1 results with oxidizer mass flow fixed at 550 g/s for fair comparison: SH2 is SH1 with larger orifices (higher flow at the same 60 bar feed pressure), while SH3 and SH4 differ in orifice count and distribution density across the plate face.

Related findings cited in the same literature: Knuth et al. reported vortex injectors inducing regression rates up to ~8× a classical hybrid; Yuasa et al. achieved ~3× with head-end vortex GOX injection; Bellomo et al. measured up to **51% regression rate increase with vortex-injected liquid N2O, with lower chamber instability than axial injection**.

**Why you need it:** This is the closest thing in the literature to a controlled experiment on injector plate design for your exact propellants. The SH1–SH4 progression is a design methodology you can copy directly.

---

#### S18 — *Design of Injector Plates for Hybrid Rocket Motors Test Bench with Gaseous Oxygen* **[abstract-level]**
**Access:** ResearchGate — `https://www.researchgate.net/publication/373822615`

**What this source contains:** A CAD-plus-CFD design study of four injector plate geometries (axial, conical, and two swirl variants). Reports that **Swirl type 1 gave the highest regression rate, followed by conical, then axial, then swirl type 2**, but that the **conical injector gave the worst efficiency** — the authors attribute this to a relatively large amount of grain chunks being exhausted through the nozzle due to paraffin's poor mechanical properties, while both swirl designs showed good specific-impulse efficiency. Describes the numerical simulation setup for each injector including control volume, boundary conditions and mesh.

**Why you need it:** It is a caution: the injector that maximizes regression rate is not necessarily the injector that maximizes efficiency, because aggressive injection tears your soft paraffin grain apart.

---

#### S19 — *Classification of Angled-Hole Oxidizer Injector Designs for Hybrid Rockets, and Experimental Study of Hole Angle on Discharge Coefficients* (McGill Rocket Team, AIAA 2026-2872) **[abstract-level]**
**Access:** AIAA — `https://arc.aiaa.org/doi/10.2514/6.2026-2872`

**What this source contains:** A framework paper written explicitly as a **general resource for the design, analysis and modeling of orifice-plate oxidizer injectors**, from a student team's perspective. States that the McGill Rocket Team currently uses an axial-hole orifice-plate (showerhead) design and wanted to evaluate angled-hole variants — vortex, hollow-cone and impinging — for combustion stability and efficiency gains. Develops a framework for understanding the angular components of any orifice-plate hole and their anticipated effects on stability and efficiency, compares the effects of swirling, diverging and impinging oxidizer flow on combustion performance parameters, and summarizes the relevant literature as a pointer set for further research. Includes an experimental study of hole angle effect on discharge coefficient.

**Why you need it:** This is the most directly applicable "how do I actually lay out holes in a plate" source I found, written by a student team at roughly your level, and recent.

---

### COMBUSTION STABILITY

#### S20 — *Role of Precombustion Chamber Design in Feed-System Coupled Instabilities of Hybrid Rockets* (Journal of Propulsion and Power)
**Access:** Free author PDF — `https://shura.shu.ac.uk/27601/2/JPPjournal_Jungpyo_final.pdf`

**What this source contains:** Extends feed-system-coupled instability theory to include injector pressure drop, pre-combustion chamber residence time, gas residence time, and combustion time lag, analyzed via a transfer function using stability-limit analysis and root locus. Finds the **pre-combustion chamber configuration plays a major role** in the nature of feed-coupled instabilities, and proposes a correlation predicting the fundamental oscillation frequency from oxidizer pre-chamber residence time. Concludes that **pre-combustion chamber length and oxidizer injection velocity are the key parameters** setting the pressure oscillation period.

It also reports the decisive experimental comparison: in a University of Brasília test, a **showerhead injector with 19.1 bar pressure drop gave very stable combustion**, while a **single-hole axial injector showed severe pressure oscillations**. The stated mechanism: injectors with multiple small-diameter orifices act as a flow isolation element, decoupling the motor from the feed system and blocking upstream propagation of chamber pressure disturbances. Notes that injector geometry has much less influence on feed-coupled instability once pressure drop is large. For modelling, assumes the N2O entering the pre-chamber is 50% liquid / 50% gas (quality χ = 0.5) to compute injector exit velocity.

**Why you need it:** This gives you two concrete, actionable design rules — many small holes, and a deliberately-sized pre-combustion chamber — plus the theory to defend them.

---

#### S21 — *Theoretical and Experimental Study of Combustion Instability* (EUCASS 2019-0538)
**Access:** Free PDF — `https://www.eucass.eu/doi/EUCASS2019-0538.pdf`

**What this source contains:** Analysis of two lab-scale 1 kN hybrid rockets using liquid N2O, both of which exhibited feed-system-coupled instability during testing. Separates and analyses the **combustion time delay of the liquid oxidizer (τ₁)** from the **combustion time delay of the solid fuel (τ₂)**. States that the oxidizer characteristic time τ₁ is computed from the pre-chamber length L_pc and the effective axial velocity in the pre-chamber, where that velocity is taken as an average between the oxidizer velocity at the injector plate (u_inj) and the velocity at the grain entrance. Notes that when unstable combustion occurs in a bulk-mode chamber, physical quantities change together, and that N2O hybrids present a multi-flow-pattern problem rather than a single-phase one.

**Why you need it:** It gives you the actual time-lag formulation, with the geometry inputs, so you can compute your predicted chug frequency before you build.

---

#### S22 — *Low-Frequency Combustion Instability Induced by the Combustion Time Lag of Liquid Oxidizer in Hybrid Rocket Motors* **[abstract-level]**
**Access:** ResearchGate — `https://www.researchgate.net/publication/260566402`

**What this source contains:** A theoretical and experimental study concluding that the parameter **Δp/p_c — pressure drop between tank and chamber, normalized by mean chamber pressure — plays the dominant role** in chamber pressure oscillation characteristics. Modifies feed-system-coupled instability theory with a combustion time-lag model and proposes a new general analysis criterion showing good agreement with experiment. Its notable conclusion: the **combustion time delay of the liquid oxidizer matters more than the response time of the solid fuel boundary layer**. Also references stability-map plotting of experimental points against the theoretical stability limit.

**Why you need it:** Δp/p_c is your single most important stability number. See §4 for the practical threshold.

---

### IGNITER

#### S23 — *Direct Electrical Arc Ignition of Hybrid Rocket Motors* (MS thesis, Utah State University)
**Access:** Free PDF — `https://digitalcommons.usu.edu/cgi/viewcontent.cgi?article=5171&context=etd`

**What this source contains:** A full thesis on hybrid ignition, opening with a survey of every historical ignition approach: hypergolic reactants, low-voltage resistive elements, augmented high-voltage spark (liquid bipropellant torch), pyrotechnics, catalyzed monopropellants, and high-power plasma arcs — and positions direct high-voltage arc ignition as distinct from all of them. States the two things a hybrid igniter must do: deliver enough energy to **pyrolyze the solid fuel**, *and* retain enough residual energy to **initiate combustion**. Notes that restartability is commonly claimed as a hybrid advantage but that the difficulty lies specifically in igniter design, not in shutting the motor off. Includes a figure of a multi-stage pyrotechnic igniter, and notes the Shuttle used a four-stage ignition sequence. Reports Whitmore et al.'s finding that with N2O, ABS combustion temperature is lower than HTPB but the products have lower molecular weight, yielding **equivalent c\* and Isp**, with comparable regression rates — meaning ABS can substitute for HTPB without major performance loss.

**Why you need it:** Best single free document on hybrid ignition. Even if you go pyrotechnic, the requirements framing (pyrolyze + initiate) is what you present to NASA.

---

#### S24 — Whitmore et al., *Further Development of a Low-Energy Arc-Ignition System for Nytrox/ABS Hybrid Propulsion Systems* (Aerospace 13(4), 2026)
**Access:** Free (MDPI open access) — `https://doi.org/10.3390/aerospace13040366`

**What this source contains:** Development of a non-pyrotechnic arc ignition system. Reports that with 3D-printed ABS as fuel, **typical startup sequences require approximately 5–15 joules**, and once started the system can be re-fired sequentially with no additional energy input, limited only by remaining fuel. Explains the mechanism: high-voltage low-wattage charge across layered thermoplastic causes electrostatic arcing along the printed surface features, pyrolyzing a small amount of material which, introduced simultaneously with oxidizer flow, "seeds" combustion and produces immediate ignition **along the entire length of the fuel port**. Discusses Nytrox (a GOX/N2O blend) as a way to improve propellant density and volumetric efficiency while retaining acceptable Isp, noting Nytrox self-pressurizes safely and eliminates a separate pressurization system. References a flight-proven case: a 10 N thruster with an additively manufactured grain flown from Wallops Flight Facility reached 172 km and operated successfully five times in hard vacuum.

Related work from the same group reports a **low-voltage** variant achieving successful combustion and flame-holding with air and/or nitrous oxide using as little as **40 V DC for 1 second**, via resistance heating of electrically conductive plastic fuels, and over 100 combustion experiments with HDPE/N2O and PLA/N2O demonstrating reignition five times at atmospheric pressure.

**Why you need it:** If you can print an ABS igniter section at the head end of your paraffin grain, you get a restartable, non-pyrotechnic, ~10 J igniter with no explosives paperwork. That is a genuinely strong NASA-presentation talking point.

---

#### S25 — *Igniter design overview* (IOP Conf. Series: Materials Science and Engineering 973, 012004)
**Access:** Free PDF (open access) — `https://iopscience.iop.org/article/10.1088/1757-899X/973/1/012004/pdf`

**What this source contains:** A clean taxonomy of the two main igniter families. **Pyrogen igniter:** effectively a small rocket motor used to ignite a larger one; not designed to produce thrust; its objective is to produce enough energy output to ignite a large-scale motor; must be kept as small and light as possible; may have one or more nozzles, and in most cases its nozzle is subsonic. **Pelleted pyrotechnic igniter:** uses solid energetic material, delivering a large amount of energy in a very short time; with proper design no shockwave is produced, which avoids ignition pressure spikes that could damage the propellant's mechanical properties. Tabulates different pyrotechnic compositions and their relevant properties.

**Why you need it:** Short, free, and gives you the correct vocabulary plus the "no pressure spike" design constraint — which matters enormously for a soft cast paraffin grain.

---

### NOZZLE & CHAMBER

#### S26 — Balmogim, *Design and development of the Phoenix-1B hybrid rocket* (MSc, University of KwaZulu-Natal, 2017)
**Access:** Free PDF — `https://researchspace.ukzn.ac.za/server/api/core/bitstreams/9952f9a0-ff2c-467e-9d5a-1ee7320982ca/content`
Record: `https://researchspace.ukzn.ac.za/items/7b4cc369-05f3-4de4-aa13-fa0bb12c0687/full`

**What this source contains:** Possibly the most directly transferable document in this entire list. It is a masters thesis whose stated focus is **the propulsion system, with specific attention to the nozzle and injector designs**, for a paraffin/N2O sounding rocket. Context: South Africa's Phoenix-1A launched in August 2014 and suffered **nozzle and parachute failures in flight** which, combined with a reduced oxidizer load, cut apogee from a nominal 10 km to 2.5 km — so the thesis is explicitly a failure-driven redesign.

Contents include: analysis of Phoenix-1A shortcomings as the design starting point; an aerodynamic study of a 1 m ¾-parabolic nose cone and four tapered swept fins; **finite element analysis of the aluminium oxidiser tank and combustion chamber bulkheads to guarantee an operational safety factor above 1.5**; pressure testing of the oxidiser tank and combustion chamber assemblies to **80 bar and 60 bar** respectively; and an analysis of aluminium loading in the paraffin grain showing a potential **23 kg rocket mass reduction going from pure paraffin to 40% aluminium**, but with combustion temperature rising from **3300 K (pure paraffin) to 3600 K (40% Al)**. That temperature rise drove an **iterative transient thermo-structural analysis of the nozzle** to produce a design able to survive it. The thesis also records the Phoenix-1A ignition problem: during ignition the main oxidiser valve was first opened only partially to 25% to avoid igniter blow-out and motor hard start; and it discusses hot-gas recirculation downstream of the injector to heat expanding N2O and promote oxidiser vaporisation, noting the injector was changed to an **axial design for the flight test**.

From the associated project documentation: the resulting Phoenix-1B nozzle **consists of silica-phenolic convergent and divergent sections, a graphite throat, and a steel retaining structure**, designed via thermo-structural analysis to survive increased combustion temperature and erosion at 40% aluminium loading.

**Why you need it:** Nozzle *and* injector, for your propellants, with a real flight failure driving the design, plus stated safety factors and proof-test pressures. This is your primary nozzle reference.

---

#### S27 — Zilliac, Story, Karp, Jens, Whittinghill, *Combustion Efficiency in Single Port Hybrid Rocket Engines* (AIAA 2020-3746) **[abstract-level]**
**Access:** AIAA `https://arc.aiaa.org/doi/abs/10.2514/6.2020-3746`; copy on ResearchGate `.../343707061`

**What this source contains:** A synthesis paper on why single-port hybrids underperform. States that reported ground-test **c\* efficiency for single-port hybrids ranges from 55% to 97%** — an enormous spread. Identifies the characteristic behaviour: efficiency often **starts high at the beginning of a burn and decreases as the fuel port opens up**. States that differences in interior geometry, propellants, injector design, **post-combustion chamber design**, mixing devices and measurement technique have made it hard to isolate the causes, and applies fluid-mixing and chemical-kinetics reasoning plus open-literature data to identify what actually drives high combustion efficiency. Its reference list includes Karabeyoglu et al.'s High Performance Hybrid Upper Stage Motor (AIAA 2011-6025), Zilliac et al.'s Peregrine Hybrid Rocket Motor Development, Whittinghill's Mars Ascent Vehicle Hybrid Rocket Design & Testing final report to JPL (Jan 2020), and Gordon & McBride's CEA.

**Why you need it:** Your c\* efficiency directly multiplies your Isp and therefore your apogee. This paper is the state of the art on how to not lose 20% of your performance to poor mixing.

---

#### S28 — *Evaluation of a Paraffin/Nitrous Oxide Hybrid Rocket Motor with a Passive Mixing Device* (JPP 38(6), 2022) **[abstract-level]**
**Access:** AIAA — `https://arc.aiaa.org/doi/abs/10.2514/1.B38659`

**What this source contains:** Evaluation of a passive mixing device (diaphragm-class) in a paraffin/N2O motor. States a specific quantitative stability limit: **exceeding the identified limit results in combustion oscillations in excess of 20% of mean chamber pressure**. Its reference set is the diaphragm literature: Grosse's "Effect of a Diaphragm on Performance and Fuel Regression of a Laboratory Scale Hybrid Rocket Motor Using Nitrous Oxide and Paraffin" (AIAA 2009-5113) — which is the single most relevant diaphragm paper for your propellants — Bellomo et al. on diaphragm effects on hybrid efficiency (JPP 30(1), 2014, pp. 175–185), and Tian et al. on segmented-grain combustion characteristics.

**Why you need it:** A diaphragm or mixing plate between grain and post-chamber is a cheap, passive way to recover several percent of c\* efficiency. This tells you it works and where the stability cliff is.

---

#### S29 — *Erosion Rate Investigation of Various Nozzle Materials in Hybrid Rocket Motors* **[abstract-level]**
**Access:** ResearchGate — `https://www.researchgate.net/publication/343705098`

**What this source contains:** Direct treatment of the nozzle erosion problem. States that carbon graphite is one of the most widely used ablative nozzle materials in hybrid propulsion because of low cost and wide availability, and that its **erosion directly reduces chamber pressure and Isp**, with long-burn upper stages suffering most. Investigates a mitigation strategy: change fuel composition to reduce oxidizing species reaching the nozzle and create a **protective liquid fuel film on the nozzle surface**. Uses paraffin-based fuel with aluminium powder added **as a fuel ring at the front of the grain** rather than blended throughout — explicitly because that approach scales to larger motors. Reports that in GOX tests, aluminium addition **decreased nozzle erosion rate and delayed erosion onset**.

**Why you need it:** Your Phoenix-1A cautionary tale (S26) was a nozzle failure. This gives you both a materials answer and a clever propellant-side mitigation.

---

### FLIGHT-PROVEN VEHICLES — these people actually launched

#### S30 — Kobald, Fischer, Tomilin, Petrarolo, Schmierer, *Hybrid Experimental Rocket Stuttgart (HEROS): A Low-Cost Technology Demonstrator* (J. Spacecraft & Rockets 55(2), 2018) **[abstract-level]**
**Access:** AIAA `https://arc.aiaa.org/doi/10.2514/1.A34035`; conference versions on ResearchGate `.../321494881`, `.../317489538`, `.../317932960`

**What this source contains:** The flight report for the **world altitude record for student-built hybrid rockets**. On 8 November 2016 HEROS 3 launched from ESRANGE to **32,300 m (106,000 ft)** apogee — over twice your target — using **nitrous oxide and paraffin-based fuel producing 10,000 N thrust**. Vehicle: 7.5 m long, **dry mass only 75 kg thanks to a largely carbon-fibre structure** (carbon fibre and glass fibre), max airspeed 720 m/s (Mach 2.3), soft landing under drogue and main parachute, and reusable. The paper publishes and analyses flight data and engine performance data, and reports the flight data showed excellent vehicle stability.

Critical engine numbers stated: the HyRES (Hybrid Rocket Engine Stuttgart) engine was designed for **10 kN thrust**, **total impulse over 100 kN·s**, nominal burn time **10–15 s**, and a **target combustion efficiency above 90%** — with **combustion efficiency verified above 97% in ground tests**. Flight burn was **15 s of liquid N2O plus roughly 10 s additional combustion of gaseous N2O in blowdown mode**. Also documented: the loaded oxidizer mass corresponded to only about **70% fill** of the tank, and ESRANGE mandated a relatively flat **80° launch angle** for range safety, both of which reduced achieved apogee below potential.

**Why you need it:** Carbon fibre airframe, N2O/paraffin, student-built, and it more than doubled your altitude goal. Their 70%-fill and 80°-launch caveats are exactly the kind of real-world derate you should build into your own predictions.

---

#### S31 — *Design and Launch of the Hybrid Sounding Rocket N2ORTH* (HyEnD / University of Stuttgart) **[abstract-level]**
**Access:** ResearchGate — `https://www.researchgate.net/publication/386018972`

**What this source contains:** The follow-on to HEROS. Reports that in **April 2023 HyEnD successfully launched N2ORTH from ESRANGE**, developed under the German DLR STERN programme (which gives student teams a three-year window to develop, build and launch an experimental sounding rocket). States the design goal was to surpass HEROS's 32.3 km record. Records the propellant decision explicitly: in a first design study the team chose **liquid nitrous oxide as oxidizer with a paraffin-based fuel**, and optimized the design for maximum performance under the given constraints, resulting in a **simple component setup, an efficient propulsion system, and an overall lightweight design**.

**Why you need it:** The most recent large student N2O/paraffin flight vehicle with published design rationale.

---

#### S32 — Dyer et al., *Design and Development of a 100 km Nitrous Oxide/Paraffin Hybrid Rocket Vehicle* (AIAA 2007-5362) and the Peregrine series
**Access:** Free PDF for the status report — `https://ntrs.nasa.gov/api/citations/20090029211/downloads/20090029211.pdf`
NTRS record — `https://ntrs.nasa.gov/citations/20120006571`
Design paper on ResearchGate — `.../268482773`

**What this source contains:** The joint **NASA Ames / Stanford / Space Propulsion Group / NASA Wallops** program to fly 5 kg to 100 km on N2O and SP1x01, a high-regression-rate paraffin-based liquefying fuel developed by Karabeyoglu at Stanford. Stated goals: demonstrate operational maturity of liquefying hybrid propulsion for space applications, keep cost down with a lean engineering team, and enable future large-scale hybrid work.

Scale context from the NTRS record: **over 400 motor tests** were conducted with N2O, GOX and LOX at thrust levels from 5 lbf to over 15,000 lbf (22 N to 66 kN). Small hybrids of 3, 4 and 6 in. diameter had already flown; **Peregrine at 15 in. (38.1 cm) diameter and 14,000 lbf (62.3 kN) thrust was by far the largest hybrid system attempted**. In the final configuration the **nitrous oxide is slightly supercharged above its vapor pressure specifically to prevent cavitation in the feed system**.

The single most important engineering result for you: the ground test campaign found the **design peak oxidizer mass flux of 1300 kg/m²·s in the fuel port was too high to achieve satisfactory flame holding with any of the injector configurations tested**. It was further noted that **no single-port paraffin/N2O lab-scale motor exhibited stable combustion above 650 kg/m²·s oxidizer mass flux**, even though no theoretical limit is known. The status reports document the program's persistent low-frequency feed-system-coupled instabilities and acoustic instabilities. Peregrine passed its final ground test at NASA Ames on 15 March 2017.

**Why you need it:** The 650 kg/m²·s number is a hard constraint on your port sizing. Also: this is a NASA program, so citing it in a NASA presentation is good politics as well as good engineering.

---

#### S33 — University of Toronto Aerospace Team, Eos II and Eos III design papers (IAC 2015) **[abstract-level]**
**Access:** ResearchGate `.../301628024` (Eos III) and `.../301630517` (Eos II)

**What this source contains:** Two consecutive student sounding rocket design papers using paraffin + N2O, written at exactly your level of organizational maturity.

*Eos II* used a **13,000 N·s** hybrid with **paraffin wax + aluminium** fuel and N2O. Key chamber features named: **pre- and post-combustor, wagon-wheel fuel core geometry, CFD-modelled injector assembly, and nozzle**. It documents a **CFD study comparing three injector geometries** with velocity contours, where the primary comparison metric was pressure drop. It shows the fuel core manufacturing route — a **wagon-wheel geometry cast on a foam mandrel**, with igniters placed in the core — and a **nozzle and cooling assembly comprising a graphite nozzle, cooling jacket and support structure**. Everything (engine, aerodynamics, structures, flight performance) was simulated with in-house MATLAB tools plus commercial packages, then verified by ground test.

*Eos III / Helios I* used the **"Bia III" engine, 8,100 N·s tested against a 10,000 N·s target**, with a **paraffin–carbon black** fuel and N2O, targeting 3 km with a 1.33 kg 1U CubeSat payload for IREC 2015, on a carbon-fibre airframe. It documents a **shoulder-bolted nozzle assembly with a graphite nozzle**.

**Why you need it:** Foam mandrels, carbon black loading, shoulder-bolted graphite nozzle retention, wagon-wheel cores — these are the practical fabrication details that academic papers skip. Also note the honest gap between the 10 kN·s target and the 8.1 kN·s achieved.

---

### SAFETY

#### S34 — Velthuysen, Broughton, Brooks, Pitot, Lineberry, Tingley, *Safety Aspects of Nitrous Oxide Use in Hybrid Rocket Motor Design and Testing* (AIAA 2018-4411) **[abstract-level]**
**Access:** AIAA `https://doi.org/10.2514/6.2018-4411`; ResearchGate `.../326262873`

**What this source contains:** A safety review of N2O for hybrid motor design and testing, from the University of KwaZulu-Natal and University of Alabama in Huntsville. Its stated general conclusion: **despite its potential decomposition hazard, if handled properly N2O is one of the safest oxidizers used in rocket propulsion**. It sits alongside Karabeyoglu et al.'s work on modelling N2O decomposition events (AIAA JPC 2008), and Thicksten, Macklin & Campbell's paper noting that the large quantities and high pressures of N2O used in rocket motors present unique hazards.

**Why you need it:** You will be asked about N2O safety in the first five minutes of any review. Have a cited answer, not an opinion.

---

#### S35 — Karabeyoglu, Dyer, Stevens, Cantwell, *Modeling of N2O Decomposition Events* (AIAA JPC 2008) **[abstract-level]**
**Access:** cited in S32's reference list; search AIAA ARC by title

**What this source contains:** Modelling of the physics of nitrous oxide decomposition events — the exothermic, self-sustaining N2O → N2 + ½O2 reaction that is the fundamental hazard of the oxidizer. Referenced as foundational by essentially every subsequent N2O safety treatment, including the Peregrine status reports.

**Why you need it:** This is the paper behind the practical rules in §5. Adiabatic compression of N2O vapour against a fast-opening valve is how teams destroy feed systems.

---

## 3. Engine walkthrough — enough to present at NASA

This section is written so you can teach it. Each subsystem gets: what it does, what physics governs it, what you must choose, and how it fails.

### 3.1 The hybrid concept, in one paragraph

A hybrid stores fuel as a solid grain inside the combustion chamber and oxidizer as a liquid in a separate tank. Because the propellants are physically separated and in different phases, the motor cannot detonate the way a solid can crack-and-explode, and it can be shut down by closing a valve. The price you pay is that combustion is **diffusion-limited**: there is no premixed propellant, so a flame sheet establishes inside a turbulent boundary layer above the fuel surface, and the fuel burns only as fast as heat can get from that flame down to the solid. This is why hybrid fuel regression rates are historically 3–5× lower than solid propellant burn rates, and why almost every design decision in a hybrid is really a decision about heat transfer to the fuel surface.

**Paraffin changes this.** Paraffin melts into a thin, low-viscosity, hydrodynamically unstable liquid layer on the grain surface. The oxidizer flow shears droplets off that layer and entrains them into the core flow, where they burn. That entrainment is a *mass transfer* mechanism that bypasses the diffusion-limited heat transfer bottleneck, which is why paraffin regresses roughly 3–4× faster than HTPB and why a single-port grain becomes viable (S1, S5, S6, S30).

### 3.2 Oxidizer tank

**Function:** store liquid N2O and deliver it at controlled pressure and flow rate.

**Physics:** N2O has a vapour pressure of about 5.0–5.1 MPa (≈730 psia) at room temperature (S16). That means it **self-pressurizes** — no helium bottle, no regulator, no pump. As liquid leaves, some liquid boils to fill the ullage, which cools the remaining liquid, which lowers vapour pressure, which lowers your feed pressure. Your thrust decays through the burn. This is *blowdown*.

**What you must choose:**
- **Fill fraction / ullage.** Too full and thermal expansion overpressurizes the tank; too empty and you lose impulse. HEROS flew at ~70% fill and explicitly noted it cost them apogee (S30).
- **Supercharge or not.** Peregrine supercharged slightly above vapour pressure with an inert gas specifically to stop cavitation in the feed system (S32). Phoenix-1B Mk II supercharged the ullage with helium to 65 bar to drive the oxidizer. Supercharging flattens your thrust curve and protects your injector, at the cost of a gas bottle and complexity.
- **Structure.** MEOP must cover the worst-case hot-day vapour pressure with margin. Phoenix-1B Mk II designed to **80 bar MEOP with SF ≥ 2.25** (S12). Balmogim proof-tested the tank to 80 bar and the chamber to 60 bar (S26).
- **Material.** If you filament-wind the tank, you need a liner. Phoenix used **uPVC liner with aluminium bulkheads, chosen explicitly for N2O compatibility** (S12). Do not put N2O directly against bare epoxy.

**How it fails:** thermal overfill; liner incompatibility; buckling of an emptied tank under flight loads (one UKZN thesis notes closing the valve during the *gaseous* portion of the burn deliberately leaves residual internal pressure for buckling resistance); and N2O decomposition triggered by adiabatic compression or contamination (S34, S35).

**Model to use:** Zimmerman et al. compare the candidates and tell you the equilibrium model is simplest but over-predicts pressure and misses the initial transient (S10). The state-estimation thesis gives you the practical assumptions — injector opening delay, two-phase exit quality, helium staying in the ullage (S11).

### 3.3 Injector plate

**Function:** meter oxidizer flow, atomize it, and isolate the chamber from the feed system.

That third job is the one teams forget, and it's the one that will bite you (S14).

**Physics:** N2O enters the injector as a saturated liquid. As it accelerates through the orifice, static pressure drops below vapour pressure and it **flashes** — cavitating, forming vapour, and choking the flow. Neither incompressible Bernoulli (SPI) nor the homogeneous equilibrium model (HEM) predicts this correctly. Dyer et al.'s **NHNE model** weights the two (S15), and it is now the community standard. Waxman's dissertation is blunt that **no model is reliable enough to replace cold-flow testing** (S16).

**What you must choose:**

1. **Pressure drop.** The stability parameter is **Δp/p_c** — injector pressure drop normalized by chamber pressure (S22). The UKZN 100 km study kept **Δp/p_c above 15%** explicitly to mitigate combustion instability. The UnB test that produced "very stable combustion" ran a showerhead at **19.1 bar** drop (S20). **Design for 20–25%**, and treat 15% as your floor. The physics: a high-Δp injector is a flow-choking element, so chamber pressure oscillations cannot propagate upstream and modulate your oxidizer flow.

2. **Many small holes, not few big ones.** Same UnB comparison: showerhead = stable; single-hole axial = severe oscillations. The mechanism is explicitly stated — multiple small orifices act as a flow isolation element decoupling the motor from the feed system (S20). Waxman adds the subtler point that two-phase flow in the orifice itself attenuates upstream-travelling pressure waves (S14).

3. **Pattern.** Your options, from the controlled four-way comparison (S17) and the CFD plate study (S18):
   - **Showerhead (axial):** simplest, most stable, lowest regression rate enhancement. Proven at 1 kN with N2O.
   - **Pressure-swirl / vortex:** big regression rate gains — Bellomo measured **+51% with vortex-injected liquid N2O with *lower* instability than axial**; Knuth reported up to 8× in specialized vortex configurations. Swirl type 1 gave the highest regression rate in the CFD-plus-test study.
   - **Hollow cone / conical:** the conical injector gave the **worst efficiency** in that study, attributed to grain chunks being ejected through the nozzle because paraffin is mechanically weak (S18). Aggressive injection tears soft grains.
   - **Impinging:** covered in the McGill angled-hole classification framework (S19).
   
   **Recommendation for a first flight article:** showerhead. Get stable combustion and a clean flight, then chase regression rate with swirl on version 2. Phoenix-1A had high-frequency acoustic instability with a conical injector and **switched to axial for the flight test** (S26) — learn from that rather than repeating it.

4. **Geometry of each hole.** Dyer's validation data was on **sharp-entrance, short-tube** orifices (S15). Match that geometry so the correlation applies. Concrete precedent: SH1 in the 1 kN motor was **11 orifices × 1.4 mm on two radii plus one centre hole, delivering ~400 g/s of liquid N2O at 60 bar feed** (S17). That's a real, tested, published plate you can scale from.

**How it fails:** insufficient Δp → chug; too few orifices → feed coupling; poor atomization → long combustion time lag → low-frequency instability; over-aggressive spray impingement on a soft grain → chunk ejection and c\* loss.

### 3.4 Igniter

**Function:** pyrolyze enough fuel surface and supply enough residual energy to establish a self-sustaining flame — *and then get out of the way* (S23).

**Physics:** N2O is a lazy oxidizer at low temperature. Unlike GOX, it will not readily support ignition until it is hot enough to begin decomposing. This is why hybrid ignition is harder than it looks and why Phoenix-1A suffered **three consecutive failed hot-fire tests due to ignition failures attributed to igniter quenching** (S26).

**Options:**

| Type | Energy | Restart | Notes |
|---|---|---|---|
| Pyrotechnic pellet | High, very fast | No | Risk of pressure spike; proper design avoids shockwave (S25) |
| Pyrogen (small solid motor) | High, sustained | No | Subsonic nozzle typical; must be small and light (S25) |
| Rocket-candy (KNO3/sorbitol) | Moderate | No | Used by Illinois Space Society, composition set experimentally |
| Electrostatic arc on 3D-printed ABS | **5–15 J** | **Yes, unlimited** | Ignites along entire port length (S24) |
| Low-voltage resistive on conductive plastic | **40 V DC, 1 s** | Yes | Demonstrated with N2O (S24) |

**Sequencing matters as much as the igniter.** Phoenix-1B opened the main oxidizer valve to only **25% first** to avoid igniter blow-out and motor hard start (S26). Your ignition sequence is: igniter fires → confirm → MOV cracks to partial open → chamber pressure rise confirms flame holding → MOV to full open. Instrument it.

**Design note for your build:** because you are casting your own grain, you can cast or print an ABS ignition section into the head end and use arc ignition. That gives you restart capability, ~10 J of ignition energy, and removes energetics from your paperwork. Strong material for a NASA presentation.

### 3.5 Fuel grain

**Function:** be the fuel, be the chamber liner, and hold together under 30+ bar and 10+ g.

**Fuel choice.** Paraffin regresses ~3–5× faster than HTPB and ~5× faster than PMMA (S6). N2O/paraffin and GOX/paraffin give similar average regression at optimum O/F, though the flux exponent *n* is larger for GOX (S7).

**Regression rate law:**

  ṙ = a · G_ox^n,  where G_ox = ṁ_ox / A_port

Note the coupling: as the port opens, A_port grows, G_ox falls, ṙ falls, and your O/F ratio **shifts through the burn**. This is why you need a time-marching internal ballistics code, not a spreadsheet (S3, S4).

**The hard constraint you must respect:** no single-port paraffin/N2O lab-scale motor has shown stable combustion above **650 kg/m²·s** oxidizer mass flux, and Peregrine's 1300 kg/m²·s design point **failed to achieve flame holding with any injector tested** (S32). This sets a floor on your initial port diameter. The UKZN 100 km study kept flux below 650 kg/m²·s as an explicit design rule.

**Geometry.** Because paraffin regresses fast, a **single circular port** is usually sufficient — this is paraffin's whole advantage (S30). Multi-port and wagon-wheel geometries (used on UTAT's Eos II, S33) buy burn area at the cost of slivers, structural weakness and casting complexity. Start single-port.

**Additives — an honest trade:**

| Additive | Buys you | Costs you |
|---|---|---|
| Aluminium (2 μm, 5–20%+) | Higher density, higher peak Isp, **lower optimum O/F → less oxidizer carried** (S5). UKZN: 23 kg vehicle mass saving at 40% Al (S26) | Lower combustion efficiency, **more nozzle erosion** (S5); flame temp 3300 K → 3600 K (S26); casting difficulty; instability tendency (S9) |
| Carbon black | Radiation absorption, opacity (used by UTAT, S33) | Minor |
| EVA / SEBS / LDPE | **Mechanical strength** — the thing paraffin lacks (S9) | Reduced regression rate; less elastic than HTPB (S8) |
| Al as a *front ring* rather than blended | Erosion reduction via protective fuel film on nozzle, and it **scales to large motors** (S29) | Non-uniform grain |

**Manufacturing — this is where student teams lose motors.** Paraffin shrinks **17–19%** on solidification. Voids come from entrained air during pouring *and* from shrinkage (S8). Two proven fixes:
1. **Heated mould-piston with applied pressure (~1.0 MPa) during cooling** — the only lab-scale method found to avoid critical defects (S8).
2. **Centrifugal (spin) casting** — optimized at 2.5 kg scale and successfully scaled to 25 kg grains meeting mechanical specs, but requires an expensive machine and careful tuning of spin rate, melt temperature and flow rate (S8).

Cast on a **mandrel** (UTAT used foam, S33). NDI your grains — void content is a flight-safety item, not a nice-to-have.

**How it fails:** cracks and voids from shrinkage → uncontrolled burn area → pressure spike; poor mechanical properties → chunks shed and exhausted through the nozzle → c\* collapse (S18); burn-through of the web before the oxidizer is spent (S5).

### 3.6 Combustion chamber, pre-chamber, post-chamber

**Pre-combustion chamber:** the volume between injector plate and grain face. Its job is to let injected N2O droplets vaporize and begin reacting before they reach the grain, and to establish a recirculation zone that anchors the flame. Balmogim documents using **hot-gas recirculation downstream of the injector to heat the expanding N2O and promote oxidiser vaporisation** (S26).

But it is also a stability driver: **pre-chamber length and oxidizer injection velocity are the key parameters setting the pressure oscillation period**, and pre-chamber residence time predicts the fundamental instability frequency (S20). Too long and you build a resonator; too short and you get incomplete vaporization and a long combustion time lag. There is a published optimal length-to-diameter band on the order of **0.26–0.66** from droplet vaporization stability analysis.

**Post-combustion chamber:** the mixing volume between grain exit and nozzle. Hybrid combustion is diffusion-limited and stratified — oxidizer-rich core, fuel-rich near-wall — so unmixed propellant leaves the grain. The post-chamber is where you recover it. This is a primary driver of the **55%–97% spread in single-port c\* efficiency** (S27). Longer post-chambers improve combustion efficiency roughly linearly, traded against structural mass.

**Passive mixing device / diaphragm:** a plate or restriction between grain and post-chamber that forces mixing. Demonstrated on paraffin/N2O (S28), with the caveat that exceeding the identified limit produces **oscillations above 20% of mean chamber pressure**.

**Thermal protection:** Phoenix-1B Mk II's chamber stack is: injector bulkhead → injector plate → bulkhead insulation → pre-combustion chamber insert → fuel grain → **thermal liner** → chamber casing → post-combustion chamber insert → nozzle (S12 project doc). Illinois Space Society used **0.5 in of ablative phenolic** as the thermal protection system (Nytrox-paraffin engine paper). Note that the paraffin grain itself insulates the casing where it is present — your exposed areas are the pre-chamber, post-chamber, and wherever the web has burned through.

### 3.7 Nozzle

**Function:** choke the flow to set chamber pressure, then expand it to convert thermal energy into directed kinetic energy.

**Throat sizing** is not a free choice — it *sets* your chamber pressure:

  A_t = ṁ_total · c\* / p_c

Pick p_c, get c\* from CEA at your O/F, and A_t falls out. If the throat erodes, A_t grows, p_c drops, and both thrust and Isp fall — which is exactly why erosion is a performance problem, not just a structural one (S29).

**Expansion ratio.** For a 50,000 ft flight, burnout happens low (typically 10–20 kft), so you optimize for a pressure well above vacuum. The UKZN blowdown sensitivity study used an **80% bell (80% of the equivalent conical length)** for higher efficiency than a conical nozzle of similar parameters, with a **0.985 nozzle correction factor** for friction losses (S35 lineage / blowdown study). Nozzle design altitude was one of the parameters they swept — do the same sweep for your mission.

**Materials.** Two proven architectures:
- **Monolithic graphite.** Minimizes erosion of the nozzle profile and has been successful in similar hybrid engines. Illinois Space Society calculated it would be **64% heavier** than a canvas/phenolic composite nozzle, and noted graphite machining generates fine conductive dust (a handling hazard around electronics).
- **Segmented: graphite throat + silica-phenolic convergent and divergent sections + steel retaining structure.** This is the Phoenix-1B solution, arrived at through **iterative transient thermo-structural analysis** after the Phoenix-1A nozzle failed in flight (S26). UTAT used a **shoulder-bolted graphite nozzle** with a cooling jacket (S33).

**How it fails:** throat erosion → p_c and Isp decay; thermal shock cracking of graphite; and retention failure — the nozzle physically departing the motor, which is what happened to Phoenix-1A and cost them 75% of their apogee (S26). **Design the retention as carefully as the contour.**

---

## 4. Design rules extracted from the literature

Pin these above your workbench. Every one is traceable to a source above.

| # | Rule | Value | Source |
|---|---|---|---|
| 1 | Oxidizer mass flux in port | **< 650 kg/m²·s** — no single-port paraffin/N2O motor has been stable above this | S32 |
| 2 | Injector Δp / p_c | **≥ 15% floor, design 20–25%** | S20, S22, UKZN 100 km study |
| 3 | Injector hole count | Many small orifices, never one large | S20 |
| 4 | Injector geometry for NHNE validity | Sharp-entrance short tube | S15 |
| 5 | Cold-flow test the injector | No model is reliable enough to skip this | S16 |
| 6 | Pre-chamber L/D | ~0.26–0.66 band from vaporization stability | S20 lineage |
| 7 | Paraffin casting shrinkage | 17–19%; apply ~1.0 MPa during cure or spin cast | S8 |
| 8 | Chamber pressure oscillation limit | Treat >20% of mean p_c as failed | S28 |
| 9 | Tank MEOP safety factor | ≥ 2.25 (Phoenix Mk II); proof test tank 80 bar, chamber 60 bar | S12, S26 |
| 10 | Ignition sequence | Igniter → confirm → MOV to ~25% → confirm p_c → full open | S26 |
| 11 | Target c\* efficiency | >90% is achievable; HyRES verified >97% on the ground | S30 |
| 12 | Nozzle efficiency factor | ~0.985 for friction; 80% bell over conical | blowdown study |

---

## 5. Sanity-check sizing for *your* vehicle

**Illustrative only.** These numbers exist to show you the method and to check that nothing in your concept is wildly infeasible. Every one must be replaced by output from a real time-marching internal ballistics code (start from S3).

**Given:** AeroTech O6000W reference point — total impulse 39,620 N·s, average thrust 5,853 N, peak thrust 9,564 N, burn time 6.77 s, 152 mm diameter, 22.0 kg propellant, estimated Isp ~184 s. Airframe 6 in × ~10 ft filament-wound CF. Target 50,000 ft.

**Step 1 — propellant mass.** A hybrid buys you Isp. Assume a delivered Isp of ~220 s (conservative: CEA ideal for N2O/paraffin is higher, but multiply by c\* efficiency and nozzle efficiency).

  m_prop = I_total / (Isp · g₀) = 39,620 / (220 × 9.81) ≈ **18.4 kg**

Against the solid's 22.0 kg. That's your headline: ~16% propellant mass saving for the same impulse — *before* accounting for your tank and plumbing mass, which will eat some of it back.

**Step 2 — split by O/F.** At O/F = 6.0:

  m_fuel ≈ 2.6 kg paraffin, m_ox ≈ 15.8 kg N2O

**Step 3 — tank volume.** Liquid N2O ≈ 745 kg/m³ at 20 °C → 21.2 L of liquid. At 80% fill → **~26.5 L tank volume**. In a 6 in tube with, say, 140 mm ID, that's a tank **~1.7 m (67 in) long**. Against a 3.05 m body tube, that is over half your airframe — before the motor, recovery and nose. **This is the tightest constraint in your design.** Options: accept a longer airframe, raise O/F (less N2O, more paraffin — check the Isp penalty in CEA), or accept lower total impulse.

**Step 4 — burn time and flow rate.** Hybrids usually burn longer and softer than solids. Take t_b = 15 s (HEROS ran 15 s liquid + ~10 s gas blowdown, S30):

  ṁ_ox = 15.8 / 15 ≈ **1.05 kg/s**

**Step 5 — port diameter from the flux limit (Rule 1).**

  A_port,min = ṁ_ox / 650 = 1.05 / 650 ≈ 1.62 × 10⁻³ m² → **d_port ≥ 45 mm**

Go bigger than the minimum — say **55–60 mm initial port** — to leave margin, then let the code tell you the burn-through time.

**Step 6 — throat.** At p_c = 35 bar, ṁ_total = 1.05 × (1 + 1/6) ≈ 1.23 kg/s, delivered c\* ≈ 1500 m/s:

  A_t = 1.23 × 1500 / 3.5×10⁶ ≈ 5.3 × 10⁻⁴ m² → **d_t ≈ 26 mm (1.03 in)**

**Step 7 — injector orifices.** Available Δp = N2O vapour pressure (≈50 bar at 20 °C) − p_c (35 bar) ≈ 15 bar, giving Δp/p_c ≈ 43% — comfortably above Rule 2, and you may want to *reduce* it by raising p_c. Using SPI as a first cut with Cd ≈ 0.65 (the NHNE model will give you a lower effective value — **use it, this is optimistic**):

  A_inj = ṁ_ox / (Cd · √(2ρΔp)) = 1.05 / (0.65 × √(2 × 745 × 1.5×10⁶)) ≈ 3.4 × 10⁻⁵ m²

At **1.5 mm holes** (1.77 mm² each): **~20 orifices**. That is squarely in the family of the tested SH1 plate (11 × 1.4 mm at 400 g/s) scaled to your flow. Sensible.

**Step 8 — check the flight.** 18.4 kg of propellant plus tank, chamber, nozzle, recovery and structure. HEROS was 75 kg dry and reached 32.3 km on 10 kN and >100 kN·s. You have ~40 kN·s. To reach 15.2 km you need a much lighter vehicle than HEROS or you will fall short. **Run OpenRocket/RASAero with your real mass budget before you commit to hardware.** The propellant mass fraction was the single parameter with the largest effect on performance in the UKZN sensitivity study — so fight for every kilogram of inert mass.

**Red flags this exercise surfaces:**
- Your tank wants ~55% of your body tube length. Resolve this first.
- 15 s at 1.05 kg/s N2O is a long burn for a fast-regressing paraffin grain; check web thickness against burn-through in the code.
- Δp/p_c is comfortable now, but it **collapses through blowdown** as tank pressure decays. Check stability at *end* of burn, not start. This is where most teams get chug.

---

## 6. Gaps in this library, and what to do about them

1. **No open-source large-scale N2O/paraffin O-class engine design with full drawings exists.** The closest are Phoenix-1B (S26) and HEROS (S30). Email both teams — UKZN's aerospace group (ASReG) and Stuttgart's HyEnD publish contact details and have historically been generous with student teams.
2. **Grosse, "Effect of a Diaphragm on Performance and Fuel Regression of a Laboratory Scale Hybrid Rocket Motor Using Nitrous Oxide and Paraffin," AIAA 2009-5113** is the single most relevant diaphragm paper for your propellants and I could not find an open copy. Get it through your university library.
3. **Zilliac & Karabeyoglu, AIAA 2006-4504** (regression rate data compilation) is the canonical *a* and *n* dataset. Paywalled. Worth an ILL request.
4. **Nozzle contour design** is under-served here. Supplement with Sutton & Biblarz *Rocket Propulsion Elements* Ch. 3, and Cantwell AA283 Ch. 7 (free, S1's directory).
5. **You will need NASA CEA.** Get it from `https://www1.grc.nasa.gov/research-and-engineering/ceaweb/` or use the `rocketcea` Python wrapper. Every O/F decision in this document assumes you can run it.
6. **Cold-flow test rig.** Waxman is explicit that no model substitutes for it (S16). Budget for it now, not later.

---

## 7. Suggested next actions

1. Download the seven direct-PDF sources with the `curl` block in §0. Read S1 and S3 this week.
2. Port the McGill control-volume model (S3) to Python. Validate it by reproducing HEROS's published performance (S30) — if your code can predict a rocket that flew, you can trust it on yours.
3. Run CEA sweeps for N2O/paraffin across O/F 4–10 at p_c 25–45 bar. Plot Isp and c\* against O/F. Pick your design point and *defend it*.
4. Resolve the tank-length problem in §5 before designing anything else.
5. Design the showerhead plate first. Build a cold-flow rig. Test it with water, then with N2O.
6. Design the ignition *sequence*, with instrumentation, at the same time you design the igniter.
7. Cast test grains and section them. Measure void content. Iterate the casting method until it's clean.

---

*Compiled August 2026. Every access link was live at time of compilation; AIAA and ScienceDirect items may require institutional access.*
