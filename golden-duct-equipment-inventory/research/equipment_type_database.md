# Equipment type reference database for photo classification

**Date:** 2026-09-30
**Deliverable:** `equipment_types_starter.csv` (64 rows) in this folder.
**Scope:** what a phone-photo agent will meet in a 5-story San Francisco office, and the vocabulary to label it with.

## What the repo already has

- `research/energy-lever-taxonomy.md` and `research/intervention-database/`: intervention vocabulary (Replace / Add / Retrofit, end-use categories A-K). The CSV `category` column lines up with its end uses (Space Heating, Space Cooling, Ventilation & Air Distribution, Water Heating, Lighting, Controls, Envelope, Motors & Drives) so a classified photo can be joined to a lever.
- `research/past/Building Equipment List & Decarb Lever Library.xlsx`, tab `Equipment List_Rev 2`: 48 BAU/ALT equipment names (RTU, Split, PTAC, Chiller, AHU, FCU, ERV/HRV, DOAS, boilers, water heaters, LED, BAS, solar). The CSV reuses those names where they exist and splits them only where a photo can tell the difference (condensing vs non-condensing boiler, VRF outdoor vs indoor).
- `datasets_research/ashrae_equipment/fetch_ashrae.py`: 63 ASHRAE median service lives (HVAC Applications Handbook, Owning and Operating Costs chapter). Every HVAC row in the CSV cites it. ASHRAE has no rows for lighting, elevators, electrical gear or envelope, so those use the Florida Housing Estimated Useful Life tables (2024) or a stated industry convention.
- `research/intervention-reference.md`: kW/ton, W/cfm and Et conventions used in savings maths. The CSV `typical_efficiency_metric` column uses the same units so nameplate readings flow into that model.

## Public sources reviewed

| Source | What it gives us | Verdict |
|---|---|---|
| Brick Schema 1.4 (BSD-3, cloned from GitHub) | 193 HVAC equipment classes plus Elevator, Transformer, Switchgear, Breaker_Panel, Meter, PV_Panel, Luminaire, Water_Heater, VFD, Controller | Best class hierarchy for "what object is this" |
| BuildingSync 2.x (BSD-style, cloned) | Audit-record schema: YearInstalled, YearOfManufacture, Manufacturer, ModelNumber, SerialNumber, EquipmentCondition (Excellent/Good/Average/Poor), AnnualCoolingEfficiencyUnits (COP, EER, SEER, kW/ton), AnnualHeatingEfficiencyUnits (COP, AFUE, HSPF, Thermal Efficiency), ConveyanceSystem (Elevator, Escalator) | Best attribute schema; it is the XML form of BEDES |
| BEDES (LBNL) | The term dictionary BuildingSync implements | Site returned 404 during this research; terms taken via BuildingSync |
| DOE Asset Score | 19 HVAC system types (PSZ, PVAV, VAV with reheat, DOAS, PTAC, WLHP, VRF, fan coil, baseboard) | System-level, not object-level; used for the mapping below |
| NREL ComStock | Same system vocabulary; medium office floor-area shares: PSZ-AC with gas heat 26%, PVAV gas boiler reheat 10%, PVAV with PFP boxes 9%, VAV chiller with gas boiler reheat 7%, PVAV gas heat electric reheat 5%, VAV air-cooled chiller 4%, PSZ-HP 3%, PTAC 3% (NREL 86602) | Prior for what to expect; feeds `baseline_creation` |
| ASHRAE 90.1-2022 Tables 6.8.1 and 7.8 | Metric by equipment class and size: SEER2/EER2 below 65 kBtu/h, EER/IEER above, kW/ton + IPLV for chillers, Et/Ec for boilers, UEF vs thermal efficiency + standby loss for water heaters, gpm/hp for towers, FEI for fans | Used for `typical_efficiency_metric` |
| ENERGY STAR | Commercial boilers (>=300 kBtu/h), commercial water heaters, light commercial HVAC, ductless; Product Finder API lists certified models | Useful for looking up a model number once read |
| Project Haystack | Tags (ahu, rtu, vav, chiller, boiler, coolingTower) | Same objects as Brick, terser names; Brick publishes the mapping |
| Manufacturers | Carrier, Trane, Daikin, York/JCI, Lennox, Aaon, Greenheck, Mitsubishi, AO Smith, Lochinvar | Serial formats encode manufacture date; public decoders exist (building-center.org, not verified here) |

