"""Join visually transcribed Clear Roads dry-salt use to FHWA's 2022 state-owned lane mileage."""
import csv, html, json, re
from pathlib import Path
root=Path(__file__).resolve().parent
lanes={}
for name, cells in re.findall(r'<th scope="row"[^>]*>([^<]+)</th>(.*?)</tr>',(root/'hm81.html').read_text(),re.S|re.I):
    values=re.findall(r'<td[^>]*>(.*?)</td>',cells,re.S|re.I)
    if len(values)==21:
        lanes[html.unescape(name.strip())]=int(values[15].replace(',','').strip())
out={}
for row in csv.DictReader((root/'salt_2021_22.csv').open()):
    mass=int(row['dry_salt_tons'])
    miles=lanes[row['name']]
    out[row['state']]=[round(mass/miles,2),mass,miles]
(root/'salt_states.json').write_text(json.dumps(out,separators=(',',':')))
print(len(out),'states',out['IN'],out['NY'],out['CA'])
