"""Assemble the single-file building-equipment-inventory skill.

The skill ships as one Markdown file, so the serial-number rules and service
lives are rendered from their research CSVs into appendices. Edit the CSVs or
skill_body.md, never the generated SKILL.md.
"""

import csv
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = PROJECT_DIR.parents[1]
BODY_PATH = Path(__file__).resolve().parent / "skill_body.md"
SERIAL_RULE_PATHS = [
    PROJECT_DIR / "research" / "serial_formats.csv",
    PROJECT_DIR / "research" / "serial_formats_extended.csv",
]
LIFE_TABLE_PATH = PROJECT_DIR / "research" / "equipment_types_starter.csv"
PACKAGE_OUTPUT_PATH = PROJECT_DIR / "output" / "SKILL.md"
# Only present inside the energy-management repo, not in the shared package.
REPO_SKILL_PATH = REPO_DIR / ".claude" / "skills" / "building-equipment-inventory" / "SKILL.md"

SERIAL_HEADER = "| Brand (also sold as) | Equipment | Era | Serial pattern | Year | Week or month | Example | Conf. |"
LIFE_HEADER = "| Equipment type | Median life (yrs) | Source | Efficiency metric |"


def _cell(text: str) -> str:
    return text.replace("|", "\\|").strip()


def _table_row(cells: list[str]) -> str:
    return "| " + " | ".join(_cell(c) for c in cells) + " |"


def _separator(header: str) -> str:
    return "|" + "---|" * header.count(" | ") + "---|"


def _load_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        with path.open() as f:
            rows.extend(csv.DictReader(f))
    return rows


def _serial_row(rule: dict[str, str]) -> str:
    aliases = rule["aliases"].strip()
    brand = rule["brand"] + (f" ({aliases.replace(';', ', ')})" if aliases else "")
    era = f"{rule['era_start'] or '?'}-{rule['era_end'] or 'now'}"
    example = f"{rule['example_serial']} = {rule['example_decoded']}"
    return _table_row([
        brand,
        rule["equipment_types"].replace(";", ", "),
        era,
        f"`{rule['pattern']}`",
        rule["year_rule"],
        rule["month_or_week_rule"],
        example,
        rule["confidence"][:1],
    ])


def _serial_appendix(rules: list[dict[str, str]]) -> str:
    rules = sorted(rules, key=lambda r: (r["brand"].lower(), r["era_start"] or "0"))
    dated = [r for r in rules if r["pattern"].strip()]
    undated = sorted({r["brand"] for r in rules if not r["pattern"].strip()})
    lines = [
        "## Appendix A: serial-number date rules",
        "",
        f"{len(dated)} rules. Sources and full notes for every rule are in the research CSVs this file is built from.",
        "",
        SERIAL_HEADER,
        _separator(SERIAL_HEADER),
        *(_serial_row(r) for r in dated),
        "",
        "**No date in the serial** (use the nameplate date, permit or service records): " + ", ".join(undated) + ".",
    ]
    return "\n".join(lines)


def _life_appendix(types: list[dict[str, str]]) -> str:
    lines = [
        "## Appendix B: median service life by equipment type",
        "",
        LIFE_HEADER,
        _separator(LIFE_HEADER),
        *(
            _table_row([
                t["equipment_type"],
                t["typical_useful_life_years"],
                t["useful_life_source"].split(" (see")[0],
                t["typical_efficiency_metric"],
            ])
            for t in types
        ),
    ]
    return "\n".join(lines)


def build_skill() -> str:
    body = BODY_PATH.read_text().rstrip()
    serial = _serial_appendix(_load_rows(SERIAL_RULE_PATHS))
    life = _life_appendix(_load_rows([LIFE_TABLE_PATH]))
    return f"{body}\n\n{serial}\n\n{life}\n"


if __name__ == "__main__":
    skill = build_skill()
    targets = [PACKAGE_OUTPUT_PATH]
    if (REPO_DIR / ".claude").is_dir():
        targets.append(REPO_SKILL_PATH)
    for path in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(skill)
        print(f"wrote {path} ({len(skill) // 4:,} tokens approx)")
