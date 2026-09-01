# Reference documents

Background and design-record material. **These are sources, not the model.**
Numbers extracted from them are tracked in
[`../DESIGN_POINT.md`](../DESIGN_POINT.md), which maps each one to its register
ID and flags the three that conflict with previously-confirmed values.

| File | What it is |
|---|---|
| `02_BUDGET_50KFT_DESIGN.md` | **The design point.** Every value, evaluated and referenced. 61,962 ft nominal / 53,298 ft after derates. Start here. |
| `04_ENGINE_DESIGN.md` | Engine groundwork front to back — oxidiser, tank, feed, injector, igniter, grain, chamber, nozzle |
| `NOZZLE_DESIGN.md` | Nozzle contour derivation, Bartz heat transfer, erosion allowance |
| `00_HYBRID_ENGINE_REFERENCE.md` | Hybrid literature survey, source keys S1–S35 |
| `01_NOSECONE_AVIONICS_REFERENCE.md` | Nose cone and avionics literature, source keys N1–N24 |
| `CEA_and_CFD_guide.md` | How the CEA and CFD runs were set up |
| `SETUP.md` | Environment setup for the authors' own analysis scripts |
| `nozzle_design.png` | Nozzle contour plot |
| `references_engine.bib` | Bibliography, engine side |
| `references_nosecone.bib` | Bibliography, nose cone and avionics side |

## Relationship to `docs/references.bib`

Separate bibliographies, deliberately. `docs/references.bib` cites the sources
behind **equations implemented in the model** — one entry per module, DOIs
publisher-verified. The two files here are the design authors' own reading
lists, keyed S1–S35 and N1–N24 against their documents. They are not merged
because they answer different questions: *"why is this equation correct"* versus
*"why is this design choice reasonable"*.

## Data extracted into the model

- `../../data/cea_S10W1_N2O_35bar.csv` — NASA CEA O/F sweep at 35 bar for the
  S10W1 blend. **This resolved register G11**, the model's only PLACEHOLDER.
  Loaded by `goddard.props.cea.load_of_sweep`; pinned by
  `tests/test_cea_real_table.py`.
