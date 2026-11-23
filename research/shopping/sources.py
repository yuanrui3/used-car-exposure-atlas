"""Fetch the locked public snapshots and convert the county topology into geographic polygons."""

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
from shutil import copyfileobj

P = Path(__file__).resolve().parent / "cache"
P.mkdir(exist_ok=True)
sources = [
    (
        "listings.zip",
        "https://www.kaggle.com/api/v1/datasets/download/austinreese/craigslist-carstrucks-data?datasetVersionNumber=11",
        "729dc4d4d87013d6ec0645b79041b04b98f42f06794a94acfbb3dabffb613151",
    ),
    (
        "counties.topo.json",
        "https://cdn.jsdelivr.net/npm/us-atlas@3.0.1/counties-10m.json",
        "145aaf5d1433352a6a1d8e86b5f149c7c653f9171baf14aaf75ee66575def1b0",
    ),
]
for name, url, digest in sources:
    dest = P / name
    if not dest.exists():
        with urlopen(
            Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=120
        ) as response, dest.open("wb") as out:
            copyfileobj(response, out)
    with dest.open("rb") as inp:
        if hashlib.file_digest(inp, "sha256").hexdigest() != digest:
            raise ValueError(
                f"{name} differs from the November 2026 analysis snapshot. Use the archived version for reproduction."
            )
t = json.loads((P / "counties.topo.json").read_text())
sx, sy = t["transform"]["scale"]
tx, ty = t["transform"]["translate"]
arcs = []
for arc in t["arcs"]:
    x = y = 0
    line = []
    for dx, dy in arc:
        x += dx
        y += dy
        line.append([x * sx + tx, y * sy + ty])
    arcs.append(line)


def ring(indices):
    points = []
    for i in indices:
        part = arcs[i] if i >= 0 else arcs[~i][::-1]
        points.extend(part if not points else part[1:])
    while len(points) < 4:
        points.append(points[0])
    return points


features = []
for g in t["objects"]["counties"]["geometries"]:
    if g["type"] == "Polygon":
        coords = [ring(r) for r in g["arcs"]]
    else:
        coords = [[ring(r) for r in polygon] for polygon in g["arcs"]]
    features.append(
        {
            "type": "Feature",
            "id": g["id"],
            "geometry": {"type": g["type"], "coordinates": coords},
        }
    )
(P / "boundaries.json").write_text(
    json.dumps(
        {"type": "FeatureCollection", "features": features}, separators=(",", ":")
    )
)
