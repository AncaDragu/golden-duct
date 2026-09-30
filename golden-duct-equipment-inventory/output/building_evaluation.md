# 360 9th Street: what's in the building

Watershed HQ, San Francisco. Based on 79 photos taken 30 Sep 2026, 14 months of PG&E bills (Jan 2025 to Feb 2026), and public city records. It is written for sustainability decisions, and a facilities lead should check it before it is used.

The report covers the equipment that drives the energy bills: heating, cooling, ventilation, water heating, lighting and HVAC controls. Everything else is listed once at the end as low priority.

## Bottom line

- **The building runs on small, gas-heated, rooftop-cooled units, and most are near median life.** Five of the seven cooling units have 2012–2013 manufacture dates that match a Feb 2013 permit to replace all the HVAC. A sixth dates from 2014 and the seventh from 2024. The six older units reach median service life (a statistical midpoint, not a failure date) in 2028–2029. The one furnace found reaches it in 2031.
- **Replacement timing is the decision that matters.** Replacing each unit with a heat pump at end of life removes about 80% of the building's gas use at little extra cost. Replacing like-for-like locks in gas for another 15 years. One rooftop unit is a 2024 gas unit. It looks like a like-for-like replacement, but no permit for it was found.
- **Electricity is two-thirds of the energy and about 90% of the cost.** The building uses 172,754 kWh and 2,992 therms a year, about $80k before one-off credits. Site energy is about 38 kBtu per sq ft on 23,200 sq ft. This matches the city benchmarking filing to within 1%.
- **The envelope is a 1920 masonry loft with single-pane steel windows and a foam roof.** Insulation is only likely in the roof. In San Francisco's mild climate this affects comfort more than the energy bill.

## Building at a glance

| Item | Value | Source |
|---|---|---|
| Built | 1920. Seismic upgrade, reroof and full HVAC replacement 2013. Kitchen added 2014 | SF Assessor, DBI permits |
| Size | 23,200 sq ft (Watershed records; Assessor says 21,500, benchmark filings 22,800) | Watershed |
| Stories | 4. Floor 1 is the main (ground) floor | Assessor, permits, confirmed |
| Ownership | Treated as owner-occupied, so replacement decisions and capital sit with Watershed | Confirmed |
| ENERGY STAR score | 58 (2025 filing), 64 (2024) | SF benchmarking |
| Meters | 5 electric (Units 1–4 = floors 1–4, plus House) and 1 gas, all on Watershed's PG&E account | Bills, photos, confirmed |
| Rate | PG&E B-6 time-of-use with CleanPowerSF generation. No demand charge. No solar | Bills |

## Energy use

| | Annual | Share of site energy | Pattern |
|---|---|---|---|
| Electricity | 172,754 kWh ($80.3k before credits) | 66% | Fairly flat. A mild bump in Sep–Oct. Units 3 and 4 rise in summer, which is cooling |
| Gas | 2,992 therms ($7.4k) | 34% | Strongly seasonal: 540–690 therms per winter month, 30–80 per summer month |

- **Gas is mostly space heating.** The summer base of about 50 therms a month is water heating and cooking, so roughly 2,400 therms (80%) goes to heating.
- **Electricity is mostly base load**: lighting, plug loads, IT, kitchen and ventilation fans. Cooling looks like a small share, under 10%, which is normal for San Francisco.
- **Electricity costs about $0.46 per kWh and gas about $2.46 per therm.** Switching heat to heat pumps would add roughly 18 MWh a year (about +10% electricity). At today's prices it would cost a few thousand dollars a year more to run than gas. The case rests on emissions and end-of-life timing, not operating savings.
- **Floor 2 uses the most electricity (29%).** Floors 3 and 4 show the summer cooling rise.

## High-impact equipment

Full detail: `equipment_inventory.csv` (27 rows, including a `primary_fuel` column). Counting and condition rules: `csv_criteria.md`. Condition is a visual judgement from the outside of each unit, not a technician's test.

