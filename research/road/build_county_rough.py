"""Retrieve 2024 HPMS section-length sums by county. Missing or nonpositive IRI is excluded."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
import json,time

ROOT=Path(__file__).resolve().parent
CACHE=ROOT/'raw'
CACHE.mkdir(exist_ok=True)
def groups(filename,where,columns):
    path=CACHE/filename
    if path.exists():
        return json.loads(path.read_bytes())
    params={'$select':columns+',sum(sectionlength) as miles,count(*) as n',
            '$where':where,'$group':columns,'$limit':10000}
    url='https://data.transportation.gov/resource/42um-tgh5.json?'+urlencode(params)
    for attempt in range(3):
        try:
            rows=json.load(urlopen(url,timeout=120))
            assert isinstance(rows,list)
            path.write_text(json.dumps(rows))
            return rows
        except (TimeoutError,OSError):
            if attempt==2:raise
            time.sleep(2**attempt)

eligible='iri>0 AND sectionlength>0 AND f_system in(1,2,3,4,5) AND facility_type in(1,2)'
rough={f"{int(r['stateid']):02d}{int(r['county_id']):03d}":float(r['miles'])
       for r in groups('iri_poor.json',eligible+' AND iri>170','stateid,county_id') if r.get('county_id')}

def state_results(state):
    rows=groups('iri_state_'+state+'.json',f'stateid={int(state)} AND '+eligible,'county_id')
    result={}
    for row in rows:
        if not row.get('county_id') or int(row['county_id'])==0 or float(row['miles'])<=0:continue
        key=f"{state}{int(row['county_id']):03d}"
        total=float(row['miles'])
        poor=rough.get(key,0)
        assert 0<=poor<=total+1e-3
        result[key]=[round(100*poor/total,2),round(total,3),round(poor,3)]
    return result

data={}
with ThreadPoolExecutor(5) as pool:
    for item in pool.map(state_results,json.loads((ROOT/'state_road.json').read_bytes())):
        data.update(item)
(ROOT/'county_rough.json').write_text(json.dumps(dict(sorted(data.items())),separators=(',',':')))
print('Covered county FIPS:',len(data),'in',len({k[:2] for k in data}),'states')
