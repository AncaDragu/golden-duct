# How photos become rows in `equipment_inventory.csv`

These rules turned 77 photos of 360 9th St into 27 inventory rows. They are written so the Watershed agent skill can apply them the same way next time.

## 1. What counts as a row

- **One row per parent piece of equipment.** A rooftop unit is one row. Its fans, compressor and filters are not.
- **Distribution, fittings and labels are not rows.** Duct fittings, grease-duct section tags (P2, P4, P11), disconnect switches and refrigerant lines appear only in the notes of the unit they serve.
- **Systems of many small items get one row.** Lighting and thermostats get one system row each, with the count in the notes. They are not listed fixture by fixture.
- **Items dropped as not energy-relevant:** the antenna mast, security panels, the portable air purifier and the Bevi water dispenser. The IT rack is also dropped: it is a small 24/7 load, and it belongs in the utility analysis, not the inventory.

## 2. De-duplicating photos

Several photos often show the same unit. They merge into one row in this order:

1. **Same serial number** means the same unit. Sequential serials (4812E04427 and 4812E04428) are separate units.
2. **Same make and model, no serial:** merge only if the photos are seconds apart and the surroundings match.
3. **Overview shots** (roof panoramas) are used for counting and condition only. They never create a row on their own.
4. **Duplicate uploads** (the same image as .jpeg and .HEIC) are skipped.

## 3. Evidence level (`evidence_level`)

| Level | Meaning | Example |
|---|---|---|
| nameplate | Make, model and serial read from a photographed plate | Carrier RTUs |
| visual | Unit photographed, but no readable plate | Rheem tankless heaters |
| permit | Not photographed; an SF building permit says it exists | 3 of the 4 furnaces |
| inferred | Not photographed; implied indirectly | Ice machine, from a Hoshizaki filter |

`confidence` (High / Medium / Low) is the reviewer's view that the unit exists as described. It is separate from the evidence level.

## 4. Field rules

| Field | Rule |
|---|---|
| equipment_id | `GD-<type code>-<nn>`. Type codes: RTU, CU (condensing unit), FURN, WH, KEF (kitchen exhaust fan), MUA (make-up air), HOOD, OVEN, REF, DW, ICE, ELEV, LTG, CTRL, ELEC |
| equipment_type | Plain name matched to `research/equipment_types_starter.csv`, which maps to Brick classes (a standard building-equipment naming scheme) |
| make / model / serial | Transcribed exactly as printed. Unreadable characters are marked "partly faded". Nothing is guessed |
| install_year | In priority order: printed date of manufacture, then the serial decode, then a matching SF permit date. `install_year_basis` says which one was used |
| serial decode | Carrier, Bryant and ICP serials start with week then year (0813 = week 8 of 2013). Other brands use the rules in `research/cv_prior_art.md`, section 3 |
| useful_life_years | ASHRAE median service life, taken from the reference CSV so every unit of a type gets the same number |
| remaining_life_years | install year + useful life − 2026. A negative number means past median life |
| condition | A visual judgement from the photos only, on the outside of the unit. **Good**: no visible defects. **Fair**: cosmetic wear only (surface rust on guards or brackets, faded labels, overspray). **Poor**: damage that cuts performance (corroded coil fins, torn refrigerant-line insulation, missing panels, leaks). "Unknown" if not photographed. Age is not used. It says nothing about compressors, heat exchangers or controls, which need a technician. `condition_basis` says what was seen |
| nameplate_efficiency | Only what is printed on the plate or an EnergyGuide label. Series ratings (for example "13 SEER") are allowed but labelled as series ratings in `efficiency_basis` |
| primary_fuel | One of Natural gas, Electricity, Propane, Fuel oil, None, Unknown. Equipment that burns a fuel is listed under that fuel even if fans or controls run on electricity, because the burned fuel is what electrification replaces. `fuel_detail` records the secondary fuel |
| energy_significance | High for heating, cooling, ventilation, their controls, water heating and lighting (together these drive most of both bills); Medium for the kitchen exhaust fan and cooking; Low for everything else |
| photos | Relative paths under `photos/raw/`, separated by semicolons, best nameplate shot first |

## 5. What the model is not allowed to do

- It may not invent a model or serial from a unit's appearance.
- It may not turn a series rating into a nameplate rating.
- It may not count an overview-photo unit as new when it could be a unit already listed.
- It may not fill install year from "looks about 10 years old".

## 6. Known limits of this pass

- **No location data.** Photo GPS altitude was too noisy to tell floors apart, so floor locations come only from labels ("2nd floor").
- **Only one of four furnaces was photographed.** Two more indoor units must exist because each roof condenser needs one. The fourth rests on the 2013 permit alone. None of the three has a nameplate efficiency, because nothing was photographed to read.
- **Efficiency is not yet cross-checked against a public database.** The ENERGY STAR API (free) and AHRI (the industry certification directory, paywalled) would be the next step.
