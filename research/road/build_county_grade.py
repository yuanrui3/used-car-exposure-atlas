"""Assign only unambiguous whole, length-checked grade intervals to counties."""
from collections import defaultdict
from bisect import bisect_right
import csv,gzip,json
from pathlib import Path
from fetch_grade_detail import CODES,ROOT,D,chunks

valid_counties=set(json.loads((ROOT/'county_rough.json').read_text()))
# Preserve counties with little or no measured pavement; Census and HPMS vintage differ in Connecticut.
from zipfile import ZipFile
from io import TextIOWrapper
with ZipFile(ROOT/'raw'/'2020_Gaz_counties_national.zip') as z:
    valid_counties.update(r['GEOID'] for r in csv.DictReader(TextIOWrapper(z.open(z.namelist()[0]),encoding='latin1'),delimiter='\t'))

result,log={},{}
for st in CODES:
    sf=D/(st+'_grade.csv.gz')
    if not sf.exists():continue
    with gzip.open(sf,'rt') as f:
        rr=list(csv.DictReader(f))
    ids=sorted({r['routeid'] for r in rr})
    refs=[D/f'{st}_county{i}.csv.gz' for i,_ in enumerate(chunks(ids))]
    if not all(p.exists() for p in refs):continue
    county_intervals=defaultdict(list)
    for p in refs:
        with gzip.open(p,'rt') as f:
            for r in csv.DictReader(f):
                try:
                    code=f'{int(st):02}{int(float(r["valuenumeric"])):03}'
                    a,b=map(float,(r['beginpoint'],r['endpoint']))
                except (ValueError,TypeError):continue
                if code in valid_counties and b>a:county_intervals[r['routeid']].append((a,b,code))
    # Merge adjacent/overlapping references in the same county. Keep intervals
    # in different counties distinct so ambiguous overlaps can be rejected.
    byroute={}
    for rt,v in county_intervals.items():
        merged=[]
        for a,b,county in sorted(set(v)):
            if merged and merged[-1][2]==county and a<=merged[-1][1]+1e-6:
                merged[-1][1]=max(merged[-1][1],b)
            else:merged.append([a,b,county])
        byroute[rt]=merged

    segments=defaultdict(lambda:defaultdict(list))
    duplicates=set()
    for r in rr:
        rt=r['routeid'];a,b=map(float,(r['beginpoint'],r['endpoint']))
        if b<=a:continue
        key=(rt,a,b);letter=r['dataitem'][-1];vals=segments[rt][(a,b)]
        if any(row[0]==letter for row in vals):duplicates.add(key)
        vals.append((letter,float(r['valuenumeric'])))
    miles=defaultdict(lambda:[0.,0.,0])
    raw=sum(float(r['valuenumeric']) for r in rr)
    for rt,samples in segments.items():
        ramps=byroute.get(rt,[])
        if not ramps:continue
        ordered=sorted(samples)
        overlaps=set()
        max_end=-1.;max_seg=None
        for ab in ordered:
            if ab[0]<max_end-1e-6:
                overlaps.add(ab);overlaps.add(max_seg)
            if ab[1]>max_end:max_end=ab[1];max_seg=ab
        def consistent(a,b,val):
            return abs(sum(v for _,v in val)-(b-a)) <= max(0.005,0.02*(b-a))
        candidates=[]
        pending=None
        for a,b in ordered:
            if (a,b) in overlaps or (rt,a,b) in duplicates:
                pending=None
                continue
            vals=tuple(sorted(samples[a,b]))
            if consistent(a,b,vals):
                pending=None
                if b-a>=0.05:candidates.append((a,b,vals))
                continue
            # Some states repeat a sample's grade-class vector on each shorter
            # child event. Count it once, only if a continuous run with an
            # identical vector reconstructs the stated mileage independently.
            if pending is not None and abs(a-pending[1])<=1e-6 and vals==pending[2]:
                pending=(pending[0],b,vals)
            else:
                pending=(a,b,vals)
            if consistent(*pending):
                if pending[1]-pending[0]>=0.05:candidates.append(pending)
                pending=None
        for a,b,vals in candidates:
            total=sum(v for _,v in vals)
            cs={county for x,y,county in ramps if x < b-1e-6 and y>a+1e-6}
            if len(cs)!=1:continue
            county=next(iter(cs))
            if not any(c==county and x<=a+1e-6 and b<=y+1e-6 for x,y,c in ramps):continue
            steep=sum(v for k,v in vals if k in 'DEF')
            m=miles[county];m[0]+=steep;m[1]+=total;m[2]+=1
    accepted=sum(x[1] for x in miles.values())
    log[st]=[round(raw,2),round(accepted,2),len(miles)]
    for k,(steep,total,n) in miles.items():
        assert 0<=steep<=total+1e-6
        result[k]=[round(100*steep/total,2),round(total,3),round(steep,3),n]

(ROOT/'county_grade.json').write_text(json.dumps(dict(sorted(result.items())),separators=(',',':')))
(ROOT/'grade_audit.json').write_text(json.dumps(dict(sorted(log.items())),indent=2))
print('States fully downloaded:',len(log),'counties with any sample:',len(result),'counties with 10+ mi and ≥3 intervals:',sum(1 for v in result.values() if v[1]>=10 and v[3]>=3),flush=True)
