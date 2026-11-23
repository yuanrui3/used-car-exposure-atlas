"""Feasibility audit: public NY inspection transactions and join coverage. No vehicle identifiers are requested."""
import collections
import json
from pathlib import Path
import urllib.parse
import urllib.request

HERE=Path(__file__).resolve().parent
def retrieve(asset,params):
    url='https://data.ny.gov/resource/'+asset+'.json?'+urllib.parse.urlencode(params)
    with urllib.request.urlopen(url,timeout=65) as r:
        return json.load(r)

def main():
    # Short timestamp interval is available in this historical DMV release.
    period="inspection_date >= '2026-05-29T12:00:00' AND inspection_date < '2026-05-29T13:00:00'"
    fields='inspection_date,inspection_type,safety_inspection_result,registration_class,make_code,model_year,model_name,odometer_reading,dmv_facility_number'
    rows=retrieve('vezn-fmmk',{'$select':fields,'$where':period,'$limit':50000})
    assert len(rows)<50000 and rows
    facilities = retrieve('nhjr-rpi2',{'$select':'distinct facility,facility_county','$where':"business_type in ('ISP','ISD','ISF') AND facility_county is not null",'$limit':50000})
    assert len(facilities)<50000
    counties=collections.defaultdict(set)
    for f in facilities: counties[f['facility']].add(f['facility_county'])
    # Restrict to initial passenger inspections with a pass/fail result, positive odometer and identifiable make, model and model year.
    eligible = [r for r in rows if r.get('inspection_type')=='INITIAL INSPECTION' and r.get('registration_class')=='PASSENGER' and r.get('safety_inspection_result') in ('PASS','FAIL') and 0<float(r.get('odometer_reading') or 0)<1_000_000 and all(r.get(key) for key in ('make_code','model_name','model_year'))]
    matched = [r for r in eligible if len(counties.get(r.get('dmv_facility_number',''),set()))==1]
    result=dict(period='2026-05-29 12:00 to before 13:00, source local time',transactions=len(rows),eligible=len(eligible),result_counts=dict(collections.Counter(r['safety_inspection_result'] for r in eligible)),matchable_to_one_facility_county=len(matched),distinct_matched_counties=len({next(iter(counties[r['dmv_facility_number']])) for r in matched}),source_facility_rows=len(facilities),eligibility='Initial inspection; passenger registration; system safety PASS/FAIL; nonempty make, model and model year; reported odometer >0 and <1,000,000 miles.',limitations='One hour of transactions; facility county describes where the vehicle was inspected; it provides no ownership history or cause of rejection. This tests availability only.')
    print(json.dumps(result,indent=2))
    (HERE/'ny_inspection_feasibility.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':
    main()
