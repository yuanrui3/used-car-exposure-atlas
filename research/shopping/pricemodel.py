"""Estimate county asking-price deviations on geographically held-out listings."""

from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

root = Path(__file__).resolve().parent
d = pd.read_pickle(root / "cache/eligible.pkl").copy()


def family(s):
    words = s.split()
    if len(words) >= 2 and words[0] in {
        "grand",
        "town",
        "range",
        "land",
        "santa",
        "super",
        "silverado",
        "sierra",
        "ram",
        "transit",
        "f",
        "e",
        "cx",
        "mx",
        "sprinter",
        "pro",
        "model",
        "golf",
        "country",
        "new",
        "outlander",
    }:
        return " ".join(words[:2])
    return words[0]


d["family"] = d.manufacturer + " " + d.model_key.map(family)
d["full"] = d.manufacturer + " " + d.model_key
d["yr"] = d.year.astype(int).astype(str)
d["family_year"] = d.family + " " + d.yr
d["trim_year"] = d.full + " " + d.yr
d["vin_spec"] = d.validvin.fillna("").str.slice(0, 8)
d["vin_available"] = d.validvin.notna().astype(float)
d["body"] = d.type.fillna("unknown")
d["condition_age"] = (
    d.condition
    + " "
    + pd.cut(d.year, [2005, 2010, 2015, 2020, 2025], labels=False).astype(str)
)
age = 2026 - d.year.to_numpy()
miles = d.odometer.to_numpy() / 1e5
num = np.column_stack(
    [
        age / 10,
        np.maximum(age - 5, 0) / 10,
        np.maximum(age - 12, 0) / 10,
        miles,
        np.maximum(miles - 0.5, 0),
        np.maximum(miles - 1, 0),
        np.maximum(miles - 1.5, 0),
        miles * age / 10,
        d.vin_available,
    ]
)
blocks = [sparse.csr_matrix(num)]
# Multipliers control relative shrinkage under a single ridge penalty.
for name, scale in {
    "manufacturer": 1,
    "family": 1,
    "full": 0.55,
    "family_year": 0.55,
    "trim_year": 0.3,
    "vin_spec": 0.6,
    "yr": 0.5,
    "condition": 1,
    "condition_age": 0.5,
    "seller": 1,
    "drive": 1,
    "transmission": 1,
    "fuel": 1,
    "body": 1,
}.items():
    ids, vals = pd.factorize(d[name], sort=True)
    blocks.append(
        sparse.csr_matrix(
            (np.full(len(d), scale), (np.arange(len(d)), ids)),
            shape=(len(d), len(vals)),
        )
    )
X = sparse.hstack(blocks, format="csr")
y = np.log(d.price.to_numpy())
pred = np.empty(len(d))
supported = np.zeros(len(d), bool)
base = np.empty(len(d))
for tr, te in GroupKFold(5).split(X, y, groups=d.fips):
    model = Ridge(alpha=2, solver="lsqr", tol=1e-5, max_iter=600)
    model.fit(X[tr], y[tr])
    err = np.abs(y[tr] - model.predict(X[tr]))
    w = np.minimum(1, 0.45 / np.maximum(err, 1e-8))
    model.fit(X[tr], y[tr], sample_weight=w)
    pred[te] = model.predict(X[te])
    base[te] = np.median(y[tr])
    counts = d.iloc[tr].groupby(["family", "year"]).size()
    families = d.iloc[te].family
    years = d.iloc[te].year
    support = sum(
        counts.reindex(
            pd.MultiIndex.from_arrays([families, years + k]), fill_value=0
        ).to_numpy()
        for k in [-2, -1, 0, 1, 2]
    )
    supported[te] = support >= 5
d["residual"] = y - pred
d["median_error"] = np.abs(np.exp(pred - y) - 1)
d["base_error"] = np.abs(np.exp(base - y) - 1)
d = d.loc[supported].copy()
d["residual"] -= d.residual.median()
d["early"] = d.posting_date.str.slice(0, 10) <= "2026-10-17"
d.to_pickle(root / "cache/residuals.pkl")
c = pd.read_csv(root / "cache/county_prices.csv", dtype={"fips": str}).set_index("fips")
c["supported"] = d.groupby("fips").size()
c["supported"] = c.supported.fillna(0).astype(int)
c["families"] = d.groupby("fips").family.nunique()
c["families"] = c.families.fillna(0).astype(int)
c[["model_pct", "model_lo", "model_hi"]] = np.nan
rng = np.random.default_rng(51141)
cross = []
for f, g in d.groupby("fips", sort=True):
    gs = [q.residual.to_numpy() for _, q in g.groupby("family")]
    if len(g) < 40 or len(gs) < 8 or max(map(len, gs)) > len(g) * 0.25:
        continue
    samps = [
        np.median(np.concatenate([gs[j] for j in rng.integers(len(gs), size=len(gs))]))
        for _ in range(400)
    ]
    vals = [g.residual.median(), *np.quantile(samps, [0.025, 0.975])]
    c.loc[f, ["model_pct", "model_lo", "model_hi"]] = 100 * np.expm1(vals)
    if g.early.sum() >= 15 and (~g.early).sum() >= 15:
        cross.append(
            [g.loc[g.early, "residual"].median(), g.loc[~g.early, "residual"].median()]
        )
c = c.round(2)
c.to_csv(root / "cache/market.csv")
cross = np.array(cross)
summary = {
    "raw": 295451,
    "eligible": len(pred),
    "strict_matched": int(c.matched.sum()),
    "strict_counties": int(c.index_pct.notna().sum()),
    "supported": len(d),
    "shown": int(c.model_pct.notna().sum()),
    "total_counties": len(c),
    "median_abs_pct_error": round(100 * d.median_error.median(), 1),
    "baseline_abs_pct_error": round(100 * d.base_error.median(), 1),
    "temporal_counties": len(cross),
    "temporal_rank_corr": round(
        float(spearmanr(cross[:, 0], cross[:, 1]).statistic), 2
    ),
}
(root / "cache/summary.json").write_text(json.dumps(summary))
print(summary)
print(c.loc[["18157", "18089", "18097", "17019", "17183", "18057"]].to_string())
