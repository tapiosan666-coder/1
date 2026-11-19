"""Prepare the lightweight entrance index for the directory from source drawings."""
import csv
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
with (ROOT / "source/v22/store-status.csv").open(encoding="utf-8-sig") as handle:
    entries = {row["店舗ID"]: [float(row["入口X"]),float(row["入口Z"])] for row in csv.DictReader(handle)}
for row in json.loads((ROOT / "source/v32/sales-design.json").read_bytes())["stores"]:
    entries[row["id"]] = [row["entry"][0],row["entry"][2]]
assert len(entries) == 480
dest = ROOT / "source/v36/map-entrances.json"
dest.write_text(json.dumps({k:[round(x-429,4),round(z+46,4)] for k,(x,z) in sorted(entries.items())}, separators=(",", ":")))
