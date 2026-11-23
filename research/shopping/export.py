"""Publish only county aggregates and model diagnostics."""

from pathlib import Path
import json
import pandas as pd

P = Path(__file__).resolve().parent
D = P.parents[1] / "docs/assets"


def export(cache=P / "cache", output=D):
    market = pd.read_csv(cache / "market.csv", dtype={"fips": str})
    exposure = pd.read_csv(output / "annual-exposure.csv", dtype={"fips": str})
    data = market.merge(
        exposure[
            [
                "fips",
                "annualExposure",
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
        ],
        on="fips",
        validate="1:1",
    )
    result = {}
    for r in data.itertuples():
        metrics = [
            None if pd.isna(n) else n for n in (r.model_pct, r.model_lo, r.model_hi)
        ]
        result[r.fips] = [
            r.supported,
            r.families,
            *metrics,
            r.annualExposure,
            *[
                round(getattr(r, k), 1)
                for k in [
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
            ],
        ]
    summary = json.loads((cache / "summary.json").read_text())
    (output / "county-shopping.json").write_text(
        json.dumps(
            {"summary": summary, "counties": result},
            separators=(",", ":"),
            allow_nan=False,
        )
    )
    market.to_csv(output / "county-shopping.csv", index=False)


if __name__ == "__main__":
    export()
