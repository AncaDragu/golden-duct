# Golden Duct: building equipment inventory skill

Read this first if you are a Claude (or a person) picking up this package. It explains what we were trying to do, what was decided, and what each file is for.

## The goal

A sustainability lead walks a building with a phone, photographs the mechanical equipment, and hands over the photos plus the utility bills. The Watershed agent should turn that into:

1. **An equipment inventory CSV:** one row per parent piece of equipment (rooftop unit, furnace, water heater...), with make, model, serial, install year, remaining useful life, condition, rated efficiency, primary fuel, location and the photos.
2. **A short evaluation report** for sustainability decisions: what the building runs on, what reaches end of life first, and which upgrades that opens up. It is written so a facilities lead can check it.
3. **A six-bullet reply:** equipment count, the HVAC loop, primary heating (with what comes up first), primary cooling (with what comes up first), other energy-using equipment, and missing information.

The decision-making altitude is sustainability, not facilities. The report only cares about equipment that moves the bills: heating, cooling, ventilation, water heating, lighting and HVAC controls. Everything else is low priority.

This was built during the Golden Duct Hackathon (Sep 2026) on Watershed's own office, 360 9th St, San Francisco: a 4-story, 23,200 sq ft, 1920 masonry office. 79 photos, 14 months of PG&E bills and public city records produced 27 inventory rows.

## Where the customer data is

**All building data lives in Google Drive, not in this zip:** https://drive.google.com/drive/folders/1ERRVruUtz9KJYYR2aWicCVG5jWLgCIWi

| Drive item | What it holds |
|---|---|
| `Photos/` | The 79 walk-through photos. The inventory cites them by IMG number |
| `Utility Bills/` | 14 PG&E statements, Jan 2025 to Feb 2026 |
| `facility_metadata.md` | Address, building type, size, stories, ownership, meters, facts confirmed on site, and what is still to collect. Read this first |
| `Outputs/` | The finished run, unredacted: inventory CSV, report, photo notes, bill extraction, public-records research, lookup results |

Each new building gets its own Drive folder with the same layout. The skill reads from it and writes back to `Outputs/`. The `output/` folder in this zip is a redacted copy for reference only.

## What to do with this package

- **To run the skill:** give a Claude `SKILL.md`. It is self-contained (about 23k tokens): the workflow, the CSV schema, the reply format, and two appendices with the serial-number date rules and the equipment service lives. It needs web access for the public-records research and the efficiency lookups.
- **To understand how it was built or change it:** read `skill_architecture.md`, then the files below.
- **To see a finished run:** open `output/`.

## Key decisions (and why)

- **No computer-vision product beats Claude on the photos.** The commercial tools (ServiceTitan, XOi, AkitaBox and others) are app features on top of a general vision model. The value is in the reference data behind them: serial-number date rules, efficiency databases and service-life tables. So we built those instead. Evidence: `research/cv_prior_art.md`.
- **One skill file, not a folder of scripts.** The Watershed agent may not run code, so the serial rules are embedded as a table the model applies. The Python decoder in `code/` does the same thing deterministically and is how the table is tested. Whether the agent should run code instead is an open question for engineering.
- **Confidence and significance are separate columns.** energy_significance says how much a type of equipment matters to the bills. confidence says how sure we are that the unit exists exactly as the row describes. A high-significance row can have low confidence.
- **Rows can come from evidence other than photos, and are labelled.** A permit that lists 4 furnaces creates rows at permit confidence. A roof condenser implies an indoor unit, because a split system cannot run without one; that row is inferred at High confidence.
- **Nothing is guessed from appearance.** No model, serial, install year or efficiency is filled from how a unit looks. Condition is graded only from visible defects, never from age.
- **primary_fuel is the fuel the unit burns.** A gas-heat rooftop unit is Natural gas even though its fans are electric, because the burned fuel is what electrification replaces.

## What the reference run found

- 4 gas-heat rooftop units, 3 split-system condensers and their gas furnaces, 3 gas water heaters. Most of the HVAC dates from a 2013 replacement and reaches median service life in 2028-2031.
- One rooftop unit was replaced in 2024 with a gas unit at exactly the federal minimum efficiency: a like-for-like replacement that locked in gas.
- Electricity is 66% of site energy and about 90% of cost. About 80% of the gas goes to space heating.
- Still open: the 3rd furnace (probably a unit marked 2-B on floor 2) and a possible 4th, economizers on the rooftop units, and water heater nameplates.

## File map

| Path | What it is |
|---|---|
| `SKILL.md` | The skill. Generated: do not edit by hand |
| `skill_architecture.md` | How the skill is built, and the open code-vs-model decision |
| `research/serial_formats.csv` | 35 serial date rules for the 22 brands in the reference building, each with regex, worked example and source URL |
| `research/serial_formats_extended.csv` | 303 more rows for the long tail of brands, some back to the 1940s, same columns (32 are brands with no date in the serial) |
| `research/serial_formats_extended_gaps.md` | Brands and eras with no public serial format, and what would close them |
| `research/equipment_types_starter.csv` | 64 equipment types: service life, efficiency metric, visual identifiers, nameplate fields to read |
| `research/equipment_type_database.md` | Notes behind the equipment type table |
| `research/cv_prior_art.md` | The scan of existing photo-to-inventory tools |
| `research/building_history.md` | Example public-records research: parcel, permits, benchmarking, envelope |
| `code/skill_body.md` | The skill's workflow sections. Edit this, then rebuild |
| `code/build_skill.py` | Renders `skill_body.md` plus both appendices into `output/SKILL.md` |
| `code/serial_decoder/` | Python serial decoder that reads both serial CSVs |
| `code/efficiency_lookup/` | ENERGY STAR and DOE certification-database lookup, cached |
| `code/run_reference_lookup.py`, `code/reference_lookup/` | Runs both against an inventory CSV |
| `code/tests/` | 887 tests, including every serial example decoding to its stated date |
| `output/` | The reference run: inventory CSV, evaluation report, CSV rules, photo log, lookup results |

Commands (from this folder, with [uv](https://docs.astral.sh/uv/) installed):

```
uv run --with pytest pytest code/tests      # run the tests
uv run python code/build_skill.py          # rebuild SKILL.md after editing the body or CSVs
```

## What is left out

- Photos and utility bills: they are in the Drive folder above, not here, because the bills carry PG&E account numbers. Meter and account numbers are also redacted from the example outputs in this zip.
- The per-building rows script used for the reference run, since it is specific to that building.

## Open items

1. **Code or model decoding:** can the Watershed agent run Python? If yes, running `code/serial_decoder` is more reliable than the model reading Appendix A.
2. **Paid serial guide:** Building Intelligence Center ($15/yr, https://www.building-center.org/) would close some serial gaps (see the gaps file).
3. **Low-confidence rules:** 144 of the 303 extended rules rest on a single third-party source.
