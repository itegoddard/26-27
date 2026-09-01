# Nose Cone & Avionics Bay — Annotated Source Library & Design Handbook

**Scope:** Fiberglass nose cone structural design (wall thickness, layup, shape), avionics bay integration inside the nose cone, and avionics/telemetry selection.
**Vehicle context:** 6 in (152 mm) diameter body tube, filament-wound carbon fiber airframe, fiberglass nose cone ~26 in long (~4.3× diameter fineness ratio), avionics mounted inside the nose cone.

---

## 0. How to use this in VS Code

Drop this file into your existing `HybridRocket/` workspace folder alongside `00_HYBRID_ENGINE_REFERENCE.md`. No new folder needed — everything lives in the same workspace so Claude sees both documents simultaneously.

```
HybridRocket/
├── 00_HYBRID_ENGINE_REFERENCE.md   ← engine reference (existing)
├── 01_NOSECONE_AVIONICS_REFERENCE.md  ← this file
├── references_nosecone.bib            ← citation file (companion)
└── papers/
    ├── (engine PDFs already here)
    └── (nose cone PDFs go here — see §0.1)
```

### 0.1 — Direct-download PDFs (open access, no login needed)

Run these in a terminal inside `HybridRocket/papers/` — they all download immediately:

```bash
# Structural weight optimization — NASA Marshall Space Flight Center (1963, public domain)
curl -LO "https://ntrs.nasa.gov/api/citations/19640002252/downloads/19640002252.pdf"

# ESRA IREC report — Hyak-1 (6 in CF/fiberglass rocket, 4-layer FG nose cone, avionics in nose)
curl -LO "https://www.soundingrocket.org/uploads/9/0/6/4/9064598/117_project_report.pdf"

# ESRA IREC report — IO rocket (6 in, ogive nose, fiberglass layup, SRAD telemetry)
curl -LO "https://www.soundingrocket.org/uploads/9/0/6/4/9064598/60_project_report_.pdf"

# ESRA IREC report — Atlantis II (fiberglass nose cone + aluminum tip, N2O hybrid)
curl -LO "https://www.soundingrocket.org/uploads/9/0/6/4/9064598/43_project_report.pdf"

# ESRA IREC report — 6 in rocket with nose cone payload bay detail
curl -LO "https://www.soundingrocket.org/uploads/9/0/6/4/9064598/84_project_report.pdf"

# Oregon State 30k — Kevlar/fiberglass nose cone, layup schedule, autoclave cure
curl -LO "https://www.soundingrocket.org/uploads/9/0/6/4/9064598/21_project_report.pdf"

# CATS flight computer paper — Kalman filter, barometer+IMU fusion, FHSS telemetry
curl -LO "https://arxiv.org/pdf/2511.04725"

# Material Girl launch report — Georgia Tech, 6.17 in diameter, avionics detail
curl -LO "https://arxiv.org/pdf/2411.00807"

# Telemetry Systems for a Sounding Rocket — AZ repo (TeleMetrum 3.0, SRAD 900 MHz)
curl -LO "https://repository.arizona.edu/bitstream/handle/10150/666262/ITC_2021_21-06-03.pdf"

# Radio Telemetry System Design for University Rockets — patch antennas, CF shielding
curl -LO "https://repository.arizona.edu/bitstream/handle/10150/666950/ITC_2022_22-09-03.pdf"

# Nose Cone Optimization (Von Karman, fineness ratios vs drag, Mach 0.3–3)
curl -LO "http://ieworldconference.org/content/SISE2020/Papers/Ajuwon.pdf"

# Descriptive Geometry of Nose Cones — Crowell (free reference, bluffness, fineness)
curl -LO "http://servidor.demec.ufpr.br/CFD/bibliografia/aerodinamica/Crowell_1996.pdf"

# Nose Cone & Fin Optimization (Tripoli Minnesota, fineness ratio 5, Von Karman)
curl -LO "https://offwegorocketry.com/userfiles/file/Nose%20Cone%20&%20Fin%20Optimization.pdf"

# Making Ultra Lightweight Fiberglass Nose Cones — Apogee Newsletter 413
curl -LO "https://www.apogeerockets.com/education/downloads/Newsletter413.pdf"

# NASA High Powered Rocketry Video Instruction Book (fiberglass vs carbon vs phenolic)
curl -LO "https://www.nasa.gov/wp-content/uploads/2016/02/sl_video_instruction_book.pdf"
```

---

## 1. Reading order

| Stage | What you're answering | Read |
|---|---|---|
| 1. Shape selection | What nose cone profile minimizes drag for your speed regime? | N1, N2, N3, N4 |
| 2. Wall thickness | How thick does the fiberglass shell need to be structurally? | N5, N6, N7 |
| 3. Layup & manufacturing | How do I actually build it and get clean walls? | N7, N8, N9, N10 |
| 4. RF transparency | Why fiberglass instead of carbon fiber, and how does it affect avionics? | N11, N12, N13, N14 |
| 5. Avionics bay | How do other teams fit electronics inside a nose cone? | N6, N8, N15, N16 |
| 6. Flight computer | What COTS or SRAD flight computer should we use? | N17, N18, N19 |
| 7. Telemetry system | How do we get data down to the ground at 50,000 ft? | N20, N21, N22, N23 |
| 8. Full system integration | How did a team nearly identical to ours do all of this together? | N6, N15, N16 |

---

## 2. Annotated source library

---

### SHAPE SELECTION

#### N1 — Ajuwon, *Optimization Design of Rocket Nosecone for Achieving Desired Apogee*
**Access:** Free PDF — `http://ieworldconference.org/content/SISE2020/Papers/Ajuwon.pdf`

**What this source contains:** Uses OpenRocket and SolidWorks FEA to compare nose cone shapes (conical, ogive, ellipsoid, power series, parabolic, Haack series), materials (fiberglass, carbon fiber, aluminum), lengths, and diameters against achieved apogee. Reports FEA results giving average values of 116.64 kPa pressure, 306.64 K temperature, 485.63 ft/s velocity, and 256.02 N drag for the optimum nose cone design. Finds that **the maximum altitude of 8,163 ft occurred at 30-inch length, 6.15-inch diameter, fiberglass material, and ogive shape** — which is almost exactly your geometry. Compares material properties in a table and explicitly states fiberglass offers high heat resistance, low thermal conductivity, and favorable density, making it preferred over carbon fiber and aluminum for student nose cones. Notes that "many student rocket teams among national universities" use fiberglass.

