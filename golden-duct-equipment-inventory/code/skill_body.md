---
name: building-equipment-inventory
description: Turn a building walk-through (equipment photos, utility bills, facility metadata) into an equipment inventory CSV, a sustainability-level evaluation report, and a six-bullet summary. Pulls public permit, assessor and benchmarking records, decodes serial numbers into manufacture dates, looks up rated efficiency in ENERGY STAR, and applies median service lives. Use when someone has photographed a building's mechanical equipment and wants to know what is in the building, how old it is, what comes up for replacement first, and what is still missing. Built on the Golden Duct Hackathon run for 360 9th St, San Francisco (Sep 2026).
---

# Building equipment inventory

Photos + bills + facility metadata in. Three files and a six-bullet reply out. The decision-making altitude is sustainability, not facilities: the report must be vettable by a facilities lead, but it is written for the person deciding what to upgrade and when.

Reference run: 360 9th St, San Francisco (Watershed HQ), Sep 2026. Appendix A holds the serial-number rules and Appendix B the service lives, so this file is self-contained.

## 0. Inputs and questions up front

**Customer data lives in one Google Drive folder per building.** Look there first for photos, bills and metadata. The layout:

```
Photos/                  every equipment and building photo (HEIC or JPEG)
Utility Bills/           bill PDFs
facility_metadata.md     address, type, size, stories, ownership, meters, facts confirmed on site, open items
Outputs/                 written by this skill: inventory CSV, report, photo notes, bill extraction, records research
```

Reference building (360 9th St, San Francisco): https://drive.google.com/drive/folders/1ERRVruUtz9KJYYR2aWicCVG5jWLgCIWi

If facility_metadata.md exists, treat its "confirmed on site" facts as ground truth and its open items as the checklist. If it does not exist, create it from step 1. Work on local copies, then write results back to `Outputs/` and update facility_metadata.md with anything newly confirmed. In a local repo, keep photos and bills git-ignored: bills carry utility account numbers.

Before starting, ask every question in one batch, then run without stopping:

1. The building's Drive folder link, if not given.
2. Any facility metadata from step 1 that is missing.
3. Owner-occupied, or leased? This decides who holds the replacement decision.

## 1. Facility metadata

Read what is already known first (`facility_metadata.md`, a Watershed facility record, or what the user says), then fill gaps from public records in step 2. Record every field with its source. When sources disagree, keep all values, pick one, and say why.

| Field | Notes |
|---|---|
| Address | Street, city, state, ZIP. Check for a lot with several addresses (350-360 9th St is one parcel) |
| Building type | Use the benchmarking category where one exists (Office, Retail, Hospital...) |
| Location and climate | City, and the climate zone (ASHRAE, plus the state energy-code zone) |
| Year built and major renovations | From the assessor and permits |
| Stories | Assessor and permits. Users misremember this; the reference run was told 5 and records said 4 |
| Floor area | The owner's records win for reporting. List the assessor and benchmarking values too |
| Construction | Wall type, structure, roof. From permit construction type codes and photos |
| Ownership and occupancy | Owner-occupied, single tenant, multi-tenant. Who pays which meters |
| Meters | Count and type from the bills. Map meters to floors or tenants and ask the user to confirm |

## 2. Public records research

Run this as a background agent while photos are processed. Output: `research/building_history.md`, every row cited with a URL you actually fetched. If a source is paywalled or fails, say so in the row. Never fill a gap from memory.

Look for, in this order:

1. **Parcel and assessor roll:** parcel ID, year built, stories, floor area, use class, construction type, last sale.
2. **Building permits, all types:** building, mechanical, plumbing, electrical, boiler. Mechanical permits are the most valuable: they name equipment counts and replacement years ("replace 4 forced air furnaces, 2 split air conditioners and four packaged units, in-kind"). List every energy-relevant permit with number, date, description and cost.
3. **Energy benchmarking filings:** yearly site EUI (energy per square foot), ENERGY STAR score, kWh and therms, reported floor area. Flag years that jump 4-5x as likely data-entry errors.
4. **Envelope clues:** reroofing, window replacement and seismic permits; the permit construction-type code for wall type.
5. **Owner, manager and certifications (LEED):** best effort, low priority.

Where to look:

