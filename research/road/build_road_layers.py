"""Rebuild 2024 state inventory layers. Python 3 + lxml. Cached raw inputs are optional."""
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
import json
from lxml import html

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw'
RAW.mkdir(exist_ok=True)
PAVEMENT = 'https://www.fhwa.dot.gov/policyinformation/statistics/2024/hm47i.cfm'
SURFACE = 'https://www.fhwa.dot.gov/policyinformation/statistics/2024/hm51.cfm'
EVENTS = 'https://data.transportation.gov/resource/4wpf-u82y.json'
GRADE_CLASSES = tuple('ABCDEF')
STATE_IDS = {
    'Alabama':1,'Arizona':4,'Arkansas':5,'California':6,'Colorado':8,
    'Connecticut':9,'Delaware':10,'Florida':12,'Georgia':13,'Idaho':16,
    'Illinois':17,'Indiana':18,'Iowa':19,'Kansas':20,'Kentucky':21,
    'Louisiana':22,'Maine':23,'Maryland':24,'Massachusetts':25,'Michigan':26,
    'Minnesota':27,'Mississippi':28,'Missouri':29,'Montana':30,'Nebraska':31,
    'Nevada':32,'New Hampshire':33,'New Jersey':34,'New Mexico':35,
    'New York':36,'North Carolina':37,'North Dakota':38,'Ohio':39,'Oklahoma':40,
    'Oregon':41,'Pennsylvania':42,'Rhode Island':44,'South Carolina':45,
    'South Dakota':46,'Tennessee':47,'Texas':48,'Utah':49,'Vermont':50,
    'Virginia':51,'Washington':53,'West Virginia':54,'Wisconsin':55,'Wyoming':56
}

def retrieve(url, filename):
    path = RAW / filename
    if not path.is_file():
        with urlopen(url, timeout=90) as response:
            path.write_bytes(response.read())
    return path

def table_rows(table):
    rows = {}
    for tr in table.xpath('.//tr'):
        cells = [' '.join(td.text_content().split()).strip() for td in tr.xpath('./td|./th')]
        if cells and cells[0] in STATE_IDS:
            rows[cells[0]] = cells[1:]
    assert len(rows) == 48
    return rows

def read_miles(cell):
    if cell == '-':
        return 0
    return int(cell.replace(',',''))

def pct(a,b):
    return round(100 * a / b, 2) if b and a is not None else None

pavement_doc = html.parse(retrieve(PAVEMENT,'2024-hm47i.cfm'))
surface_doc = html.parse(retrieve(SURFACE,'2024-hm51.cfm'))
pavement = table_rows(pavement_doc.xpath('//table')[0])
rural = table_rows(surface_doc.xpath('//table')[1])
urban = table_rows(surface_doc.xpath('//table')[3])

params = {'$select':'stateid,dataitem,sum(valuenumeric) as miles,count(*) as n',
          '$where':"dataitem in('Grades_A','Grades_B','Grades_C','Grades_D','Grades_E','Grades_F','GRADES_A','GRADES_B','GRADES_C','GRADES_D','GRADES_E','GRADES_F')",
          '$group':'stateid,dataitem','$limit':900}
grades = defaultdict(dict)
for row in json.loads(retrieve(EVENTS+'?'+urlencode(params),'grade.json').read_bytes()):
    code = int(row['stateid'])
    letter = row['dataitem'].upper()[-1]
    assert letter in GRADE_CLASSES and letter not in grades[code]
    grades[code][letter] = float(row['miles'])

clean_by_state=defaultdict(lambda:[0.0,0.0,0])
county_grades=ROOT/'county_grade.json'
if county_grades.exists():
    for fips, (_,miles,steep_miles,intervals) in json.loads(county_grades.read_bytes()).items():
        record=clean_by_state[int(fips[:2])]
        record[0]+=miles;record[1]+=steep_miles;record[2]+=intervals

data = {}
for name, code in STATE_IDS.items():
    p = pavement[name]
    assert len(p)==15 and len(rural[name])==12 and len(urban[name])==15
    rough, reported, unreported = map(read_miles, [p[-2],p[-1],p[-5]])
    by_surface = [x[-3:] for x in [rural[name],urban[name]]]
    locations_complete = all(read_miles(xs[-1])>0 for xs in by_surface)
    unpaved = sum(read_miles(xs[0]) for xs in by_surface) if locations_complete else None
    local_total = sum(read_miles(xs[-1]) for xs in by_surface) if locations_complete else None
    g = grades[code]
    grade_total,steep,intervals=clean_by_state[code]
    usable=grade_total>=100 and intervals>=10
    grade_total=round(grade_total,3)
    steep=round(steep,3) if usable else None
    data[f'{code:02d}'] = dict(name=name,
        rough_pct=pct(rough,reported),rough_miles=rough,rough_reported_miles=reported,
        rough_unreported_miles=unreported,rough_coverage_pct=pct(reported,reported+unreported),
        unpaved_local_pct=pct(unpaved,local_total),unpaved_local_miles=unpaved,local_miles=local_total,
        steep_pct=pct(steep,grade_total),steep_miles=steep,grade_reported_miles=grade_total,
        grade_accepted_intervals=intervals,grade_event_classes_reported=sorted(g))
(ROOT/'state_road.json').write_text(json.dumps(data,indent=2)+'\n')
for metric in ['rough_pct','unpaved_local_pct','steep_pct']:
    valid = [r for r in data.values() if r[metric] is not None]
    assert all(0<=r[metric]<=100 for r in valid)
    print(metric,len(valid),'states; missing', [r['name'] for r in data.values() if r[metric] is None])