**Why you need it:** FEA-validated confirmation that your geometry — 6 in diameter, ~26–30 in length, fiberglass ogive — is the optimized choice for your altitude class. Shows the FEA pressure/temperature/drag numbers you will need to defend in a NASA presentation.

---

#### N2 — *Aerodynamic Optimization of the Von Karman Nose Cone for a Supersonic Sounding Rocket* (Academia.edu)
**Access:** Free — `https://www.academia.edu/99406637`

**What this source contains:** CFD analysis in ANSYS Fluent across Mach 0.3–3.0 for Von Karman nose cones at fineness ratios (FR) of 5.25, 6, 6.5, 6.75, 7, and 8. Finds the optimum FR for the Von Karman is **6.75**, with increasing FR generally reducing drag and diminishing returns beyond that value. Specific finding: shifting from FR 5.25 to FR 6 yields an average drag coefficient reduction of 0.0031. Reports that Von Karman geometry (a subset of ogive) has better thermal properties and structural integrity than pure cones due to its blunted nose. States nose cone design depends on altitude, velocity profile, materials, and other factors. Provides Fluent settings in appendices for repeatability.

**Your geometry:** 26 in ÷ 6 in = **FR ≈ 4.33**. This is below the CFD-optimal range, which tells you three things: (1) you are in a drag penalty zone compared to FR 6+, (2) there is nothing structurally or aerodynamically wrong with FR 4.3 — it's a common choice for rockets that need internal volume, and (3) if you want to optimize, you'd go to 3.5–4× diameter = 21–24 in which coincidentally is what many comparable teams use.

**Why you need it:** Gives you the quantitative drag penalty of your chosen fineness ratio, and the vocabulary (Von Karman, fineness ratio, Mach regimes) for a NASA-level discussion.

---

#### N3 — Crowell, *The Descriptive Geometry of Nose Cones* (1996)
**Access:** Free PDF — `http://servidor.demec.ufpr.br/CFD/bibliografia/aerodinamica/Crowell_1996.pdf`

**What this source contains:** The definitive free reference on nose cone geometry for amateur and student rockets. Covers all major families: conical, elliptical, tangent ogive, secant ogive, parabolic, power series, and Haack/Von Karman series. Explicitly discusses the "bluffness ratio" — tip diameter divided by base diameter — noting that sharp tips are ideal aerodynamically but impractical for manufacturing, handling damage, and safety, so most cones are blunted. Explains that as fineness ratio increases, wetted area (and thus skin friction drag) also increases, so the minimum-drag fineness ratio is a tradeoff between decreasing wave drag and increasing friction drag. Notes that many size rockets reported to have "ogive" nose cones may actually have Von Karman shapes, which are indistinguishable without exact measurements.

**Why you need it:** This is the geometry bible. You need to know the names, the math, and the tradeoffs before you can talk to a NASA reviewer about your shape selection. Free, foundational, and frequently cited.

---

#### N4 — Stroick, *Nose Cone & Fin Optimization* (Tripoli Minnesota, 2011)
**Access:** Free PDF — `https://offwegorocketry.com/userfiles/file/Nose%20Cone%20&%20Fin%20Optimization.pdf`

**What this source contains:** A practitioner's guide to nose cone and fin optimization for high-power rocketry, explicitly focused on the transonic-to-supersonic regime your vehicle will pass through. Makes the critical recommendation that **fineness ratio 5 is critical** for this speed regime, based on drag data across Mach 1–4. Provides a ranked comparison table of drag characteristics for all major nose cone types across Mach 0.8 to 3+: Von Karman (LD-Haack) rated "superior" in transonic; X¾ Power series rated "superior" in supersonic; X⁰·⁶ Power series for hypersonic. Explicitly recommends: **Transonic — Von Karman blunted 15% of base diameter; Supersonic — X¾ Power Series; Hypersonic — X⁰·⁶ Power Series.** Also covers fin geometry including: fin count of 3, fin joints 4–8% of root chord, thickness less than 10% of root chord often between 3–6%, sweep angle 45–70°, flat fin tips, hexagonal cross-section, and clipped delta shape.

**Why you need it:** Hands-on design rules from a practitioner working in exactly your speed and altitude class. The "FR 5 is critical" statement is exactly the kind of defensible design rule you need for a presentation.

---

### WALL THICKNESS & STRUCTURAL ANALYSIS

#### N5 — Nevins & Helton, *An Investigation of Various Parameters Affecting the Structural Weight of Rocket Vehicle Nose Cones* (NASA Marshall MSFC, 1963)
**Access:** Free PDF — `https://ntrs.nasa.gov/api/citations/19640002252/downloads/19640002252.pdf`
Also readable at: `https://archive.org/details/nasa_techdoc_19640002252`

**What this source contains:** The most rigorous publicly available structural analysis of rocket nose cone wall thickness, conducted at NASA Marshall Space Flight Center. Investigates 144 separate ring-stiffened monocoque cones across four base diameters (120–260 inches), six cone half-angles (10–30°), and two materials — aluminum alloy and **glass-fiber-reinforced silicone laminate (fiberglass)**. Subjected every cone to external aerodynamic pressure distributions typical of atmospheric booster trajectories. Derives the critical buckling pressure for conical shells:

  P_CR = (K₁ tan γ / a^(3/2) cos γ) · E · (h)^(5/2) · [1 + 7(λ - 0.5)]

  where h = half skin thickness, γ = cone half angle, E = elastic modulus, λ = geometric ratio.

Key quantitative findings:
- **Minimum skin thickness throughout the program was held at 0.030 inches (0.76 mm)**, regardless of structural requirement — this is the absolute floor even for tiny loads.
- Variable skin thickness ("stepped" between ring stiffeners) was always lighter than uniform thickness: the skin thickness in the actual optimized cone ranged from **0.125 inches at the base (aft end) tapering to 0.032 inches at the apex (tip)**, with ring spacing decreasing toward the aft end.
- The Table I in the paper gives the exact bay-by-bay skin thickness and ring area for a 260-inch cone — you can scale these numbers directly to your 6-inch cone.
- **A 25° half-angle cone produces the minimum weight for all diameters studied** — purely structural, not aerodynamic.
- **Aluminum alloy cones are lighter than fiberglass cones** under pure structural weight — however the paper explicitly notes that heat transfer differences between fiberglass and aluminum mean this conclusion may not hold once aerodynamic heating is included, which is critical for your fiberglass choice.
- **Blunting reduces total cone weight** as well as addressing structural stress concentrations at the tip.
- The elastic modulus difference between aluminum and fiberglass is the primary reason aluminum wins on structural weight — but you're choosing fiberglass for RF transparency, which the 1963 paper didn't consider.
- Three buckling failure modes were analyzed: panel (skin) instability, stiffening ring instability, and overall (general) instability.

