"""Find descriptions that explicitly give a down payment price or identify a branded title."""

from pathlib import Path
import re, zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parent
flagged = set()
with zipfile.ZipFile(ROOT / "cache/listings.zip") as z:
    groups = pd.read_csv(
        z.open("vehicles.csv"), usecols=["id", "description"], chunksize=40000
    )
    for batch in groups:
        desc = batch.description.fillna("").str.lower()
        # Some dealers list full prices alongside financing terms. Only explicit price-as-deposit phrases flag the ad.
        deposit = r"(?:price\s+(?:shown|listed|advertised|displayed)|(?:listed|advertised|displayed)\s+price)\s*(?:is|represents|reflects|shows|:|=)\s*(?:only\s+)?(?:the\s+|a\s+|your\s+|minimum\s+)*(?:estimated\s+)?down\s*payment"
        brand = r"\b(?:has\s+(?:a\s+)?|comes\s+with\s+(?:a\s+)?|title\s*:\s*)(?:rebuilt|salvage|flood|branded)(?:\s+title)?\b"
        bad = desc.str.contains(deposit + "|" + brand, regex=True)
        flagged.update(batch.loc[bad, "id"].to_list())
pd.Series(sorted(flagged), name="id").to_csv(ROOT / "cache/flagged.csv", index=False)
print(len(flagged))
