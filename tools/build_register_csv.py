"""Regenerate the fillable assumptions CSV from the markdown register.

The markdown is the single source of truth. This script derives the CSV and
re-tallies the status counts so the two can never drift.

Usage:
    python tools/build_register_csv.py
"""

from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "docs" / "assumptions_register.md"
CSV_OUT = ROOT / "docs" / "assumptions_register.csv"

FIELDS = [
    "ID", "Category", "Parameter", "Current", "Units", "Status", "Basis",
    "CONFIRMED_VALUE", "CONFIRMED_BY", "DATE", "NOTES",
]


def parse(md_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    category = None
    for line in md_text.split("\n"):
        heading = re.match(r"^## ([A-K])\. (.+)", line)
        if heading:
            category = f"{heading.group(1)} - {heading.group(2)}"
            continue
        if not line.startswith("|") or category is None:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 6:
            continue
        if not re.match(r"^[A-K]\d+$", cells[0]):
            continue
        clean = lambda s: s.replace("**", "").strip()
        rows.append(
            {
                "ID": cells[0],
                "Category": category,
                "Parameter": clean(cells[1]),
                "Current": clean(cells[2]),
                "Units": clean(cells[3]),
                "Status": clean(cells[4]),
                "Basis": clean(cells[5]),
            }
        )
    return rows


def main() -> int:
    if not MD.exists():
        print(f"missing {MD}", file=sys.stderr)
        return 1

    rows = parse(MD.read_text(encoding="utf-8"))
    if not rows:
        print("parsed zero rows -- did the table format change?", file=sys.stderr)
        return 1

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {**row, "CONFIRMED_VALUE": "", "CONFIRMED_BY": "", "DATE": "", "NOTES": ""}
            )

    counts = collections.Counter(
        r["Status"].split(" [")[0].split("/")[0].strip() for r in rows
    )
    print(f"wrote {CSV_OUT.relative_to(ROOT)} ({len(rows)} parameters)")
    print("\nstatus counts -- copy into the summary table in the markdown:")
    for status, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {status:14s} {n}")

    blocking = counts.get("OPEN", 0) + counts.get("PLACEHOLDER", 0)
    print(f"\n{blocking} parameters block a trustworthy run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