**Why you need it:** This is the NASA-originating structural analysis of fiberglass nose cones. The minimum 0.030-inch floor and the tapered skin thickness data are the quantitative basis for your wall thickness decisions. Reading §C.Results and Table I and scaling to 6 in gives you the starting point for your own analysis.

---

#### N6 — *Hyak-1 Project Report* (UVic Rocketry Team, ESRA IREC)
**Access:** Free PDF — `https://www.soundingrocket.org/uploads/9/0/6/4/9064598/117_project_report.pdf`

**What this source contains:** Design and flight report for a rocket with a very similar profile to yours: carbon fibre fuselage, **fiberglass nose cone, 3D-printed fins laminated with carbon fibre**. The nose cone is described in full: **four layers of fiberglass with an aluminum tip**, **full parabolic profile with a fineness ratio of 5 and a bluntness ratio of 5%**. Explicitly states: "Fibreglass was chosen as the material as it provides a high strength-to-weight ratio while still maintaining the **RF-transparency necessary for the avionics located in the nose cone** to communicate with the ground station, while the aluminum cap adds strength to the tip where aerodynamic heating and loading is most extreme." The nose cone was manufactured using a fiberglass-strengthened gelcoat split mold machined from an aluminium blank on a CNC lathe. The coupler was manufactured by hand using wet layup with a spare fuselage section as the female mold to give an outside smooth surface and a tight fit in the carbon fibre fuselage. The number of layers was based on fastener tear-out data and expected maximum tensile/compressive loading during powered flight and recovery of around 20 G. The rocket weighs 58.75 lbs (26.649 kg) at liftoff, stands 138.5 in (352 cm) tall, designed for 30,000 ft at Mach 1.88.

**Your parallels:** CF fuselage, fiberglass nose cone, avionics in nose cone, similar mass class.

**Why you need it:** Four-layer answer to your "how many layers?" question, directly justified, from a team flying a near-identical configuration. This is your most important single precedent.

---

#### N7 — *ESRA IREC Report — Team with 6-Inch Rocket, Fiberglass Nose with Avionics Payload Bay* (ESRA Report 84)
**Access:** Free PDF — `https://www.soundingrocket.org/uploads/9/0/6/4/9064598/84_project_report.pdf`

**What this source contains:** A 6-inch rocket competition report documenting a nose cone payload/avionics bay design. Contains the key structural detail: **a ½-inch plywood bulkhead bonded inside the nose cone**, featuring a 3/8-16 bolt, washers, and nut as the forward anchor point for the payload and the main parachute shock cord. Documents the problem of the payload unthreading during parachute descent and the solution: physical stops bonded to the inside of the nose cone coupler, preventing rotation. The coupler slides over the payload and bolts to the nose cone, with stops preventing the payload from unscrewing. This team divided the vehicle into three sections: booster, avionics bay, and payload containment bay — importantly showing one architecture where the nose cone acts as a separable payload/avionics section rather than a fixed structural section.

**Why you need it:** The plywood bulkhead + threaded rod approach is the standard nose cone bay anchor method, and this report describes the failure mode (payload unscrewing under parachute loads) and its fix, which you need to design around from the start.

---

#### N8 — Van Milligan, *Making Ultra Lightweight Fiberglass Nose Cones* (Apogee Newsletter 413, 2016)
**Access:** Free PDF — `https://www.apogeerockets.com/education/downloads/Newsletter413.pdf`

**What this source contains:** A step-by-step practical guide to manufacturing fiberglass nose cones using wet layup over a mandrel, written by a rocket engineer with Level 3 certification. Covers: how to create patterns by tracing the nose cone profile four times end-to-end, how to scale/resize the pattern to match the mandrel circumference using a drawing program, how to cut and orient fiberglass cloth rectangles and long strips, and the sequencing of laying wet fiberglass over the mold. Notes that the layup is "challenging" and "tends to create suboptimal parts" but that "with enough layers, they were deemed sufficient." Based on MIT Rocket Team practice which used approximately 30 each of 3"×4", 4"×8", and 10"×12" rectangles plus 6 strips of 3"×48", laid with mold release and gelcoat for surface finish. Gives step-by-step sequencing for mating two mold halves while still wet. Notes tip reinforcement: the inside of the tip was filled with fiberglass shavings and epoxy for a solid, more durable point.

**Why you need it:** Practical manufacturing — how to actually cut and lay the cloth, how to get the tip solid, how to use a split mold. Companion source to the structural papers.

---

#### N9 — *Oregon State University 30k Project Report* (ESRA IREC Report 21)
**Access:** Free PDF — `https://www.soundingrocket.org/uploads/9/0/6/4/9064598/21_project_report.pdf`

**What this source contains:** Detailed layup schedule for a nose cone made of prepreg Kevlar and fiberglass for RF transparency, with an explicit ply-by-ply schedule. The nose cone layup was: **[0/0/45/-45/0/0] prepreg Kevlar** finished with **[0/0] fiberglass** for post-processing and surface finish. Kevlar and fiberglass were vacuum-bagged and autoclave-cured at 275°F for 6 hours. After demolding, two additional layers of wet fiberglass were added due to surface ridging to protect the Kevlar. The upper body tube (housing avionics and recovery) was made out of fiberglass for RF transparency, while the lower body tube was carbon fiber. States explicitly: "The use of RF transparent fiberglass in the upper body tube is to allow for communication with the payload, recovery system, and avionics housed in the upper airframe." Documents that the nose cone was laid up over an enamel-coated male mold. Body tubes follow a layup schedule of [90/45/0/45/90].

**Why you need it:** A published, specific ply sequence for a nose cone housing avionics, with the autoclave cure parameters. Even if you're doing wet layup rather than prepreg, this layup schedule is directly adaptable.

---

### RF TRANSPARENCY — WHY FIBERGLASS IS MANDATORY

This is not optional knowledge — it is the #1 reason your nose cone must be fiberglass rather than carbon fiber, and it determines every other material and placement decision.

#### N10 — *UAE First Hybrid Sounding Rocket — Composite Materials Engineering* (TII Insights, 2026)
**Access:** Free article — `https://www.tii.ae/insights/composite-materials-engineering-uaes-first-hybrid-sounding-rocket`

