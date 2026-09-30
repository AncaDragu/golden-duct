# Photo-to-equipment-inventory: prior art scan

Question: does anything exist that would process ~75 phone photos of building mechanical/electrical gear better than a general Claude vision model alone? Scanned 30 Sep 2026.

Short answer: no off-the-shelf product exposes photo-to-inventory as an API we could call in a hackathon. The commercial tools that do this (ServiceTrade, ServiceTitan, XOi, AkitaBox, MaintainX, Equipment Tracker Pro) are all mobile-app features on top of a general multimodal LLM (Equipment Tracker Pro says Gemini outright). The value they add is not the vision model, it is the reference data behind it: serial-date rules, model-to-efficiency lookups, and life tables. Those are what to bolt on.

## 1. Commercial products

| Product | What it does | Access / pricing | Verdict |
|---|---|---|---|
| [ServiceTrade Smart Scan](https://servicetrade.com/products/servicetrade-platform/features/smart-ai-for-service-contractors/) | Nameplate photo to make/model/serial, creates asset record. Launched Nov 2025 | Included in platform, from $199/mo. No public API for the scan itself | App feature, not a service. Skip |
| [ServiceTitan Nameplate Scan](https://help.servicetitan.com/docs/track-and-manage-installed-equipment) | Same: photo fills manufacturer, model, serial | Enterprise FSM, no standalone access | Skip |
| [XOi](https://xoi.io/how-xoi-helps/hvac/) | Dataplate OCR plus enrichment (capacity, refrigerant, efficiency, age) from its own equipment database | Contractor SaaS, no public API or pricing | Closest to what we want. Enrichment DB is proprietary. Skip for hackathon |
| [AkitaBox Capture](https://home.akitabox.com/software/ai/) | FCA tool: nameplate OCR fills type/make/model/serial, pins asset to floor plan | Demo-only pricing, no API | Skip |
| [MaintainX Assist](https://help.getmaintainx.com/create-an-asset) | Create asset from nameplate photo | Enterprise plan only | Skip |
| [UpKeep](https://upkeep.com/upkeep-ai/) | Photo-to-Part (parts, not equipment) | Not asset-level | Skip |
| [Facilio](https://facilio.com/), [Brightly](https://facilio.com/blog/best-brightly-alternatives/), Building Engines, Hippo (sunset into Eptura) | Agentic work-order AI, copilots. No nameplate capture found | n/a | Skip |
| [Equipment Tracker Pro](https://equipment-tracker.com/) | Gemini-based nameplate scan, estimates age from serial format | Free tier, Pro $9.99/mo, no API | Proof that a general LLM is the industry baseline. Skip |
| [Tag Wizard](https://tagwizard.ai/asset-equipment-tracking-mechanical-room-and-beyond/) | Nameplate to structured record incl. refrigerant charge, condition photos | Pricing and API not published | Skip |
| [FOScore](https://www.foscd.com/foscore) | FCA software, AI reads label photo | Enterprise | Skip |
| Measurabl, BlocPower, Carbon Lighthouse | Utility data, sensors, ESG reporting. No photo capture found | n/a | Not relevant |
| [DOE/PNNL Building Energy Asset Score API](https://buildingenergyscore.energy.gov/reports/api) | Takes an asset inventory as input, returns a score. Does not read photos | Free, token by email to asset.score@pnnl.gov | Downstream consumer, not a photo tool |
| [Building Intelligence Center](https://www.building-center.org/) | Serial-to-age reference site (see section 3) | $15/yr | Reference, not CV |

Home-service apps (Housecall Pro, Jobber) have no nameplate AI.

## 2. Open-source CV

| Tool | Notes | Verdict |
|---|---|---|
| [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) (PP-OCRv5/v6, PaddleOCR-VL 1.6) | Best general scene-text OCR in recent benchmarks, strong on stamped/embossed and low-contrast text. pip install, CPU ok | Worth a second-pass on nameplate crops for serial/model verification |
| [Surya](https://github.com/datalab-to/surya) | 650M-param OCR, document-oriented, GPU preferred | Weaker on scene text than Paddle. Optional |
| [docTR](https://github.com/mindee/doctr) | Document OCR, easy API | Document-tuned, not nameplates. Skip |
| Tesseract | Poor on curved, glare, dot-matrix plates | Skip |
| [Florence-2](https://huggingface.co/microsoft/Florence-2-large) | Vision model with OCR-with-region task, 0.8B | Fine, but Claude already does this better |
| [Roboflow: nameplate datasets](https://universe.roboflow.com/search?q=class%3Anameplate), [HVAC class search](https://universe.roboflow.com/search?q=class:hvac) | Small hobby datasets (HVAC_EQ has 27 images with chiller/AHU/cooling tower classes). Roboflow blocks non-browser fetch, so counts unverified | Too small to train on. Skip |
| [Equipment Nameplate Dataset](https://github.com/zhangzhengfu/EquipmentNameplateDataset) (IEEE 2019) | Industrial nameplate scene-text dataset, Baidu Pan download, no licence stated | Useful only for eval, hard to download. Skip |
| [motor-nameplate](https://huggingface.co/datasets/sergiudanstan/motor-nameplate) (HF, MIT) | 286 motor nameplate images with structured fields (make, model, serial, HP, RPM, volts) | Good free eval set for the motor/pump subset. Use for a quick accuracy check |

Nothing trained specifically on building HVAC nameplates is public. No published benchmark of Claude vs dedicated OCR on nameplates; general OCR comparisons show frontier LLMs at or above PaddleOCR-VL on field extraction, with Claude having the lowest hallucination rate.

## 3. Serial number decoding

| Source | Coverage | Licence / access | Verdict |
|---|---|---|---|
| [Inspector Handbook](https://inspectorhandbook.com/) | 41 HVAC brands, 2 water heater brands. Rules as prose plus worked examples | CC BY 4.0, stated on every page. No JSON or API | Best free source. Hand-encode top 15 brands into a table |
| [Building Intelligence Center](https://www.building-center.org/) | Broadest: residential and commercial HVAC, boilers, water heaters, RTUs, PTACs, includes Lochinvar, Raypak, AO Smith, Bradford White, Mitsubishi, Daikin/McQuay | $15/yr Platinum, $50/yr for 5+ seats. [Terms](https://www.building-center.org/terms-of-use/) say CC-BY-SA/GFDL but also "should not be relied upon for commercial use". No API, ad-heavy pages | Use to cross-check commercial brands; do not scrape into a product |
| [HVAC Decoder Pro](https://www.hvacserialnumber.com/en), [hvacbase.org](https://www.hvacbase.org/hvac-serial-number-decoder), [decodemyitem.com](https://www.decodemyitem.com/decoder-tool) | Free web decoders, mostly residential brands | No API, no licence, unknown accuracy | Skip |
| Manufacturer warranty lookups ([Carrier](https://www.carrier.com/residential/en/us/warranty-lookup/), [Trane](https://www.trane.com/residential/homeowner-product-support/)) | Serial in, ship/registration date out | Web forms, residential, no API | Manual spot-check only |
| GitHub | No maintained open-source decoder found | n/a | Build our own |

Rules for the big commercial brands are simple (Carrier/Bryant/ICP: 4-digit week+year prefix; Trane: year letter or digits in positions 1-2; York/JCI: letter-coded month and year; Lennox: 2-digit year in positions 3-4; Rheem/Ruud: 4-digit prefix; AO Smith and Bradford White: letter-coded year plus month). Encoding 15 brands from Inspector Handbook is a two-hour task and removes the main hallucination risk in the install-year field.

## 4. Model number to efficiency

| Source | Coverage | Access | Verdict |
|---|---|---|---|
| [ENERGY STAR data.energystar.gov](https://www.energystar.gov/productfinder/advanced) | Light Commercial HVAC (`e4mh-a2u3`, 12.5k rows, EER2/SEER2/IEER), Commercial Boilers (`3393-mxju`), Commercial Water Heaters (`xmq6-bm79`), plus residential sets | Free Socrata SODA API, verified live: `https://data.energystar.gov/resource/e4mh-a2u3.json?$limit=1`. No key needed at low volume | Use. Model numbers contain wildcards (`N5A4S36*L*NAA*`), so match with a wildcard-aware regex |
| [AHRI Directory](https://www.ahrinet.org/certification/license-ahri-directory-data) | The definitive source for unitary, chillers, boilers, water heaters | Public site caps exports at 250 records and [terms](https://ahridirectory.org/terms) forbid use in software. Paid subscription with Unitary and Heating APIs as add-ons, NET-30 onboarding | Paywalled. Manual lookups only for the hackathon |
| [DOE CCMS Compliance Certification Database](https://www.regulations.doe.gov/certification-data/) | All federally covered products incl. commercial package AC, boilers, water heaters, motors, minimum-efficiency certification data | Free, CSV export per product group via web search. No documented API. Site blocks scripted fetch, so not verified beyond the landing page | Fallback for models absent from ENERGY STAR (non-certified units are the majority in an older building) |
| [CEC MAEDbS](https://cacertappliances.energy.ca.gov/Pages/Search/AdvancedSearch.aspx) | Title 20 California-legal appliances, includes commercial HVAC and water heating | Free, Excel/CSV export from the search UI, no API | Relevant for SF, but manual export only |

Expect low hit rates: chillers, cooling towers, AHUs, pumps and switchgear do not appear in ENERGY STAR at all. For those the nameplate itself (kW, tons, EER, full-load amps) is the efficiency source.

## 5. Useful-life references

| Source | Access | Verdict |
|---|---|---|
| [ASHRAE Service Life and Maintenance Cost Database](https://costdatabase.ashrae.org/) | Free, no login. [Full service life dataset as Excel](https://costdatabase.ashrae.org/download.asp). Provided "as is", no licence restriction stated | Use. Also the median-life table in ASHRAE Handbook Applications ch. 38 (paywalled, but widely reproduced, e.g. [this chart](https://www.naturalhandyman.com/iip/infhvac/ASHRAE_Chart_HVAC_Life_Expectancy.pdf)) |
| [CPUC DEER EUL tables](https://cedars.cpuc.ca.gov/deer-resources/deer-versions/2020/) | Free via READI tool download. California-specific effective useful life by measure | Good second source for an SF building |
| [BOMA Preventive Maintenance Guidebook](https://www.boma.org/BOMA/BOMA/Research-Resources/Publication_Pages/Preventive%20Maintenance%20Guidebook.aspx) | Paid PDF, life appendix reproduced in [this excerpt](https://icap.sustainability.illinois.edu/files/projectupdate/2289/Project%20Lifespan%20Estimates.pdf) | Cite, do not buy |
| NREL | No standalone useful-life table found; NREL work cites ASHRAE | Skip |

## Recommendation

Nothing here beats Claude vision at the photo step, and nothing exposes an API we could call in a hackathon. What complements it is reference data. Suggested pipeline:

1. **Claude vision, per photo, structured output.** Equipment type, make, model, serial, nameplate fields (volts, amps, kW, tons, MBH, refrigerant, EER/thermal efficiency if printed), condition notes, and a confidence per field. Ask it to transcribe the serial character by character and flag ambiguous glyphs (0/O, 1/I, 5/S, 8/B).
2. **Optional PaddleOCR pass on the nameplate crop.** Only where Claude reports low confidence on serial or model. Agreement between the two raises confidence; disagreement gets a human flag. Cheap to add, skip if time is short.
3. **Serial decoder table.** Hand-encoded rules for ~15 brands from Inspector Handbook (CC BY 4.0), returning manufacture month/year plus the rule used, so the output is auditable. Do not let the LLM guess dates.
4. **Efficiency lookup.** ENERGY STAR SODA API by brand plus wildcard model match, three datasets (light commercial HVAC, commercial boilers, commercial water heaters). Fall back to nameplate values, then to code-minimum for the install year.
5. **Life lookup.** ASHRAE service life Excel keyed by equipment type, DEER as a cross-check. Remaining life = median life minus (2026 minus manufacture year).
6. **Dedupe across the 75 photos** by serial, then by make+model+location caption, since one unit often appears in several shots.

Gaps to state in the demo: AHRI is the real efficiency source and is paywalled; most equipment in a 1980s-2000s office will not be in ENERGY STAR; serial rules for smaller commercial brands are unverified.
