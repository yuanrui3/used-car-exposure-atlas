"""Prepare an Allstate city point layer and a Census county urban-population proxy."""
import csv
import io
import json
from pathlib import Path
import re
import subprocess
from urllib.request import urlretrieve
import zipfile

from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
CACHE.mkdir(exist_ok=True)
SOURCES = {
    "places.zip": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_place_national.zip",
    "allstate.pdf": "https://www.allstate.com/resources/allstate/attachments/best-drivers/full-americas-best-drivers-report-v2.pdf",
    "urban.xlsx": "https://www2.census.gov/geo/docs/reference/ua/2020_UA_COUNTY.xlsx",
}
STATES = dict(s.split(":") for s in (
    "Alabama:AL|Alaska:AK|Arizona:AZ|Arkansas:AR|California:CA|Colorado:CO|Connecticut:CT|Delaware:DE|District of Columbia:DC|"
    "Florida:FL|Georgia:GA|Hawaii:HI|Idaho:ID|Illinois:IL|Indiana:IN|Iowa:IA|Kansas:KS|Kentucky:KY|Louisiana:LA|Maine:ME|Maryland:MD|"
    "Massachusetts:MA|Michigan:MI|Minnesota:MN|Mississippi:MS|Missouri:MO|Montana:MT|Nebraska:NE|Nevada:NV|New Hampshire:NH|"
    "New Jersey:NJ|New Mexico:NM|New York:NY|North Carolina:NC|North Dakota:ND|Ohio:OH|Oklahoma:OK|Oregon:OR|Pennsylvania:PA|"
    "Rhode Island:RI|South Carolina:SC|South Dakota:SD|Tennessee:TN|Texas:TX|Utah:UT|Vermont:VT|Virginia:VA|Washington:WA|"
    "West Virginia:WV|Wisconsin:WI|Wyoming:WY"
).split("|"))
ALIASES = {
    ("Boise", "ID"): "Boise City city",
    ("Lexington", "KY"): "Lexington-Fayette urban county",
    ("Louisville", "KY"): "Louisville/Jefferson County metro government (balance)",
    ("Nashville", "TN"): "Nashville-Davidson metropolitan government (balance)",
    ("Indianapolis", "IN"): "Indianapolis city (balance)",
    ("Augusta", "GA"): "Augusta-Richmond County consolidated government (balance)",
    ("Macon", "GA"): "Macon-Bibb County",
}

def write_json(name, rows):
    (HERE / name).write_text(json.dumps(rows, ensure_ascii=False, separators=(",",":"))+"\n")


def city_braking():
    with zipfile.ZipFile(CACHE / "places.zip") as z:
        with z.open(z.namelist()[0]) as file:
            reader = csv.DictReader(io.TextIOWrapper(file, encoding="utf8"), delimiter="\t")
            places = {(r["USPS"], r["NAME"]): {k.strip(): v.strip() for k, v in r.items()} for r in reader}
    subprocess.run(["pdftotext","-layout",str(CACHE / "allstate.pdf"),str(CACHE / "allstate.txt")],check=True)
    reported = [re.split(r"\s{2,}",line.strip()) for line in (CACHE / "allstate.txt").read_text().splitlines() if re.match(r"^\s*\d+\s{2,}",line)]
    assert [int(row[0]) for row in reported]==list(range(1,201))
    rows = []
    for row in reported:
        if row[2] in ("Alaska","Hawaii") or row[-1]=="N/A":
            continue
        assert len(row) in (9,10)
        city = row[1]
        st = STATES[row[2]]
        name = ALIASES.get((city,st))
        options = [name] if name else [f"{city} {qualifier}" for qualifier in ("city","town","CDP","municipality","village")]
        matches = [places[(st,n)] for n in options if (st,n) in places]
        assert len(matches)==1,(city,st,[n for s,n in places if s==st and n.startswith(city[:5])])
        place = matches[0]
        rows.append(dict(city=city,state=st,place_geoid=place["GEOID"],lat=float(place["INTPTLAT"]),lon=float(place["INTPTLONG"]),hard_brakes_per_1000_miles=float(row[-1])))
    assert all(0<r["hard_brakes_per_1000_miles"]<100 for r in rows)
    write_json("city_braking.json",rows)
    return len(rows)

def urban_share():
    wb=load_workbook(CACHE / "urban.xlsx",read_only=True,data_only=True)
    county, alternative = {}, {}
    for sheet,dest in [(wb["2020_UA_COUNTY"],county),(wb["CT_2022"],alternative)]:
        row_iter = sheet.values
        fields = next(row_iter)
        for raw in row_iter:
            r=dict(zip(fields,raw))
            if r["STATE"] is None:
                break
            if r["STATE_NAME"] not in STATES or r["STATE_NAME"] in ("Alaska","Hawaii"):
                continue
            geoid=str(r["STATE"]).zfill(2)+str(r["COUNTY"]).zfill(3)
            total,urban=int(r["POP_COU"]),int(r["POP_URB"])
            pct=round(100 * urban / total,2)
            assert 0 <= pct <= 100 and len(geoid)==5
            dest[geoid]=pct
    assert len(county)==3108 and len(alternative)==9, (len(county),len(alternative))
    write_json("county_urban_population_pct.json",{**county,**alternative})
    return len(county),len(alternative)

if __name__ == "__main__":
    for name, link in SOURCES.items():
        if not (CACHE / name).is_file(): urlretrieve(link,CACHE / name)
    print("Braking city count",city_braking())
    print("Urban counties + alternative CT regions",urban_share())