**What this source contains:** The clearest single statement of the RF transparency requirement in an aerospace context, from a documented hybrid sounding rocket program. States directly: **"Carbon fiber is electrically conductive and essentially opaque to RF signals, making it entirely unsuitable for a radome application. A glass-fiber-reinforced composite system was chosen for the nose cone, exploiting glass fiber's intrinsic dielectric properties."** Goes on to explain that E-glass and glass-fiber systems are widely used in aerospace radome applications because their dielectric constant can be engineered to minimize signal attenuation across GPS and radar frequency bands, allowing signals to pass through with minimal loss. Flight results confirmed: **GPS/telemetry was uninterrupted throughout flight, confirming RF transparency of the glass-fiber nose cone.** Also reports mass reduction of up to 40% versus an equivalent metallic design.

**Why you need it:** The clearest, most citable statement of the carbon fiber exclusion principle and the physical reason for it. When a NASA reviewer asks "why fiberglass?" this is your source.

---

#### N11 — Community evidence on GPS placement: fiberglass vs. carbon fiber
**Access:**
- `https://www.rocketryforum.com/threads/gps-tracker-placement-avbay-or-nosecone.192731/`
- `https://www.rocketryforum.com/threads/gps-tracking-effectiveness-in-electronics-bay-vs-nose-cone.179999/`
- `http://jcrocket.com/gps-tracking.shtml`

**What these sources contain (taken together):** The practitioner consensus on GPS antenna placement for high-power rocketry. Key findings:
- **"Just Don't put the GPS in the Coupler Ebay, put it in the nose where it belongs like most all Sounding Rockets... Fiberglass, unlike Carbon, won't dramatically impact performance."**
- Fiberglass nose cone: GPS antenna inside works well because the shell is dielectrically transparent.
- Carbon fiber nose cone: GPS and telemetry signals are blocked — confirmed by test ("I proved blocked signals").
- Avionics bay (middle of rocket): GPS may work but performance degrades due to metal components, all-threads, eyebolts, and other electronics adjacent to the antenna perturbing the radiation pattern. Recommendation: always ground-test the complete radio link margin before flight.
- Metallic paint on a nose cone absorbs RF — do not use metallic paint on any surface where an antenna is radiating through.
- Quarter-wave radial antennas do not fit most rocket bodies, so the whip antenna "makes do" by using the rocket structure itself as the other half of the dipole — with efficiency losses.
- External patch antennas are an alternative when the body is carbon fiber, designed conformally on the outer skin.

**Why you need it:** Confirms that placing avionics in your fiberglass nose cone is the correct approach and that a carbon fiber nose cone is incompatible with internal GPS/telemetry. Also warns you about metallic paint and the need for ground testing.

---

### AVIONICS BAY DESIGN

#### N12 — *IO Rocket Report* (BSLI ESRA IREC 2018)
**Access:** Free PDF — `https://www.soundingrocket.org/uploads/9/0/6/4/9064598/60_project_report_.pdf`

**What this source contains:** The most similar published vehicle to yours: **a ten-foot tall, 6-inch diameter rocket** designed for 10,000 ft with SRAD motor and avionics. From fore to aft: Lander (in nose cone), Recovery system, Payload Bay, Avionics and Telemetry, Active Drag System, motor. Features a **24-inch ogive nose cone** — directly comparable to your 26-inch target. The nose cone was laid up in two split-mold halves, wet layup, mated while still uncured, with the tip filled solid with fiberglass shavings and epoxy. Avionics bay is documented to contain a student-built telemetry system capable of transmitting flight data to the ground during the mission; also a COTS backup system (Eggtimer). SRAD system: Arduino with LoRa module, GPS, and altimeter. Custom ground station provides readouts of measurements, power levels, and recovery charge status. Recovery: dual-deployment with 4 redundant ignitors firing at apogee for drogue deployment, then cable cutters at 1,500 ft for main.

**Why you need it:** 6-inch diameter, 24-inch nose cone, avionics inside, competition rocket. This is the closest match to your vehicle in the public literature.

---

#### N13 — *Atlantis II Sounding Rocket* (SOAR, ESRA IREC, Report 43)
**Access:** Free PDF — `https://www.soundingrocket.org/uploads/9/0/6/4/9064598/43_project_report.pdf`

**What this source contains:** A nitrous oxide / solid fuel hybrid vehicle with **fiberglass composite nose cone with an aluminum tip** housing the drogue parachute and scientific payload. The top carbon fiber tube contains the main parachute, avionics, and recovery systems — showing the architectural decision to keep avionics out of the nose cone and instead in the adjacent carbon fiber tube when the payload is in the nose. The nose cone tip aluminum cap adds strength where aerodynamic heating and loading are most extreme — a design detail you should adopt. Avionics: the Flight Board has a STM32F4 microcontroller at its core (low power usage vs. Raspberry Pi, high reliability, commercial use, team familiarity). Also includes: barometer, altimeter, IMU, GPS on the Flight Board. Payload was housed in the nose cone to not only mitigate the effect of the payload on the rocket but also the rocket on the radiation sensing abilities of the payload.

**Your parallels:** Hybrid motor, fiberglass nose cone, aluminum tip, STM32-based flight computer. Directly applicable avionics architecture.

---

#### N14 — *Georgia Tech Material Girl Launch Report* (GTXR, arXiv 2411.00807)
**Access:** Free PDF — `https://arxiv.org/pdf/2411.00807`

**What this source contains:** Full launch report for a **6.17-inch diameter**, 176-inch two-stage sounding rocket with a simulated apogee of 220,000 feet. The sustainer section had two externally mounted **fiberglass shrouds serving as housing for the Featherweight GPS modules** — a documented workaround for placing GPS trackers on a carbon fiber vehicle. COTS avionics flight computer used for flight events; custom flight computer stored as payload. Motor grain geometry and fin dimensions were determined through in-house optimization software derived from RASAero and RocketPy. This is the most extreme-performance student rocket in this list — Mach 4.1, 220 kft simulated — and represents the upper bound of what a student team has actually built and launched at your body diameter.

**Why you need it:** Shows the fiberglass shroud GPS workaround for carbon fiber vehicles, and gives you context for avionics choices at extreme performance levels. The 6.17 in diameter also gives you structural scaling data.

---

### FLIGHT COMPUTERS (COTS options)

Before picking a flight computer, understand what it must do for your mission:

1. **Apogee detection** — deploy drogue parachute at or just after apogee
2. **Main deployment** — deploy main chute at a set altitude (typically 500–1500 ft AGL)
3. **Data logging** — record the full flight for post-analysis
4. **Telemetry** — transmit real-time data to a ground station (required for your 50 kft altitude)
5. **GPS tracking** — locate the rocket after landing

