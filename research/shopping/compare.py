"""Within-vehicle asking-price comparisons from a dated Craigslist snapshot."""

from pathlib import Path
import re
import json
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parent
d = pd.read_pickle(ROOT / "cache/listings.pkl")
d["price"] = pd.to_numeric(d.price, errors="coerce")
d = d[~d.id.isin(pd.read_csv(ROOT / "cache/flagged.csv").id)].copy()
geo = pd.read_csv(
    Path(__file__).resolve().parents[1] / "geodata/counties.csv", dtype={"fips": str}
)
states = geo.set_index("fips").state
boundary = json.loads((ROOT / "cache/boundaries.json").read_text())
features = [f for f in boundary["features"] if f["id"] in states.index]
polys = [shape(f["geometry"]) for f in features]
tree = STRtree(polys)
d["seller"] = d.url.str.extract(r"/(ct[od])/")[0]
d["model_key"] = (
    d.model.fillna("")
    .str.lower()
    .str.replace(r"[^a-z0-9]+", " ", regex=True)
    .str.strip()
)
d = d[
    d.title_status.eq("clean")
    & d.condition.isin(["excellent", "good", "like new", "fair"])
    & d.year.between(2006, 2025)
    & d.price.between(3500, 75000)
    & d.odometer.between(10000, 200000)
    & d.model_key.ne("")
    & d.drive.notna()
    & d.fuel.notna()
    & d.transmission.notna()
    & d.manufacturer.notna()
    & d.seller.notna()
    & d.lat.between(24, 50)
    & d.long.between(-125, -66)
].copy()
points = shapely.points(d.long.to_numpy(), d.lat.to_numpy())
p_i, c_i = tree.query(points, predicate="within")
res = pd.Series(index=d.index, dtype="object")
res.loc[d.index[p_i]] = [features[i]["id"] for i in c_i]
d["fips"] = res
# Advertised markets sometimes cross state lines. The geographic location is taken from the coordinates.
d = d.dropna(subset=["fips"])
# A VIN marketed in several counties gives no dependable venue. Keep the latest observed listing otherwise.
validvin = d.VIN.fillna("").str.upper().str.fullmatch(r"[0-9A-HJ-NPR-Z]{17}")
d["validvin"] = d.VIN.str.upper().where(validvin)
keys = [
    "manufacturer",
    "model_key",
    "year",
    "drive",
    "fuel",
    "transmission",
    "condition",
    "seller",
]
d["grp"] = d.groupby(keys, sort=True).ngroup()
d["fallback"] = d.groupby(
    ["manufacturer", "model_key", "year", "odometer", "drive", "fuel", "transmission"],
    sort=True,
).ngroup()
d = d.sort_values(["posting_date", "id"])
has = d[d.validvin.notna()].copy()
has = has[has.groupby("validvin").fips.transform("nunique") == 1].drop_duplicates(
    "validvin", keep="last"
)
no = d[d.validvin.isna()].copy()
no = no[
    (~no.fallback.isin(has.fallback))
    & (no.groupby("fallback").fips.transform("nunique") == 1)
].drop_duplicates("fallback", keep="last")
d = pd.concat([has, no], ignore_index=True)
d.to_pickle(ROOT / "cache/eligible.pkl")
print("eligible", len(d), "locations", d.fips.nunique(), flush=True)
# Each other county contributes one median. Each benchmark needs at least three vehicles across two outside counties.
match = []
for group, g in d.groupby("grp"):
    if len(g) < 4 or g.fips.nunique() < 3:
        continue
    g = g.sort_values("odometer")
    miles = g.odometer.to_numpy()
    f = g.fips.to_numpy()
    price = g.price.to_numpy()
    for i, (a, b) in enumerate(
        zip(
            np.searchsorted(miles, miles - 5000),
            np.searchsorted(miles, miles + 5000, side="right"),
        )
    ):
        if b - a < 4:
            continue
        other = f[a:b] != f[i]
        if other.sum() < 3:
            continue
        fs = f[a:b][other]
        ps = price[a:b][other]
        counties = np.unique(fs)
        if len(counties) < 2:
            continue
        bench = np.median([np.median(ps[fs == co]) for co in counties])
        match.append((f[i], group, float(np.log(price[i] / bench)), int(other.sum())))
m = pd.DataFrame(match, columns=["fips", "group", "logratio", "outside_comps"])
print("matched", len(m), "locations", m.fips.nunique(), flush=True)
c = geo[["fips", "county", "state"]].set_index("fips").copy()
c["qualified"] = d.groupby("fips").size()
c["matched"] = m.groupby("fips").size()
c["strata"] = m.groupby("fips").group.nunique()
c[["qualified", "matched", "strata"]] = (
    c[["qualified", "matched", "strata"]].fillna(0).astype(int)
)
c[["index_pct", "lo_pct", "hi_pct"]] = np.nan
rng = np.random.default_rng(231126)
for f, g in m.groupby("fips"):
    gs = [gg.logratio.to_numpy() for _, gg in g.groupby("group")]
    if len(g) < 15 or len(gs) < 5 or max(map(len, gs)) > 0.4 * len(g):
        continue
    samples = [
        np.median(np.concatenate([gs[j] for j in rng.integers(len(gs), size=len(gs))]))
        for _ in range(600)
    ]
    c.loc[f, ["index_pct", "lo_pct", "hi_pct"]] = 100 * np.expm1(
        [g.logratio.median(), *np.quantile(samples, [0.025, 0.975])]
    )
c.round(2).to_csv(ROOT / "cache/county_prices.csv")
print(
    "display",
    c.index_pct.notna().sum(),
    "Indiana",
    c.loc[
        (c.state == "IN")
        & ((c.index_pct.notna()) | c.index.isin(["18157", "18089", "18097"]))
    ].to_string(),
    flush=True,
)
