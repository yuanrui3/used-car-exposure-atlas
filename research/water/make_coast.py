"""Approximate nearest marine coast from a Census internal point (km)."""
import csv
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
radius_km = 6371.0088

def xyz(lon_lat):
    lon, lat = np.radians(np.asarray(lon_lat, dtype=float)).T
    return np.stack([np.cos(lat)*np.cos(lon), np.cos(lat)*np.sin(lon), np.sin(lat)], axis=1)
    
def coast_points(path):
    points = []
    for feat in json.loads(path.read_text())['features']:
        if feat['geometry']['type'] != 'LineString':
            raise ValueError('Unexpected coastline geometry')
        a = np.asarray(feat['geometry']['coordinates'])[:,:2]
        p, q = a[:-1], a[1:]
        # Wider than CONUS to include coasts in Canada and Mexico.
        keep = (np.maximum(p[:,0],q[:,0]) >= -164) & (np.minimum(p[:,0],q[:,0]) <= -51) & (np.maximum(p[:,1],q[:,1]) >= 12) & (np.minimum(p[:,1],q[:,1]) <= 73) & (np.abs(q[:,0]-p[:,0])<180)
        p, q = p[keep], q[keep]
        if not len(p): continue
        # No gap between sampled coastline points larger than ~0.5 km.
        u, v = xyz(p), xyz(q)
        counts = np.maximum(1,np.ceil(2*radius_km*np.arcsin(np.minimum(1,np.linalg.norm(u-v,axis=1)/2))/.5).astype(int))
        ends = np.cumsum(counts)
        start = np.r_[0,ends[:-1]]
        ix=np.repeat(np.arange(len(p)),counts)
        frac=(np.arange(ends[-1])-start[ix])/counts[ix]
        samples=u[ix]+frac[:,None]*(v[ix]-u[ix])
        samples /= np.linalg.norm(samples,axis=1)[:,None]
        points.extend((samples,v[-1:]))
    return np.vstack(points)
    
if __name__ == '__main__':
    rows=list(csv.DictReader(open(HERE.parent/'geodata/counties.csv')))
    tree=cKDTree(coast_points(HERE/'coastline.geojson'))
    with (HERE/'census_tracts.csv').open(encoding='utf-8-sig') as src:
        tracts=list(csv.DictReader(src))
    fips={row['fips'] for row in rows}
    tracts=[r for r in tracts if r['STATEFP']+r['COUNTYFP'] in fips and int(r['POPULATION'])>0]
    coords=xyz([(r['LONGITUDE'],r['LATITUDE']) for r in tracts])
    d,_=tree.query(coords)
    km=2*radius_km*np.arcsin(np.minimum(1,d/2))
    from collections import defaultdict
    totals=defaultdict(lambda: [0,0,0])
    for t,dist in zip(tracts,km):
        z=totals[t['STATEFP']+t['COUNTYFP']]; n=int(t['POPULATION'])
        z[0]+=n; z[1]+=n*dist; z[2]+=n*(dist<=5)
    assert len(totals)==len(rows),(fips-set(totals))
    data={k:[round(d/n,1),round(100*close/n,1)] for k,(n,d,close) in totals.items()}
    (HERE/'coast_counties.json').write_text(json.dumps(dict(sorted(data.items())),separators=(',',':')))
    print('Counties, populated tracts',len(totals),len(tracts))
    for k in ['17031','06075','12086','18001','06037','22071','53033','26081','42003','08031']:
        print(k,data[k])