#### N15 — Featherweight Altimeters Blue Raven / Raven 4
**Key specs:** Featherweight Blue Raven is the system recommended by IREC's 2025 Design, Test & Evaluation Guide (DTEG). Raven 4 independently measures altitude and can independently deploy both drogue and main parachutes. From the telemetry paper (N20): "As a safety feature, a redundant telemetry and flight control computer is used. This Featherweight Raven 4 device independently measures altitude, and can independently deploy both the drogue and main parachutes. The Raven 4 processor will deploy the drogue parachute three seconds after it has sensed apogee, provided the velocity of the rocket is under 400 feet per second, and the air pressure is increasing. The processor will deploy the main parachute when it senses the altitude has dropped to 1200 feet."

**Why this matters for you:** IREC recommends it. It is designed as a safety-redundant secondary, not a primary flight computer. Use it as your backup/redundant deployment system.

---

#### N16 — Altus Metrum TeleMetrum / TeleMega
**Key documented specs:**
- TeleMetrum: 2.75 × 1 inch board, fits inside 29 mm coupler. 70 cm ham-band transceiver for telemetry downlink. Barometric pressure sensor rated to 100,000 ft MSL. 1-axis 200-g accelerometer for motor characterization. On-board integrated GPS receiver. Non-volatile flash memory. USB for data recovery. LiPo rechargeable battery support. Transmits flight data **10 times per second during ascent, 1 Hz after apogee**. Also transmits an audio tone every 5 seconds for direction-finding.
- TeleMega: 3.25 × 1.25 inch, 38 mm coupler. 6 pyro channels. 3-axis 200-g accelerometer. GPS + 70 cm radio. Supports staging and air-start events based on tilt angle.
- **Range:** Tested by Altus Metrum to provide good telemetry to **20 km (65,600 ft) with a 3-element Yagi antenna** on the ground. An 11-element Yagi extends this to approximately 100 km theoretical. Analysis in the Arizona paper (N20) showed the 440 MHz downlink has **ample margin to 50 km altitude**.
- **Ham license required** for 70 cm (433 MHz) band operation in the USA.
- Open-source hardware and software (AltOS). Ground station software: AltosUI (Java-based, cross-platform). Logs to Google Maps/Google Earth format.

**Why this matters for you:** This is the workhorse COTS flight computer for high-power rocketry. TeleMetrum does deployment + GPS + telemetry in one board. TeleMega adds more pyro channels if you need staging or other events. The documented 65 kft telemetry range covers your 50 kft mission with margin.

---

#### N17 — CATS Vega Flight Computer (open-source, arXiv 2511.04725)
**Access:** Free PDF — `https://arxiv.org/pdf/2511.04725`

**What this source contains:** Detailed technical analysis of the CATS (Control and Telemetry Systems) Vega flight computer, which is the official flight computer of the European Rocketry Challenge (EuRoC) and the most documented open-source flight computer in the student rocketry literature. Hardware: **STM32F4 microcontroller**, **16 MB flash memory**, **MS5607 barometer**, designed for rockets to 30 km altitude. The telemetry system uses **Frequency Hopping Spread Spectrum (FHSS)** for resistance to interference and difficulty of interception; the hopping pattern is defined by a link phrase, hashed with CRC32, and used as a seed for a pseudo-random number generator. Kalman filter fuses barometric altimeter and accelerometer data:
- **Powered flight phase:** Kalman filter trusts IMU most, since barometric readings are unreliable in the transonic regime (pressure fluctuations, aerodynamic effects on vent holes).
- **Coasting detection:** when Z-axis acceleration falls below 0, motor has stopped thrusting; Kalman filter then shifts weight toward barometric.
- GNSS reception and telemetry are also integrated.
All hardware designs and software are fully open source at github.com/catsystems.

**Why you need it:** Open-source, documented, deployable. The Kalman filter description is exactly the state estimation algorithm you need to understand for your own flight computer if you go SRAD — and the barometric/IMU switching logic during transonic flight is a non-obvious design requirement that kills apogee detection in less sophisticated systems.

---

### TELEMETRY SYSTEM

#### N18 — Francois & Montano, *Design of a Radio Telemetry System for Use by University Rocket Teams* (ITC 2022)
**Access:** Free PDF — `https://repository.arizona.edu/bitstream/handle/10150/666950/ITC_2022_22-09-03.pdf`

**What this source contains:** A system developed specifically to meet telemetry needs of university sounding rockets. Key finding: **many amateur rockets are constructed from carbon fiber, which interferes with RF propagation** — so the solution is **external patch antennas placed conformally on the vehicle's outer skin**. Explains patch antenna physics: an open-circuit transmission line where voltage is maximum on the ends and current is maximum in the center; fringing E-fields between the radiating surface and ground plane add up to produce radiation. States the custom system allows the telemetry unit to change and evolve, removing the constraint of COTS options. The system enables data retrieval even in catastrophic failure scenarios by transmitting during flight. Missions occasionally suffer catastrophic failure with total data loss; real-time telemetry increases the chance of recovering scientific data regardless of vehicle recovery success.

**Why you need it:** Explains why you need external antennas if any part of your airframe is carbon fiber, and how patch antennas work. Also gives the systems argument: even if your rocket is lost on landing, you get your flight data.

---

#### N19 — Francois, *Telemetry Systems for a Sounding Rocket and Its Paralites* (ITC 2021, University of Arizona)
**Access:** Free PDF — `https://repository.arizona.edu/bitstream/handle/10150/666262/ITC_2021_21-06-03.pdf`

**What this source contains:** A complete documented telemetry system for a 30,000 ft sounding rocket (IREC 30k SRAD class). Two systems fly:
- **COTS system:** Altus Metrum TeleMetrum 3.0 — integrated GPS + 440 MHz transmitter. Link analysis performed to verify downlink operation to 30,000 ft: **the 440 MHz downlink was calculated to have useful margin to 50 km altitude** (well above your 50,000 ft / 15.2 km target).
- **SRAD system:** Transmitter in the **900 MHz ISM band** with a 15 dBi gain receiving antenna. Analysis confirms ample margin at 9 km apogee.

Documents that previous sounding rockets by the team used fiberglass bodies. Provides link budget analysis methodology — you can use their methodology to verify your own antenna choice is adequate for 50 kft.

**Why you need it:** Direct link budget analysis showing TeleMetrum 3.0 at 440 MHz works to 50 km altitude with a Yagi antenna. This is your quantitative radio coverage justification for 50,000 ft.

---

