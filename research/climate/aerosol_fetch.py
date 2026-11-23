from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
import shutil,time,os
DIR=Path(__file__).resolve().parent
DEST=DIR/'aerosol'
DEST.mkdir(exist_ok=True)
def fetch(pair):
    v,year=pair
    fn=f'V6NA01.CNNPM25.{v}.{year}01-{year}12.nc'
    url=f'https://satpmdata.s3.amazonaws.com/V6NA01/CNN{v}/Annual/{fn}'
    out=DEST/fn
    if not out.exists():
        for attempt in range(3):
            try:
                with urlopen(url,timeout=75) as r, open(str(out)+'.tmp','wb') as o:
                    shutil.copyfileobj(r,o)
                os.replace(str(out)+'.tmp',out)
                break
            except Exception:
                if attempt==2:raise
                time.sleep(2+attempt)
    return str(out)
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=6) as pool:
        for f in pool.map(fetch,[(v,y) for y in range(2019,2024) for v in ('DUST','SS')]):print(f,flush=True)
