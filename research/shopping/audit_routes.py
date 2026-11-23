from pathlib import Path
import pandas as pd, numpy as np

R = Path(__file__).resolve().parent / "cache"
d = pd.read_pickle(R / "residuals.pkl")
d["site"] = d.lat.round(2).astype(str) + "," + d.long.round(2).astype(str)
t = pd.read_csv(R / "routes.csv", dtype={"ofips": str, "dfips": str})
t = t.query(
    "cautious>0 and orank>=65 and missgap>0 and leavegap>0 and snow25gap>0 and dist<=155"
).copy()


def stats(a, b):
    pct = lambda v: 100 * (1 - np.exp(v))
    calc = lambda aa, bb: pct(bb.residual.median() - aa.residual.median())
    vals = [calc(a[a.early == e], b[b.early == e]) for e in [True, False]]
    top = lambda x: x.site.value_counts().index[0]
    maxsite = lambda x: 100 * (x.site == top(x)).mean()
    vals.extend(
        [calc(a[a.site != top(a)], b[b.site != top(b)]), maxsite(a), maxsite(b)]
    )
    # Direct near-matches. Greedy mileage-first pairing uses the price only after selecting disjoint cars.
    a = a.reset_index(drop=True)
    b = b.reset_index(drop=True)
    cols = ["family", "fuel", "drive", "transmission", "condition", "seller"]
    q = a.reset_index().merge(b.reset_index(), on=cols, suffixes=("_a", "_b"))
    q["dy"] = abs(q.year_a - q.year_b)
    q["dm"] = abs(q.odometer_a - q.odometer_b)
    q = q[(q.dy <= 1) & (q.dm <= 10000)].sort_values(["dy", "dm", "id_a", "id_b"])
    ai = set()
    bi = set()
    v = []
    for pair in q.itertuples():
        if pair.index_a not in ai and pair.index_b not in bi:
            ai.add(pair.index_a)
            bi.add(pair.index_b)
            v.append(np.log(pair.price_b / pair.price_a))
    vals.extend([len(v), pct(np.median(v)) if v else np.nan])
    return vals


cols = ["early", "late", "drop_top", "top_a", "top_b", "near_pairs", "near_saving"]
for k, row in t.iterrows():
    a = d[d.fips == row.ofips]
    b = d[d.fips == row.dfips]
    t.loc[k, cols] = stats(a, b)
t.to_csv(R / "audit_routes.csv", index=False)
print(
    t[
        [
            "origin",
            "dest",
            "early",
            "late",
            "drop_top",
            "top_a",
            "top_b",
            "near_pairs",
            "near_saving",
        ]
    ]
    .round(1)
    .to_string(index=False)
)