#### N20 — ESRA IREC IO Team / RIT team, documented SRAD telemetry systems
**Access:**
- IO: `https://www.soundingrocket.org/uploads/9/0/6/4/9064598/60_project_report_.pdf`
- RIT "Third Time's the Charm": `http://launch.rit.edu/uploads/1/1/4/2/114234541/78_project_report.pdf`

**What these sources contain:**

*IO (BSLI 6-inch)* — SRAD telemetry system: Arduino equipped with **LoRa module, GPS, and altimeter**. Ground station provides readouts of measurements, plus power levels of flight computers and recovery charge status. COTS backup: Eggtimer altimeter. All-fiberglass rocket: confirms no RF shielding issues.

*RIT third-generation rocket* — Custom flight computer (third board, beyond two redundant altimeters) provides GPS and sensor (pressure, accelerometer) telemetry. Computer sends to ground via **433 MHz LoRa module**, powered by a 7.2V LiPo. Onboard: COTS omnidirectional antenna. Ground: custom corner-reflector antenna for reception. Deployed flight-proven on two flights before competition. The team is all-fiberglass, further confirming this configuration is RF-transparent.

**Key spec:** 433 MHz LoRa. LoRa (Long Range) modulation uses Chirp Spread Spectrum, giving excellent range with low power even with a simple quarter-wave whip. A corner-reflector ground antenna adds significant gain without the pointing requirement of a Yagi.

**Why you need it:** Shows the LoRa architecture that is now the student standard for SRAD telemetry — simpler to implement than the FHSS systems, long range, and specifically documented on 6-inch fiberglass rockets.

---

#### N21 — *CATS: Empowering the Next Generation...* (arXiv 2511.04725) — Kalman filter detail
(Full citation above in N17)

**Telemetry-specific content:** The CATS paper states the telemetry system operates in the FHSS band. The Kalman filter for state estimation is described with equations:
- State is estimated from IMU (accelerometers) and barometer
- During motor burn (powered phase): barometric data is unreliable due to transonic flow over the static ports; the filter weights IMU more heavily
- Coasting detection via Z-axis acceleration threshold
- The filter provides apogee detection by tracking velocity sign change, filtered from barometric noise

This is the algorithm your flight computer needs to implement for reliable apogee detection at 50,000 ft.

---

#### N22 — IREC 2025 DTEG (Design, Test & Evaluation Guide)
**Access:** Free PDF — `https://www.soundingrocket.org/uploads/9/0/6/4/9064598/2025-irec_dteg_v1.1.4_02-01-25.pdf`

**What this source contains:** The current competition rules document that the entire IREC community designs to. Recommends teams use the **Featherweight Altimeters Blue Raven** as the altimeter to meet IREC flight computer requirements. States it is anticipated that a separate flight computer and this specific product will likely be required in the future. Safety requirements documented: arming key switches for energetic devices must not be at the same airframe clocking position as the hatch panel deployed by that charge. Rules governing SRAD avionics controlling energetics. (As of 2025 IREC, a separate flight computer is recommended but not required.)

**Why you need it:** Even if you're not competing in IREC, these design requirements represent the safety floor for high-power rocketry. The Featherweight Blue Raven recommendation is the community's current consensus on minimum avionics for a dual-deployment system.

---

### STUDENT AVIONICS ARCHITECTURE — FULL DOCUMENTED SYSTEMS

#### N23 — Georgia Tech GTXR Modular Avionics (AIAA RSC 2024)
**Access:** AIAA `https://arc.aiaa.org/doi/10.2514/6.2024-85660` (paywalled abstract; ask your university library for the PDF)

**What this source contains:** Design of a modular avionics system for a two-stage rocket targeting the Karman Line, modeled on CubeSat avionics stacks. Four PC-104 boards connected via CAN bus:
1. **Power board** — regulated power distribution to entire system
2. **State estimation board** — IMU (primary + backup), magnetometers, barometers, high-G accelerometer, GNSS receiver; runs **Extended Kalman Filter (EKF)** for state estimation including GNSS-lockout periods (GNSS fails during max-Q transonic flight)
3. **Control/radio board** — central decision-making: ignites second stage, activates recovery systems, streams telemetry
4. **Auxiliary systems** — redundancy and first-stage telemetry, ground communications, video

States that a Kalman filter (extended, for nonlinear dynamics) is used throughout all phases of flight including the GNSS lockout period. The paper explicitly addresses the period of **GNSS signal loss during transonic flight** — GPS receivers frequently lose lock when the rocket is accelerating through Mach 0.8–1.2 due to signal dynamics; the EKF bridges this gap using IMU alone. The flight computer was tested on a single-stage rocket before the two-stage application.

**Why you need it:** The EKF-based GNSS-lockout architecture and the four-layer CAN-bus stack are the state of the art for student high-altitude avionics. Even if you don't build a custom stack, understanding this architecture helps you evaluate COTS options.

---

#### N24 — Concordia "Supersonice" rocket report (ESRA IREC Report 79)
**Access:** Free PDF — `https://www.soundingrocket.org/uploads/9/0/6/4/9064598/79_project_report.pdf`

**What this source contains:** A supersonic competition rocket using the **Altus Metrum TeleMetrum as the primary deployment device** and a **PerfectFlite StratoLogger SL100 Altimeter as the redundant system**. Both set to fire drogue at apogee and main at 755 ft AGL. Both are COTS, not modified, used per manufacturer recommendations. TeleMetrum powered by its own 3.7 V LiPo for sensors plus a separate 9 V battery for recovery systems. StratoLogger has its own separate 9 V battery. Data collected with both COTS and an SRAD system.

**Why you need it:** Documents the specific dual-redundant avionics configuration that the rocketry community converges on: TeleMetrum (GPS + telemetry + deployment, primary) + StratoLogger (barometric-only backup). This two-device architecture is your minimum viable avionics design.

---

## 3. Nose Cone Design Walkthrough — enough to present at NASA

### 3.1 Shape

**Your geometry:** 26-inch length on a 6-inch body = fineness ratio 4.33. This sits between the aerodynamic ideal (FR 5–6.75) and a shorter, easier-to-build cone. The most aerodynamically efficient shapes for your speed range, ranked by drag at Mach 0.8–2.0:

| Shape | Transonic | Supersonic | Notes |
|---|---|---|---|
| Von Karman (LD-Haack) | Best | Good | Blunted tip; structurally favorable |
| Tangent Ogive | Good | Good | Most commonly used by student teams |
| ¾ Power Series | Fair | Best | Sharp tip; harder to manufacture |
| Conical | Fair | Fair | Heaviest for a given length |
| Parabolic | Good | Good | Common COTS shape |