- **San Francisco:** DataSF Socrata API, no key needed. Parcels `acdm-wktn`, assessor roll `wv5m-vpq2`, land use `fdfd-xptc`, building permits `i98e-djp9`, electrical `ftty-kx6y`, plumbing and mechanical `a6aw-rudh`, benchmarking `4ua7-5sfx`. Query by block/lot where the dataset has it, since address queries pick up look-alikes (360 9th Avenue).
- **Other cities:** find the city's open-data portal (most are Socrata or ArcGIS Hub) and search it for "building permits", "assessor" and "benchmarking". Benchmarking laws with public data include NYC (LL84), Chicago, Boston (BERDO), Washington DC, Seattle, Denver, Philadelphia, Los Angeles (EBEWE), Austin and Minneapolis. NYC permits are in DOB NOW / BIS open data; LA in LADBS open data. Where no portal exists, web-search the address with "permit" and the county assessor site.
- **Broker listings** (LoopNet, CompStak) for stories, size and renovation year. Usually search snippets only; they block fetches.

## 3. Photos

1. Get every photo from wherever the user put it (a Drive folder, an upload). If the Drive connector only returns base64, use a Drive client such as rclone instead: base64 photos are too large to pass around.
2. Convert HEIC to JPEG at about 1600 px for viewing (on a Mac: `sips -s format jpeg -Z 1600 in.HEIC --out out.jpg`).
3. Look at every photo. Write one line per photo to `Outputs/photo_notes.md`: what it shows, every nameplate field you can read exactly, and any hand markings ("Floor #2-A"), panel labels or disconnect labels. Labels tie equipment to floors and meters: circuit directories name what each breaker feeds, and roof disconnects are often labelled by the floor they serve.
4. For 50 or more photos, split the photo reading across parallel agents in batches of about 20, and have each return its notes lines.

Photo evidence that is worth asking for if missing: the rating plate on every furnace and air handler (often inside the door), the side label on tankless water heaters, the rooftop units' outside-air hoods (economizers), the elevator machine room, above a ceiling tile, a window corner.

## 4. Photos to rows

**What counts as a row**

- One row per parent piece of equipment. A rooftop unit is one row; its fans, compressor and filters are not.
- Distribution, fittings and labels are not rows. Duct fittings, disconnects and refrigerant lines go in the notes of the unit they serve. So does the indoor cooling coil sitting on a furnace.
- Systems of many small items get one row: lighting, thermostats. The count goes in the notes.
- Drop items with no meaningful energy use (antenna masts, security panels, portable purifiers). Drop the IT rack: it belongs in the bill analysis.

**De-duplicating**

1. Same serial = same unit. Sequential serials (4812E04427, 4812E04428) are separate units.
2. Same make and model, no serial: merge only if the photos are seconds apart and the surroundings match. Two photos of one unit from different angles are one row, even if the user calls them two units.
3. Overview shots (roof panoramas) count and grade condition. They never create a row on their own.
4. The same image uploaded twice (JPEG and HEIC) is skipped.

**Rows that were not photographed**

Add a row when something must exist or a record says it exists, and label it:

- **inferred, High confidence:** physically required. Each split-system condenser needs an indoor half, so three roof condensers and one furnace found means two more indoor units.
- **permit, Medium or Low:** a permit says it was installed. It proves it existed then, not that it exists now.
- **inferred, Low:** indirect evidence, such as a Hoshizaki filter implying an ice machine.

**The model may not:** invent a model or serial from appearance; turn a series rating into a nameplate rating; count an overview-photo unit as new when it could be one already listed; set an install year from "looks about 10 years old"; use age to grade condition.

## 5. Schema

One CSV, `Outputs/equipment_inventory.csv`, one row per parent unit. Columns in this order:

