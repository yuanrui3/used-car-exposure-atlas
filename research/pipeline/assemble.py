from pathlib import Path
import csv, json, html, zipfile
from annual import build_annual
from collections import OrderedDict
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT.parent/'docs/assets'
WEB.mkdir(parents=True,exist_ok=True)
def read(path,default=None):
    p=ROOT/path
    if p.exists(): return json.loads(p.read_text())
    if default is not None: return default
    raise FileNotFoundError(p)
def write(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')))
def src(title,url):return [title,url]
NOAA=src('NOAA climate normals','https://www.ncei.noaa.gov/access/us-climate-normals/')
TMY=src('NREL TMY3 technical manual','https://www.nrel.gov/docs/fy08osti/43156.pdf')
EPW=src('DOE EnergyPlus station files','https://energyplus.net/weather')
SHORE=src('Natural Earth coastlines','https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/')
CENS=src('Census population centers','https://www.census.gov/geographies/reference-files/2020/geo/2020-centers-population.html')
CLR=src('Clear Roads survey','https://www.clearroads.org/winter-maintenance-survey/')
VTRANS=src('VTrans survey map, p. 7','https://legislature.vermont.gov/Documents/2024/WorkGroups/House%20Transportation/Agency%20of%20Transportation%20Overview/Agency%20of%20Transportation%20Overview/AOT%20District%20Maintenance%20Division/Witness%20Documents/W~Todd%20Law~AOT%20District%20Maintenance%20and%20Fleet%20Division%20Water%20Quality%2C%20Stormwater%20Management%20and%20Winter%20Road%20Treatment%20Practices~1-18-2023.pdf#page=7')
HM81=src('FHWA state lane-miles','https://www.fhwa.dot.gov/policyinformation/statistics/2022/hm81.cfm')
HPMS=src('FHWA grade records','https://data.transportation.gov/d/4wpf-u82y')
GRADE=src('FHWA grade definitions','https://www.fhwa.dot.gov/policyinformation/hpms/fieldmanual/page06.cfm')
ROUGH=src('FHWA pavement ratings','https://www.fhwa.dot.gov/policyinformation/statistics/2024/hm47i.cfm')
UNPAVED=src('FHWA road surfaces','https://www.fhwa.dot.gov/policyinformation/statistics/2024/hm51.cfm')
URBAN=src('Census urban and rural data','https://www.census.gov/programs-surveys/geography/guidance/geo-areas/urban-rural.html')
BRAKE=src('Allstate city measurements','https://www.allstate.com/resources/allstate/attachments/best-drivers/full-americas-best-drivers-report-v2.pdf')
STORM=src('NOAA Storm Events Database','https://www.ncei.noaa.gov/stormevents/')
STORM_RAW=src('NOAA annual event files','https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/')
groups={};metrics={}
def group(id,title,mode='exposure'):groups[id]=dict(id=id,title=title,mode=mode,keys=[])
for id,title in [('winter','Snow, ice & road salt'),('coast','Coastal salt air'),('wet','Moisture & humid heat'),('heat','Extreme heat & sun'),('cold','Extreme cold & freeze–thaw'),('grade','Hills & sustained grades'),('traffic','Braking & congestion'),('rough','Rough pavement'),('dust','Dust & unpaved roads')]:group(id,title)
group('flood','Flood history','events');group('hail','Hail history','events')
def metric(g,key,title,unit,bins,palette,scale,period,desc,method,sources,**kwargs):
    entry=dict(title=title,unit=unit,bins=bins,palette=palette,scale=scale,period=period,desc=desc,method=method,src=sources,digits=1,**{k:v for k,v in kwargs.items() if k!='digits'})
    entry['digits']=kwargs.get('digits',1);groups[g]['keys'].append(key);metrics[key]=entry
def movefirst(g,k):
    groups[g]['keys'].remove(k);groups[g]['keys'].insert(0,k)
metric('winter','salt','Dry road salt applied','tons/lane-mi',[.5,2,5,10,16],'earth','State DOT','Winter 2021–22','Dry road salt used by the state highway agency per state-owned lane-mile. Municipal application and liquid brine are outside this reading.','Divides reported US short tons of dry salt by 2022 state-owned lane-miles. One winter. States that did not report remain unshaded.',[CLR,VTRANS,HM81],digits=2,note='State average over the state-owned network.')
metric('coast','coast5','Residents within 5 km of the sea','% of residents',[.1,5,15,35,65],'cool','County · tract proxy','2020 population','Share of county residents represented by populated tract centers within 5 km of an ocean or marine bay. Wind and shelter change local exposure.','Distance from each populated Census tract’s population center to the Natural Earth marine coastline. Sum tract populations inside a 5 km threshold and divide by county population. Great Lakes excluded. The 5 km cutoff illustrates proximity.',[CENS,SHORE],note='The 5 km band is a proximity proxy.')
metric('coast','coastkm','Mean distance to saltwater coast','km',[10,50,150,400,800],'cool','County · tract proxy','2020 population','Population-weighted distance between Census tract centers and the nearest mapped marine coastline. Darker shading marks closer locations.','Length is approximate great-circle distance. It covers coasts in the U.S., Canada and Mexico. Census tract population weights locate residences within large counties.',[CENS,SHORE],reverse=True)
tmyper='TMY3 · records through 2005'
for g,k,name,unit,bins,pal,how,d in [
    ('wet','hh','Humid heat','hr/typical yr',[25,150,400,900,1600],'hot','Hours with air temperature ≥27°C (81°F) and relative humidity ≥70% at the same time.',0),
    ('wet','wet','Atmospheric wetness proxy','hr/typical yr',[950,1800,2400,3300,4500],'cool','Hours with air temperature >0°C and relative humidity >80%. This estimates conditions favorable to surface wetness. Rain, dew and vehicle shelter can change actual wetness.',0),
    ('wet','highrh','High relative humidity','hr/typical yr',[1200,2000,2800,3600,4400],'cool','Hours of high outdoor relative humidity at the matched station.',0),
    ('heat','hoth','Heat at or above 35°C','hr/typical yr',[5,50,160,350,650],'hot','Hours with station air temperature ≥35°C (95°F).',0),
    ('heat','solar','Solar energy at ground level','kWh/m²/day',[3.5,4,4.5,5,5.5],'hot','Annual mean daily global horizontal solar irradiation. Outdoor solar energy serves as a proxy for sun exposure. UV dose and indoor parking require additional information.',2),
    ('cold','coldh','Hours of severe cold','hr/typical yr',[1,10,60,200,500],'cool','Hours at the severe-cold temperature threshold in the typical station year.',0),
]:
    metric(g,k,name,unit,bins,pal,'Nearest TMY3 station',tmyper,how,how+' Nearest qualifying station to the county internal point. TMY3 assembles 12 historical representative months from 15- or 30-year archives; this is a typical weather year and cannot reconstruct a particular ownership period.',[TMY,EPW],digits=d,station='tmy',note='Station-based estimate for the county reference point.')
for g,k,title,bins,pal,how in [
    ('heat','hot90','Days reaching 90°F',[5,20,45,75,105],'hot','Average days each year when the daily high reaches at least 90°F.'),
    ('heat','hot100','Days reaching 100°F',[.5,2,8,20,45],'hot','Average days each year when the daily high reaches at least 100°F.'),
    ('cold','ft','Freeze–thaw days',[15,40,65,90,120],'cool','Average days with a low at or below 32°F and a high above 32°F. Air temperature is a proxy for vehicle-surface temperature.'),
    ('cold','cold0','Nights reaching 0°F or colder',[.1,2,7,15,30],'cool','Average days per year when the minimum reaches 0°F or colder. Cold-start counts depend on when the vehicle was driven.')
]:
    metric(g,k,title,'days/year',bins,pal,'Nearest NOAA station','1991–2020',how,how+' Each county internal point is matched to the nearest station with standard NOAA completeness flags in the five temperature inputs. Freeze–thaw days equal the count of nights ≤32°F minus days with a maximum ≤32°F.',[NOAA],station='noaa',note='30-year climate normal at the matched station.')
movefirst('heat','hot90');movefirst('cold','ft')
metric('grade','steep','Road miles at ≥4.5% grade','% of sampled miles',[1,3,7,14,25],'earth','State · sampled roads','2024','Share of grade-classified road miles with absolute grade of at least 4.5%. Both uphill and downhill miles contribute.','FHWA reported grade D, E and F mileage divided by grade A–F mileage. Sample composition and reporting vary by state. Direction, continuous descent length and local-road coverage are unavailable. Ambiguous steep-class reporting is left missing.',[HPMS,GRADE],note='Measured sample largely covers major roads.')
metric('traffic','urban','Population living in urban areas','% of residents',[10,30,50,70,90],'violet','County · urbanization proxy','2020','Share of county residents in Census-defined urban areas. It gives a nationwide proxy for stop-and-go exposure.','2020 Census urban population divided by total county population. Local roads, commute patterns and trip times can differ considerably within this area. The value cannot be converted directly to stops, brake applications or idle time.',[URBAN])
metric('traffic','brake','Hard-braking events','events/1,000 mi',[13,16,19,23,28],'hot','City · measured trips','2016–17','Hard-braking events per 1,000 miles in the participating city’s Drivewise sample. Normal stops and braking energy require separate measurements.','2019 Allstate report using opt-in Drivewise observations from 2016–17. Points locate 125 city or Census-designated place centers with published rates in the contiguous U.S. Only observed places are shown. A city point displayed for a county identifies its location and does not extend its rate to the whole county.',[BRAKE],point='brake',digits=3,binDigits=0,note='City point observations. Gray land falls outside the point sample.')
metric('rough','rough','Rough federal-aid road miles','% of rated miles',[5,10,15,22,32],'earth','State · rated roads','2024','Share of rated federal-aid network miles with poor ride quality. The proportion of the network rated varies by state.','Poor = International Roughness Index >170 in/mi or Present Serviceability Rating <2.6 in FHWA HM-47I. The denominator is rated network mileage. Check reporting coverage before comparing states.',[ROUGH])
metric('rough','roughcov','Federal-aid pavement rating coverage','% of network miles',[45,65,80,90,98],'cool','State · rated roads','2024','Share of federal-aid network mileage included in the state pavement ratings. Larger values mean more complete measurements.','Reported mileage divided by reported plus unreported mileage as tabulated in HM-47I.',[ROUGH],note='This layer describes reporting coverage.')
metric('dust','unpaved','Unpaved local-road miles','% of local-road miles',[2,8,20,35,55],'earth','State · road surface proxy','2024','Share of reported local public road mileage classified as unpaved. This measures the chance of encountering unpaved roads on the network.','FHWA HM-51 rural and urban local-system miles, combined. Does not weight routes by traffic or estimate dust concentrations. Both rural and urban local mileage totals must be reported.',[UNPAVED])
for g,k,which,bins in [('flood','flood','flood or flash-flood',[2,5,10,20,40]),('hail','hail','hail',[2,5,15,30,55])]:
    metric(g,k,('Flood' if g=='flood' else 'Hail')+' report days','days/10 yr',bins,'violet','County · event reports','2015–2024','Distinct dates with one or more county-coded '+which+' reports. A report can involve only part of the county.','Unique local begin dates per county across 10 calendar years. NOAA types '+('Flood and Flash Flood' if g=='flood' else 'Hail')+'. Excludes forecast-zone reports, including coastal-flood categories, and events without a county code. A zero records no qualifying report. Reporting intensity and county size affect comparisons; vehicle damage requires its own evidence.',[STORM,STORM_RAW],digits=0)
SAT=src('SatPM V6.NA.01','https://www.satpm.org/v6-na-01')
SAT_PAPER=src('Shen et al.','https://doi.org/10.1021/acsestair.5c00251')
CC=src('CC BY 4.0','https://creativecommons.org/licenses/by/4.0/')
for g,k,title,kind,bins,pal in [('coast','seaSalt','Airborne fine sea salt','sea salt',[.025,.05,.08,.15,.3],'cool'),('dust','dust','Airborne fine mineral dust','mineral dust',[.25,.4,.55,.85,1.5],'earth')]:
    metric(g,k,title,'µg/m³',bins,pal,'County · modeled PM₂.₅','2019–2023','Five-year mean outdoor concentration of '+kind+' in the fine-particle fraction. Larger particles, vehicle deposits and road spray require different measurements.','Satellite, chemical transport model and ground-monitor estimates. Within each 2017 county, average valid 0.01° grid cells with latitude-dependent area weights, then average five annual estimates equally. Adapted from Siyuan Shen and coauthors, Washington University ACAG, CC BY 4.0.',[SAT,SAT_PAPER,CC],digits=3,note='Fine-particle concentration near the ground.')
    movefirst(g,k)
TTI=src('Texas A&M Urban Mobility Report','https://mobility.tamu.edu/umr/report/')
for k,title,unit,bins,desc in [
    ('delay','Traffic delay per auto commuter','hr/commuter/year',[15,25,40,55,75],'Annual excess travel time per auto commuter. A delay includes moving slowly and waiting.'),
    ('peak','Peak travel in congestion','% of peak VMT',[8,15,22,30,40],'Share of peak-period vehicle-miles traveled in congested conditions. Only areas with a published value are shown.')
]:
    metric('traffic',k,title,unit,bins,'violet','Urban area · travel model','2024',desc,desc+' Texas A&M Transportation Institute 2025 Urban Mobility Report. The point locates the lead city or a Census urban-area reference point. The value applies to the wider urban area. Time spent stopped and brake counts require separate measurements.',[TTI],point='metro',note='Urban-area observations shown at reference points.')
PC=src('FHWA HPMS spatial inventory','https://data.transportation.gov/d/42um-tgh5')
metric('rough','roughLocal','Rough miles on sampled major roads','% of sampled miles',[5,10,15,25,40],'earth','County · measured sections','2024','Share of eligible major-road mileage with measured roughness above 170 inches per mile. Local streets and ramps are outside the sample.','Sum eligible section lengths with International Roughness Index >170 in/mi and divide by the sum of section lengths with a positive IRI. FHWA functional classes 1–5 and one-/two-way facilities only. Weights use inventoried miles, independent of traffic.',[PC],digits=2)
movefirst('rough','roughLocal')
metrics['highrh']['desc']='Hours with relative humidity above 80%, at any temperature.'
metrics['highrh']['method']=metrics['highrh']['desc']+' Nearest TMY3 station with complete hourly readings.'
metrics['coldh']['title']='Hours at or below −18°C'
metrics['coldh']['desc']='Hours with outdoor air temperature at or below −18°C (about 0°F) in the matched typical year.'
metrics['coldh']['method']=metrics['coldh']['desc']+' TMY3 represents ordinary seasonal patterns. NOAA 30-year normals are preferable for frequent extreme thresholds.'
geo=list(csv.DictReader((ROOT/'geodata/counties.csv').open()))
clim=read('climate/climate_counties.json'); aerosol=read('climate/aerosol_counties.json')
coast=read('water/coast_counties.json');salt=read('water/salt_states.json')
roads=read('road/state_road.json');local=read('road/county_rough.json')
events=read('geodata/events.json');urban=read('braking/county_urban_population_pct.json')
values={};station={};points=read('geodata/cities.json');metros=read('geodata/metros.json')
for r in geo:
    f=r['fips'];s=r['state'];c=clim[f];rs=roads.get(f[:2],{})
    station[f]=[c['noaa_site'],c['noaa_km'],c['tmy_site'],c['tmy_km']]
    v={k:c[k] for k in ('wet','hh','highrh','solar','hoth','coldh','hot90','hot100','ft','cold0')}
    v.update(aerosol[f]);v.update(events[f]);v.update(urban=urban[f],coast5=coast[f][1],coastkm=coast[f][0],
        salt=salt.get(s,[None])[0],rough=rs.get('rough_pct'),roughcov=rs.get('rough_coverage_pct'),steep=rs.get('steep_pct'),unpaved=rs.get('unpaved_local_pct'),
        roughLocal=local.get(f,[None,None])[0],ratedMi=local.get(f,[None,None])[1])
    values[f]=v
# Optional extensions specified by data vintages and coverage.
extensions=ROOT/'pipeline/extensions.py'
if extensions.is_file(): exec(compile(extensions.read_text(),str(extensions),'exec'))
metric('winter','snowYear','Snow-covered days in a typical year','days/year',[1,10,30,60,120],'cool','County point · ~24 km','2006–2025','Expected days of mapped snow cover over a typical calendar year.','Multiply each monthly IMS snow-cover fraction by the average number of calendar days in that month during 2006–2025, then sum January through December. All 12 months must be observed. Snow on land measures a different exposure from salt applied to roads.',[IMS])
for event, label in [('flood','Flood'),('hail','Hail')]:
    metric(event,event+'Year',label+' report days per year','days/year',[.2,.5,1,2,4],'violet','County · event reports','2015–2024','Average number of days per year with one or more qualifying reports.','Divide the ten-year count of distinct reported event dates by ten. County size and reporting intensity affect this measure.',[STORM,STORM_RAW])
group('overall','Annual overview','annual')
metric('overall','annualExposure','Annual exposure score','/ 100',[40,45,50,55,60],'earth','County · relative exposure','Typical year · mixed source periods','Higher scores indicate greater combined exposure across the eleven categories. The U.S. county average is 50.','Rank each indicator against counties with data, splitting ties at the midpoint. Average ranks within each category, then average the eleven categories equally. A missing indicator receives 50. The missing-data range uses 0 and 100 instead. The weights describe exposure and have not been fitted to vehicle inspections or repair bills.',[src('How the score is calculated','#annual-method')],digits=1,note='50 is the county average. Each exposure category carries the same weight.')
# Put the overall layer ahead of the original drill-down groups.
groups={'overall':groups['overall'],**groups}
annual=build_annual(values,terrain)
assert len(values)==3108 and len(points)==125 and len(metros)==478
for k,m in metrics.items():
    assert len(m['bins'])==5 and list(sorted(set(m['bins'])))==m['bins']
    if not m.get('point') and not m.get('seasonal'): assert any(v.get(k) is not None for v in values.values()),k
assert all(x.get('fips') in values for x in points+metros)
for v in values.values():
    assert all(x is None or isinstance(x,(int,float)) for x in v.values())
    for k in ('urban','coast5','rough','roughcov','roughLocal','steep','gradeLocal','unpaved'):
        assert v.get(k) is None or 0<=v[k]<=100
coverage='''<p>County averages use 2017 FIPS boundaries, including the eight historical Connecticut counties. County and independent-city records include Washington, D.C. Some small county polygons are easier to reach through search. County search accepts a name or a five-digit FIPS code.</p><p>Weather stations describe a county’s reference point. The median distance to a matched temperature-normals station is 23.7 km, and to a TMY3 station 40.6 km. Local elevation and coastal microclimates can differ. Fine-particle layers average modeled concentrations over county area. Time spent outdoors and travel routes determine personal exposure.</p><p>Color breaks are display choices in physical units. Hatching marks unavailable readings. On a point map, gray land provides geographic context. Some areas have several observed places. Select a marker to isolate one place, or click the county to see all associated readings.</p><p>Historical normals, single-year road inventories and separate event counts describe different periods. Summing their map colors would double-count several mechanisms. The annual score ranks selected indicators within each category and gives each category equal weight. Estimating vehicle life or repair costs requires vehicle-specific outcome data.</p><p>Geography: <a href="https://github.com/topojson/us-atlas" target="_blank" rel="noopener">US Atlas / U.S. Census</a>. <a href="assets/metric-definitions.json" download>Download the reading definitions</a> · <a href="assets/point-readings.csv" download>Download city and urban-area readings</a>.</p>'''
audit=read('braking/ny_inspection_feasibility.json')
validation='''<p><b>New York inspection-data feasibility check.</b> In one hour on May 29, 2026, the DMV recorded 4,932 transactions. Restricting the sample to initial passenger inspections with a usable odometer, make, model, model year and a safety result left 3,107. Of these, 62 failed and 3,045 passed. Facility IDs linked 2,946 (94.8%) to one inspection county across 61 counties.</p><p>A facility county locates the test. Ownership history is needed to estimate accumulated exposure. The public file reports overall pass/fail; the examiner form also contains component rejection categories. A component-level validation would use corrosion or brake-specific findings alongside age, odometer and ownership geography.</p><p><a href="https://data.ny.gov/d/vezn-fmmk" target="_blank" rel="noopener">NY inspection data</a> · <a href="https://data.ny.gov/d/nhjr-rpi2" target="_blank" rel="noopener">Facility register</a> · <a href="https://dmv.ny.gov/forms/vs1074s.pdf" target="_blank" rel="noopener">Inspection record form</a>.</p>'''
validation += '<p>In a second sample, New York recorded 364 initial statewide inspections of model-year 2018 Toyota Camrys with 60,000–129,999 miles in May 2026. Ten failed the overall safety check. Statewide, only two of 71 inspections in the 80,000–89,999-mile band failed. A county-by-county component study needs a larger time window and more detailed outcomes.</p>'
validation += '<p><b>Snow as a proxy for salt.</b> In all 72 Wisconsin counties, total snowfall in winter 2025–26 had a Spearman rank correlation of 0.375 with observed state-highway salt use per lane-mile in the same winter. That is enough variation to warrant keeping the two layers separate. <a href="'+WI[1]+'" target="_blank" rel="noopener">WisDOT winter report, table 1.4</a>.</p>'
coverage += '<p><b>Stops per mile.</b> A U.S. study of 148,105 driving cycles measured 0.3 stops per mile in freeway trips, 0.8 in urban trips and 1.4 in congested urban trips. These are drive-cycle categories. The atlas displays local hard-braking and metro delay where measured. A statewide idle-time or county stops-per-mile estimate would need representative local speed traces. <a href="https://www.osti.gov/servlets/purl/1660173" target="_blank" rel="noopener">Driving-cycle study, table 3</a>.</p>'
assert read('braking/camry_feasibility.json')['n']==364
coverage += '<p><b>Road salt coverage.</b> Direct dry-salt rates are available for 36 state agencies in 2021–22 and for Wisconsin’s 72 counties on the state system in 2025–26. The USGS nationwide 1 km estimates for 1992–2019 have a separate <a href="https://doi.org/10.5066/P96IX385" target="_blank" rel="noopener">data release</a>. The current atlas does not include those raster values. Snowfall can be viewed independently in the other counties.</p>'
coverage += '<p><b>Terrain Atlas reuse.</b> The project’s November 2026 release supplies 12 monthly snow-cover frequencies, average daily highs and lows for all 12 months, and a static regional slope. County readings sample the archived map cells at the Census internal point. Resolution, original sources and time windows follow the parent release. The road-only USDA and FHWA measurements remain available in the hills group. <a href="assets/seasonal-readings.csv" download>Download the monthly readings</a> · <a href="assets/terrain-provenance.json" download>Terrain release checksums</a>.</p>'
assert audit['eligible']==3107 and audit['matchable_to_one_facility_county']==2946
blob=dict(annual=annual,seasons={f:{k:v[k] for k in ('snowCover','monthlyHigh','monthlyLow')} for f,v in terrain.items()},values=values,metrics=metrics,groups=list(groups.values()),cities=points,metros=metros,stationInfo=station,coverageHtml=coverage,validationHtml=validation)
(WEB/'readings.js').write_text('const DATA='+json.dumps(blob,ensure_ascii=False,separators=(',',':'))+';\n')
write(WEB/'metric-definitions.json',{'conditions':list(groups.values()),'readings':metrics,'annual_score_inputs':annual['components'],'additional_fields':{'snow_site':'NOAA source station ID for snowfall','snow_km':'Distance to snow station (km)','gradeMi':'Audited grade miles before county minimum thresholds','gradeN':'Audited grade interval count before county minimum thresholds','ratedMi':'Miles of eligible road sections with measured roughness','noaa_site':'NOAA source station ID','noaa_km':'Distance from county internal point to NOAA station (km)','tmy_site':'TMY3 source station ID','tmy_km':'Distance from county internal point to TMY3 station (km)'}})
with (WEB/'county-readings.csv').open('w',newline='') as file:
    keys=[k for g in groups.values() for k in g['keys'] if not metrics[k].get('point') and not metrics[k].get('seasonal')]+['ratedMi','gradeMi','gradeN']
    w=csv.writer(file);w.writerow(['fips','county','state',*keys,'noaa_site','noaa_km','tmy_site','tmy_km','snow_site','snow_km'])
    for r in geo:
        f=r['fips'];w.writerow([f,r['county'],r['state'],*[values[f].get(k) for k in keys],*station[f]])
with (WEB/'point-readings.csv').open('w',newline='') as file:
    w=csv.writer(file);w.writerow(['place','state','reference_point_county_fips','lat','lon','metric_id','value','unit','period'])
    for data,ks in [(points,[('brake','value')]),(metros,[('delay','delay'),('peak','peak')])]:
        for c in data:
            for k,valuekey in ks:
                if c[valuekey] is not None:w.writerow([c['name'],c['state'],c['fips'],c['lat'],c['lon'],k,c[valuekey],metrics[k]['unit'],metrics[k]['period']])
print(len(metrics),'metrics; example Tippecanoe',values['18157'])

with (WEB/'seasonal-readings.csv').open('w',newline='') as file:
    w=csv.writer(file);w.writerow(['fips','county','state','month','snowCover_pct','monthlyHigh_degF','monthlyLow_degF'])
    for r in geo:
        v=terrain[r['fips']]
        for i in range(12):w.writerow([r['fips'],r['county'],r['state'],i+1,*[v[k][i] for k in ('snowCover','monthlyHigh','monthlyLow')]])
write(WEB/'terrain-provenance.json',read('geodata/terrain-provenance.json'))

with (WEB/'annual-exposure.csv').open('w',newline='') as file:
    w=csv.writer(file)
    w.writerow(['fips','county','state','annualExposure','missing_data_low','missing_data_high','observed_inputs','total_inputs',*annual['components']])
    for r in geo:
        f=r['fips']; rec=annual['records'][f]
        w.writerow([f,r['county'],r['state'],values[f]['annualExposure'],rec['low'],rec['high'],rec['observed'],annual['inputCount'],*rec['categories'].values()])

# Keep the in-app download in sync with the data and scoring code.
with zipfile.ZipFile(WEB/'research-data.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
    archive.write(ROOT.parent/'README.md','README.md')
    for path in sorted(ROOT.rglob('*')):
        if path.is_file() and path.suffix in {'.py','.cjs','.json','.geojson','.md','.csv','.list'} and 'raw' not in path.parts:
            archive.write(path,path.relative_to(ROOT.parent))
    for name in ('county-readings.csv','point-readings.csv','seasonal-readings.csv','annual-exposure.csv','terrain-provenance.json','metric-definitions.json'):
        archive.write(WEB/name,name)
