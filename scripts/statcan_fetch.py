"""Download the market benchmark from Statistics Canada and keep a dated copy.

Run from the repository root, between 8:30 and midnight (Eastern time):
    python -m scripts.statcan_fetch
"""

import json
from pathlib import Path

from api.market.statcan import PROVINCES, core_retail, extract, fetch

OUT = Path("scripts/out")
TEST_DATA = Path("tests/data")


def save(snapshot: dict, path: Path) -> None:
    path.write_text(json.dumps(snapshot, indent=1) + "\n", encoding="utf-8")
    print("Saved", path, f"({path.stat().st_size // 1024} KB)")


def main() -> None:
    snapshot = fetch()
    day, month = snapshot["released"][:10], snapshot["published"]
    print("Released", snapshot["released"], "- latest month", month)
    OUT.mkdir(exist_ok=True)
    save(snapshot, OUT / f"statcan_retail_{day}.json")
    save(extract(snapshot, "ON", "2024-01"), TEST_DATA / f"statcan_on_{day}.json")

    print(f"\n{month}, thousands of dollars: retail trade, core retail, share")
    for code, (name, _) in PROVINCES.items():
        total = snapshot["series"][code]["retail_trade"][month]
        core = core_retail(snapshot, code)[month]
        share = f"{core / total:.1%}" if core is not None else "not published"
        print(f"  {code}  {name:<27} {total!s:>12} {core!s:>12}  {share}")


if __name__ == "__main__":
    main()