## Recommendation: Brick for the type, BuildingSync/BEDES for the record

Use a flat list of about 60 photographable types (the CSV) as the agent's label set, with each label pinned to a **Brick 1.4 class** as its canonical identity, and store the filled record in **BuildingSync field names**.

Why Brick for the type:
- It is a class hierarchy of physical objects, one name per thing, which is what a photo shows. BEDES/BuildingSync describe systems (heating plant, cooling source, delivery) and you cannot see a "delivery type" in a picture.
- Coverage spans HVAC, electrical, lighting, elevators, PV, meters and controls in one namespace. BSD-licensed, machine-readable (Turtle/OWL), maps to Haystack, and the parent classes let the agent fall back (Chiller when it cannot tell Centrifugal from Screw).

Why BuildingSync for the record:
- The hackathon's output fields (make, model, serial, install year, condition, efficiency) exist there already, including the condition enumeration and the efficiency-unit enumerations. Emitting BuildingSync XML also makes the output readable by Asset Score and Audit Template for free.

Brick gaps to patch with BuildingSync names (flagged in `brick_or_bedes_class`): furnace, generator, UPS, refrigeration, windows, roof, escalator. Do not use ComStock or Asset Score types as labels; use them as a derived field: RTU + VAV boxes = PVAV; chiller + boiler + AHU + VAV boxes = VAV chiller with gas boiler reheat; VRF outdoor + DOAS = DOAS with VRF; WSHP units + fluid cooler + boiler = water-loop heat pump.

## Notes for the fill step

- **Install year is rarely on the nameplate.** The serial number encodes manufacture date for nearly every HVAC and water-heater brand (Carrier WWYY prefix, Trane letter-year, AO Smith YYWW, Lennox YYMM). Install year is manufacture year plus zero to two. Elevators carry a state permit with an inspection date, and the controller nameplate carries the modernization year.
- **Two photos per asset:** one wide shot for type and location, one nameplate close-up. Most classification errors are subtype-level (RTU vs RTU-HP vs air-cooled chiller vs VRF outdoor; condensing vs non-condensing boiler; WSHP vs FCU vs VAV box), and the cue that resolves them is usually piping, flue material or the model number, not the cabinet shape. The CSV `visual_identifiers` column lists those cues.
- **Condition** uses the BuildingSync four-level scale plus age against `typical_useful_life_years`; do not invent a percent.
- **Energy significance** is for a typical office; n/a for meters and switchgear, which are photographed to tie the building to its bills and electrical capacity.

## Reference photos: worth it, narrowly. Yes for a 15-type cue sheet, no for a dataset

**Yes** to a curated few-shot cue sheet: 3-5 labelled photos plus one line of distinguishing cues for the roughly 15 visually confusable types listed above. Effort is one to two person-days. Put them in the prompt or a retrieval index; the model then compares, rather than recalls.

**No** to building or buying a training dataset:
- Current vision-language models already recognise common HVAC objects; the residual errors are subtype and nameplate reading, which a classifier trained on cabinet photos does not fix. OCR quality and serial decoding matter more.
- Roboflow Universe coverage is thin: the `HVAC_EQ` set has 27 images across 20 classes; the larger "chiller" and "boiler" hits are industrial or fault-detection sets. Licences are set per uploader, with documented cases of CC BY-NC data re-uploaded as CC BY, so provenance needs checking image by image.
- Wikimedia Commons is CC BY-SA or CC0, fine for internal reference with attribution, but commercial rooftop and plant-room coverage is sparse.
- Manufacturer photos and spec sheets are copyrighted. Internal few-shot use is defensible; shipping them in a customer-facing product needs permission. Spec sheets stay the right source for text (capacity and efficiency by model number), which the ENERGY STAR Product Finder and AHRI directory also give under open terms.

Better use of the same effort: photograph the hackathon building properly (both shots per asset) and label it. Sixty real SF-office photos beat 600 scraped ones for this task.

## Caveats

- BEDES and the BuildingSync docs site returned 404 on the day; enumerations came from the cloned schema.
- Useful lives for condensing boilers, heat pump water heaters, VFDs, LED fixtures, meters and IT are industry conventions, flagged in `useful_life_source`.
- Manufacturer lists are North American incumbents by category, not market-share verified.
