# Reference lookup notes

Results: `reference_lookup_results.csv`. Rerun: `uv run python run_reference_lookup.py` in `code/` (cached, so free).

## What each tool covers

- **Serial decoder** (`code/serial_decoder/`): rules live in `research/serial_formats.csv`, one row per format with its source URL. Covers Carrier/Bryant/Payne, ICP brands, ADP, Lennox, Trane, Rheem/Ruud, Goodman/Amana, Daikin, York/Luxaire, A.O. Smith, Bradford White, Rinnai, Navien, HTP, Hoshizaki, Mitsubishi. True, Auto-Chlor and CaptiveAire have no published date code. Also loads `serial_formats_extended.csv`. Returns all matching rules, ranked.
- **Efficiency lookup** (`code/efficiency_lookup/`): ENERGY STAR datasets plus the DOE certification database (CCMS). AHRI not used: its terms forbid use in software and the API is paid.

## Dates

- All 8 decodable serials agree with the CSV: the 3 RTUs (Feb 2013), 3 condensers (Nov 2012, Nov 2012, Jul 2014), GD-FURN-01 (Jan 2013), GD-RTU-04 (May 2024).
- New: ADP coil on GD-FURN-02 is Feb 2012 (Medium confidence).

## Efficiency

- GD-RTU-04: CCMS lists SEER2 13.4, EER2 11.05 and 81% AFUE, but as a near match: the listing has K at position 10, the CSV has H. Check the plate.
- GD-WH-01: Phoenix series 94-96% thermal efficiency, agrees with the CSV's 95%.
- GD-REF-01: True 3-door glass reach-ins use 2.35-7.14 kWh/day. Series range only.
- **Conflict, GD-DW-01:** model "AC" matches ENERGY STAR exactly, but that listing is an undercounter glasswasher. The CSV says door-type. Check the model.

## Gaps

- The 2012-2014 Carrier models (48ES, 24ABB, 59SC5) are discontinued, and both databases drop discontinued models. CEC MAEDbS keeps archived models but only exports by hand.
- The coil is listed only with current condensers, so no rating fits this system.
- No model number for the Rheem Prestige heaters, ice machine or oven, so no lookup.
- No serial read for the HTP, Rheem Prestige, True or Hoshizaki units.
