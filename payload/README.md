# Payload — CosmicWatch Desktop Muon Detector v3X

The flight payload. A compact scintillator + silicon-photomultiplier muon
telescope, flown to measure the cosmic-ray muon rate against altitude.

## Provenance and licence

Source: <https://github.com/spenceraxani/CosmicWatch-Desktop-Muon-Detector-v3X>
Author: Spencer Axani.

> ⚠️ **Licensed CC BY-NC 4.0** — attribution required, **commercial use and
> redistribution prohibited** without the author's permission. Our use is
> educational, which the licence permits. The full licence text is in
> [`cosmicwatch/LICENSE`](cosmicwatch/LICENSE) and must stay with these files.
> Credit Spencer Axani in any report, poster or presentation that includes
> payload data.

**Only what the rocket work needs is vendored here** — about 3.3 MB of a
~200 MB repository. The GUI (78 MB), sample data (57 MB) and photographs
(52 MB) are deliberately not copied; clone upstream if you need them.

| Here | Why |
|---|---|
| `cosmicwatch/drawings/Enclosure dimensions.pdf` | fit check and enclosure mass |
| `cosmicwatch/drawings/Scintillator dimensions.pdf` | scintillator mass |
| `cosmicwatch/drawings/SiPM datasheet.pdf` | sensor limits, incl. temperature |
| `cosmicwatch/drawings/Circuit_Diagram.pdf` | integration and power |
| `cosmicwatch/Purchasing_List_v3X_sa.xlsx` | bill of materials |
| `cosmicwatch/firmware/` | flight firmware, v3X.1.1.52 |
| `cosmicwatch/UPSTREAM_README.md` | upstream description as-is |

## What it means for the vehicle

### Mass — 0.215 kg, computed, not measured

**The upstream repository states no mass anywhere.** This is built from its own
drawings:

| Item | Basis | Mass |
|---|---|---|
| Enclosure PN2506 | aluminium extrusion, 66.4 × 39.9 mm, 73.7 mm long, 1.88 mm wall → 50.3 cm³ | 136 g |
| Endplates ×2 | acrylic, 3 mm | 19 g |
| Scintillator | 50 × 50 × 10 mm at 1.03 g/cc | 26 g |
| Boards | PCBs, Pico, OLED, connectors | ~25 g |
| Sundries | microSD, screws, foil, tape | ~10 g |
| | **total** | **~215 g** |

Two caveats, both recorded in `goddard/config/schema.py`:

1. **The scintillator drawing gives 50 × 50 but no thickness.** 10 mm assumed.
   At 20 mm the total rises to ~241 g.
2. **Coincidence mode needs two detectors** — roughly 0.43 kg plus the CAT5
   cable. Which configuration flies is still open.

**Weigh the real unit** and this becomes a confirmed number rather than an
estimate.

### Fit — comfortable

Enclosure is 66.4 × 39.9 mm against a 145.4 mm tank bore. No packaging problem.

> Note the *"10 × 15 cm"* in the upstream enclosure README is the **acrylic
> sheet** you send to the laser cutter, which yields ten endplates. It is not
> the enclosure footprint. Easy to misread as a fit failure.

### Power — 0.5 W

Small, but it is a continuous draw for the whole flight plus pad hold. Feeds
the avionics battery sizing (avionics mass is still open).

### It already logs flight data

The detector records **timestamp, ADC value, coincidence flag, temperature,
pressure and acceleration** to microSD. That makes it a secondary flight-data
recorder for free, which may reduce what the primary avionics has to carry —
worth considering before sizing the avionics stack.

## Open questions

- **Weigh the assembled detector.** Closes the payload mass estimate.
- **One detector or two?** Coincidence rejects background but doubles mass.
- **Scintillator thickness** — not dimensioned upstream.
- **Cold soak.** SiPM gain is strongly temperature-dependent and the vehicle
  reaches roughly −50 °C near apogee. Check the SiPM datasheet limits and
  decide whether the payload needs thermal management or an in-flight gain
  correction. This is a payload-performance question, not a trajectory one, so
  the flight model does not currently capture it.
