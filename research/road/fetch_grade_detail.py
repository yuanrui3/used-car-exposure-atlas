"""Download original grade events and county reference intervals for the same route IDs."""
import csv,gzip,io,json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen,Request
from concurrent.futures import ThreadPoolExecutor
from time import sleep
ROOT=Path(__file__).resolve().parent
D=ROOT/'raw'/'slope';D.mkdir(exist_ok=True)
S=json.loads((ROOT/'state_road.json').read_text())
CODES=[str(int(k)) for k,v in S.items() if set('ABC') <= set(v.get('grade_event_classes_reported',v.get('grade_classes',{}))) and set('DEF').intersection(v.get('grade_event_classes_reported',v.get('grade_classes',{})))]
GWHERE="dataitem in ('GRADES_A','GRADES_B','GRADES_C','GRADES_D','GRADES_E','GRADES_F') and valuenumeric>0"
ENDPOINT='https://data.transportation.gov/resource/4wpf-u82y.csv?'
def rows(st,tag,where,select):
    path=D/(st+'_'+tag+'.csv.gz')
    if not path.exists():
        params={'$select':select,'$where':f'stateid={st} and '+where,'$limit':300000}
        url=ENDPOINT+urlencode(params)
        for j in range(3):
            try:
                req=Request(url,headers={'Accept-Encoding':'gzip'})
                with urlopen(req,timeout=65) as r:
                    body=r.read()
                    if r.headers.get('Content-Encoding','').lower()=='gzip':body=gzip.decompress(body)
                if not body.startswith(b'"routeid"') and not body.startswith(b'routeid'):raise ValueError(body[:180])
                path.write_bytes(gzip.compress(body))
                break
            except Exception:
                if j==2:raise
                sleep(2+j)
    with gzip.open(path,'rt',encoding='utf-8') as f:return list(csv.DictReader(f))

def grade(st):
    q=rows(st,'grade',GWHERE,'routeid,beginpoint,endpoint,dataitem,valuenumeric')
    assert len(q)<300000
    return sorted({r['routeid'] for r in q})

def chunks(ids,maxchars=2800):
    group=[];p=0
    for id in ids:
        if p+len(id)>maxchars and group:
            yield group;group=[];p=0
        group.append(id);p+=len(id)+4
    if group:yield group

def county(st,idx,ids):
    escaped=",".join("'"+i.replace("'","''")+"'" for i in ids)
    recs=rows(st,'county'+str(idx),"dataitem='COUNTY_ID' and routeid in("+escaped+')','routeid,beginpoint,endpoint,valuenumeric')
    assert len(recs)<300000
    return len(recs)

if __name__=='__main__':
    import concurrent.futures as cf
    with ThreadPoolExecutor(7) as ex, ThreadPoolExecutor(12) as cex:
        g={ex.submit(grade,s):s for s in CODES}
        c={}
        for task in cf.as_completed(g):
            st=g[task]
            try:ids=task.result()
            except Exception as e:print('grade failed',st,str(e),flush=True);continue
            for idx,group in enumerate(chunks(ids)):
                c[cex.submit(county,st,idx,group)]=(st,idx)
            print('grade',st,len(ids),flush=True)
        err=[]
        for task in cf.as_completed(c):
            try:task.result()
            except Exception as e:err.append((c[task],str(e)))
        print('completed',len(c),'chunks; failures:',err,flush=True)
