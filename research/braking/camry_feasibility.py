"""Count initial safety results in one NY make/model/year and mileage cohort."""
from pathlib import Path
import json
from pilot import retrieve

HERE=Path(__file__).resolve().parent
filters=[
    "inspection_date >= '2026-05-01T00:00:00'",
    "inspection_date < '2026-06-01T00:00:00'",
    "inspection_type='INITIAL INSPECTION'",
    "registration_class='PASSENGER'",
    "model_year=2018",
    "make_code='TOYOT'",
    "upper(model_name)='CAMRY'",
    "odometer_reading >= 60000",
    "odometer_reading < 130000",
    "safety_inspection_result in ('PASS','FAIL')"
]
rows=retrieve('vezn-fmmk',{'$select':'odometer_reading,safety_inspection_result','$where':' AND '.join(filters),'$limit':5000})
assert 0<len(rows)<5000
results={k:{'PASS':0,'FAIL':0} for k in range(60000,130000,10000)}
for row in rows:
    key=int(row['odometer_reading'])//10000*10000
    assert key in results
    results[key][row['safety_inspection_result']]+=1
cohort={'period':'2026-05, New York statewide','filters':filters,'mileage_bins_lower_inclusive_width_10000':results,'n':sum(sum(row.values()) for row in results.values()),'fails':sum(row['FAIL'] for row in results.values()),'role':'A sizing exercise using transactions, overall safety outcome and DMV-entered model. Does not test geography, identify a failing part or measure individual lifetime exposure.'}
print(json.dumps(cohort, indent=2))
(HERE/'camry_feasibility.json').write_text(json.dumps(cohort,indent=2)+'\n')
