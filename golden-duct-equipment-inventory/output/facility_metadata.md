# 360 9th Street: facility metadata

Customer data for the building equipment inventory skill. Everything a Claude needs about this building, apart from the photos and bills, is here. Last updated 30 Sep 2026.

## Folder layout

| Item | What it holds |
|---|---|
| `Photos/` | 79 equipment and building photos from the 30 Sep 2026 walk-through (HEIC and JPEG). File names are the phone's IMG numbers, which the inventory CSV and photo notes cite |
| `Utility Bills/` | 14 PG&E statements, Jan 2025 to Feb 2026, plus a CleanPowerSF bill explainer |
| `facility_metadata.md` | This file |
| `Outputs/` | The finished run: inventory CSV, evaluation report, photo notes, bill extraction, public-records research, lookup results |

## Building

| Field | Value | Source |
|---|---|---|
| Name | Watershed HQ | Watershed |
| Address | 360 9th Street, San Francisco, CA 94103. One parcel with 350 9th St (block 3519, lot 005) | SF Assessor, DataSF parcels |
| Building type | Office (benchmarking category); Assessor use Commercial Office | SF benchmarking, Assessor |
| Climate | ASHRAE zone 3C (marine); California Title 24 climate zone 3 | Standard maps for San Francisco |
| Year built | 1920. Seismic upgrade, reroof and full HVAC replacement 2013; kitchen added 2014 | Assessor, DBI permits |
| Stories | 4 | Assessor, permits, confirmed by Robbie |
| Floor area | 23,200 sq ft (use this). Assessor says 21,500; benchmark filings 22,800 | Watershed records |
| Construction | Masonry exterior walls, heavy timber and concrete interior, steel braced frames (2013), spray-foam roof, single-pane steel-sash windows | Permits, photos |
| Ownership | Treated as owner-occupied: replacement decisions and capital sit with Watershed | Confirmed by Robbie |
| ENERGY STAR score | 58 (2025 filing), 64 (2024) | SF benchmarking |

## Floors and meters

- Floor 1 is the main (ground) floor.
- Electric: 5 PG&E meters. Units 1-4 are floors 1-4 (confirmed by Robbie), plus a House meter for common areas. Rate B-6 time-of-use, CleanPowerSF generation, no demand charge, no solar.
- Gas: 1 PG&E natural gas meter (the House account). No propane on site.
- All meters are on Watershed's PG&E account, so the bills cover the whole building.

## Facts confirmed on site (by Robbie)

- Gas furnace GD-FURN-01 (Carrier 59SC5) is on floor 1.
- Gas furnace GD-FURN-02 (Carrier, marked "Floor #2-A") is on floor 2 (photos IMG_2880, IMG_2881).
- The HTP Phoenix water heater (GD-WH-01) is on floor 2, in the closet by the men's restroom.

## Still to collect on site

1. The 3rd furnace (probably marked 2-B, near the 2-A unit on floor 2) and a possible 4th listed on the 2013 permit.
2. The rating plate inside the 2-A furnace door.
3. Whether the rooftop units have working economizers (outside-air hoods).
4. Nameplates on the two roof Rheem tankless water heaters and the HTP Phoenix size.
5. Which HVAC unit serves which floor.