| System | Fuel | Count | What it is | Age / end of life | Confidence |
|---|---|---|---|---|---|
| Rooftop packaged units (gas heat, AC) | Gas heat, electric cooling | 4 | Carrier WeatherMaker 48ES ×3 (2013) and ICP PGD4 ×1 (2024). About 5 tons each. Cooling EER about 11, gas heat 81–82% efficient | 2013 units: median life 2028. 2024 unit: 2039 | High (nameplates) |
| Split-system AC condensers (roof) | Electric | 3 | Carrier 24ABB3, 5 tons, 13 SEER. Two from Nov 2012 (corroded coils, rated Poor), one from Jul 2014 | Median life 2028–2029 | High (nameplates) |
| Gas furnaces (indoor halves of the split systems) | Gas | 2 found, 3 certain, 4 per permit | Floor 1: Carrier 59SC5, 120k Btu/h, 95.5% AFUE, Jan 2013. Floor 2 (marked 2-A): Carrier condensing furnace with a 5-ton cooling coil, rating plate not photographed. A 3rd must exist because each roof condenser needs an indoor unit, probably a 2-B beside it. A 4th is on the 2013 permit only | 2031 | 2 photographed, 1 high (physically required), 1 low (permit only) |
| Water heaters | Gas | 3 | HTP Phoenix condensing tank (floor 2 closet, size not read) and 2 Rheem Prestige outdoor tankless units (roof, ENERGY STAR) | Phoenix about 2029. Rheem ages unknown | Medium (no nameplates read) |
| Lighting | Electric | 1 system, ~120 fixtures | Linear pendants, likely LED. Some have end-cap sensors | Installed 2013 | Medium |
| HVAC controls | n/a | Standalone thermostats | Emerson programmable, set to 72 F cooling. No building automation system seen | n/a | Medium |

**Cooling totals about 34 tons, roughly 670 sq ft per ton**, which is typical for an office. All space heating is gas: about 435k Btu/h in the rooftop units, plus the furnaces.

**Why only one furnace has an efficiency:** efficiency comes only from a rating plate or EnergyGuide label. The floor 2 furnace's plate is behind the door and the other two were not found. Its plastic vent pipe means it is a condensing furnace (90% or higher). If they match the floor 1 unit, expect about 95%, unverified.

## What this means for upgrade decisions

1. **The HVAC replacement window is now.** RTU-01 to 03 and CU-01 to 02 reach median life in 2028, and the two older condensers already have corroded coils. A heat-pump rooftop unit and a heat-pump split system are drop-in replacements at this size. Decide the replacement spec before a unit fails, because emergency replacements default to like-for-like gas.
2. **Water heating is the second gas load.** It is three small units, so a heat pump water heater swap is simple on paper. The rooftop tankless pair is the easier candidate: outdoor, no tank space needed indoors.
3. **Controls are a low-cost lever now.** Standalone thermostats per zone mean schedules and setpoints are set unit by unit. Smart thermostats or a light building automation system (central scheduling) would catch after-hours running.
4. **Lighting is the largest electric lever to confirm.** Electricity is 90% of cost and mostly base load. If the pendants are already LED, the remaining lever is controls (occupancy and daylight sensors).

## Envelope and insulation

| Element | What we can tell | Confidence |
|---|---|---|
| Walls | 1920 masonry and board-formed concrete, exposed inside. No insulation visible. Likely uninsulated | Medium-high |
| Windows | Steel-sash industrial windows, single-pane clear glass, no thermal break (photos 2806, 2879). Front windows on floors 1–2 were replaced in 2003 with bronze aluminium frames; glazing type unknown | High for the steel sash |
| Roof | Spray polyurethane foam with a white reflective coating. The foam itself insulates (about R-6 per inch), but the thickness is unknown. Reroofed 2013 | Medium |
| Ducts and lines | Rooftop ducts are foam-encased (insulated). Interior ducts are bare but inside heated space. Roof refrigerant-line insulation is torn in places | High |

About 2,400 therms a year for heating works out to about 10 kBtu per sq ft. That is moderate for an old masonry building here, so heat loss is not extreme. Window work is a comfort measure first and an energy measure second.

## What to validate

A facilities lead should confirm these before the inventory is final, ranked by effect on the upgrade case. All are high-impact.

1. **The 3rd furnace, and the possible 4th:** location, rating plate, and whether each is a gas furnace or an electric air handler. The floor 2 unit is marked 2-A and Panel A has a second A/C circuit, so look for a 2-B nearby. Also photograph the rating plate inside the 2-A furnace door.
2. **Rooftop unit ventilation:** whether they have economizers (free cooling from outside air) and whether those work. A big lever in San Francisco that photos can't show.
3. **Which HVAC unit serves which floor.** Meters map to floors, so this ties equipment to bills.
4. **Water heater nameplates:** Rheem tankless side labels (model, date, efficiency) and HTP Phoenix size.
5. **Lighting:** LED confirmed, fixture count and controls.
6. **RTU-04 (2024):** whether it replaced a 2013 unit or was added, and why it is gas.

**Low priority (not needed for the upgrade case):** kitchen hood, exhaust fan and possible make-up air unit; oven fuel; refrigerator, dishwasher and ice machine; elevator drive type; electrical panels.

## Sources

- Photo log: `photo_notes.md`
- Bills: `utility_bills_extracted.csv`, `utility_bills_summary.md`
- Permits and benchmarking: `../research/building_history.md`
- Useful lives: `../research/equipment_types_starter.csv` (ASHRAE medians)
