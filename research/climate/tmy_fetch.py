"""Collect historical NREL TMY3 climate summaries from DOE EnergyPlus weather files."""
import csv
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO, TextIOWrapper
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlencode, quote
from urllib.request import urlopen
from xml.etree import ElementTree as ET
from zipfile import ZipFile

DIR = Path(__file__).resolve().parent
BASE = 'https://energyplus-weather.s3.amazonaws.com/'
CACHE = DIR/'tmy_summary'
CACHE.mkdir(exist_ok=True)
BASE_PREFIX = 'north_and_central_america_wmo_region_4/USA/'
STATES = 'AL AZ AR CA CO CT DE DC FL GA ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split()

def read(url):
    for attempt in range(3):
        try:
            with urlopen(url, timeout=30) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(1+attempt)

def list_keys(state):
    params = {'list-type':2, 'prefix': BASE_PREFIX+state+'/'}
    result = []
    while True:
        root = ET.fromstring(read(BASE+'?'+urlencode(params)))
        for el in root.findall('{*}Contents'):
            key = el.findtext('{*}Key')
            if key.endswith('_TMY3.zip'):
                result.append(key)
        token=root.findtext('{*}NextContinuationToken')
        if not token:
            return result
        params['continuation-token'] = token

def process(key):
    out = CACHE/(key.split('/')[-1]+'.json')
    if out.exists():
        return
    buf = read(BASE+quote(key))
    with ZipFile(BytesIO(buf)) as z:
        member=next(n for n in z.namelist() if n.lower().endswith('.epw'))
        with z.open(member) as f:
            reader=csv.reader(TextIOWrapper(f, encoding='latin1'))
            hdr=next(reader)
            for _ in range(7):
                next(reader)
            ah=hh=wet=highrh=heat=cold=solar=sh=trh=0
            for row in reader:
                t,rh,ghi = map(float, (row[6],row[8],row[13]))
                ah+=1
                if -80<t<80 and 0<=rh<=100:
                    trh+=1
                    hh+=t>=27 and rh>=70
                    wet+=t>0 and rh>80
                    highrh+=rh>80
                    heat+=t>=35
                    cold+=t<=-18
                if 0<=ghi<1800:
                    solar+=ghi
                    sh+=1
            assert ah==8760,(key,ah)
            data={'name':hdr[1], 'state':key.split('/')[2], 'id':hdr[5], 'lat':float(hdr[6]), 'lon':float(hdr[7]), 'key':key,'hh':hh,'wet':wet,'highrh':highrh,'solar':round(solar / (1000 * 365),2) if sh==8760 else None,'hoth':heat,'coldh':cold,'joint_valid':trh,'solar_valid':sh}
            if trh!=8760:
                for v in ('hh','wet','highrh','hoth','coldh'):
                    data[v]=None
            out.write_text(json.dumps(data))
def safe(key):
    try:
        process(key);return None
    except Exception as e:
        return (key,repr(e))
if __name__=='__main__':
    keys_file=DIR/'keys.json'
    if not keys_file.exists():
        with ThreadPoolExecutor(max_workers=10) as pool:
            keys=[k for state in pool.map(list_keys,STATES) for k in state]
        keys_file.write_text(json.dumps(keys))
    keys=json.loads(keys_file.read_text())
    print(len(keys), 'TMY3 files',flush=True)
    with ThreadPoolExecutor(max_workers=14) as pool:
        errors=[e for e in pool.map(safe,keys) if e]
    print('summarized:',len(list(CACHE.glob('*.json'))),'errors:',errors[:10],flush=True)