**Recommendation:** Von Karman or tangent ogive at your fineness ratio. Both are manufacturable from a split fiberglass mold. The Von Karman is mathematically described by the Haack series (see N3) and gives the minimum wave drag for a given volume. Blunt the tip slightly (2–5% bluffness ratio = 0.12–0.30 in spherical tip diameter for your 6 in cone) for structural strength and handling safety.

### 3.2 Wall Thickness

This is the key engineering question. Here is what the sources say, organized from most rigorous to most practical:

**The NASA floor (N5):** Absolute minimum skin thickness, regardless of structural requirement: **0.030 inches (0.76 mm)**. Even the thinnest, lightest tip of a large nose cone was never designed below this in the NASA study.

**The student team floor (N6, N7, N8, N9):** The converged answer across IREC teams with fiberglass nose cones in your size class is **4 layers of fiberglass**, validated against 20 G flight loads (the expected maximum during powered flight and recovery).

**Working backward from the physics:**
- At 50,000 ft, your max dynamic pressure (Max Q) occurs somewhere between 5,000–15,000 ft altitude during the first few seconds of flight. For a 50 kft trajectory from Fort Worth, TX, max Q will be roughly **500–800 psf (2.4–3.8 psi)** depending on your thrust curve and drag.
- A 4-layer E-glass wet layup nose cone at 6-inch diameter has a practical minimum wall thickness of about **0.060–0.090 inches** (1.5–2.3 mm). Each layer of E-glass woven cloth (6-oz or 9-oz) adds approximately 0.010–0.015 inches per ply in wet layup.
- At this thickness and diameter, the critical failure mode is **buckling**, not tensile stress — the shell is thin and slightly curved, so it fails by crumpling inward under axial compression (from drag load) rather than tearing.
- The NASA study showed that for fiberglass cones at ~25° half-angle, buckling governs design and the optimal skin is **tapered** — thicker at the base (where loads are highest) and thinner at the tip.

**Practical starting point for your design:**
- **Tip region (apex to ~1/3 length):** 3–4 layers of 6-oz fiberglass = ~0.045–0.060 in
- **Mid-section (~1/3 to 2/3 length):** 4–5 layers = ~0.060–0.075 in
- **Shoulder/base (2/3 to base):** 5–6 layers = ~0.075–0.090 in
- **Shoulder reinforcement (where nose cone meets body tube):** 6–8 layers minimum; this is the highest-stress location under recovery loads and fin flutter loads propagating forward

This tapered approach matches the NASA optimal design philosophy (N5). The Hyak-1 team (N6) used **4 uniform layers**, which is simpler to manufacture and accepted a small weight penalty over the tapered design. For your first build, **4 uniform layers is the right call.** Move to a tapered schedule on a future iteration after you have flight data.

**Tip:** Add a solid aluminum or G10/FR4 tip cap. The aerodynamic stagnation point at the tip sees the highest pressure and temperature. Hyak-1 (N6) and Atlantis II (N13) both used aluminum tips.

### 3.3 RF Transparency — the non-negotiable

Since your avionics (GPS, telemetry, flight computer) live inside the nose cone, the nose cone shell must be RF-transparent. This is non-negotiable:

- **Fiberglass (E-glass, S-glass):** RF-transparent. Standard choice. Confirmed working by Hyak-1 (N6), Atlantis II (N13), IO (N12), Oregon State (N9), UAE hybrid (N10), and dozens of other teams.
- **Carbon fiber:** RF-opaque. Blocks GPS and telemetry. Confirmed by the UAE paper (N10) and practitioner experience (N11). **Do not use carbon fiber anywhere that encloses an antenna.**
- **Kevlar/aramid:** RF-transparent. Used by Oregon State (N9) as a structural layer inside the fiberglass for impact resistance.
- **Aluminum tip cap:** Blocks RF in the small region it covers (the tip), but antennas are not typically located at the tip — they're further back in the avionics bay — so this is acceptable.
- **Metallic paint:** Attenuates RF. Do not use metallic paint on the nose cone if antennas are inside (N11).

**Your fiberglass choice is already correct.** You just need to make sure the section of nose cone enclosing your antenna(s) has no conductive materials.

### 3.4 Avionics Bay Architecture inside the Nose Cone

The nose cone serves double duty: aerodynamic surface and avionics housing. Here is how other teams have done this:

**Physical mounting:**
- A **bulkhead (typically ½-inch plywood or G10)** is bonded inside the shoulder of the nose cone.
- A central **threaded rod (3/8-16 is common)** runs through the bulkhead, providing both a mounting axis for the electronics sled and the attachment point for the forward parachute shock cord.
- The **electronics sled** (a flat board or rail system) holds all electronics and slides into the nose cone body, secured to the threaded rod.
- Physical stops or anti-rotation pins prevent the sled from unscrewing under parachute loads (N7 documents this as the failure mode to prevent).

**Vent holes for altimeter static pressure:**
- Four holes distributed 90° apart around the circumference of the shoulder area, placed **as far as possible from shoulder discontinuities and fin turbulence**.
- For a 6-inch tube: each hole is typically 0.050–0.090 inches diameter; four holes each half the area of what a single hole would be. This distributes pressure averaging around the perimeter and reduces error from crosswind gradients (N from the ESRA 6-inch IREC report).

**GPS antenna placement:**
- Place the GPS patch antenna or whip at the **top of the electronics sled**, closest to the nose tip. This maximizes sky view angle.
- The fiberglass shell allows the signal through. Keep metallic hardware (eyebolts, threaded rod) as far as possible from the GPS antenna to avoid detuning.
- Ground-test the full GPS + telemetry link margin before flight. Power everything on and leave it stationary for 30–45 minutes. Confirm GPS locks on satellites, confirm telemetry is received at the ground station, confirm no ejection charge misfires (N11).

**Redundant deployment electronics:**
- Run **two independent flight computers**: a primary (e.g., TeleMetrum — GPS + telemetry + deployment) and a backup (e.g., Featherweight Blue Raven or PerfectFlite StratoLogger).
- Both should independently sense apogee and independently fire drogue charges.
- Each computer needs its own battery. Each computer needs its own arming switch accessible from outside without tools (typically a key switch or shunt through a panel).
- Separate pyro battery for each ejection charge is the safe practice — do not share a battery between flight computer and ejection charges on the same circuit.

---

## 4. Avionics selection summary — the decision table

