"""Prepare 2024 urban-area congestion readings at Census points of the lead named cities."""
import csv
import io
import json
import re
import zipfile
from urllib.request import urlretrieve
from openpyxl import load_workbook
from build import ALIASES,CACHE,HERE,SOURCES,write_json

DATA_URL='https://static.tti.tamu.edu/tti.tamu.edu/documents/umr/data/complete-data-2025-umr-by-tti.xlsx'
def norm(name):
    return name.casefold().replace('.','').strip()

def main():
    for path,url in [(CACHE/'tamu.xlsx',DATA_URL),(CACHE/'places.zip',SOURCES['places.zip']),(CACHE/'urban_areas.zip','https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_ua_national.zip')]:
        if not path.is_file():urlretrieve(url,path)
    with zipfile.ZipFile(CACHE/'places.zip') as z:
        with z.open(z.namelist()[0]) as f:
            places={}
            for row in csv.DictReader(io.TextIOWrapper(f,encoding='utf8'),delimiter='\t'):
                p={k.strip():v.strip() for k,v in row.items()}
                places[p['USPS'],norm(p['NAME'])]=p
    # San Francisco's Census place point lies far offshore because the city includes the Farallon Islands.
    with zipfile.ZipFile(CACHE/'urban_areas.zip') as z:
        with z.open(z.namelist()[0]) as f:
            sf_area = next({k.strip():v.strip() for k,v in r.items()} for r in csv.DictReader(io.TextIOWrapper(f,encoding='utf8'),delimiter='\t') if r['GEOID']=='78904')
    wb=load_workbook(CACHE/'tamu.xlsx',read_only=True,data_only=True)
    records=wb.worksheets[0].values
    for _ in range(5):next(records)
    out=[];missing=[]
    aliases={**ALIASES,('Athens','GA'):'Athens-Clarke County unified government (balance)',('East Stoudsburg','PA'):'East Stroudsburg borough',('El Paso de Robles','CA'):'El Paso de Robles (Paso Robles) city',('Homosassa Spr','FL'):'Homosassa Springs CDP',('Round Lake Bch','IL'):'Round Lake Beach village',('Urban Honolulu','HI'):'Urban Honolulu CDP',('Kailua (Hawaii County)','HI'):'Kailua CDP'}
    for row in records:
        area,state=row[1:3]
        if str(row[4])!='2024' or state in ('PR','AK','HI'):
            continue
        label=area.rsplit(' ',1)[0]
        if area=='Walla Walla-WA-OR':label='Walla Walla'
        # This multi-state area lists WI as primary but its lead named place is in IL.
        if area=='Round Lake Bch-McHenry-Grayslake IL-WI':state='IL'
        # Prefer exact full place names (e.g. Winston-Salem).
        options=[label,label.split('-')[0]]
        pts=[]
        for city in options:
            candidates=[aliases.get((city,state),'')] + [city+' '+suffix for suffix in ('city','CDP','town','village','borough','municipality','township','city (balance)')] + [city]
            pts=[places[(state,norm(n))] for n in candidates if (state,norm(n)) in places]
            if pts:break
        if not pts:
            missing.append((area,state));continue
        p=sf_area if area=="San Francisco-Oakland CA" else pts[0]
        out.append({'urban_area':area,'state':state,'lat':float(p['INTPTLAT']),'lon':float(p['INTPTLONG']),'reference_place':p['NAME'],'delay_hours_per_auto_commuter':row[23],'peak_vmt_congested_pct':row[14]})
    write_json('urban_congestion.json',out)
    print(len(out),len(missing),missing)
    assert all(r['delay_hours_per_auto_commuter']>=0 and (r['peak_vmt_congested_pct'] is None or 0<=r['peak_vmt_congested_pct']<=100) for r in out)
    assert len(out)==478 and not missing
if __name__=='__main__':main()
