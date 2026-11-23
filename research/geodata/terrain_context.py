"""Sample the user's terrain-atlas release at 2017 county internal points."""
import csv,gzip,hashlib,json,sys,zipfile
from pathlib import Path
here=Path(__file__).resolve().parent
root=here.parent
arc=Path(sys.argv[1]) if len(sys.argv)>1 else root/'terrain-context/conus-monthly-atlas-github-pages.zip'
counties=list(csv.DictReader((here/'counties.csv').open()))
def read(z,n):
    b=z.read(n)
    return json.loads(gzip.decompress(b) if n.endswith('.gz') else b)
def loc(g,r):
    x0=g['lon'][0]; y0=g['lat'][0]; dx=g['lon'][1]-x0;dy=g['lat'][1]-y0
    x=round((float(r['lon'])-x0)/dx); y=round((float(r['lat'])-y0)/dy)
    return y*g['width']+x if 0<=x<g['width'] and 0<=y<g['height'] else None
def val(arr,idx):return arr[idx] if idx is not None else None
with zipfile.ZipFile(arc) as z:
    snow=read(z,'docs/data/seasonal_snow.json.gz')
    slope=read(z,'docs/data/regional_slope.json.gz')
    meta=read(z,'docs/data/climate_months/manifest.json')
    out={r['fips']:{'snowCover':[val(m['values'],loc(snow['grid'],r)) for m in snow['months']],
        'landSlope':val(slope['variables']['slope']['values'],loc(slope['grid'],r)),'monthlyHigh':[],'monthlyLow':[]} for r in counties}
    audit={}
    for month in meta['months']:
        p='docs/'+month['path'];sha=hashlib.sha256(z.read(p)).hexdigest()
        assert sha==month['sha256'],(p,'hash mismatch')
        audit[p]=sha;c=read(z,p);grid=c['grid']
        for r in counties:
            idx=loc(grid,r);v=out[r['fips']]
            for a,b in [('monthlyHigh','max_temp_c'),('monthlyLow','min_temp_c')]:
                temp=val(grid['values'][b],idx);v[a].append(round(temp*1.8+32,1) if temp is not None else None)
    for name in ['seasonal_snow.json.gz','regional_slope.json.gz']:
        p='docs/data/'+name;audit[p]=hashlib.sha256(z.read(p)).hexdigest()
assert len(out)==3108 and all(len(o['monthlyHigh'])==len(o['snowCover'])==12 for o in out.values())
(here/'terrain_lookup.json').write_text(json.dumps(out,separators=(',',':')))
(here/'terrain-provenance.json').write_text(json.dumps({'archive':'conus-monthly-atlas-github-pages.zip','archive_sha256':hashlib.sha256(arc.read_bytes()).hexdigest(),'members_sha256':audit},indent=2))
print('Tippecanoe',out['18157'])
