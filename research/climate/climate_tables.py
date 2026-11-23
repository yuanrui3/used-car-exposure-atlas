"""Rebuild county climate proxies from NOAA normals and DOE-hosted NREL TMY3 summaries."""
import csv, io, json, math, tarfile, urllib.request, shutil
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

DIR=Path(__file__).resolve().parent
COUNTIES=DIR.parent/'geodata'/'counties.csv'
NORMALS_URL='https://noaa-normals-pds.s3.amazonaws.com/normals-annualseasonal/1991-2020/archive/us-climate-normals_1991-2020_v1.0.1_annualseasonal_multivariate_by-station_c20230404.tar.gz'
STATES=set('AL AZ AR CA CO CT DE DC FL GA ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())
CODES={'hot90':'ANN-TMAX-AVGNDS-GRTH090','hot100':'ANN-TMAX-AVGNDS-GRTH100','cold0':'ANN-TMIN-AVGNDS-LSTH000','freeze_min':'ANN-TMIN-AVGNDS-LSTH032','ice_day':'ANN-TMAX-AVGNDS-LSTH032'}
def unit_xyz(rows):
    lat,lon=np.radians([[float(r['lat']),float(r['lon'])] for r in rows]).T
    return np.column_stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])
def nearest(ct,src):
    d,i=cKDTree(unit_xyz(src)).query(unit_xyz(ct))
    return zip(i,np.arcsin(d/2)*2*6371.0088)
def norms():
    archive=DIR/'normals.tar.gz'
    if not archive.exists():
        with urllib.request.urlopen(NORMALS_URL) as src, archive.open('wb') as out:
            shutil.copyfileobj(src, out)
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            if not member.isfile() or not member.name.startswith('US'):continue
            row=next(csv.DictReader(io.StringIO(tar.extractfile(member).read().decode())))
            state=row['NAME'].split()[-2]
            if state not in STATES:continue
            if any(row.get('comp_flag_'+c,'').strip()!='S' for c in CODES.values()):continue
            vals={k:float(row[c]) for k,c in CODES.items()}
            if any(not 0<=v<=366 for v in vals.values()):continue
            ft=round(vals.pop('freeze_min')-vals.pop('ice_day'),1)
            if ft<0:continue
            yield {'id':row['STATION'],'name':row['NAME'],'lat':float(row['LATITUDE']),'lon':float(row['LONGITUDE']),'ft':ft,**vals}
def join(data, stations, keep, name):
    for row,(i,dist) in zip(data,nearest(data,stations)):
        station=stations[i]
        row.update({k:station[k] for k in keep})
        row[name+'_site']=station['id']
        row[name+'_km']=round(float(dist),1)
if __name__=='__main__':
    import sys
    data=list(csv.DictReader(COUNTIES.open()))
    normfile=DIR/'normals_stations.json'
    if not normfile.exists():
        stations=list(norms())
        normfile.write_text(json.dumps(stations,separators=(',',':')))
    n=json.loads(normfile.read_text())
    join(data,n,['hot90','hot100','cold0','ft'],'noaa')
    tfile=DIR/'keys.json'
    if '--tmy' in sys.argv:
        t=[json.loads(f.read_text()) for f in sorted((DIR/'tmy_summary').glob('*.json'))]
        t=[s for s in t if s['joint_valid']==8760 and s['solar_valid']==8760]
        (DIR/'tmy_stations.json').write_text(json.dumps(t,separators=(',',':')))
        join(data,t,['hh','wet','highrh','hoth','coldh','solar'],'tmy')
        print('TMY stations',len(t),'downloads',len(list((DIR/'tmy_summary').glob('*.json'))),flush=True)
    data={r['fips']:{k:v for k,v in r.items() if k not in ['fips','county','state','lat','lon']} for r in data}
    out=DIR/('climate_counties.json' if '--tmy' in sys.argv else 'noaa_counties.json')
    out.write_text(json.dumps(data,separators=(',',':')))
    print('NOAA sites',len(n),'rows',len(data), 'sample',[(k,data[k]) for k in ['18157','04013','12086']],flush=True)
