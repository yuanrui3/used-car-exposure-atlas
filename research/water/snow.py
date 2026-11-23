from pathlib import Path
import sys, csv, io, json, tarfile
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent/'climate'))
from climate_tables import nearest, STATES
stations=[]
with tarfile.open(here.parent/'climate/normals.tar.gz','r|gz') as tar:
 for member in tar:
  if not member.isfile() or not member.name.startswith('US'):continue
  row=next(csv.DictReader(io.StringIO(tar.extractfile(member).read().decode())))
  sn='ANN-SNOW-AVGNDS-GE010TI'
  if row['NAME'].split()[-2] not in STATES or row.get('comp_flag_'+sn,'').strip()!='S':continue
  stations.append(dict(id=row['STATION'],lat=float(row['LATITUDE']),lon=float(row['LONGITUDE']),days=float(row[sn]),name=row['NAME']))
counties=list(csv.DictReader((here.parent/'geodata/counties.csv').open()))
out={c['fips']:[stations[i]['days'],stations[i]['id'],round(float(d),1)] for c,(i,d) in zip(counties,nearest(counties,stations))}
(here/'snow.json').write_text(json.dumps(out,separators=(',',':')))
(here/'snow_stations.json').write_text(json.dumps({s['id']:s['name'] for s in stations},separators=(',',':')))
print(len(stations),len(out),out['18157'],max(v[2] for v in out.values()))
