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

## Appendix A: serial-number date rules

303 rules. Sources and full notes for every rule are in the research CSVs this file is built from.

| Brand (also sold as) | Equipment | Era | Serial pattern | Year | Week or month | Example | Conf. |
|---|---|---|---|---|---|---|---|
| A.O. Smith (National, Glascote, Perma-Glas) | tank water heater | 1970-1979 | `^[A-Z]\d{2}-?(?P<ml>[A-HJ-M])-?(?P<yy>\d{2})-?\d{5,6}$` | yy | letters:ABCDEFGHJKLM | A20-H-78-015482 = Aug 1978 | M |
| A.O. Smith (National, Glascote, Perma-Glas, State, Reliance) | tank water heater | 1982-2004 | `^[A-Z](?P<ml>[A-HJ-M])(?P<yy>\d{2})-?[A-Z]?\d{5,7}(?:-?[A-Z0-9]+)?$` | yy | letters:ABCDEFGHJKLM | GG03-1495366-S29 = Jul 2003 | M |
| A.O. Smith (State, Reliance, GSW, John Wood, U.S. Craftmaster) | water_heater | 1990-2007 | `^[A-Z]?(?P<yy>\d{2})(?P<mm>\d{2})[A-Z0-9]\d+$` | yy | mm | 0510A002243 = Oct 2005 | M |
| A.O. Smith (State, Reliance, GSW, John Wood, U.S. Craftmaster) | water_heater | 1990-2010 | `^(?P<ml>[A-HJ-M])(?P<yy>\d{2})[A-Z]\d+$` | yy | letters:ABCDEFGHJKLM | E07A135491 = May 2007 | M |
| A.O. Smith (State, Reliance, GSW, John Wood, U.S. Craftmaster) | water_heater | 1990-2010 | `^[A-Z](?P<ml>[A-HJ-M])(?P<yy>\d{2})[-A-Z0-9]+$` | yy | letters:ABCDEFGHJKLM | AF04A093001 = Jun 2004 | M |
| A.O. Smith (Glascote, Perma-Glas, Kenmore) | tank water heater | 2004-2008 | `^(?P<ml>[A-HJ-M])(?P<yy>\d{2})[A-Z]?\d{6,7}$` | yy | letters:ABCDEFGHJKLM | E07A135491 = May 2007 | M |
| A.O. Smith (State, Reliance, GSW, John Wood, U.S. Craftmaster) | water_heater | 2008-now | `^[A-Z]?(?P<yy>\d{2})(?P<ww>\d{2})[A-Z0-9]\d+$` | yy | ww | 1210A002243 = week 10 2012 | H |
| AAON (AAONAIRE) | rooftop unit, air handler, condensing unit, heat pump, chiller | ?-present | `^(?P<yyyy>(?:19\|20)\d{2})(?P<mm>0[1-9]\|1[0-2])[A-Z]{3}\d{5}$` | yyyy | mm | 200108AKG26241 = Aug 2001 | L |
| AAON (AAONAIRE) | rooftop unit, air handler, condensing unit, heat pump, chiller | 1985-1994 | `^[A-Z]{4}\d(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])$` | yy | mm | AKEC08701 = Jan 1987 | L |
| AAON (AAONAIRE) | rooftop unit, air handler, condensing unit, heat pump, chiller | 1995-1999 | `^(?P<yy>\d{2})(?P<ml>[A-HJ-M])[A-Z]{3}\d{3}$` | yy | letters:ABCDEFGHJKLM | 97JKGK153 = Sep 1997 | L |
| ABB (drives) | variable frequency drive | ?-present | `^[0-9](?P<yy>[0-9]{2})(?P<ww>0[1-9]\|[1-4][0-9]\|5[0-3])[0-9]{5}$` | yy | ww | 1114201234 = week 42 2011 (Oct 2011) | M |
| Addison (Addison Products, APCO) | air handler, DOAS, water source heat pump, rooftop unit | ?-present | `^(?P<yy>\d{2})\d{2}-\d{3}-\d{3}-\d{4}$` | yy | none | 0710-043-115-0006 = 2007 | L |
| Addison (Addison Products, APCO) | air handler, DOAS, water source heat pump, rooftop unit | 1975-1990 | `^\d(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{6}$` | yy | mm | 28607168189 = Jul 1986 | L |
| Addison (Addison Products, APCO) | air handler, DOAS, water source heat pump, rooftop unit | 1975-1995 | `^(?P<yy>\d{2})(?P<ml>[A-HJ-M])-?[A-Z0-9]\d{5}$` | yy | letters:ABCDEFGHJKLM | 92A-C70097 = Jan 1992 | L |
| Addison (Addison Products, APCO) | air handler, DOAS, water source heat pump, rooftop unit | 1990-present | `^\d{2}(?P<yy>\d{2})\d{8}$` | yy | none | 009920304091 = 1999 | L |
| ADP (Advanced Distributor Products) | coil, hvac | 1990-now | `^\d{2}(?P<yy>\d{2})(?P<ml>[A-HJ-M])\d+$` | yy | letters:ABCDEFGHJKLM | 3412J17723 = Sep 2012 | M |
| AERCO | boiler, water heater | ?-present | `^[A-Z]-(?P<yy>\d{2})-\d{3,4}$` | yy | none | G-97-031 = 1997 | L |
| Airtemp | air conditioner, heat pump, furnace | 2012-present | `^[A-Z]{3}(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{5}$` | yy | mm | VSG181150070 = Nov 2018 | L |
| Amana | furnace, air conditioner, heat pump | ?-now | `^(?P<yy>\d{2})-?\d{5}$` | yy | none | 96-90391 = 1996 | M |
| Amana | furnace, air conditioner, heat pump | ?-present | `^(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{4,6}$` | yy | mm | 0109145052 = Sep 2001 | M |
| Amana | furnace, air conditioner, heat pump | 1971-1995 | `^(?P<yl>[BLACKHORSE])[A-Z0-9]{5,11}$` | letter:B=1971,L=1972,A=1973,C=1974,K=1975,H=1976,O=1977,R=1978,S=1979,E=1980;cycle=10 | none | BB80200127 = 1971 or 1981 or 1991 | M |
| Amana PTAC (Amana) | PTAC, packaged terminal heat pump | ?-present | `^(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{6}$` | yy | mm | 1306123456 = Jun 2013 | H |
| American Appliance (American) | tank water heater | 1985-1986 | `^[A-Z](?P<yy>\d{2})(?P<ww>\d{2})\d{2,5}[A-Z]?$` | yy | ww | C860305922A = week 3 1986 (Jan 1986) | M |
| American Water Heater (U.S. Craftmaster, Whirlpool, Envirotemp, Premier, Mor-Flo/American, Proline, Hotmaster, Polaris, Ace, Tru Value, Servistar, Standard, Revere, Shamrock, Champion, Craftmaster) | tank water heater | 1989-present | `^[A-Z]?(?P<yy>\d{2})(?P<ww>\d{2})[A-Z]?\d{5,9}$` | yy | ww | 0020118002 = week 20 2000 (May 2000) | M |
| AquaSnap (Carrier AquaSnap) | chiller | 1980-present | `^(?P<ww>\d{2})(?P<yy>\d{2})[A-Z]\d{5}$` | yy | ww | 4311Q76606 = week 43 2011 | L |
| Aquazone (Carrier Aquazone) | water source heat pump | 1980-present | `^(?P<ww>\d{2})(?P<yy>\d{2})[A-Z]\d{5}$` | yy | ww | 4006A17330 = week 40 2006 | L |
| Armstrong (AirEase, Ducane, Concord, Magic-Pak, Allied, Aire-Flo) | furnace, air conditioner, heat pump | 1970-1977 | `^(?P<dd>[0-3]\d)(?P<ml>[A-HJ-M])(?P<y>\d)7[A-Z]{2}\d{3}$` | y | letters:ABCDEFGHJKLM | 15A67JA098 = 15 Jan 1976 | M |
| Armstrong (AirEase, Ducane, Concord, Magic-Pak, Allied, Aire-Flo) | furnace, air conditioner, heat pump | 1978-1992 | `^[A-Z]\d{5}(?P<ml>[A-HJ-M])(?P<yl>[89A-HJ-N])[ABC]$` | letter:8=1978,9=1979,A=1980,B=1981,C=1982,D=1983,E=1984,F=1985,G=1986,H=1987,J=1988,K=1989,L=1990,M=1991,N=1992 | letters:ABCDEFGHJKLM | C89274AAC = Jan 1980 | M |
| Armstrong (AirEase, Ducane, Concord, Magic-Pak, Allied, Aire-Flo) | furnace, air conditioner, heat pump | 1993-present | `^\d{2}(?P<yy>\d{2})(?P<ml>[A-HJ-M])\d{5}$` | yy | letters:ABCDEFGHJKLM | 8495A12345 = Jan 1995 | M |
| Armstrong (circulators) (Armstrong Pumps) | circulator | ?-present | `^(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])$` | yy | mm | 0106 = June 2001 | H |
| Armstrong (VMS pumps) (Duijvelaar Pompen) | vertical multistage pump | ?-present | `^(?P<ww>0[1-9]\|[1-4][0-9]\|5[0-3])/(?P<yyyy>(19\|20)[0-9]{2})[/-][0-9]{3,6}$` | yyyy | ww | 19/2004/234567 = week 19 2004 (May 2004) | H |
| Baldor (Baldor-Reliance, Dodge) | AC motor, DC motor, grinder | 1966-1974 | `^(?P<ml>[A-HJ-M])(?P<yl>[R-Z])$` | letter:R=1966,S=1967,T=1968,U=1969,V=1970,W=1971,X=1972,Y=1973,Z=1974 | letters:ABCDEFGHJKLM | CU = March 1969 | H |
| Baldor (Baldor-Reliance, Dodge) | AC motor, DC motor, grinder | 1975-1997 | `^(?P<ml>[NP-Z])(?P<yl>[A-HJ-NP-UW-Z])$` | letter:A=1975,B=1976,C=1977,D=1978,E=1979,F=1980,G=1981,H=1982,J=1983,K=1984,L=1985,M=1986,N=1987,P=1988,Q=1989,R=1990,S=1991,T=1992,U=1993,W=1994,X=1995,Y=1996,Z=1997 | letters:NPQRSTUVWXYZ | RK = April 1984 | H |
| Baldor (Baldor-Reliance, Dodge) | AC motor, DC motor, grinder | 1998-2020 | `^(?P<ml>[A-HJ-M])(?P<yl>[A-HJ-NP-UW-Z])$` | letter:A=1998,B=1999,C=2000,D=2001,E=2002,F=2003,G=2004,H=2005,J=2006,K=2007,L=2008,M=2009,N=2010,P=2011,Q=2012,R=2013,S=2014,T=2015,U=2016,W=2017,X=2018,Y=2019,Z=2020 | letters:ABCDEFGHJKLM | FL = June 2008 | H |
| Baldor (Baldor-Reliance, Dodge) | AC motor, DC motor, grinder | 2021-2027 | `^(?P<ml>[NP-Z])(?P<yl>[A-G])$` | letter:A=2021,B=2022,C=2023,D=2024,E=2025,F=2026,G=2027 | letters:NPQRSTUVWXYZ | SD = May 2024 | H |
| Bard | wall-mount air conditioner, wall-mount heat pump, furnace | 1962-1980 | `^\d{5,6}(?P<ml>[A-HJ-M])(?P<yl>[B-HJ-PR-V])$` | letter:B=1962,C=1963,D=1964,E=1965,F=1966,G=1967,H=1968,J=1969,K=1970,L=1971,M=1972,N=1973,O=1974,P=1975,R=1976,S=1977,T=1978,U=1979,V=1980 | letters:ABCDEFGHJKLM | 28193MT = Dec 1978 | M |
| Bard | wall-mount air conditioner, wall-mount heat pump, furnace | 1980-1980 | `^\d{3}(?P<ml>[DF])(?P<yl>A)\d{5,6}$` | letter:A=1980 | letters:ABCDFHJKLMNP | 123DA123456 = Apr 1980 | M |
| Bard | wall-mount air conditioner, wall-mount heat pump, furnace | 1980-present | `^[0-9A-Z]{3}(?P<ml>[A-DFHJ-NP])(?P<yy>\d{2})\d{7}(?:-?\d{1,2})?$` | yy | letters:ABCDFHJKLMNP | 000F950926066-1 = May 1995 | M |
| Bell & Gossett (B&G) | circulator, pump | ?-present | `^(?P<ml>[A-L])(?P<y2>[0-9])(?P<y1>[0-9])$` | concat:y1,y2 | letters:ABCDEFGHIJKL | C32 = March 2023 | L |
| Beverage-Air (Bev Air, Beverage Air) | reach-in refrigerator, back bar cooler, bottle cooler, undercounter refrigerator | 2005-2014 | `^(?P<y>[0-9])(?P<mm>0[1-9]\|1[0-2])[A-Z]{4}[0-9]{5}$` | y | mm | 803KAKN00192 = March 2008 | L |
| Beverage-Air (Bev Air, Beverage Air) | reach-in refrigerator, back bar cooler, bottle cooler, undercounter refrigerator | 2015-present | `^(?P<y>[0-9])(?P<mm>0[1-9]\|1[0-2])[A-Z0-9]{9}$` | y | mm | 507KCDG0M514 = July 2015 or July 2025 | L |
| Blodgett | convection oven, deck oven, combi oven | ?-present | `^(?P<mm>0[1-9]\|1[0-2])(?P<dd>[0-3][0-9])(?P<yy>[0-9]{2})[0-9A-Z]*$` | yy | mm | 010816123 = January 8, 2016 | L |
| Bosch (Bosch Aquastar, Bosch Therm) | tankless water heater, electric water heater | 1998-1999 | `^(?:[A-Z]{2})?(?P<y>[89])6(?P<mm>[1-9])\d{6}$` | y | mm | 861123456 = Jan 1998 | M |
| Bosch (Bosch Aquastar, Bosch Therm) | tankless water heater, electric water heater | 1998-1999 | `^(?:[A-Z]{2})?(?P<y>[89])7(?P<ml>[0-2])\d{6}$` | y | letters:ABCDEFGHJ012 | 870123456 = Oct 1998 | M |
| Bosch (Bosch Aquastar, Bosch Therm) | tankless water heater, electric water heater | 2000-2009 | `^(?:[A-Z]{2})?(?P<y>\d)8(?P<mm>[1-9])\d{6}$` | y | mm | FD687400341 = Jul 2006 | M |
| Bosch (Bosch Aquastar, Bosch Therm) | tankless water heater, electric water heater | 2000-2009 | `^(?:[A-Z]{2})?(?P<y>\d)9(?P<ml>[0-2])\d{6}$` | y | letters:ABCDEFGHJ012 | 390123456 = Oct 2003 | M |
| Bosch | heat pump, air conditioner, ductless mini-split | 2010-present | `^[0-9A-Z]{4}-?(?P<y>\d)\d{2}-?[0-9A-Z-]{8,20}$` | y | none | 3540-112-000001-T111M01973 = 2011 or 2021 | M |
| Bradford White (Jetglas, Energy Saver, Golden Knight) | tank water heater | 1964-1983 | `^(?P<yl>[A-HJ-NPSTW-Z])(?P<ml>[A-HJ-M])\d{7}$` | letter:A=1964,B=1965,C=1966,D=1967,E=1968,F=1969,G=1970,H=1971,J=1972,K=1973,L=1974,M=1975,N=1976,P=1977,S=1978,T=1979,W=1980,X=1981,Y=1982,Z=1983;cycle=20 | letters:ABCDEFGHJKLM | TK1234567 = Oct 1979 | M |
| Bradford White (Jetglas) | tank water heater | 1967-1983 | `^(?P<yl>[A-HJ-NPSTW-Z])\d{7}(?P<ml>[A-HJ-M])$` | letter:A=1964,B=1965,C=1966,D=1967,E=1968,F=1969,G=1970,H=1971,J=1972,K=1973,L=1974,M=1975,N=1976,P=1977,S=1978,T=1979,W=1980,X=1981,Y=1982,Z=1983;cycle=20 | letters:ABCDEFGHJKLM | D1234567F = Jun 1967 | L |
| Bradford White | water_heater | 1984-now | `^(?P<yl>[A-HJ-NPSTW-Z])(?P<ml>[A-HJ-M])\d{6}\d?$` | letter:A=1984,B=1985,C=1986,D=1987,E=1988,F=1989,G=1990,H=1991,J=1992,K=1993,L=1994,M=1995,N=1996,P=1997,S=1998,T=1999,W=2000,X=2001,Y=2002,Z=2003;cycle=20 | letters:ABCDEFGHJKLM | DG6322957 = Jul 1987 or Jul 2007 | M |
| Bristol | reciprocating compressor | ?-2018 | `^(?P<doy>[0-3][0-9]{2})(?P<yy>[0-9]{2})[0-9][0-9]{5}(-[A-Z])?$` | yy | doy | 19597011199-S = Day 195 of 1997 (July 14 1997) | L |
| Brute (Brute II, Magnatherm) | boiler, water heater | 1984-2007 | `^(?P<yl>[A-HJ-NPSTW-Z])(?P<ml>[A-HJ-M])\d{7}$` | letter:A=1984,B=1985,C=1986,D=1987,E=1988,F=1989,G=1990,H=1991,J=1992,K=1993,L=1994,M=1995,N=1996,P=1997,S=1998,T=1999,W=2000,X=2001,Y=2002,Z=2003;cycle=20 | letters:ABCDEFGHJKLM | WC9876553 = Mar 2000 | M |
| Brute (Brute II, Magnatherm) | boiler, water heater | 2007-present | `^(?P<yl>[A-HJ-NPSTW-Z])(?P<ml>[A-HJ-M])\d{8}$` | letter:A=1984,B=1985,C=1986,D=1987,E=1988,F=1989,G=1990,H=1991,J=1992,K=1993,L=1994,M=1995,N=1996,P=1997,S=1998,T=1999,W=2000,X=2001,Y=2002,Z=2003;cycle=20 | letters:ABCDEFGHJKLM | LE12345678 = May 2014 | M |
| Bryant (Carrier) | furnace, air conditioner, heat pump | 1960-1979 | `^(?P<ww>[1-9]\|[1-4]\d\|5[0-2])(?P<yl>[A-HJ-NPR-Y])\d{5,6}$` | letter:L=1960,M=1961,N=1962,P=1963,R=1964,S=1965,T=1966,U=1967,V=1968,W=1969,X=1970,Y=1971,A=1972,B=1973,C=1974,D=1975,E=1976,F=1977,G=1978,H=1979 | ww | 46U152456 = week 46 1967 | M |
| Bryant | furnace, air conditioner, heat pump | 1980-1989 | `^(?P<yy>[89]\d)(?P<mm>0[1-9]\|1[0-2])\d{5}$` | yy | mm | 850304091 = Mar 1985 | L |
| Buderus | boiler | ?-present | `^\d{6}-(?P<yy>\d{2})(?P<doy>[0-3]\d{2})-\d{5}-\d{8,12}$` | yy | doy | 253000-08217-01241-7747019703 = 4 Aug 2008 | M |
| Buderus | boiler | ?-present | `^\d{8}-\d{2}-(?P<y>\d)(?P<doy>[0-3]\d{2})-\d{4}$` | y | doy | 63036333-00-7080-3241 = Mar 2007 or Mar 2017 | L |
| Burnham (U.S. Boiler Company, Alliance, Independence, MegaSteam, Revolution) | boiler | ?-present | `^\d{7,8}\((?P<mm>0[1-9]\|1[0-2])/(?P<yyyy>(?:19\|20)\d{2})\)$` | yyyy | mm | 64157594(10/1999) = Oct 1999 | M |
| CaptiveAire (Captive-Aire, Captive Aire) | kitchen hood, exhaust fan, make-up air | 1976-2010 | `^(?P<mm>0[1-9]\|1[0-2])/(?P<dd>\d{2})/(?P<yyyy>(?:19\|20)\d{2})$` | yyyy | mm | 08/15/2008 = Aug 2008 | L |
| Carlyle | semi-hermetic compressor | ?-present | `^(?P<ww>0[1-9]\|[1-4][0-9]\|5[0-2])(?P<yy>[0-9]{2})(?P<plant>[JUMP])[DE]?[0-9]{4,5}$` | yy | ww | 3695J00123 = week 36 1995 (Sep 1995) | H |
| Carrier (Payne) | furnace, air conditioner, heat pump | 1970-1979 | `^(?P<ml>[A-HJ-M])(?P<y>\d)\d{5}$` | y | letters:ABCDEFGHJKLM | A167890 = Jan 1971 | M |
| Carrier (Bryant, Payne) | hvac | 1980-1989 | `^(?P<yy>\d{2})(?P<mm>\d{2})[A-Z]\d{5}$` | yy | mm | 8308A12345 = Aug 1983 | M |
| Carrier (Payne, Bryant) | furnace, air conditioner, heat pump | 1980-1989 | `^(?P<ml>[MNP-TV-Z])(?P<y>\d)[A-Z0-9]\d{5}$` | y | letters:MNPQRSTVWXYZ | W4D14008 = Sep 1984 | L |
| Carrier (Payne, Bryant) | furnace, air conditioner, heat pump | 1980-1989 | `^(?P<y>\d)(?P<ml>[MNP-TV-Z])[A-Z0-9]\d{5}$` | y | letters:MNPQRSTVWXYZ | 4WD14008 = Sep 1984 | L |
| Carrier (Bryant, Payne) | hvac, coil | 1990-now | `^(?P<ww>\d{2})(?P<yy>\d{2})[A-Z]\d{5}$` | yy | ww | 1014A12345 = week 10 2014 | H |
| Century (A.O. Smith, AO Smith) | fractional motor, pool pump motor, fan motor | ?-2006 | `^[0-9](?P<ml>[A-L])(?P<yy>[0-9]{2})$` | yy | letters:ABCDEFGHIJKL | 7B99 = February 1999 | H |
| Century (A.O. Smith, AO Smith, Indiana General, Louis Allis) | fractional motor, pool pump motor, fan motor | 1992-2010 | `^(?P<yl>[BC][A-Z])(?P<mm>1[0-2]\|[1-9])$` | letter:BK=1992,BL=1993,BM=1994,BN=1995,BP=1996,BR=1997,BS=1998,BT=1999,BU=2000,BW=2001,BX=2002,BY=2003,BZ=2004,CA=2005,CB=2006,CC=2007,CD=2008,CE=2009,CF=2010 | mm | BM6 = June 1994 | H |
| Cleaver-Brooks | boiler, burner | ?-present | `^PSIDATE(?P<yyyy>(?:19\|20)\d{2})$` | yyyy | none | PSIDATE2013 = 2013 | L |
| Cleveland (Cleveland Range) | steam kettle, tilting skillet, steamer | ?-2008 | `^[A-Z]{2}-[0-9]{4,5}-(?P<yy>[0-9]{2})(?P<ml>[A-L])-[0-9]{2}$` | yy | letters:ABCDEFGHIJKL | WC-1234-95B-01 = February 1995 | L |
| Cleveland (Cleveland Range) | steam kettle, tilting skillet, steamer | 2008-present | `^(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])-?[0-9]{4}-?[0-9]{5}$` | yy | mm | 1109-1234-12345 = September 2011 | L |
| ClimateMaster (ClimaCool) | water source heat pump, geothermal heat pump | 1972-1998 | `^(?P<yy>\d{2})(?P<ml>[A-HJ-M])\d{6}$` | yy | letters:ABCDEFGHJKLM | 92J010915 = Sep 1992 | M |
| ClimateMaster (ClimaCool) | water source heat pump, geothermal heat pump | 1998-2021 | `^(?P<yl>[A-HJ-NP-Z])\d(?P<ww>\d{2})\d{6}$` | letter:H=1998,A=1999,B=2000,C=2001,D=2002,E=2003,F=2004,G=2005,J=2006,K=2007,L=2008,M=2009,N=2010,P=2011,Q=2012,R=2013,S=2014,T=2015,U=2016,V=2017,W=2018,X=2019,Y=2020,Z=2021 | ww | K111300076 = week 11 2007 | M |
| Coleman (Evcon, Luxaire) | furnace, air conditioner, heat pump | ?-1992 | `^(?P<mm>0[1-9]\|1[0-2])(?P<yy>[6-9]\d)\d{4,6}$` | yy | mm | 0188123456 = Jan 1988 | M |
| Coleman (Evcon, Luxaire) | furnace, air conditioner, heat pump | 1992-2004 | `^(?P<yy>9[2-9]\|0[0-4])(?P<mm>0[1-9]\|1[0-2])\d{4,6}$` | yy | mm | 97104119 = Oct 1997 | M |
| Coleman (Evcon, Luxaire, Guardian, Fraser-Johnston, York) | furnace, air conditioner, heat pump | 2004-present | `^[A-Z](?P<y1>\d)(?P<ml>[A-HJ-N])(?P<y2>\d)\d{6}$` | concat:y1,y2 | letters:ABCDEFGHKLMN | W0K5896070 = Sep 2005 | M |
| Copeland (Emerson Copeland) | scroll compressor, semi-hermetic compressor, hermetic compressor, condensing unit | ?-present | `^(?P<yy>[0-9]{2})(?P<ml>[A-L])[0-9A-Z]{5,6}$` | yy | letters:ABCDEFGHIJKL | 01D1020HL = April 2001 | H |
| Crown | indirect water heater | ?-present | `^(?P<yy>\d{2})\d{6,7}[A-Z]?$` | yy | none | 98023429 = 1998 | M |
| Crown | boiler | 2004-2018 | `^(?P<yl>[A-O])(?P<ml>[A-L])$` | letter:A=2004,B=2005,C=2006,D=2007,E=2008,F=2009,G=2010,H=2011,I=2012,J=2013,K=2014,L=2015,M=2016,N=2017,O=2018 | letters:ABCDEFGHIJKL | AC = Mar 2004 | L |
| Cutler-Hammer (Eaton, Westinghouse) | load center, circuit breaker | 1980-1989 | `^[A-Z0-9](?P<y>[0-9])(?P<ww>[0-5][0-9])\+$` | y | ww | A507+ = week 7 1985 (Feb 1985) | M |
| Cutler-Hammer (Eaton, Westinghouse) | load center, circuit breaker | 1990-1999 | `^[A-Z0-9](?P<y>[0-9])(?P<ww>[0-5][0-9])=$` | y | ww | B312= = week 12 1993 (Mar 1993) | M |
| Cutler-Hammer (Eaton, Westinghouse) | load center, circuit breaker | 2000-2009 | `^[A-Z0-9](?P<y>[0-9])(?P<ww>[0-5][0-9])\&$` | y | ww | F251& = week 51 2002 (Dec 2002) | M |
| Cutler-Hammer (Eaton, Westinghouse) | load center, circuit breaker | 2010-2019 | `^[A-Z0-9](?P<y>[0-9])(?P<ww>[0-5][0-9])!$` | y | ww | C614! = week 14 2016 (Apr 2016) | M |
| Cutler-Hammer (Eaton, Westinghouse) | load center, circuit breaker | 2020-2029 | `^[A-Z0-9](?P<y>[0-9])(?P<ww>[0-5][0-9])@$` | y | ww | D105@ = week 5 2021 (Feb 2021) | M |
| Daikin (Daikin Applied, McQuay) | hvac | 2000-now | `^[A-Z]{4}(?P<yy>\d{2})(?P<mm>\d{2})\d+$` | yy | mm | FBOU0905048200 = May 2009 | M |
| Daikin | hvac | 2000-now | `^(?P<yy>\d{2})(?P<mm>\d{2})\d{6}$` | yy | mm | 1602393269 = Feb 2016 | M |
| Danfoss Maneurop (Maneurop, Danfoss) | reciprocating compressor | 1990-present | `^(?P<yl>[A-HJ-NP-V])(?P<ml>[A-HJ-M])[0-9]{2}[0-9]{8}$` | letter:A=1990,B=1991,C=1992,D=1993,E=1994,F=1995,G=1996,H=1997,J=1998,K=1999,L=2000,M=2001,N=2002,P=2003,Q=2004,R=2005,S=2006,T=2007,U=2008,V=2009;cycle=20 | letters:ABCDEFGHJKLM | AA1006235612 = January 1990 or January 2010 | H |
| Danfoss VLT (VLT) | variable frequency drive | ?-present | `^[0-9]{4}[0-9A-Z]{2}[0-9A-Z](?P<ww>0[1-9]\|[1-4][0-9]\|5[0-3])(?P<y>[0-9])$` | y | ww | 123411G380 = week 38 2020 (Sep 2020) | L |
| Data Aire (Data-Aire, DataAire) | CRAC, computer room air conditioner | ?-1999 | `^(?P<yy>\d{2})-\d{4}-[A-Z]$` | yy | none | 98-3140-A = 1998 | L |
| Data Aire (Data-Aire, DataAire) | CRAC, computer room air conditioner | 2000-present | `^(?P<yyyy>20\d{2})-\d{4}-[A-Z]$` | yyyy | none | 2000-3737-B = 2000 | L |
| Day & Night | furnace, air conditioner, heat pump | 1970-1979 | `^(?P<ml>[A-HJ-M])(?P<yl>[A-J])\d{5,7}$` | letter:A=1970,B=1971,C=1972,D=1973,E=1974,F=1975,G=1976,H=1977,I=1978,J=1979 | letters:ABCDEFGHJKLM | AA123456 = Jan 1970 | M |
| Desert Aire (Desert-Aire) | dehumidifier, pool dehumidifier | ?-present | `^(?P<ww>\d{2})(?P<yy>\d{2})[A-Z]\d{4}$` | yy | ww | 4099D9330 = week 40 1999 | L |
| Ducane (Concord, Magic-Pak, AirEase) | furnace, air conditioner, heat pump | ?-now | `^\d{6}(?P<yy>\d{2})(?P<ww>0[1-9]\|[1-4]\d\|5[0-3])$` | yy | ww | 0183290431 = week 31 2004 | M |
| Dunham-Bush (Dunham Bush) | chiller, fan coil, air handler, condensing unit | ?-present | `^\d{5}-\d{2}(?P<ml>[A-HJ-M])(?P<yy>\d{2})[A-Z]$` | yy | letters:ABCDEFGHJKLM | 50347-01A85F = Jan 1985 | L |
| Dunkirk | boiler | ?-present | `^(?P<ww>0[1-9]\|[1-4]\d\|5[0-3])(?P<yy>\d{2})\d{5}$` | yy | ww | 500100433 = week 50 2001 | M |
| Duo-Therm | RV furnace, RV air conditioner | 1961-1985 | `^[A-Z](?P<yy>\d{2})\d{5}$` | yy | none | A7500525 = 1975 | L |
| Eccotemp | tankless water heater | ?-present | `^(?:ECC)?(?P<yy>\d{2})(?P<mm>1[0-2]\|[1-9])\d{4,6}$` | yy | mm | ECC20290387 = Feb 2020 | L |
| Energy Kinetics | boiler | ?-present | `^\d(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{4}$` | yy | mm | 299078847 = Jul 1999 | L |
| Energy Kinetics | boiler | ?-present | `^F\d(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{6}$` | yy | mm | F10608063248 = Aug 2006 | L |
| Evapco (Evapcold) | cooling tower, evaporative condenser, closed circuit cooler | ?-present | `^(?P<yy>\d{2})-\d{6}$` | yy | none | 10-399266 = 2010 | L |
| Fedders (Emerson Quiet Kool, Quiet Kool, Airwell, Airwell-Fedders) | room air conditioner, PTAC, air conditioner | ?-now | `^(?P<yy>\d{2})(?P<ml>[A-L])-?\d{5}$` | yy | letters:ABCDEFGHIJKL | 02J-60002 = Oct 2002 | L |
| Fedders (Emerson Quiet Kool, Quiet Kool, Airwell, Airwell-Fedders) | room air conditioner, air conditioner | ?-now | `^[A-Z]{2}(?P<ww>\d{2})(?P<yy>\d{2})\d{5}[A-Z]$` | yy | ww | EW020144126H = week 02 2001 | L |
| Fedders (Emerson Quiet Kool, Quiet Kool, Airwell, Airwell-Fedders) | air conditioner, heat pump | 1966-1977 | `^[A-Z](?P<yl>[A-HJ-M])\d{4,6}$` | letter:A=1966,B=1967,C=1968,D=1969,E=1970,F=1971,G=1972,H=1973,J=1974,K=1975,L=1976,M=1977 | none | AH11877 = 1973 | L |
| Fedders (Emerson Quiet Kool, Quiet Kool, Airwell, Airwell-Fedders) | room air conditioner, PTAC, air conditioner | 2006-2014 | `^(?P<ml>[A-L])(?P<yl>[R-Z])[0-9A-Z]{6,10}$` | letter:R=2006,S=2007,T=2008,U=2009,V=2010,W=2011,X=2012,Y=2013,Z=2014 | letters:ABCDEFGHIJKL | AS298488006X = Jan 2007 | L |
| FHP (Florida Heat Pump) | water source heat pump, geothermal heat pump | 1975-2016 | `^(?P<yl>[A-HJ-NPR-Z])(?P<ml>[A-HJ-M])\d{6}[A-Z]$` | letter:A=1971,B=1972,C=1973,D=1974,E=1975,F=1976,G=1977,H=1978,J=1979,K=1980,L=1981,M=1982,N=1983,P=1984,R=1985,S=1986,T=1987,U=1988,V=1989,W=1990,X=1991,Y=1992,Z=1993;cycle=23 | letters:ABCDEFGHJKLM | EG013220D = Jul 1975 or Jul 1998 | L |
| First Co (First Company, FirstCo) | fan coil, air handler, water source heat pump, PTAC | 1975-present | `^(?P<yl>[A-HJ-NPR-Z])(?P<mm>0[1-9]\|1[0-2])[A-Z]\d{6}$` | letter:A=1971,B=1972,C=1973,D=1974,E=1975,F=1976,G=1977,H=1978,J=1979,K=1980,L=1981,M=1982,N=1983,P=1984,R=1985,S=1986,T=1987,U=1988,V=1989,W=1990,X=1991,Y=1992,Z=1993;cycle=23 | mm | S05A881350 = May 1986 or May 2009 | L |
| First Co (First Company, FirstCo) | fan coil, air handler, water source heat pump, PTAC | 1975-present | `^(?P<yl>[A-HJ-NPR-Z])(?P<mm>0[1-9]\|1[0-2])[A-Z]{2}\d{12}$` | letter:A=1971,B=1972,C=1973,D=1974,E=1975,F=1976,G=1977,H=1978,J=1979,K=1980,L=1981,M=1982,N=1983,P=1984,R=1985,S=1986,T=1987,U=1988,V=1989,W=1990,X=1991,Y=1992,Z=1993;cycle=23 | mm | F05FC032358927092 = May 1999 or May 2022 | L |
| First Co (First Company, FirstCo) | fan coil, air handler, water source heat pump, PTAC | 2000-present | `^(?P<yy>\d{2})\d{2}-\d{4}$` | yy | none | 2408-1663 = 2024 | L |
| Friedrich | room air conditioner, heat pump, air conditioner | ?-1999 | `^(?P<yy>\d{2})(?P<ml>[A-M])\d{6}$` | yy | letters:ABCDEFGHJKLM | 92J010915 = Sep 1992 | M |
| Friedrich (Kuhl, WallMaster) | room air conditioner, PTAC, vertical packaged unit | 1990-1999 | `^(?P<yl>J[A-HJK])(?P<ml>[A-HJ-M])[A-Z]\d{5}$` | letter:JK=1990,JA=1991,JB=1992,JC=1993,JD=1994,JE=1995,JF=1996,JG=1997,JH=1998,JJ=1999 | letters:ABCDEFGHJKLM | JGFP01234 = Jun 1997 | H |
| Friedrich (Kuhl, WallMaster, Uni-Fit, Zoneaire) | room air conditioner, PTAC, vertical packaged unit, ductless mini-split | 2000-2017 | `^(?P<yl>[LA][A-HJK])(?P<ml>[A-HJ-M])[A-Z]\d{5}$` | letter:LK=2000,LA=2001,LB=2002,LC=2003,LD=2004,LE=2005,LF=2006,LG=2007,LH=2008,LJ=2009,AK=2010,AA=2011,AB=2012,AC=2013,AD=2014,AE=2015,AF=2016,AG=2017,AH=2018,AJ=2019 | letters:ABCDEFGHJKLM | AKDZ03116 = Apr 2010 | H |
| Friedrich (Kuhl, WallMaster, Uni-Fit, Zoneaire) | room air conditioner, PTAC, vertical packaged unit, ductless mini-split | 2017-present | `^(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])[A-Z]\d{5}$` | yy | mm | 1801M01258 = Jan 2018 | H |
| Frigidaire (Electrolux, Gibson, Kelvinator, White-Westinghouse, Tappan, Philco) | room air conditioner, dehumidifier | 1986-present | `^[A-Z]{2}(?P<y>\d)(?P<ww>\d{2})\d{5}$` | y | ww | KG44312523 = week 43 2014 (or 2004, 1994) | M |
| Frymaster | fryer | ?-present | `^(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])[0-9A-Z]{4,12}$` | yy | mm | 2510ABC123 = October 2025 | H |
| Garland (US Range) | range, oven, broiler, griddle | ?-2006 | `^[0-9]{5}[A-Z][0-9]{3}(?P<mlet>[A-Z])(?P<yy>[0-9]{2})$` | yy | none | 45729A001D95 = 1995 | H |
| Garland (US Range) | range, oven, broiler, griddle | ?-2006 | `^(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])[A-Z]{2}[0-9]{3}R?$` | yy | mm | 9904RG002R = April 1999 | H |
| Garland (US Range) | range, oven, broiler, griddle | 2007-present | `^(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])[0-9]{4,9}$` | yy | mm | 0703123456 = March 2007 | L |
| GE (General Electric) | tank water heater | ?-2011 | `^(?:GE[A-Z]{0,2}\|RN)?(?P<mm>0[1-9]\|1[0-2])(?P<yy>\d{2})[A-Z]?\d{5,7}$` | yy | mm | GENG0601D13586 = Jun 2001 | M |
| GE (Hotpoint, RCA) | room air conditioner, dehumidifier | 1975-present | `^(?P<ml>[ADFGHLMRSTVZ])(?P<yl>[ADFGHLMRSTVZ])[0-9A-Z]{6,10}$` | letter:V=1975,Z=1976,A=1977,D=1978,F=1979,G=1980,H=1981,L=1982,M=1983,R=1984,S=1985,T=1986;cycle=12 | letters:ADFGHLMRSTVZ | AS123456S = Jan 1985 or Jan 1997 or Jan 2009 or Jan 2021 | H |
| GE (load centers) (General Electric) | load center, panelboard | 1976-present | `^(?P<m1>[A-Z])(?P<yl>[ADFGHLMRSTVZ])[0-9]{6}$` | letter:Z=1976,A=1977,D=1978,F=1979,G=1980,H=1981,L=1982,M=1983,R=1984,S=1985,T=1986,V=1987;cycle=12 | none | MR123456 = 1984, 1996, 2008 or 2020 | L |
| GE GeoSpring (GeoSpring) | heat pump water heater | 2009-2017 | `^(?P<ml>[ADFGHLMRSTVZ])(?P<yl>[ADFGHLMRSTVZ])[0-9A-Z]{6,10}$` | letter:V=1975,Z=1976,A=1977,D=1978,F=1979,G=1980,H=1981,L=1982,M=1983,R=1984,S=1985,T=1986;cycle=12 | letters:ADFGHLMRSTVZ | AZ123456S = Jan 2012 | H |
| GE Zoneline (Zoneline) | PTAC, vertical terminal air conditioner, heat pump | 1975-present | `^(?P<ml>[ADFGHLMRSTVZ])(?P<yl>[ADFGHLMRSTVZ])[0-9A-Z]{6,10}$` | letter:V=1975,Z=1976,A=1977,D=1978,F=1979,G=1980,H=1981,L=1982,M=1983,R=1984,S=1985,T=1986;cycle=12 | letters:ADFGHLMRSTVZ | LA123456S = Jun 2013 (or Jun 2001, Jun 2025) | H |
| Goodman | packaged terminal air conditioner | 1990-2013 | `^[0-9A-Z](?P<ml>[A-HJ-M])(?P<yl>[A-HJ-NP-Z])\d{7}[PD]$` | letter:A=1990,B=1991,C=1992,D=1993,E=1994,F=1995,G=1996,H=1997,J=1998,K=1999,L=2000,M=2001,N=2002,P=2003,Q=2004,R=2005,S=2006,T=2007,U=2008,V=2009,W=2010,X=2011,Y=2012,Z=2013 | letters:ABCDEFGHJKLM | 5FU5472618P = Jun 2008 | L |
| Goodman (Amana) | hvac, coil | 2000-now | `^(?P<yy>\d{2})(?P<mm>\d{2})\d{6}$` | yy | mm | 2108317723 = Aug 2021 | H |
| Gree | ductless mini-split, heat pump, room air conditioner, PTAC | ?-present | `^(?P<ww>\d{2})(?P<yy>\d{2})[A-Z][0-9A-Z]{4,10}$` | yy | ww | 0625GS12345 = week 06 2025 | M |
| Greenheck | fan, exhaust fan, energy recovery ventilator, make-up air, damper | 1985-2005 | `^(?P<yy>\d{2})(?P<ml>[A-L])\d{5}$` | yy | letters:ABCDEFGHIJKL | 98C12345 = Mar 1998 | H |
| Greenheck | fan, exhaust fan, energy recovery ventilator, make-up air, damper | 2005-present | `^\d{8}(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])$` | yy | mm | 103443330610 = Oct 2006 | H |
| Grundfos | circulator, centrifugal pump, CR pump, lift station | ?-present | `^(?P<pc>[A-Z][0-9])?(?P<yy>[0-9]{2})(?P<ww>0[1-9]\|[1-4][0-9]\|5[0-3])$` | yy | ww | P10320 = week 20 2003 (May 2003) | H |
| H.B. Smith | boiler | ?-present | `^[A-Z](?P<yy>\d{2})-\d{3,5}[A-Z]?$` | yy | none | J80-2747 = 1980 | M |
| H.B. Smith | boiler | ?-present | `^[A-Z0-9]{2}(?P<yyyy>(?:19\|20)\d{2})-\d{4}$` | yyyy | none | AB1998-1234 = 1998 | L |
| H.B. Smith | boiler | ?-present | `^(?P<mm>0[1-9]\|1[0-2])(?P<yy>\d{2})\d{5}$` | yy | mm | 059989310 = May 1999 | L |
| Haier | room air conditioner, ductless mini-split | ?-now | `^[A-Z](?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])[A-Z0-9]{5,6}$` | yy | mm | C1208A320E = Aug 2012 | L |
| Haier | room air conditioner | ?-now | `^(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{4}$` | yy | mm | 07021234 = Feb 2007 | L |
| Haier | room air conditioner, ductless mini-split, PTAC | 2000-2022 | `^(?P<ml>[A-L])(?P<yl>[A-NPR-WYZ])\d{6}[A-Z0-9]?$` | letter:A=2000,B=2001,C=2002,D=2003,E=2004,F=2005,G=2006,H=2007,I=2008,J=2009,K=2010,L=2011,M=2012,N=2013,P=2014,R=2015,S=2016,T=2017,U=2018,V=2019,W=2020,Y=2021,Z=2022 | letters:ABCDEFGHIJKL | AM001358B = Jan 2012 | L |
| Haier | room air conditioner, ductless mini-split | 2010-2024 | `^[A-Z0-9]{13}(?P<yl>[0-9A-E])(?P<ml>[1-9ABC])[A-Z0-9]{3,5}$` | letter:0=2010,1=2011,2=2012,3=2013,4=2014,5=2015,6=2016,7=2017,8=2018,9=2019,A=2020,B=2021,C=2022,D=2023,E=2024 | letters:123456789ABC | AA5YW0E0200NK74W0009 = Apr 2017 | L |
| Heatcraft (Bohn, Larkin, Climate Control, Chandler, InterLink) | condensing unit, unit cooler, evaporator | ?-present | `^[A-Z](?P<yy>[0-9]{2})(?P<ml>[A-M])[0-9]{5}$` | yy | letters:ABCDEFGHIJKL | T16H14196 = August 2016 | H |
| Heil-Quaker (Heil) | furnace, air conditioner, heat pump | 1962-1979 | `^(?P<y>\d)\d{5}$` | y | none | 297448 = 1972 (or 1962) | L |
| Heil-Quaker (Heil) | furnace, air conditioner, heat pump | 1980-1989 | `^H(?P<y>\d)(?P<ww>0[1-9]\|[1-4]\d\|5[0-3])\d{5}$` | y | ww | H55116328 = week 51 1985 | M |
| Heil-Quaker (Heil, Arcoaire, KeepRite, Tempstar, Comfortmaker, Airquest) | furnace, air conditioner, heat pump | 1988-present | `^[A-Z](?P<yy>\d{2})(?P<ww>0[1-9]\|[1-4]\d\|5[0-3])\d{5}$` | yy | ww | L943321238 = week 33 1994 | M |
| Honeywell (gas valves) (Honeywell, Resideo) | gas valve, gas control | ?-present | `^(?P<yy>[0-9]{2})(?P<ww>0[1-9]\|[1-4][0-9]\|5[0-3])$` | yy | ww | 9437 = week 37 1994 (Sep 1994) | L |
| Hoshizaki | ice_machine, refrigeration | 2010-now | `^(?P<yl>[A-HJ-NP-V])\d{5}(?P<ml>[A-L])$` | letter:A=2011,B=2012,C=2013,D=2014,E=2015,F=2016,G=2017,H=2018,J=2019,K=2020,L=2021,M=2022,N=2023,P=2024,Q=2025,R=2026,S=2027,T=2028,U=2029,V=2030 | letters:ABCDEFGHIJKL | C20103B = Feb 2013 | L |
| Hotpoint | tank water heater | ?-2001 | `^(?:HP[A-Z]{0,2}\|R)?(?P<mm>0[1-9]\|1[0-2])(?P<yy>\d{2})[A-Z]\d{5}$` | yy | mm | 0301A03043 = Mar 2001 | M |
| HTP | water_heater, boiler | 2011-2022 | `^(?P<mm>\d{2})(?P<dd>\d{2})(?P<yy>\d{2})[A-Z]\d{6}$` | yy | mm | 112116E205445 = 21 Nov 2016 | M |
| HTP | water_heater, boiler | 2011-2022 | `^\d{2}(?P<mm>\d{2})(?P<dd>\d{2})(?P<yy>\d{2})\d{8}$` | yy | mm | 2103302238194208 = 30 Mar 2022 | M |
| HTP | water_heater, boiler | 2021-now | `^[0-9A-Z]{9}(?P<yy>\d{2})(?P<doy>\d{3})\d{7}$` | yy | doy | 3253087U4221610000082 = day 161 of 2022 (10 Jun 2022) | M |
| HTPG (Russell) (Russell, Witt, ColdZone, Kramer, HTPG) | unit cooler, condensing unit, evaporator, walk-in refrigeration system | 2008-present | `^(?P<fac>[EW])(?P<yy>[0-9]{2})(?P<ml>[A-HJ-M])([0-9]{8}[0-9]{3}\|[0-9]{6}[0-9]{2})[0-9]{3}$` | yy | letters:ABCDEFGHJKLM | E13C00123456001001 = March 2013 | H |
| Hussmann | display case, refrigerated merchandiser, walk-in cooler | ?-present | `^104(?P<mm>0[1-9]\|1[0-2])(?P<dd>[0-3][0-9])(?P<yyyy>(19\|20)[0-9]{2})[0-9]{5}$` | yyyy | mm | 1040315201212345 = March 15 2012 (ship date) | L |
| Hussmann | display case, refrigerated merchandiser | ?-present | `^103(?P<mm>0[1-9]\|1[0-2])(?P<dd>[0-3][0-9])(?P<yyyy>(19\|20)[0-9]{2})[0-9]{5}$` | yyyy | mm | 1031102201812345 = November 2 2018 (ship date) | L |
| I-T-E (ITE, ITE Gould, Gould) | load center, panelboard | ?-1990 | `^(?P<ml>[A-HJ-M])(?P<dd>[0-3][0-9])(?P<yy>[0-9]{2})$` | yy | letters:ABCDEFGHJKLM | B2685 = February 26 1985 | L |
| Ice-O-Matic (IceOMatic) | ice machine, ice dispenser | 1990-1999 | `^(?P<ml>[MNPQRSTUVWYZ])(?P<y>[0-9])[0-9A-Z]{2}-?[0-9A-Z]{5}-?[A-Z]$` | y | letters:MNPQRSTUVWYZ | M7XX-XXXXX-Z = January 1997 | H |
| Ice-O-Matic (IceOMatic) | ice machine, ice dispenser | 2000-2004 | `^(?P<ml>[A-L])(?P<y>[0-4])[0-9A-Z]{2}-?[0-9A-Z]{5}-?[A-Z]$` | y | letters:ABCDEFGHIJKL | A1XX-XXXXX-Z = January 2001 | H |
| Ice-O-Matic (IceOMatic) | ice machine, ice dispenser | 2004-present | `^(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])1280[0-9]{6}$` | yy | mm | 04071280010077 = July 2004 | H |
| ICP (Heil, Tempstar, Comfortmaker, Day & Night, Arcoaire, KeepRite, Airquest, ACiQ, International Comfort Products) | hvac | 1990-now | `^[A-Z](?P<yy>\d{2})(?P<ww>\d{2})\d{5}$` | yy | ww | G051650885 = week 16 2005 | H |
| Janitrol | furnace, air conditioner, heat pump | 1959-1985 | `^\d{2}(?P<yy>\d{2})[A-Z]\d{4}$` | yy | none | 0759F5616 = 1959 | L |
| Janitrol (Goodman) | furnace, air conditioner, heat pump | 1985-present | `^(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{6}$` | yy | mm | 9704011000 = Apr 1997 | M |
| John Wood (GSW, Moffat, Superflue, Medal) | tank water heater | 1975-1986 | `^\d{6}-?(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])$` | yy | mm | 137945-7503 = Mar 1975 | L |
| John Wood (GSW, Moffat, Superflue, Medal) | tank water heater | 1987-2007 | `^[A-Z]?(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])-?\d{6}$` | yy | mm | U0106413635 = Jun 2001 | H |
| John Wood (GSW, Moffat) | tank water heater | 2008-present | `^[A-Z]?(?P<yy>\d{2})(?P<ww>\d{2})[A-Z]?\d{6,7}$` | yy | ww | U0928413635 = week 28 2009 (Jul 2009) | H |
| KeepRite (Tempstar) | furnace, air conditioner, heat pump | ?-now | `^(?P<yy>\d{2})(?P<ww>0[1-9]\|[1-4]\d\|5[0-3])[A-Z]\d{5}$` | yy | ww | 9414B39332 = week 14 1994 | L |
| KeepRite (Tempstar) | furnace, air conditioner, heat pump | 1970-1994 | `^(?:[A-Z]\d?)?(?P<yl>[A-HJ-Z])\d{4,7}$` | letter:S=1970,T=1971,U=1972,V=1973,W=1974,X=1975,Y=1976,Z=1977,A=1978,B=1979,C=1980,D=1981,E=1982,F=1983,G=1984,H=1985,J=1986,K=1987,L=1988,M=1989,N=1990,O=1991,P=1992,Q=1993,R=1994 | none | Z3Z12345 = 1977 | M |
| KeepRite (Tempstar) | furnace, air conditioner, heat pump | 1980-1993 | `^(?P<y>\d)(?P<ww>0[1-9]\|[1-4]\d\|5[0-3])\d{5,6}$` | y | ww | 30512345 = week 05 1983 or 1993 | M |
| Kenmore (Sears) | room air conditioner | 1986-present | `^[A-Z]{2}(?P<y>\d)(?P<ww>\d{2})\d{5}$` | y | ww | WA54012345 = week 40 2015 (or 2005, 1995) | L |
| Kenmore (Sears) | room air conditioner | 1990-2009 | `^[A-Z]{1,2}(?P<yl>[A-HJ-MPR-UWXY])(?P<ww>\d{2})\d{5,6}$` | letter:X=1990,A=1991,B=1992,C=1993,D=1994,E=1995,F=1996,G=1997,H=1998,J=1999,K=2000,L=2001,M=2002,P=2003,R=2004,S=2005,T=2006,U=2007,W=2008,Y=2009 | ww | MB1402320 = week 14 1992 | L |
| Laars (Teledyne Laars, Mascot, Mighty Therm, Mini-Therm) | boiler, water heater | ?-present | `^(?P<ml>[A-HJ-M])(?P<yy>\d{2})[A-Z]?\d{5,6}$` | yy | letters:ABCDEFGHJKLM | C00B01803 = Mar 2000 | M |
| Lennox (Lennox Industries) | hvac, coil | 1973-now | `^\d{2}(?P<yy>\d{2})(?P<ml>[A-HJ-M])\d+$` | yy | letters:ABCDEFGHJKLM | 5899L17212 = Nov 1999 | H |
| LG (Goldstar) | ductless mini-split, VRF, room air conditioner, heat pump | ?-present | `^(?P<y>\d)(?P<mm>0[1-9]\|1[0-2])[A-Z0-9]{9}$` | y | mm | 407HAVN79423 = Jul 2014 or Jul 2024 | M |
| Liebert (Vertiv) | CRAC, computer room air conditioner, condenser, drycooler | ?-present | `^(?P<yy>\d{2})(?P<ww>\d{2})[A-Z]\d{5,6}$` | yy | ww | 0107C44893 = week 7 2001 | L |
| Liebert (Vertiv) | CRAC, computer room air conditioner, condenser, drycooler | ?-present | `^(?P<ml>[A-HJ-M])-(?:19\|20)?(?P<yy>\d{2})$` | yy | letters:ABCDEFGHJKLM | J-97 = Sep 1997 | L |
| Lochinvar (Knight, Copper-Fin) | boiler, water heater | 1965-1997 | `^(?P<ml>[A-HJ-M])-?(?P<yy>\d{2})-?\d{3,6}[A-Z]?$` | yy | letters:ABCDEFGHJKLM | J93-1030F = Sep 1993 | L |
| Lochinvar | commercial water heater, boiler | 1965-present | `^(?P<ml>[A-HJ-M])-?(?P<yy>\d{2})(?:-?\d{3,6}[A-Z]?\|[A-Z]\d{8})$` | yy | letters:ABCDEFGHJKLM | J-930001 = Sep 1993 | L |
| Lochinvar (Knight) | boiler, water heater | 1978-present | `^(?P<ml>[A-HJ-M])(?P<yy>\d{2})[A-Z]\d{8}$` | yy | letters:ABCDEFGHJKLM | A07H00123456 = Jan 2007 | L |
| Lochinvar | electric booster water heater | 1978-2010 | `^\d{6}(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])$` | yy | mm | 1234569708 = Aug 1997 | L |
| Lochinvar (Knight, Crest, Copper-Fin, Armor) | boiler, water heater | 1979-2011 | `^(?P<yl>[A-HJ-NPSTW-Z])(?P<ml>[A-HJ-M])-?\d{5,8}$` | letter:T=1979,W=1980,X=1981,Y=1982,Z=1983,A=1984,B=1985,C=1986,D=1987,E=1988,F=1989,G=1990,H=1991,J=1992,K=1993,L=1994,M=1995,N=1996,P=1997,S=1998;cycle=20 | letters:ABCDEFGHJKLM | KJ-1000130 = Sep 1993 | M |
| Lochinvar (Knight) | boiler, water heater | 1984-present | `^(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{4}$` | yy | mm | 85041234 = Apr 1985 | L |
| Lochinvar (Knight, Armor) | commercial water heater, boiler | 1984-2011 | `^(?P<yl>[A-HJ-NPSTW-Z])(?P<ml>[A-HJ-M])-?\d{5,7}$` | letter:A=1984,B=1985,C=1986,D=1987,E=1988,F=1989,G=1990,H=1991,J=1992,K=1993,L=1994,M=1995,N=1996,P=1997,S=1998,T=1999,W=2000,X=2001,Y=2002,Z=2003;cycle=20 | letters:ABCDEFGHJKLM | KJ-1000130 = Sep 1993 | L |
| Lochinvar (Knight, Crest, Copper-Fin, Armor) | boiler, water heater | 2011-present | `^(?P<yy>[1-3]\d)(?P<ww>0[1-9]\|[1-4]\d\|5[0-3])[A-Z]\d{6}$` | yy | ww | 1142N012345 = week 42 2011 | M |
| Lochinvar (Knight, Armor) | commercial water heater, boiler | 2011-present | `^(?P<yy>\d{2})(?P<ww>\d{2})[A-Z]\d{6}$` | yy | ww | 1142N012345 = week 42 2011 (Oct 2011) | L |
| Luxaire (Fraser-Johnston, York) | furnace, air conditioner, heat pump | 1971-2004 | `^(?P<ml>[A-HJ-N])(?P<yl>[A-HJ-NPR-TV-Y])\d{6}$` | letter:A=1971,B=1972,C=1973,D=1974,E=1975,F=1976,G=1977,H=1978,J=1979,K=1980,L=1981,M=1982,N=1983,P=1984,R=1985,S=1986,T=1987,V=1988,W=1989,X=1990,Y=1991;cycle=21 | letters:ABCDEFGHKLMN | HM409295 = Aug 1982 or Aug 2003 | M |
| MagicAire (Magic Aire, Magic-Aire) | fan coil, air handler, water source heat pump | 1970-1979 | `^(?P<yy>\d{2})-\d{4}$` | yy | none | 74-1234 = 1974 | L |
| MagicAire (Magic Aire, Magic-Aire) | fan coil, air handler, water source heat pump | 1980-1999 | `^(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])[0-9A-Z]{5}$` | yy | mm | 950630A51 = Jun 1995 | L |
| MagicAire (Magic Aire, Magic-Aire) | fan coil, air handler, water source heat pump | 1999-present | `^[A-Z](?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{5}$` | yy | mm | W070698322 = Jun 2007 | L |
| Manitowoc Ice (Manitowoc) | ice machine | ?-2006 | `^(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])[0-9]{5,6}$` | yy | mm | 050164303 = January 2005 | M |
| Manitowoc Ice (Manitowoc) | ice machine | 2006-present | `^(MF\|MFG)DT(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])$` | yy | mm | MFGDT1809 = September 2018 | M |
| Marathon | tank water heater, electric water heater | 1989-present | `^(?P<mm>0[1-9]\|1[0-2])(?P<yy>\d{2})\d{6}$` | yy | mm | 0189123456 = Jan 1989 | M |
| Marathon Electric (Marathon) | AC motor, fan motor, pump motor | 1994-2002 | `^(?P<yl>[1-9])(?P<prot>[PQSUVWXZ])?(?P<ml>[A-FHJ-N])[0-9][0-9A-Z]+$` | letter:1=1994,2=1995,3=1996,4=1997,5=1998,6=1999,7=2000,8=2001,9=2002 | letters:ABCDEFHJKLMN | 8QE48A11O787NP = May 2001 | H |
| Marathon Electric (Marathon) | AC motor, fan motor, pump motor | 2003-2024 | `^(?P<yl>[A-HJ-NPR-Z])(?P<prot>[PQSUVWXZ])?(?P<ml>[A-FHJ-N])[0-9][0-9A-Z]+$` | letter:A=2003,B=2004,C=2005,D=2006,E=2007,F=2008,H=2009,J=2010,K=2011,L=2012,M=2013,N=2014,P=2015,R=2016,S=2017,T=2018,U=2019,V=2020,W=2021,X=2022,Y=2023,Z=2024 | letters:ABCDEFHJKLMN | KC56T34F5301 = March 2011 | H |
| Marley (SPX Cooling, SPX, Marley Cooling Tower) | cooling tower | ?-present | `^\d{7,8}-[A-Z]\d-[A-Z0-9]+-(?P<yy>\d{2})$` | yy | none | 10067198-A1-NC8405BG-13 = 2013 | L |
| Master-Bilt (Masterbilt) | walk-in cooler, walk-in freezer, reach-in refrigerator, display freezer | ?-present | `^(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])[0-9]{4}$` | yy | mm | 19062547 = June 2019 | H |
| McQuay (Daikin Applied, Daikin McQuay, McQuay International, AAF-McQuay) | chiller | 1968-1982 | `^(?P<ml>[A-L])(?P<yl>[M-ZA])\d{4,6}$` | letter:M=1968,N=1969,O=1970,P=1971,Q=1972,R=1973,S=1974,T=1975,U=1976,V=1977,W=1978,X=1979,Y=1980,Z=1981,A=1982 | letters:ABCDEFGHIJKL | AU1234 = Jan 1976 | H |
| McQuay (Daikin Applied, Daikin McQuay, McQuay International, AAF-McQuay) | condensing unit | 1974-1988 | `^\d{10,12}(?P<yl>[A-HJ-NPR])(?P<ww>\d{2})\d{4}$` | letter:A=1974,B=1975,C=1976,D=1977,E=1978,F=1979,G=1980,H=1981,J=1982,K=1983,L=1984,M=1985,N=1986,P=1987,R=1988 | ww | 1230456789M151234 = week 15 1985 | L |
| McQuay (Daikin Applied, Daikin McQuay, McQuay International, AAF-McQuay) | chiller, fan coil, air handler, water source heat pump, rooftop unit | 1975-1981 | `^\d(?P<yl>[E-HJ-L])(?P<ml>[A-HJ-M])\d{5}(?:\d{2})?$` | letter:E=1975,F=1976,G=1977,H=1978,J=1979,K=1980,L=1981 | letters:ABCDEFGHJKLM | 3HC1234501 = Mar 1978 | L |
| McQuay (Daikin Applied, Daikin McQuay, McQuay International, AAF-McQuay) | PTAC, water source heat pump | 1977-1989 | `^\d{2}(?P<y>\d)(?P<ww>\d{2})\d{4}$` | y | ww | 049270032 = week 27 1979 (or 1989) | L |
| McQuay (Daikin Applied, Daikin McQuay, McQuay International, AAF-McQuay) | chiller, fan coil, air handler, water source heat pump, rooftop unit, condensing unit | 1982-1994 | `^\d(?P<yl>[N-Z])(?P<ml>[A-HJ-M])\d{5}(?:\d{2})?$` | letter:N=1982,O=1983,P=1984,Q=1985,R=1986,S=1987,T=1988,U=1989,V=1990,W=1991,X=1992,Y=1993,Z=1994 | letters:ABCDEFGHJKLM | 5ZA1234500 = Jan 1994 | H |
| McQuay (Daikin Applied, Daikin McQuay, McQuay International, AAF-McQuay) | condensing unit | 1988-present | `^[RH](?P<yy>\d{2})(?P<ww>\d{2})\d{5}$` | yy | ww | R881212345 = week 12 1988 | L |
| McQuay (Daikin Applied, Daikin McQuay, McQuay International, AAF-McQuay) | chiller, fan coil, air handler, water source heat pump, rooftop unit, condensing unit, PTAC | 1995-1999 | `^\d(?P<y>[5-9])(?P<ml>[A-HJ-M])\d{5}(?:\d{2})?$` | y | letters:ABCDEFGHJKLM | 55A1234500 = Jan 1995 | H |
| McQuay (Daikin Applied, Daikin McQuay, McQuay International, AAF-McQuay) | chiller, fan coil, air handler, water source heat pump, rooftop unit, condensing unit | 1999-present | `^[A-Z]{3}[A-Z](?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{3,7}$` | yy | mm | STNU9905048 = May 1999 | H |
| McQuay (Daikin Applied, Daikin McQuay, McQuay International, AAF-McQuay) | ductless split | 2000-present | `^(?P<yl>20[4-6]\d)(?P<ww>\d{2})\d{8}$` | letter:2043=2000,2044=2001,2045=2002,2046=2003,2047=2004,2048=2005,2049=2006,2050=2007,2051=2008,2052=2009,2053=2010,2054=2011,2055=2012,2056=2013,2057=2014,2058=2015,2059=2016,2060=2017,2061=2018,2062=2019,2063=2020,2064=2021,2065=2022,2066=2023,2067=2024,2068=2025,2069=2026 | ww | 20444501000138 = week 45 2001 | L |
| Midea | ductless mini-split, heat pump, room air conditioner | ?-present | `^[A-Z][0-9A-Z]{10}(?P<yy>\d{2})(?P<ml>[1-9A-C])[0-9A-Z]{8}$` | yy | letters:123456789ABC | C703095030711704400004 = Jul 2011 | M |
| Midea | ductless mini-split, heat pump, air conditioner | ?-present | `^V(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{5}$` | yy | mm | V180543529 = May 2018 | M |
| Mitsubishi Electric (Mitsubishi) | hvac | 2000-now | `^(?P<y>\d)[0-9A-Z]{5,}$` | y | none | 8012345 = 2018 | L |
| Modine | unit heater, duct furnace, rooftop unit | 1976-1999 | `^\d{7}(?P<mm>0[1-9]\|1[0-2])(?P<yy>\d{2})(?:-?\d{4})?$` | yy | mm | 01121010691 = Jun 1991 | L |
| Modine (Hot Dawg) | unit heater, duct furnace, rooftop unit | 1995-present | `^\d{7}(?P<ww>\d{2})(?P<yy>\d{2})\d{4}$` | yy | ww | 010110101971000 = week 1 1997 | H |
| Modine | unit heater, duct furnace, rooftop unit | 2005-present | `^\d{10}(?P<ww>\d{2})(?P<yy>\d{2})\d{4}$` | yy | ww | 010100170901051000 = week 1 2005 | H |
| Mor-Flo (Mor-Flo/American) | tank water heater | 1986-2004 | `^[A-Z]?(?P<yy>\d{2})(?P<ww>\d{2})\d{5,6}$` | yy | ww | J861425155 = week 14 1986 (Apr 1986) | L |
| MrCool (Mr Cool) | ductless mini-split, heat pump | ?-present | `^(?P<ww>\d{2})(?P<yy>\d{2})[A-Z][0-9A-Z]{4,10}$` | yy | ww | 1920K08283 = week 19 2020 | L |
| MrCool (Mr Cool) | ductless mini-split, heat pump | 2010-2019 | `^[0-9A-Z]{11}(?P<y>\d)(?P<ml>[1-9A-C])(?P<dd>\d{2})[0-9A-Z]{7}$` | y | letters:123456789ABC | 2402135890267230130069 = Jul 23 2016 | L |
| Multistack (Airstack) | chiller, modular chiller | 1991-2009 | `^(?P<yl>[IJ][A-I])-?(?P<mm>0[1-9]\|1[0-2])-?\d{2}$` | letter:IA=1991,IB=1992,IC=1993,ID=1994,IE=1995,IF=1996,IG=1997,IH=1998,II=1999,JA=2001,JB=2002,JC=2003,JD=2004,JE=2005,JF=2006,JG=2007,JH=2008,JI=2009 | mm | JC-06-25 = Jun 2003 | H |
| Munters | desiccant dehumidifier | 2000-present | `^(?P<yy>\d{2})(?P<ww>\d{2})\d{11}$` | yy | ww | 091017012312345 = week 10 2009 | H |
| Navien | tankless_water_heater, water_heater, boiler | 2005-2015 | `^\d{4}-(?P<yyyy>\d{4})(?P<mm>\d{2})(?P<dd>\d{2})-\d+$` | yyyy | mm | 8881-20100520-3026 = 20 May 2010 | M |
| Navien | tankless_water_heater, water_heater, boiler | 2010-now | `^[0-9A-Z]{5}(?P<yy>\d{2})(?P<ml>[1-9XYZ])(?P<dd>\d{2})\d{0,6}$` | yy | letters:123456789XYZ | 7414C21X17 = 17 Oct 2021 | M |
| Nor-Lake (Norlake) | walk-in cooler, walk-in freezer, reach-in refrigerator | ?-present | `^(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])[0-9A-Z]{4}$` | yy | mm | 09011234 = January 2009 | L |
| Nordyne (Miller, Frigidaire, Intertherm, Kelvinator, Maytag, Broan, Mammoth) | furnace, air conditioner, heat pump, manufactured-home furnace | ?-now | `^[A-Z]\d[A-Z](?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])-?\d{5}$` | yy | mm | G6R9905-05028 = May 1999 | M |
| Nordyne (Philco, Westinghouse, Tappan) | air conditioner, heat pump | ?-now | `^[A-Z0-9]{7}[A-Z](?P<ww>0[1-9]\|[1-4]\d\|5[0-3])(?P<yy>\d{2})\d{4,5}$` | yy | ww | MN3D102F38914228 = week 38 1991 | M |
| Nordyne (Frigidaire, Maytag, Westinghouse, Tappan, Gibson, Kelvinator, Intertherm, Miller, Broan, Philco, Mammoth, NuTone) | furnace, air conditioner, heat pump, manufactured-home furnace | 1998-present | `^[A-Z]{3}-?(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])-?\d{5}$` | yy | mm | GBB030708229 = Jul 2003 | M |
| Noritz | tankless water heater | ?-present | `^(?P<yyyy>(?:19\|20)\d{2})\.(?P<mm>0[1-9]\|1[0-2])-?\d{5,6}$` | yyyy | mm | 2005.06-004472 = Jun 2005 | M |
| NTI | indirect water heater | ?-present | `^(?P<yy>\d{2})\d{6}$` | yy | none | 22033999 = 2022 | H |
| NTI | boiler | ?-2010 | `^(?P<yy>\d{2})[A-Z]{1,4}-\d{4,6}$` | yy | none | 09TI-21647 = 2009 | H |
| NTI | boiler | 2011-present | `^\d{2}(?P<mm>0[1-9]\|1[0-2])(?P<dd>[0-3]\d)(?P<yy>\d{2})\d{8}$` | yy | mm | 2110202138184177 = 20 Oct 2021 | H |
| NTI | boiler | 2021-present | `^\d{7}[A-Z]\d(?P<yy>\d{2})(?P<doy>[0-3]\d{2})\d{7}$` | yy | doy | 3260053C8222930000005 = 20 Oct 2022 | H |
| Olsen | furnace, boiler | ?-present | `^\d{2}(?P<yy>\d{2})[A-Z]\d{6}$` | yy | none | 1207A012064 = 2007 | L |
| Panasonic | ductless mini-split, heat pump | ?-present | `^(?P<yyyy>(?:19\|20)\d{2})(?P<mm>0[1-9]\|1[0-2])$` | yyyy | mm | 201011 = Nov 2010 | M |
| Peerless (Pinnacle, Purefire) | boiler | 1984-present | `^\d{5,7}-(?P<mm>0[1-9]\|1[0-2])(?P<yy>\d{2})$` | yy | mm | 123456-1284 = Dec 1984 | H |
| Peerless (Pinnacle, Purefire) | boiler | 2000-present | `^\d{5,7}-(?P<yyyy>(?:19\|20)\d{2})(?P<mm>0[1-9]\|1[0-2])$` | yyyy | mm | 123456-201003 = Mar 2010 | H |
| Pennco | boiler | ?-present | `^P(?P<ww>0[1-9]\|[1-4]\d\|5[0-3])(?P<yy>\d{2})\d{5,6}$` | yy | ww | P3604001133 = week 36 2004 | L |
| Pitco | fryer | ?-present | `^[GEF](?P<yy>[0-9]{2})(?P<ml>[A-HJ-M])[0-9A-Z]+$` | yy | letters:ABCDEFGHJKLM | G11E012345 = May 2011 | L |
| Rational | combi oven | 1993-1997 | `^[CMD](61\|62\|101\|102\|201\|202\|11\|12\|21\|22)[A-Z](?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])[0-9]{4}$` | yy | mm | C61C95051234 = May 1995 | H |
| Rational | combi oven | 1997-2004 | `^[EG](61\|62\|101\|102\|201\|202\|11\|12\|21\|22)[CMBD][A-Z]?(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])([0-9]{4}\|[0-9]{7})$` | yy | mm | E61CB03072345678 = July 2003 | H |
| Rational | combi oven | 2004-present | `^[EG](61\|62\|101\|102\|201\|202\|11\|12\|21\|22)[SMFG][A-Z](?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])[0-9]{7}$` | yy | mm | E61SE04072345678 = July 2004 | H |
| Raypak | boiler, pool heater, water heater | ?-1994 | `^(?P<mm>0[1-9]\|1[0-2])(?P<yy>\d{2})\d{6}$` | yy | mm | 0386010019 = Mar 1986 | M |
| Raypak | boiler, pool heater, water heater | 1995-present | `^(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{6}$` | yy | mm | 1604304448 = Apr 2016 | M |
| Regal (Century / A.O. Smith motors) (Century, A.O. Smith, AO Smith, Universal) | fractional motor, integral motor, pool pump motor, fan motor | 2006-present | `^(?P<doy>[0-3][0-9]{2})(?P<yy>[0-9]{2})[0-9A-Z]{2}$` | yy | doy | 123064M = May 3 2006 | H |
| Reznor | unit heater, duct furnace, make-up air, rooftop unit, infrared heater | ?-present | `^(?P<mm>0[1-9]\|1[0-2])(?P<yy>\d{2})\d{4}[A-Z]$` | yy | mm | 09087238A = Sep 2008 | L |
| Reznor | unit heater, duct furnace, make-up air, rooftop unit, infrared heater | 1975-2001 | `^(?P<yl>A[A-Z]\|BA)(?P<ml>[A-L])[A-Z0-9]+$` | letter:AA=1975,AB=1976,AC=1977,AD=1978,AE=1979,AF=1980,AG=1981,AH=1982,AI=1983,AJ=1984,AK=1985,AL=1986,AM=1987,AN=1988,AO=1989,AP=1990,AQ=1991,AR=1992,AS=1993,AT=1994,AU=1995,AV=1996,AW=1997,AX=1998,AY=1999,AZ=2000,BA=2001 | letters:ABCDEFGHIJKL | AWD79Y2N35171X = Apr 1997 | M |
| Reznor | unit heater, duct furnace, make-up air, rooftop unit, infrared heater | 2002-present | `^(?P<yl>B[B-Z]\|C[A-Z])(?P<ml>[A-L])[A-Z0-9]+$` | letter:BB=2002,BC=2003,BD=2004,BE=2005,BF=2006,BG=2007,BH=2008,BI=2009,BJ=2010,BK=2011,BL=2012,BM=2013,BN=2014,BO=2015,BP=2016,BQ=2017,BR=2018,BS=2019,BT=2020,BU=2021,BV=2022,BW=2023,BX=2024,BY=2025,BZ=2026 | letters:ABCDEFGHIJKL | BBD79X7N00000 = Apr 2002 | H |
| Rheem (Ruud, Richmond, Vanguard, Professional, Western Auto, Montgomery Ward, Citation, Vista Therm) | tank water heater | 1969-1999 | `^(?:R[A-Z]{0,3})?(?P<mm>0[1-9]\|1[0-2])(?P<yy>\d{2})[A-Z]?\d{5,6}$` | yy | mm | R0884B10488 = Aug 1984 | M |
| Rheem (Ruud) | tank water heater | 1970-1979 | `^\d{5}(?P<ww>\d{2})(?P<yy>\d{2})$` | yy | ww | 168252873 = week 28 1973 (Jul 1973) | L |
| Rheem (Ruud, Weatherking) | hvac | 1990-now | `^[A-Z](?P<ww>\d{2})(?P<yy>\d{2})\d{5}$` | yy | ww | W291013412 = week 29 2010 | M |
| Rheem (Ruud, Weatherking) | hvac | 1990-now | `^[0-9A-Z]{3,8}?[FMGWN](?P<ww>\d{2})(?P<yy>\d{2})\d{5}$` | yy | ww | 7351M280616735 = week 28 2006 | M |
| Rheem (Ruud, Richmond) | water_heater | 1990-now | `^[A-Z]{1,4}(?P<mm>\d{2})(?P<yy>\d{2})[A-Z0-9]+$` | yy | mm | RHLN0106534307 = Jan 2006 | M |
| Rheem (Ruud, Richmond) | water_heater | 1990-now | `^[A-Z]{1,5}(?P<ww>\d{2})(?P<yy>\d{2})\d{5}$` | yy | ww | A141511869 = week 14 2015 | M |
| Rheem (Ruud) | tankless_water_heater, water_heater | 1990-now | `^(?P<yy>\d{2})\.(?P<mm>\d{2})-?\d+$` | yy | mm | 05.05-000021 = May 2005 | M |
| Rinnai | tankless_water_heater, water_heater | 1999-2008 | `^(?P<yy>\d{2})\.(?P<mm>\d{2})-?\d+$` | yy | mm | 04.03-102521 = Mar 2004 | M |
| Rinnai | tankless_water_heater, water_heater | 1999-2008 | `^(?P<yy>\d{2})(?P<mm>\d{2})\d{4,5}$` | yy | mm | 05083453 = Aug 2005 | M |
| Rinnai | tankless water heater | 1999-2009 | `^(?P<yy>\d{2})\.?(?P<mm>0[1-9]\|1[0-2])-?\d{4,6}$` | yy | mm | 04.03-102521 = Mar 2004 | M |
| Rinnai | tankless_water_heater, water_heater | 2009-now | `^(?P<yl>[A-HJ-PR-TW-Z])(?P<ml>[A-HJ-M])\.?[A-Z]{2}-?\d+$` | letter:A=2009,B=2010,C=2011,D=2012,E=2013,F=2014,G=2015,H=2016,J=2017,K=2018,L=2019,M=2020,N=2021,O=2022,P=2022,R=2023,S=2024,T=2025,W=2026,X=2027,Y=2028,Z=2029 | letters:ABCDEFGHJKLM | BL.CA-051306 = Nov 2010 | H |
| Ruud (Rheem, Weather King) | furnace, air conditioner, heat pump | 1955-1975 | `^\d{4,6}(?P<ww>0[1-9]\|[1-4]\d\|5[0-3])(?P<yy>[5-7]\d)$` | yy | ww | 123451872 = week 18 1972 | M |
| Ruud (Rheem, Weather King) | furnace, air conditioner, heat pump | 1974-present | `^[A-Z0-9]{3,8}?[FMGWN](?P<ww>0[1-9]\|[1-4]\d\|5[0-3])(?P<yy>\d{2})\d{5}$` | yy | ww | CB5D302F099903346 = week 09 1999 | M |
| Samsung | ductless mini-split, heat pump, room air conditioner | 1997-2004 | `^[A-Z0-9]{3}(?P<yl>[HJKNRTWX])(?P<ml>[1-9ABC])[A-Z0-9]{5,6}$` | letter:H=1997,J=1998,K=1999,N=2000,R=2001,T=2002,W=2003,X=2004 | letters:123456789ABC | P1BW612345 = Jun 2003 | H |
| Samsung | ductless mini-split, heat pump, room air conditioner | 2004-2018 | `^[A-Z0-9]{7}(?P<yl>[RTWXYALPQSZBCDFGHJK])(?P<ml>[1-9ABC])[A-Z0-9]{6}$` | letter:R=2001,T=2002,W=2003,X=2004,Y=2005,A=2006,L=2006,P=2007,Q=2008,S=2009,Z=2010,B=2011,C=2012,D=2013,F=2014,G=2015,H=2016,J=2017,K=2018 | letters:123456789ABC | 0B4MPABD8N50012 = Aug 2013 | M |
| Samsung | ductless mini-split, heat pump, room air conditioner | 2005-2018 | `^[A-Z0-9]{3}(?P<yl>[RTWXYALPQSZBCDFGHJK])(?P<ml>[1-9ABC])[A-Z0-9]{6}$` | letter:R=2001,T=2002,W=2003,X=2004,Y=2005,A=2006,L=2006,P=2007,Q=2008,S=2009,Z=2010,B=2011,C=2012,D=2013,F=2014,G=2015,H=2016,J=2017,K=2018 | letters:123456789ABC | P1CP2473381 = Feb 2007 | M |
| Sanyo | ductless mini-split, heat pump, air conditioner | ?-now | `^\d{5}(?P<y>\d)\d$` | y | none | 0247381 = 1998 or 2008 or 2018 | L |
| Sanyo (Panasonic) | ductless split, VRF, air conditioner | 2000-present | `^(?P<yyyy>20\d{2})(?P<mm>0[1-9]\|1[0-2])$` | yyyy | mm | 201011 = Nov 2010 | L |
| Scotsman | ice machine | 1976-1995 | `^[0-9]{5,7}-?(?P<mcode>0[1-9]\|1[0-2])(?P<yl>[A-HJ-NP-Z])$` | letter:B=1975,Q=1976,C=1977,R=1978,D=1979,S=1980,E=1981,T=1982,F=1983,U=1984,G=1985,V=1986,H=1987,W=1988,J=1989,X=1990,K=1991,Y=1992,L=1993,Z=1994,M=1995,N=1972,A=1973,P=1974 | none | 123456-07H = 1987 | L |
| Scotsman | ice machine | 1996-2004 | `^[0-9]{5,7}-?(?P<mcode>0[1-9]\|1[0-2])(?P<yl>[A-HJ-NP-Z])$` | letter:A=1996,N=1997,B=1998,P=1999,C=2000,R=2001,D=2002,S=2003,E=2004 | none | 123456-09D = 2002 | L |
| Scotsman | ice machine | 2004-present | `^(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])[0-9]{4}[0-9]{6}$` | yy | mm | 07111320123456 = November 2007 | L |
| Scroll Technologies (Danfoss Scroll Technologies) | scroll compressor | ?-now | `^S(?P<ww>[0-5][0-9])(?P<yy>[0-9]{2})[A-Z][0-9]{5}$` | yy | ww | S3497K05252 = week 34 1997 (Aug 1997) | L |
| Slant/Fin | boiler | 1985-present | `^(?P<ml>[A-HJ-M])(?P<y>\d)\d{7}$` | y | letters:ABCDEFGHJKLM | L43045429 = Nov 1994 or Nov 2004 | L |
| Square D | circuit breaker, load center, panelboard, safety switch, distribution equipment | 1966-1996 | `^(?P<ml>[A-HJ-M])(?P<dd>[0-3]?[0-9])?(?P<yl>[A-HJ-NPR-X])(?P<op>[0-9]{3})?(?P<shift>[0-9])?$` | letter:A=1950,B=1951,C=1952,D=1953,E=1954,F=1955,G=1956,H=1957,J=1958,K=1959,L=1960,M=1961,N=1962,P=1963,R=1964,S=1965,T=1966,U=1967,V=1968,W=1969,X=1970;cycle=21 | letters:ABCDEFGHJKLM | H25W0652 = August 25 1969 or August 25 1990 | H |
| Square D | QO circuit breaker, Homeline circuit breaker | 1966-present | `^(?P<ml>[A-HJ-M])(?P<yl>[A-HJ-NPR-X])$` | letter:A=1950,B=1951,C=1952,D=1953,E=1954,F=1955,G=1956,H=1957,J=1958,K=1959,L=1960,M=1961,N=1962,P=1963,R=1964,S=1965,T=1966,U=1967,V=1968,W=1969,X=1970;cycle=21 | letters:ABCDEFGHJKLM | LW = November 1969, 1990 or 2011 | H |
| Square D | molded case circuit breaker, panelboard, load center, QO/HOM AFCI/GFCI breaker, enclosure | 1996-present | `^(?P<yy>[0-9]{2})(?P<ww>0[1-9]\|[1-4][0-9]\|5[0-3])(?P<wd>[1-7])?(?P<shift>[0-9H])?$` | yy | ww | 97171 = week 17 1997 (Apr 1997, Monday) | H |
| State (State Industries, Reliance, Sears, Kenmore, Ambassador, Crosley, JC Penney, Thermo-King) | tank water heater | 1976-2008 | `^(?P<ml>[A-HJ-M])(?P<yy>\d{2})[A-Z]?\d{6,7}$` | yy | letters:ABCDEFGHJKLM | H765662231 = Aug 1976 | M |
| State (Reliance, Kenmore, Sears) | tank water heater | 2008-present | `^[A-Z]?(?P<yy>\d{2})(?P<ww>\d{2})(?:[A-Z]\d{6}\|\d{9})$` | yy | ww | 1210A002243 = week 10 2012 (Mar 2012) | M |
| Stiebel Eltron (Accelera, Tempra) | heat pump water heater, electric water heater, tankless water heater | ?-present | `^\d{6}-?(?P<yl>\d{2})(?:2[6-9]\|[3-6]\d\|7[0-8])-?\d{7}$` | letter:51=1976,52=1977,53=1978,54=1979,55=1980,56=1981,57=1982,58=1983,59=1984,60=1985,61=1986,62=1987,63=1988,64=1989,65=1990,66=1991,67=1992,68=1993,69=1994,70=1995,71=1996,72=1997,73=1998,74=1999,75=2000,76=2001,77=2002,78=2003,79=2004,80=2005,81=2006,82=2007,83=2008,84=2009,85=2010,86=2011,87=2012,88=2013,89=2014,90=2015,91=2016,92=2017,93=2018,94=2019,95=2020,96=2021,97=2022,98=2023,99=2024,00=2025,01=2026 | none | 223426-9137-9000359 = week 12 2016 | M |
| Stiebel Eltron (Tempra) | tankless water heater, heat pump water heater | ?-present | `^\d+-(?P<yl>\d{2})\d{2}-\d+$` | letter:75=2000,76=2001,77=2002,78=2003,79=2004,80=2005,81=2006,82=2007,83=2008,84=2009,85=2010,86=2011,87=2012,88=2013,89=2014,90=2015,91=2016,92=2017,93=2018,94=2019,95=2020,96=2021,97=2022,98=2023,99=2024,00=2025,01=2026 | none | 123456-8965-000123 = 2014 (week 40, not decoded) | L |
| Takagi | tankless water heater | 2010-present | `^(?P<yy>\d{2})(?P<ww>\d{2})[A-Z]?\d{4,9}$` | yy | ww | 1544E000453 = week 44 2015 (Nov 2015) | M |
| Tappan (Frigidaire) | furnace, air conditioner, heat pump | ?-now | `^\d{5}-?(?P<yy>\d{2})(?P<ml>[A-HJ-M])$` | yy | letters:ABCDEFGHJKLM | 21584-97B = Feb 1997 | M |
| Tecumseh | condensing unit | ?-present | `^[A-Z]\d{2}(?P<yy>\d{2})$` | yy | none | B0613 = 2013 | L |
| Tecumseh | hermetic compressor, condensing unit | ?-now | `^(?P<ml>[A-L])(?P<dd>[0-3][0-9])(?P<yy>[0-9]{2})$` | yy | letters:ABCDEFGHIJKL | H2995 = August 29, 1995 | M |
| Trane | rooftop unit, air handler, unit heater | 1970-1999 | `^(?P<ml>[A-HJ-M])(?P<yy>\d{2})-\d{5}$` | yy | letters:ABCDEFGHJKLM | F91-90391 = Jun 1991 | L |
| Trane (American Standard) | furnace, air conditioner, heat pump | 1971-1979 | `^(?P<y>\d)[A-M]-?\d{4}$` | y | none | 1C-1234 = 1971 | M |
| Trane | unit heater, rooftop unit, air handler | 1975-1999 | `^[A-Z](?P<yy>\d{2})(?P<ml>[A-HJ-M])\d{5}$` | yy | letters:ABCDEFGHJKLM | A92M07217 = Dec 1992 | L |
| Trane (American Standard) | furnace, air conditioner, heat pump | 1980-1982 | `^\d{6}(?P<yl>[OTU])$` | letter:O=1980,T=1981,U=1982 | none | 123456T = 1981 | M |
| Trane (American Standard) | furnace, air conditioner, heat pump | 1980-1982 | `^(?P<yl>[ABC])\d{6}$` | letter:A=1980,B=1981,C=1982 | none | B123456 = 1981 | L |
| Trane | furnace, rooftop unit, air handler | 1980-1982 | `^[A-Z]\d{6}(?P<yl>[ABCLMNOTU])(?P<ww>\d{2})$` | letter:A=1980,L=1980,O=1980,B=1981,M=1981,T=1981,C=1982,N=1982,U=1982 | ww | H011870M03 = week 3 1981 | M |
| Trane | rooftop unit, air handler, chiller | 1980-1982 | `^(?P<yl>[ABCOTU])\d{6}$` | letter:A=1980,O=1980,B=1981,T=1981,C=1982,U=1982 | none | B123456 = 1981 | M |
| Trane (American Standard) | furnace, air conditioner, heat pump | 1983-2001 | `^(?P<yl>[B-HJ-NPRSW-Z])(?P<ww>0[1-9]\|[1-4]\d\|5[0-3])[A-Z0-9]{4,7}$` | letter:W=1983,X=1984,Y=1985,S=1986,B=1987,C=1988,D=1989,E=1990,F=1991,G=1992,H=1993,J=1994,K=1995,L=1996,M=1997,N=1998,P=1999,R=2000,Z=2001 | ww | B50632891 = week 50 1987 (Dec 1987) | M |
| Trane (American Standard, Ameristar, Ingersoll Rand) | hvac | 2002-2009 | `^(?P<y>\d)(?P<ww>\d{2})[0-9A-Z]{4,}$` | y | ww | 91531S41F = week 15 2009 | H |
| Trane (American Standard, Ameristar, Ingersoll Rand) | hvac | 2010-now | `^(?P<yy>\d{2})(?P<ww>\d{2})[0-9A-Z]{4,}$` | yy | ww | 130313596L = week 3 2013 | H |
| Traulsen | reach-in refrigerator, reach-in freezer, blast chiller | ?-now | `^T[0-9]{5}(?P<ml>[A-L])(?P<yy>[0-9]{2})$` | yy | letters:ABCDEFGHIJKL | T12345C98 = March 1998 | L |
| Traulsen | reach-in refrigerator, reach-in freezer, blast chiller | ?-present | `^(?P<yy>[0-9]{2})(?P<ml>[A-L])[0-9]{6}$` | yy | letters:ABCDEFGHIJKL | 17A000123 = January 2017 | L |
| U.S. Motors (US Motors, Nidec) | integral horsepower motor, pump motor | 2009-present | `^(?P<yl>[A-HJ-NPR-Z])(?P<mm>0[1-9]\|1[0-2])[0-9]{8}-?[0-9]{3}(R\|M\|GT)?(-[0-9]+)?$` | letter:P=2009,R=2010,S=2011,T=2012,U=2013,V=2014,W=2015,X=2016,Y=2017,Z=2018,A=2019,B=2020,C=2021,D=2022,E=2023,F=2024,G=2025,H=2026,J=2027,K=2028,L=2029,M=2030,N=2031 | mm | U0612345678-100R-1 = June 2013 | H |
| U.S. Motors (US Motors, Nidec) | fractional horsepower motor, pool pump motor, fan motor | 2010-present | `^(?P<ml>[A-HJ-M])(?P<yy>[0-9]{2})[A-Z]{1,2}$` | yy | letters:ABCDEFGHJKLM | A13C = January 2013 | H |
| Unico (The Unico System) | air handler, small duct high velocity | 1985-present | `^(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])[A-Z]\d{6}$` | yy | mm | 0603A184624 = Mar 2006 | L |
| Universal (Century) (Universal Electric) | fractional motor, fan motor | 1988-2009 | `^(?P<ww>[1-9]\|[1-4][0-9]\|5[0-2])(?P<yl>[A-HJ-NP-Z])[0-9]{6,7}[A-Z]$` | letter:Z=1988,D=1992,E=1993,F=1994,G=1995,H=1996,J=1997,K=1998,L=1999,M=2000,N=2001,P=2002,R=2003,S=2004,T=2005,U=2006,V=2007,W=2008,X=2009 | ww | 8Z0275592R = week 8 1988 (Feb 1988) | H |
| Utica (ECR, Ultimate) | boiler | ?-present | `^(?P<ww>0[1-9]\|[1-4]\d\|5[0-3])(?P<yy>\d{2})\d{5}[A-Z]?$` | yy | ww | 160500150 = week 16 2005 | M |
| Utica | boiler | 2003-2012 | `^U(?P<ml>[A-L])(?P<yl>[A-J])[A-Z]?\d{4,6}$` | letter:A=2003,B=2004,C=2005,D=2006,E=2007,F=2008,G=2009,H=2010,I=2011,J=2012 | letters:ABCDEFGHIJKL | UBC14945 = Feb 2005 | M |
| Vaughn | tank water heater, indirect water heater | 1986-1986 | `^(?P<mm>0[1-9]\|1[0-2])(?P<yy>\d{2})\d{5}[A-Z]?$` | yy | mm | 098600840 = Sep 1986 | L |
| Viessmann | boiler | ?-present | `^\d{6}(?P<yy>\d{2})\d{8,10}$` | yy | none | 73748610026311101 = 2010 | L |
| WaterFurnace | geothermal heat pump, water source heat pump | 1983-1985 | `^(?P<ml>[A-HJ-M])(?P<yy>\d{2})\d{5}$` | yy | letters:ABCDEFGHJKLM | D8367019 = Apr 1983 | L |
| WaterFurnace | geothermal heat pump, water source heat pump | 1985-2012 | `^(?P<yl>[A-HJ-Z])(?P<ml>[A-HJ-M])\d{4,6}$` | letter:A=1985,B=1986,C=1987,D=1988,E=1989,F=1990,G=1991,H=1992,J=1993,K=1994,L=1995,M=1996,N=1997,O=1998,P=1999,Q=2000,R=2001,S=2002,T=2003,U=2004,V=2005,W=2006,X=2007,Y=2008,Z=2009;cycle=25 | letters:ABCDEFGHJKLM | UJ1087 = Sep 2004 | L |
| WaterFurnace | geothermal heat pump, water source heat pump | 2012-present | `^(?P<yy>\d{2})(?P<mm>0[1-9]\|1[0-2])\d{5}$` | yy | mm | 180100228 = Jan 2018 | L |
| WEG (drives) | variable frequency drive | 2004-present | `^(?P<ww>0[1-9]\|[1-4][0-9]\|5[0-3])(?P<yl>[A-Z])$` | letter:A=2004,B=2005,C=2006,D=2007,E=2008,F=2009,G=2010,H=2011,I=2012,J=2013,K=2014,L=2015,M=2016,N=2017,O=2018,P=2019,Q=2020,R=2021,S=2022,T=2023,U=2024,V=2025,W=2026 | ww | 03H = week 3 2011 (Jan 2011) | L |
| Whirlpool | furnace, air conditioner, heat pump | 1970-1999 | `^(?P<yl>[GHJ]\d)(?P<ww>0[1-9]\|[1-4]\d\|5[0-3])[A-Z0-9]{4,6}$` | letter:G0=1970,G1=1971,G2=1972,G3=1973,G4=1974,G5=1975,G6=1976,G7=1977,G8=1978,G9=1979,H0=1980,H1=1981,H2=1982,H3=1983,H4=1984,H5=1985,H6=1986,H7=1987,H8=1988,H9=1989,J0=1990,J1=1991,J2=1992,J3=1993,J4=1994,J5=1995,J6=1996,J7=1997,J8=1998,J9=1999 | ww | H41612345 = week 16 1984 | M |
| Whirlpool (Roper, Estate) | room air conditioner, dehumidifier | 1975-1989 | `^[A-Z]{1,2}(?P<y>\d)(?P<ww>\d{2})\d{5,6}$` | y | ww | C51234567 = week 12 1975 or week 12 1985 | L |
| Whirlpool (Roper, Estate, Maytag) | room air conditioner, dehumidifier | 1990-2009 | `^[A-Z]{1,2}(?P<yl>[A-HJ-MPR-UWXY])(?P<ww>\d{2})\d{5,6}$` | letter:X=1990,A=1991,B=1992,C=1993,D=1994,E=1995,F=1996,G=1997,H=1998,J=1999,K=2000,L=2001,M=2002,P=2003,R=2004,S=2005,T=2006,U=2007,W=2008,Y=2009 | ww | MB1402320 = week 14 1992 | L |
| Whirlpool (Roper, Estate, Maytag) | room air conditioner, dehumidifier | 2010-2019 | `^[A-Z]{1,2}(?P<y>\d)(?P<ww>\d{2})\d{5,6}$` | y | ww | C60842986 = week 08 2016 | L |
| Whirlpool (Roper, Estate, Maytag) | room air conditioner, dehumidifier | 2020-present | `^[A-Z]{1,2}(?P<yl>[XA-HJ])(?P<ww>\d{2})\d{5,6}$` | letter:X=2020,A=2021,B=2022,C=2023,D=2024,E=2025,F=2026,G=2027,H=2028,J=2029 | ww | MX06404786 = week 06 2020 | L |
| White-Rodgers (Emerson White-Rodgers) | thermostat, control | ?-present | `^(?P<yy>[0-9]{2})(?P<ww>0[1-9]\|[1-4][0-9]\|5[0-3])$` | yy | ww | 1416 = week 16 2014 (Apr 2014) | L |
| Williamson | furnace | ?-now | `^[A-D](?P<yy>\d{2})\d{5}$` | yy | none | A8602779 = 1986 | L |
| Williamson | furnace | 1940-now | `^(?P<yy>[4-9]\d)\d{5}$` | yy | none | 7302764 = 1973 | L |
| Yaskawa | variable frequency drive | ?-now | `^U-?(?P<yy>[0-9]{2})(?P<mm>0[1-9]\|1[0-2])[0-9]{3,5}-?[0-9]{1,3}$` | yy | mm | U-9603250-3 = March 1996 | H |
| York (Luxaire, Coleman, Fraser-Johnston) | hvac | 1971-2004 | `^\(?[A-Z]\)?(?P<ml>[A-HK-N])(?P<yl>[A-HJ-NP-TV-Y])[A-Z]\d+$` | letter:A=1971,B=1972,C=1973,D=1974,E=1975,F=1976,G=1977,H=1978,J=1979,K=1980,L=1981,M=1982,N=1983,P=1984,R=1985,S=1986,T=1987,V=1988,W=1989,X=1990,Y=1991;cycle=21 | letters:ABCDEFGHKLMN | MKWQ123456 = Sep 1989 | L |
| York (Coleman, Evcon, Luxaire, Fraser-Johnston, Guardian, Moncrief) | furnace, air conditioner, heat pump | 1971-2004 | `^(?:\([A-Z]\))?[A-Z](?P<ml>[A-HJ-N])(?P<yl>[A-HJ-NPR-TV-Y])[A-Z]\d{6}$` | letter:A=1971,B=1972,C=1973,D=1974,E=1975,F=1976,G=1977,H=1978,J=1979,K=1980,L=1981,M=1982,N=1983,P=1984,R=1985,S=1986,T=1987,V=1988,W=1989,X=1990,Y=1991;cycle=21 | letters:ABCDEFGHKLMN | WAKM011379 = Jan 1980 or Jan 2001 | M |
| York (Luxaire, Coleman, Fraser-Johnston, Johnson Controls) | hvac | 2004-now | `^[A-Z](?P<y1>\d)(?P<ml>[A-HJ-M])(?P<y2>\d)\d+$` | concat:y1,y2 | letters:ABCDEFGHJKLM | W0K5896070 = Oct 2005 | H |

