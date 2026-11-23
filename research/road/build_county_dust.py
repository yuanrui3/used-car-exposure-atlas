"""Compile EPA modeled road-dust emissions per 2020 Census county land area."""
import csv, json
from io import TextIOWrapper
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile
from shutil import copyfileobj

ROOT=Path(__file__).resolve().parent
D=ROOT/'raw'
NEI='https://gaftp.epa.gov/air/nei/2020/data_summaries/2020neiMar_county_tribe_allsector.zip'
CENSUS='https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_counties_national.zip'
def archive(url):
    f=D/url.rsplit('/',1)[-1]
    if not f.exists():
        with urlopen(url,timeout=240) as src,open(f,'wb') as dst:
            copyfileobj(src,dst)
    return ZipFile(f)

states=json.loads((ROOT/'state_road.json').read_text())
with archive(CENSUS) as z:
    geog={r['GEOID']:float(r['ALAND_SQMI']) for r in csv.DictReader(TextIOWrapper(z.open(z.namelist()[0]),encoding='latin1'),delimiter='\t') if r['GEOID'][:2] in states}
dust={}
with archive(NEI) as z:
    member=next(x for x in z.namelist() if x.endswith('.csv'))
    rows=csv.DictReader(TextIOWrapper(z.open(member),encoding='latin1',newline=''))
    for r in rows:
        if r['sector']!='Dust - Unpaved Road Dust' or r['pollutant code']!='PM10-PRI' or r['tribal name']:continue
        fips=r['fips code']
        if fips not in geog:continue
        assert r['emissions uom']=='TON' and r['reporting period']=='A' and r['data set']=='2020NEI'
        assert fips not in dust
        dust[fips]=float(r['total emissions'])
data={fips:{'pm10_tons':v,'land_sqmi':geog[fips],'tons_per_sqmi':round(v/geog[fips],4)} for fips,v in sorted(dust.items())}
(ROOT/'county_dust.json').write_text(json.dumps(data,separators=(',',':')))
stats={}
for state in states:
    area={k:v for k,v in geog.items() if k[:2]==state}
    reported={k:dust[k] for k in area if k in dust}
    reported_area=sum(area[k] for k in reported)
    stats[state]={'total_counties':len(area),'reported_counties':len(reported),'reported_land_sqmi':round(reported_area,2),'pm10_tons':round(sum(reported.values()),3),'tons_per_sqmi':round(sum(reported.values())/reported_area,4) if reported_area else None}
(ROOT/'state_dust.json').write_text(json.dumps(stats,indent=2)+'\n')
print('Counties:',len(data),'of',len(geog),'States:',sum(1 for v in stats.values() if v['reported_counties']))
