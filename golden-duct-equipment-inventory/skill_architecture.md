# Building equipment inventory skill: architecture

For the engineering team deciding how to run this in the Watershed agent.

## What ships

One file: `SKILL.md` (about 23k tokens).

- Sections 0-9: the workflow. Inputs, facility metadata, public-records research, photos to rows, the CSV schema, serial decoding, efficiency lookup, bills, report, and the fixed six-bullet reply.
- Appendix A: 303 serial-number date rules across 147 brands, some reaching back to 1940, plus 35 brands that put no date in the serial. The model applies them by reading the table.
- Appendix B: median service life for 64 equipment types (ASHRAE medians first).

The efficiency lookup is written as instructions: the ENERGY STAR dataset ids and query shape, the DOE certification database, manufacturer spec sheets, and the California archive. The agent needs web access to use it.

## Open decision: model-applied or code-applied decoding

| | Model reads the appendix (current) | Agent runs the Python decoder |
|---|---|---|
| Files to ship | 1 | SKILL.md plus the decoder, the lookup and 2 CSVs |
| Needs code execution | No | Yes |
| Reliability | A blind test decoded 12 of 12 known serials the same as the code, using only the file. Ties it cannot break are flagged, not guessed | Deterministic; 887 tests pass |
| Efficiency lookups | Web fetches each run | Cached, free on rerun |

If the agent can run Python, the code path is more reliable. The appendix stays in the file either way as the fallback.

## Source of truth (in this repo, not shipped)

| File | Role |
|---|---|
| `code/skill_body.md` | Sections 0-9. Edit this, not SKILL.md |
| `research/serial_formats.csv`, `research/serial_formats_extended.csv` | Serial rules with regex, source URL and notes per rule |
| `research/equipment_types_starter.csv` | Service lives, efficiency metrics, visual identifiers |
| `code/build_skill.py` | Renders the body plus both appendices into `output/SKILL.md` and `.claude/skills/building-equipment-inventory/SKILL.md` |
| `code/serial_decoder/`, `code/efficiency_lookup/`, `code/run_reference_lookup.py` | Python versions of section 6 |
| `code/tests/` | 887 tests: every serial example decodes to its stated date through the decoder |

Rebuild after any edit: `uv run python code/build_skill.py`. Run tests: `uv run --with pytest pytest code/tests` (pytest is not a project dependency yet).

## Known gaps

- Serial formats not public for York chillers, Twin City Fan, Titus, Price, BAC, Fulton, Bryan, Patterson-Kelley, most kitchen brands, Toshiba-Carrier and Hitachi. Most sit behind paid guides (Building Intelligence Center, $15/yr: https://www.building-center.org/; Preston's Guide). Detail: `research/serial_formats_extended_gaps.md`.
- 144 of the 303 rules rest on one third-party source (confidence L).
- ENERGY STAR and DOE drop discontinued models; spec sheets are the fallback and need a web search per model.
