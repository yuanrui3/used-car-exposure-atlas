"""Deduplicate county-coded reports into calendar days with >=1 event."""
import csv, gzip, json, sys
from pathlib import Path
from collections import defaultdict, Counter
base = Path(__file__).resolve().parents[1]
raw=base/'water/raw'
county={r['fips'] for r in csv.DictReader((base/'geodata/counties.csv').open())}
reports=defaultdict(lambda:defaultdict(set))
totals=Counter()
invalid=Counter()
files=sorted(raw.glob('StormEvents_details*'))
assert len(files)==10, files
for path in files:
    with gzip.open(path,'rt',encoding='latin1',newline='') as f:
        for r in csv.DictReader(f):
            kind={'Hail':'hail','Flash Flood':'flash','Flood':'flood'}.get(r['EVENT_TYPE'])
            if not kind or r['CZ_TYPE']!='C': continue
            fips=r['STATE_FIPS'].zfill(2)+r['CZ_FIPS'].zfill(3)
            if fips not in county:
                invalid[fips[:2]]+=1
                continue
            day=r['BEGIN_YEARMONTH']+r['BEGIN_DAY'].zfill(2)
            reports[fips][kind].add(day)
            totals[kind]+=1
result={f:{'hail':len(reports[f]['hail']),'flood':len(reports[f]['flash']|reports[f]['flood'])} for f in sorted(county)}
(base/'geodata/events.json').write_text(json.dumps(result,separators=(',',':')))
print(totals, invalid, 'Tippecanoe',result['18157'])