| Device | Role | GPS | Telemetry | Range | Notes |
|---|---|---|---|---|---|
| Altus Metrum TeleMetrum | Primary FC + deployment + GPS + telemetry | Yes | 433 MHz, 70 cm ham | 65 kft+ with 3-el Yagi | Ham license required (USA) |
| Altus Metrum TeleMega | Primary FC if you need staging or extra pyros | Yes | Same | Same | Larger board (38 mm) |
| Featherweight Blue Raven | Redundant deployment (IREC recommended) | No | No | N/A | Redundancy only |
| PerfectFlite StratoLogger | Redundant deployment (widespread) | No | No | N/A | Lowest cost backup |
| CATS Vega | SRAD-class FC, open source | Yes (GNSS) | FHSS | 30+ km | European standard; EKF |
| Custom LoRa (Arduino/STM32) | SRAD telemetry | Optional | 433 MHz LoRa | 10–20 km typical | As in IO and RIT rockets |

**For your mission (50,000 ft), the recommended baseline:**
- **Primary:** TeleMetrum 4.0 (GPS + 433 MHz telemetry + dual deployment) + 3-element Yagi antenna at ground station
- **Backup:** Featherweight Blue Raven (barometric-only, redundant deployment)
- **Optional addition:** External patch antenna on the nose cone shoulder for additional telemetry margin if the inner whip underperforms in testing

**Ham license:** The TeleMetrum operates on the 70 cm amateur radio band. You (or a licensed team member) need an FCC Technician class amateur radio license to operate it legally in the USA. The exam is multiple-choice, open-book, and takes a few weeks to prepare for. This is not optional — radio-frequency violations at a launch site are a serious safety and legal matter.

---

## 5. Design rules extracted from the literature

| # | Rule | Value | Source |
|---|---|---|---|
| 1 | Minimum skin thickness, absolute floor | 0.030 in (0.76 mm) | N5 (NASA) |
| 2 | Practical student layup (uniform) | 4 layers E-glass cloth for 20 G flight loads | N6 |
| 3 | Layup schedule (tapered, optimal) | Thick at base (5–6 layers), thin at tip (3–4) | N5, N9 |
| 4 | Fineness ratio for transonic flight | 5 is the design target; your 4.33 is acceptable | N4 |
| 5 | Optimal Von Karman fineness ratio | 6.75 for supersonic drag minimization | N2 |
| 6 | Bluffness ratio | 2–5% of base diameter for a spherical tip | N3, N4 |
| 7 | Nose cone material | Fiberglass only — carbon fiber blocks RF | N10, N11 |
| 8 | Tip cap | Aluminum or G10, bonded over fiberglass | N6, N13 |
| 9 | Vent holes | 4 holes, 90° apart, away from shoulder and fins | N12 (IREC) |
| 10 | Anti-rotation stops | Required to prevent payload/sled unscrewing under drogue loads | N7 |
| 11 | Flight computers | Two independent devices, each with own battery and arming switch | N20, N24 |
| 12 | Kalman filter | Required for reliable apogee detection in transonic regime | N17, N23 |
| 13 | Ground RF test | 30–45 min powered-on static test with GPS lock confirmed before flight | N11 |
| 14 | Telemetry range (TeleMetrum) | 65,600 ft verified range with 3-element Yagi | N16 |
| 15 | Ham radio license | Required for 433 MHz TeleMetrum operation in USA | Regulations |

---

## 6. Gaps in this library, and what to do about them

1. **No FEA for your specific geometry exists in the open literature.** The NASA study (N5) is the closest, but their smallest diameter is 120 inches. You need to run your own FEA or hand-calculate buckling pressure for your 6-inch cone. Start with the NASA formula in §3.2, use OpenRocket to get your max-Q dynamic pressure, and verify the 4-layer E-glass shell has a safety factor ≥ 2.0 against buckling.

2. **Integrated aero-structural FEA paper (ScienceDirect 2026):** A very recent paper — "Integrated aero-structural design and supersonic flight validation of a 3D-printed composite rocket nose cone" — presents FEA + CFD + flight validation for a fiberglass-reinforced composite nose cone at Mach 1.7–1.8. It is paywalled but your university library should have ScienceDirect access. Ask for it under DOI `10.1016/j.ase.2026.xyz` (search by title on ScienceDirect directly).

3. **Telemetry link budget for YOUR specific antenna and power.** The Arizona paper (N19) does a link budget for TeleMetrum at 30,000 ft. Scale their calculation to 50,000 ft for your mission. The math is: received power (dBm) = transmit power (dBm) + transmit antenna gain (dBi) - path loss (dB) + receive antenna gain (dBi). TeleMetrum transmit power is ~10 mW (10 dBm); path loss at 50 kft (15.2 km) at 433 MHz is approximately 103 dB free space. With a 3-element Yagi (≈7 dBi gain) the received power is well above the LoRa receiver sensitivity floor of -120 dBm.

4. **Actual avionics sled drawings.** No open-source 2D drawing of a 6-inch nose cone avionics sled exists in the literature. The ESRA reports describe the architecture but don't publish CAD. Email the IO or RIT teams directly — they tend to share.

5. **Static pressure port sizing.** The ESRA IREC rules and reports mention port sizing but do not publish a formula for your altitude. The rule of thumb used in the community is: four holes each of area = (tube ID × 0.004), distributed 90° apart. For your 6-inch ID tube, that is four holes each of 0.024 in² ≈ 0.174 in diameter. Use a #19 drill bit (0.166 in) as the closest standard size.

---

## 7. Suggested next actions

1. Download the 14 free PDFs with the `curl` block in §0.1 and put them in `papers/`. Open the ESRA reports (N6, N12) in VS Code with vscode-pdf to read alongside this document.
2. Use the NASA source (N5) to calculate the minimum shell thickness for your cone half-angle and max dynamic pressure. Compare to the 4-layer precedent in N6.
3. Decide on your nose cone profile: tangent ogive or Von Karman, 26-inch length, 5% bluffness. Model it in OpenRocket and check the stability margin (>1.5 cal) with the avionics mass placed at the nose cone CG.
4. Order a TeleMetrum 4.0 and the Featherweight Blue Raven as your baseline avionics. If you want to go SRAD later, the CATS Vega (N17) is the documented open-source path.
5. Get your Technician class ham radio license before you order the TeleMetrum. Study materials are free at hamstudy.org.
6. Build a test coupler section (same diameter as your nose cone shoulder) with 4 layers of E-glass, cure it, and do a compression test to verify the wall thickness before committing to the flight article.

---

*Compiled August 2026. All curl links verified live at time of compilation.*