| Column | Rule |
|---|---|
| equipment_id | `<SITE>-<type code>-<nn>`. Type codes: RTU, CU (condensing unit), FURN, AHU, BLR, CHLR, CT, WH, KEF (kitchen exhaust fan), MUA (make-up air), HOOD, OVEN, REF, DW, ICE, ELEV, LTG, CTRL, ELEC |
| equipment_type | Plain name matched to Appendix B |
| category | HVAC heating / HVAC cooling / HVAC heating and cooling / Air distribution / Water heating / Lighting / Controls / Plug and process / Vertical transport / Electrical |
| make, model, serial | Exactly as printed. Unreadable characters marked "partly faded". Nothing guessed |
| install_year | Priority: printed manufacture date, then serial decode (step 6), then a matching permit date |
| install_year_basis | Which of the three was used, with the evidence |
| useful_life_years, useful_life_source | Median service life from Appendix B (ASHRAE medians first, then DEER, then manufacturer typical). Every unit of a type gets the same number |
| remaining_life_years | install_year + useful life - current year. Negative means past median life. Computed by the build script |
| condition | Visual only, outside of the unit. Good: no visible defects. Fair: cosmetic wear (surface rust on guards, faded labels, overspray). Poor: damage that cuts performance (corroded coil fins, torn refrigerant-line insulation, missing panels, leaks). Unknown if not photographed |
| condition_basis | What was seen |
| nameplate_efficiency | Only what the rating plate, EnergyGuide label or an ENERGY STAR / DOE listing for the exact model says. A series rating is allowed only if labelled as one in efficiency_basis |
| efficiency_basis | Where the number came from. If blank, say why (plate not photographed) and give the expected range if a matching unit is known, marked unverified |
| capacity | Btu/h, tons, kW, gallons |
| primary_fuel | Natural gas / Electricity / Propane / Fuel oil / District steam / None / Unknown. Equipment that burns a fuel is listed under that fuel even when its fans run on electricity, because the burned fuel is what electrification replaces |
| fuel_detail | Secondary fuels, for example "Natural gas (heat) + electric (blower)" |
| location | Floor and space. Floor 1 = the main (ground) floor unless the user says otherwise. Say where each floor assignment came from (label, user, inference) |
| evidence_level | nameplate / visual / permit / inferred |
| confidence | High / Medium / Low that the unit exists as described |
| energy_significance | High: heating, cooling, ventilation, their controls, water heating, lighting. Medium: kitchen exhaust, cooking, commercial refrigeration. Low: the rest |
| photos | File names in `Photos/`, best nameplate shot first |
| notes | Pairings (which condenser serves which furnace), labels, anything a facilities lead needs to check |

Write the CSV directly, one row per unit, columns in the order above. Compute remaining_life_years for every row with both an install year and a useful life. When a later answer or photo changes a row, edit that row and note the new evidence in install_year_basis, efficiency_basis or notes; never silently overwrite.

## 6. Serial decode and efficiency lookup

**Serial decode (Appendix A).** For every row with a make and serial:

1. Find the brand in Appendix A, including the "also sold as" names. Many brands share a parent's format (Bryant and Payne use Carrier's).
2. Check the serial against each of that brand's rules. The serial pattern is a regular expression. Its named groups say where the date sits: `yy` two-digit year, `yyyy` four-digit year, `y` one-digit year (decade from the era), `yl` a year letter, `ww` week, `mm` month number, `ml` a month letter, `doy` day of year, `dd` day. Other groups are plant or product codes.
3. Read the year and period with the Year and Week-or-month columns. `letter:B=1971,...;cycle=10` is a year-letter table that repeats every 10 years. `letters:ABCDEFGHJKLM` is a month-letter table: the first letter is January, the second February, and so on. `concat` joins two groups into the year. `none` means that part is not encoded. Confidence letters: H manufacturer document, M two agreeing third-party sources, L one source.
4. Reject a match when its month is outside 1-12, its week outside 1-53, or its decoded year outside that rule's era. Many patterns do not check these ranges themselves.
5. If more than one rule or century still fits, list every candidate and pick using any printed date, the permit, and the refrigerant on the plate (R-22 almost always means 2009 or earlier; R-410A mostly 2006 onward). Water heaters have no refrigerant: use the printed date (many water heater plates print one), the permit, or the look of the unit's labels. If nothing separates them, record the newest candidate with Low confidence and list the others in install_year_basis. 
6. A printed date beats a decode. A decode more than a year off a printed date is a finding: note it.
7. Brands in the "no date in the serial" list, or missing from the table: use the permit or service records and say so.

**Efficiency lookup.** For every row with a model number, in this order. Stop at the first source that lists the exact model.

1. **ENERGY STAR certified products** (free, no key). Query `https://data.energystar.gov/resource/<dataset>.json?$where=upper(<model field>) like 'PREFIX%'` using the first 4-6 characters of the model. Datasets: Light Commercial HVAC `e4mh-a2u3`, Furnaces `i97v-e8au`, Commercial Water Heaters `xmq6-bm79`, Gas Water Heaters `6sbi-yuk2`, Commercial Refrigerators and Freezers `wati-2tfp`, Commercial Dishwashers `pk8q-dim8`, Commercial Ice Machines `nak5-fsjf`, Commercial Ovens `c8av-ccf7`. The dataset catalog is at `https://data.energystar.gov/api/catalog/v1?domains=data.energystar.gov`.
2. **DOE Compliance Certification Database** (`https://www.regulations.doe.gov/certification-data/`): residential and commercial central AC and heat pumps, furnaces, water heaters. It needs a browser user agent.
3. **Manufacturer spec sheets.** Search `"<model prefix>" product data` or `specifications`. Carrier, Bryant, Payne, ICP, Heil and Tempstar documents sit on `shareddocs.com/hvac/docs/`. Spec sheets keep discontinued models, which both databases drop, and their model-number guide explains every character.
4. **California appliance database (CEC MAEDbS)** keeps archived models, but only exports by hand.

