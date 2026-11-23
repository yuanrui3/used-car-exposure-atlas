import csv,json, collections, urllib.request
from pathlib import Path
root=Path(__file__).resolve().parent
p=root/'rugged.csv'
if not p.is_file():urllib.request.urlretrieve('https://www.ers.usda.gov/media/5414/2020-area-and-road-ruggedness-scales.csv?v=54114',p)
s=collections.defaultdict(lambda:[0.,0])
county={r['fips'] for r in csv.DictReader((root/'counties.csv').open())}
seen=set()
for row in csv.DictReader(p.open(encoding='cp1252')):
    k=row['CountyFIPS20']
    if k not in county or row['TractFIPS20'] in seen:continue
    seen.add(row['TractFIPS20'])
    try:n=int(row['RoadTRI_Count']);m=float(row['RoadTRI_Mean'])
    except ValueError:continue
    if n>0 and m>=0:s[k][0]+=n*m;s[k][1]+=n
res={k:round(v/n,2) for k,(v,n) in s.items()};assert len(res)==3108
(root/'rugged.json').write_text(json.dumps(res,separators=(',',':')))
print(res['18157'],min(res.values()),max(res.values()))