**No date in the serial** (use the nameplate date, permit or service records): Applied Air, Auto-Chlor, Axeman-Anderson, Berner, CaptiveAire, Compu-Aire, Dadanco, EDPAC, Eemax, Embraco, Fujitsu, Giant, Groen, Hobart, Hydrotherm, Ice Air, Klimaire, Loren Cook, National Board (ASME plate), Peerless, Pioneer, RBI, Seisco, Semco, Smith Cast Iron Boilers, SpacePak, Sterling, Sterling Industrial, Taco, Takagi, Thermo Pride, Titan, Triangle Tube, True, Weil-McLain.

## Appendix B: median service life by equipment type

| Equipment type | Median life (yrs) | Source | Efficiency metric |
|---|---|---|---|
| Packaged rooftop unit, DX cooling with gas heat (RTU) | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | EER + IEER (>=65 kBtu/h); SEER2 + EER2 (<65 kBtu/h); gas section Et or AFUE |
| Packaged rooftop heat pump (RTU-HP) | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | EER + IEER and heating COP (>=65 kBtu/h); SEER2 + HSPF2 (<65 kBtu/h) |
| Packaged VAV rooftop unit (PVAV, 20-100 ton) | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | EER + IEER; supply fan W/cfm |
| Air-cooled condensing unit (split system) | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | SEER2 + EER2 (<65 kBtu/h); EER + IEER (larger) |
| Ductless mini-split indoor unit (wall or cassette) | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | SEER2 + HSPF2 (system rated with outdoor unit) |
| VRF outdoor unit | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | EER + IEER cooling; COP heating; SCHE for heat recovery |
| VRF indoor unit (ceiling cassette or ducted) | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | n/a (system rated) |
| Water-cooled chiller (centrifugal or screw) | 23 | ASHRAE HVAC Applications Ch. 38 Table 4 | kW/ton full load + IPLV.IP or NPLV (90.1 Table 6.8.1-3); COP |
| Air-cooled chiller (scroll or screw) | 20 | ASHRAE HVAC Applications Ch. 38 Table 4 | EER + IPLV.IP (90.1 Table 6.8.1-3) |
| Cooling tower (open circuit) | 20 | ASHRAE HVAC Applications Ch. 38 Table 4 | gpm per fan hp (90.1 Table 6.8.1-7); fan motor hp and VFD present |
| Closed-circuit fluid cooler or dry cooler | 20 | ASHRAE HVAC Applications Ch. 38 Table 4 | gpm per fan hp |
| Water-source heat pump (zone unit) | 19 | ASHRAE HVAC Applications Ch. 38 Table 4 | EER cooling + COP heating (ISO 13256-1) |
| Computer room air conditioner (CRAC/CRAH) | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | SCOP or kW/ton; net sensible capacity |
| PTAC / PTHP / through-wall AC | 10 | ASHRAE HVAC Applications Ch. 38 Table 4 | EER + COP (PTAC/PTHP); CEER (room AC) |
| Hot water boiler, gas, non-condensing | 24 | ASHRAE HVAC Applications Ch. 38 Table 4 | Thermal efficiency Et (<=2,500 kBtu/h) or combustion efficiency Ec (>2,500 kBtu/h); AFUE below 300 kBtu/h |
| Hot water boiler, gas, condensing | 20 | Industry / FEMP convention, not a published table; ASHRAE lists steel hot water boiler at 24, condensing units are usually assumed 15-20 | Thermal efficiency Et (typically 90-97%) |
| Steam boiler | 25 | ASHRAE HVAC Applications Ch. 38 Table 4 | Et or Ec |
| Electric boiler | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | n/a (100% site efficiency); kW input |
| Gas furnace (standalone or furnace section) | 18 | ASHRAE HVAC Applications Ch. 38 Table 4 | AFUE (<225 kBtu/h) or Et |
| Unit heater, gas or electric | 13 | ASHRAE HVAC Applications Ch. 38 Table 4 | Et (gas); kW (electric) |
| Electric baseboard or resistance heater | 13 | ASHRAE HVAC Applications Ch. 38 Table 4 | n/a; kW |
| Hot water radiator or fin-tube baseboard | 25 | ASHRAE HVAC Applications Ch. 38 Table 4 | n/a (hydronic terminal) |
| Air-to-water heat pump (heating plant) | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | COP heating at rated point; IPLV cooling if reversible |
| Heat recovery chiller / water-to-water heat pump | 20 | ASHRAE HVAC Applications Ch. 38 Table 4 | Combined heating+cooling COP; kW/ton |
| Central air handling unit (built-up or modular) | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | Fan power W/cfm; FEI (90.1-2019+); motor nominal efficiency; economizer present |
| Dedicated outdoor air system (DOAS) unit | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | Fan W/cfm; ERV effectiveness %; EER/IEER if DX |
| Makeup air unit (gas fired) | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | Et (direct or indirect gas) |
| VAV terminal box (with hot water or electric reheat) | 20 | ASHRAE HVAC Applications Ch. 38 Table 4 | n/a; reheat coil MBH or electric kW; min airflow setpoint |
| Fan-powered VAV box (series or parallel) | 20 | Industry / FEMP convention, not a published table | Fan motor type (ECM vs PSC) and watts |
| Fan coil unit (2-pipe or 4-pipe) | 20 | ASHRAE HVAC Applications Ch. 38 Table 4 | Fan motor type (ECM vs PSC); coil MBH |
| Energy recovery ventilator (standalone ERV/HRV) | 20 | ASHRAE HVAC Applications Ch. 38 Table 4 | Sensible and total effectiveness % |
| Exhaust fan (roof upblast, inline or cabinet) | 20 | ASHRAE HVAC Applications Ch. 38 Table 4 | FEI (90.1-2019+); motor hp; control (schedule vs constant) |
| Parking garage exhaust/supply fan with CO control | 20 | ASHRAE HVAC Applications Ch. 38 Table 4 | FEI; motor hp; VFD and CO sensor present |
| Hydronic pump (base-mounted or vertical inline) | 20 | ASHRAE HVAC Applications Ch. 38 Table 4 | Pump energy index PEI (DOE 2020); motor hp and nominal efficiency; VFD present |
| Variable frequency drive | 15 | Industry / FEMP convention, not a published table | n/a (drive ~97% efficient); presence indicates variable-flow control |
| Electric motor (NEMA, on fans and pumps) | 20 | Industry / FEMP convention, not a published table | Nominal efficiency % (NEMA Premium / IE3); hp |
| Gas storage water heater (commercial) | 10 | ASHRAE HVAC Applications Ch. 38 Table 4 | Thermal efficiency % + standby loss (>=75.5 kBtu/h, 90.1 Table 7.8); UEF (<75 kBtu/h) |
| Gas condensing or tankless water heater | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | Thermal efficiency % (95%+) or UEF |
| Electric resistance storage water heater | 12 | ASHRAE HVAC Applications Ch. 38 Table 4 | UEF (<12 kW) or standby loss % per hour (>12 kW) |
| Heat pump water heater | 10 | ASHRAE HVAC Applications Ch. 38 Table 4 | UEF or COP |
| Domestic hot water recirculation pump | 10 | ASHRAE HVAC Applications Ch. 38 Table 4 | Watts; ECM vs PSC; timer or aquastat control |
| Interior LED luminaire (troffer, panel, linear) | 15 | DOE SSL L70 50,000-100,000 h at ~4,000 h/yr; Industry / FEMP convention, not a published table | Efficacy lm/W; input watts; DLC listing |
| Interior fluorescent luminaire, T8/T5 (legacy) | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | Lamp watts x count x ballast factor; T12 magnetic ballast = worst case |
| Exterior and garage luminaire (LED or HID) | 15 | LED 15, HID 10-12 (Industry / FEMP convention, not a published table) | Watts and lm/W; HID (metal halide, HPS) = retrofit candidate |
| Lighting controls (occupancy/daylight sensors, relay panel) | 12 | Industry / FEMP convention, not a published table | n/a; presence indicates Title 24 compliance level |
| Server / IT room (racks) | 5 | Industry / FEMP convention, not a published table (IT refresh cycle) | Rack kW; room PUE if metered |
| Uninterruptible power supply (UPS) | 12 | Industry / FEMP convention, not a published table (batteries 3-5) | Efficiency % at load; eco mode |
| Break-room and kitchen refrigeration | 12 | ASHRAE HVAC Applications Ch. 38 Table 4 | ENERGY STAR kWh/day; age |
| EV charging station | 10 | Industry / FEMP convention, not a published table | kW per port; Level 2 vs DC fast; networked load management |
| Traction elevator (machine room or machine-room-less) | 25 | Florida Housing Estimated Useful Life tables, rev 2024 lists 50 for the shell; controls and drive modernized at ~25 (Industry / FEMP convention, not a published table) | Motor kW; regenerative drive Y/N; standby mode |
| Hydraulic elevator | 25 | Florida Housing Estimated Useful Life tables, rev 2024 (hydraulic 25; industry 20-25) | Motor hp; soft-start |
| Main switchgear / switchboard | 30 | Florida Housing Estimated Useful Life tables, rev 2024 lists 50; IEEE practice 30 | n/a; record service size (amps, volts) as the capacity ceiling for electrification |
| Distribution / lighting panelboard | 30 | Florida Housing Estimated Useful Life tables, rev 2024 | n/a; panel schedule reveals connected loads |
| Dry-type transformer | 30 | Florida Housing Estimated Useful Life tables, rev 2024 | DOE 10 CFR 431 efficiency % at 35% load (2016 rule); kVA |
| Utility electric meter / submeter | 15 | Industry / FEMP convention, not a published table | n/a; ties photos to utility accounts and interval data |
| Gas meter and regulator | 20 | Industry / FEMP convention, not a published table | n/a; ties photos to gas account; absence means all-electric |
| Rooftop PV array and inverter | 25 | NREL module life 25-30; inverter 10-15 (Industry / FEMP convention, not a published table) | kW DC and AC; inverter CEC efficiency %; module efficiency % |
| Emergency generator (diesel or gas) | 25 | Florida Housing Estimated Useful Life tables, rev 2024 | kW rating; fuel; runtime hours on the meter |
| BAS supervisory controller / server | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | n/a; record vendor, protocol (BACnet/IP, LonWorks, proprietary) and software version |
| Field DDC controller (AHU, VAV, plant) | 15 | ASHRAE HVAC Applications Ch. 38 Table 4 | n/a; presence per unit indicates DDC vs pneumatic |
| Thermostat (pneumatic, programmable or smart) | 20 | ASHRAE HVAC Applications Ch. 38 Table 4 | n/a; pneumatic = legacy controls flag |
| Pneumatic control air compressor | 20 | ASHRAE HVAC Applications Ch. 38 Table 4 | n/a; presence means pneumatic controls remain somewhere |
| Windows / curtain wall glazing | 30 | Florida Housing Estimated Useful Life tables, rev 2024 | U-factor; SHGC; visible transmittance (NFRC label) |
| Roof membrane and insulation | 22 | Florida Housing Estimated Useful Life tables, rev 2024 (membrane 20-25) | R-value; solar reflectance (cool roof) |