Rules:
- An exact model match fills nameplate_efficiency. A near match (one character off, or a prefix match) goes only in efficiency_basis, with the differing position. Use the spec sheet's model guide to say whether that character changes the rating. On the reference run, H vs K at position 10 on an ICP unit was the low-NOx burner version with identical ratings.
- A series rating ("13 SEER" for the whole line) is labelled as a series rating.
- Indoor coils are rated only in pairs with an outdoor unit, so a coil match does not give a rating.
- The AHRI directory is paywalled and its terms forbid software use. Do not scrape it.
- Say when a unit sits exactly at the federal minimum for its year: that marks a base-efficiency like-for-like replacement.

## 7. Utility bills

1. Extract every bill to `Outputs/utility_bills_extracted.csv`: one row per meter per bill (month, account/service ID, meter, address, rate, commodity, period, days, kWh, peak kW, therms, charges, adjustments, notes).
2. `Outputs/utility_bills_summary.md`: meters and rates, whether the bills cover the whole building, 12-month totals, cost before and after one-off credits, and share by meter.
3. Checks that feed the report:
   - **Heating share of gas:** summer months are water heating and cooking. (annual gas - 12 x summer baseline) / annual gas is roughly space heating.
   - **Cooling share of electricity:** the summer rise above the spring/fall baseline.
   - **Site energy per square foot** against the benchmarking filing. Within a few percent means the bills cover the building.
   - **Meter to floor:** tie high-impact equipment to the meter that pays for it.

## 8. The report

`Outputs/building_evaluation.md`. It covers only the high-impact equipment (heating, cooling, ventilation, water heating, lighting, HVAC controls). Everything else is one "low priority" line at the end. Plain words; gloss any technical term once. Sections:

1. **Bottom line:** 3-4 bullets. What the building runs on, the replacement timing decision, the electricity and gas split, the envelope in one line.
2. **Building at a glance:** the step 1 table, with sources.
3. **Energy use:** annual electricity and gas, share, seasonal pattern, heating share of gas, price per kWh and therm.
4. **High-impact equipment:** one table row per system: fuel, count, what it is, age and end of life, confidence. Follow it with the cooling tons per sq ft check and a line on any missing efficiencies and why.
5. **What this means for upgrade decisions:** numbered, ordered by year of end of life.
6. **Envelope and insulation:** walls, windows, roof, ducts, each with confidence. Insulation is inferred from photos, building age against the local energy code, and how strongly gas use tracks cold weather. None of these measures it.
7. **What to validate:** high-impact items only, ranked by effect on the upgrade case, each with where to look. Then one "Low priority" line.
8. **Sources.**

Also write `Outputs/csv_criteria.md` only if this run departed from the rules in this skill; otherwise point to the skill.

## 9. The reply

When the files are written, reply with exactly this and nothing else (no em-dashes, no preamble):

```
**Done.** <N> equipment items recorded (<a> read from nameplates, <b> photographed without a readable plate, <c> from permits or inference). Files: Outputs/equipment_inventory.csv, Outputs/building_evaluation.md.

- **HVAC loop:** <how heat and cooling reach the spaces: the unit types, how many, how they are controlled>.
- **Primary heating:** <system, fuel, count, share of heating capacity>. First up: <equipment_id, what it is, median end of life year>.
- **Primary cooling:** <system, count, total tons>. First up: <equipment_id, what it is, median end of life year>.
- **Other energy-using equipment:** <water heating, lighting, cooking, refrigeration, in one line>. First up: <equipment_id, year>.
- **Missing information:** <the one to three high-impact gaps that most change the upgrade case, each with where to find it>.
```

"Primary" is the system carrying the largest share of heating capacity (Btu/h) or cooling capacity (tons). "First up" is the unit with the earliest median end of life; break ties by worse condition. If a system has no dated unit, say "First up: unknown, no dated unit".
