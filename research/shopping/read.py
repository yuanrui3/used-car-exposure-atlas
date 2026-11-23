from pathlib import Path
import pandas as pd
import zipfile

root = Path(__file__).resolve().parent
fields = "id,url,price,year,manufacturer,model,condition,fuel,odometer,title_status,transmission,VIN,drive,type,state,lat,long,posting_date".split(
    ","
)
with zipfile.ZipFile(root / "cache/listings.zip") as z:
    df = pd.read_csv(z.open("vehicles.csv"), usecols=fields, low_memory=False)
print(
    "records",
    len(df),
    "dates",
    df.posting_date.str.slice(0, 10).value_counts().sort_index().to_string(),
    "missing",
    df.isna().sum().to_dict(),
    flush=True,
)
print(
    df.condition.value_counts().to_dict(),
    df.title_status.value_counts().to_dict(),
    df.url.str.extract(r"/(ct[od])/")[0].value_counts().to_dict(),
    flush=True,
)
df.to_pickle(root / "cache/listings.pkl")
