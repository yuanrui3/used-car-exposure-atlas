from pathlib import Path
import pandas as pd, numpy as np
from scipy.spatial.distance import cdist

r = Path(__file__).resolve().parent
p = pd.read_csv(r / "cache/market.csv", dtype={"fips": str})
e = pd.read_csv(
    Path(__file__).resolve().parents[2] / "docs/assets/annual-exposure.csv",
    dtype={"fips": str},
)
g = pd.read_csv(
    Path(__file__).resolve().parents[1] / "geodata/counties.csv", dtype={"fips": str}
)
d = e.merge(p, on=["fips", "county", "state"]).merge(
    g[["fips", "lat", "lon"]], on="fips"
)
d["erank"] = d.annualExposure.rank(pct=True) * 100
cats = [
    "winter",
    "coast",
    "wet",
    "heat",
    "cold",
    "grade",
    "traffic",
    "rough",
    "dust",
    "flood",
    "hail",
]
d["win25"] = 0.25 * d.winter + 0.75 * d[[x for x in cats if x != "winter"]].mean(axis=1)
rows = []
for a in d[d.model_pct.notna()].itertuples():
    for b in d[
        (d.model_pct.notna())
        & (abs(d.lat - a.lat) < 2.6)
        & (abs(d.lon - a.lon) < 4)
        & (d.erank < a.erank - 18)
    ].itertuples():
        sep = (
            (a.lat - b.lat) ** 2
            + ((a.lon - b.lon) * np.cos(np.deg2rad((a.lat + b.lat) / 2))) ** 2
        ) ** 0.5 * 69
        if sep > 155:
            continue
        dif = a.annualExposure - b.annualExposure
        robust = min((11 * dif - (getattr(a, k) - getattr(b, k))) / 10 for k in cats)
        priceratio = (1 + b.model_pct / 100) / (1 + a.model_pct / 100)
        gaplo = (1 + b.model_hi / 100) / (1 + a.model_lo / 100)
        rows.append(
            dict(
                origin=a.county + " " + a.state,
                dest=b.county + " " + b.state,
                ofips=a.fips,
                dfips=b.fips,
                state=a.state == b.state,
                dist=round(sep),
                on=a.supported,
                dn=b.supported,
                op=a.model_pct,
                dp=b.model_pct,
                oline=a.model_lo,
                dhi=b.model_hi,
                discount=round((1 - priceratio) * 100, 1),
                cautious=round((1 - gaplo) * 100, 1),
                oe=round(a.annualExposure, 1),
                de=round(b.annualExposure, 1),
                orank=round(a.erank),
                drank=round(b.erank),
                missgap=round(a.missing_data_low - b.missing_data_high, 1),
                leavegap=round(robust, 1),
                snow25gap=round(a.win25 - b.win25, 1),
            )
        )
t = pd.DataFrame(rows)
t.to_csv(r / "cache/routes.csv", index=False)
ok = t.query(
    "cautious>0 and orank>=65 and drank<=50 and missgap>0 and leavegap>0 and snow25gap>0 and dist<=145"
).sort_values(["state", "cautious"], ascending=False)
print(
    ok[
        [
            "origin",
            "dest",
            "state",
            "dist",
            "on",
            "dn",
            "discount",
            "cautious",
            "oe",
            "de",
            "orank",
            "drank",
            "missgap",
        ]
    ]
    .head(65)
    .to_string(index=False)
)
print(
    "Indiana",
    t[t.origin.str.endswith(" IN")]
    .sort_values("cautious", ascending=False)
    .head(6)[["origin", "dest", "dist", "discount", "cautious", "orank", "drank"]]
    .to_string(index=False),
)
