"""County polygon means of the 2019–2023 modeled fine dust and sea salt in SatPM V6.NA.01.
Uses system GDAL Python bindings. County boundaries are the 2017 Census cartographic boundary file, 1:500,000.
"""
import csv, json
from pathlib import Path
from osgeo import gdal, ogr, osr
import numpy as np
gdal.UseExceptions()
DIR=Path(__file__).resolve().parent
files={kind:sorted((DIR/'aerosol').glob('V6NA01.CNNPM25.'+kind+'.*.nc')) for kind in ('SS','DUST')}
assert all(len(ff)==5 for ff in files.values())
xoff,yoff,w,h=4400,2000,6000,2600
g0=gdal.Open(str(files['SS'][0])).GetGeoTransform()
gt=[g0[0]+xoff*g0[1],g0[1],0,g0[3]+yoff*g0[5],0,g0[5]]
mask=gdal.GetDriverByName('MEM').Create('',w,h,1,gdal.GDT_Int32)
mask.SetGeoTransform(gt)
srs=osr.SpatialReference()
srs.ImportFromEPSG(4326)
mask.SetProjection(srs.ExportToWkt())
shapes=ogr.Open('/vsizip/'+str(DIR/'cb_2017_us_county_500k.zip'))
gdal.RasterizeLayer(mask,[1],shapes.GetLayer(),options=['ATTRIBUTE=GEOID'])
fips=mask.ReadAsArray()
counties=list(csv.DictReader((DIR.parent/'geodata'/'counties.csv').open()))
results={r['fips']:{} for r in counties}
lat=gt[3]+(np.arange(h)+.5)*gt[5]
weights=np.broadcast_to(np.cos(np.deg2rad(lat))[:,None],(h,w))
for key,paths in files.items():
    total=np.zeros(57000)
    n=np.zeros(57000,dtype=int)
    for path in paths:
        d=gdal.Open(str(path))
        v=d.ReadAsArray(xoff,yoff,w,h)
        m=np.isfinite(v)&(fips>0)&(v>=0)
        ids,ww=fips[m],weights[m]
        sums=np.bincount(ids,weights=v[m]*ww,minlength=57000)
        den=np.bincount(ids,weights=ww,minlength=57000)
        ok=den>0
        total[ok]+=sums[ok]/den[ok]
        n+=ok
    k='seaSalt' if key=='SS' else 'dust'
    for fi,result in results.items():
        ix=int(fi)
        result[k]=round(total[ix]/5,3) if n[ix]==5 else None
    print(key, 'coverage',sum(r[k] is not None for r in results.values()),'summary',np.nanpercentile([a[k] or np.nan for a in results.values()],[0,25,50,75,100]),flush=True)
out=DIR/'aerosol_counties.json'
out.write_text(json.dumps(results,separators=(',',':')))
for f in ['18157','04013','12086','06073']:print(f,results[f])
