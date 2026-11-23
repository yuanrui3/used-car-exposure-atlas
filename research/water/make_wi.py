"""Extract Table 1.4 after pdftotext -layout wi-2026.pdf wi-2026.txt."""
import csv
import json
import re
from pathlib import Path
from scipy.stats import spearmanr

root = Path(__file__).resolve().parent

def county_key(s):
    return (s.lower().replace('saint','st').replace('trempeleau','trempealeau')
            .replace(' ','').replace('.','').replace('county',''))

known = {county_key(r['county']): r['fips']
         for r in csv.DictReader((root.parent/'geodata/counties.csv').open())
         if r['state'] == 'WI'}
text = (root/'wi-2026.txt').read_text()
text = text.split('Statewide total          34,686.45')[0]
pattern = re.compile(r'^\s*(.*?)\s+([\d,.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d,]+)\s+([\d.]+)\s+[\d.]+\s+\$')
counties = {}
for line in text.splitlines():
    match = pattern.match(line)
    if not match: continue
    name, lanes, severity, snow, tons, rate = match.groups()
    code = known.get(county_key(name))
    if not code: continue
    assert code not in counties, (code, line)
    rate, snow, tons, lanes = float(rate),float(snow),int(tons.replace(',','')),float(lanes.replace(',',''))
    assert abs(tons / lanes - rate) < 0.012, (name, tons, lanes, rate)
    counties[code] = [rate,snow,tons,lanes]
assert len(counties) == len(known) == 72
(root/'wi_salt_counties.json').write_text(json.dumps(dict(sorted(counties.items())),separators=(',',':')))
snow = json.loads((root/'snow.json').read_text())
for i in ('same-winter snowfall','NOAA normal snowy days'):
    xs = [v[1] if i == 'same-winter snowfall' else snow[k][0] for k,v in counties.items()]
    print(i, spearmanr(xs,[v[0] for v in counties.values()]).statistic)
