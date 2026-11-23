snow=read('water/snow.json');wi=read('water/wi_salt_counties.json')
rugged=read('geodata/rugged.json');gradeLocal=read('road/county_grade.json');roadDust=read('road/county_dust.json')
metric('winter','snow','Days with ≥1 inch of snowfall','days/year',[.5,2,6,12,20],'cool','Nearest NOAA snow station','1991–2020','Average days per year with at least one inch of new snow. Plowing and salt treatment vary by jurisdiction.','Nearest qualifying NOAA snow station to the county internal point, subject to a 150 km maximum. This is snowfall frequency. A winter salt rate measures a different condition.',[NOAA],station='snow',note='Snow observations farther than 150 km are unshaded.')
movefirst('winter','snow')
WI=src('WisDOT winter report, table 1.4','https://wisconsindot.gov/Documents/doing-bus/local-gov/hwy-mnt/winter-maintenance/winterannualrpt2025-2026.pdf')
metric('winter','wiSalt','Wisconsin county salt use','tons/lane-mi',[4,7,10,13,18],'earth','County · state highways','Winter 2025–26','Reported salt application per state-highway lane-mile in each Wisconsin county. Coverage is limited to the state system and this winter.','WisDOT annual report, table 1.4, all 72 Wisconsin counties. The map displays the listed rate, with county totals and lane mileage in the research data.',[WI],digits=2)
ERS=src('USDA road ruggedness','https://www.ers.usda.gov/data-products/area-and-road-ruggedness-scales/documentation')
metric('grade','rugged','Terrain variation along roads','m (road TRI)',[5,10,17,28,48],'earth','County · road terrain index','2020 tracts / 2024 roads','Mean USDA road Terrain Ruggedness Index. Higher values indicate larger elevation differences between nearby cells that contain roads.','Uses the 2020-vintage USDA ERS tract file with a 2024 road network. County mean weights each tract’s mean Road TRI by its RoadTRI_Count grid cells. Separate nearby roads may differ in elevation. This terrain proxy does not yield road grade or descent length.',[ERS],digits=2,note='Terrain ruggedness for road-containing grid cells.')
movefirst('grade','rugged')
grade_method='Assign official HPMS grade A–F mileages to county-contained route intervals. Reconcile category-mile totals with interval lengths, reject ambiguous overlaps, and merge repeated values across adjoining subdivisions only when their combined length matches. The numerator counts absolute grades ≥4.5%, classes D–F. The sample contains major roads in both directions. No continuous descent length or traffic weighting.'
metric('grade','gradeLocal','Sampled miles at ≥4.5% grade','% of sampled miles',[1,3,7,14,25],'earth','County · audited road sample','2024','Share of sampled road mileage with absolute grade ≥4.5%. Values require ≥10 accepted miles and at least three accepted intervals in the county.',grade_method,[HPMS,GRADE],digits=2,note='County estimates require ≥10 audited miles across ≥3 intervals.')
metrics['steep']['method']=grade_method+' The state display additionally requires 100 accepted miles and 10 accepted intervals with sufficient grade-class reporting.'
EPA=src('EPA 2020 emissions inventory','https://www.epa.gov/air-emissions-inventories/2020-national-emissions-inventory-nei-data')
metric('dust','roadPM10','Dust emitted from unpaved roads','tons/mi²/year',[.15,.5,1.5,3,6],'earth','County · emissions inventory','2020','Modeled primary PM₁₀ emissions from unpaved roads per square mile of county land. This is an emission rate, separate from ambient dust concentration.','Filter EPA NEI to primary PM10, unpaved-road dust and annual county totals, excluding separately listed tribal rows. Divide reported short tons per year by 2020 Census county land area. Missing entries remain blank.',[EPA],digits=3)
for f,v in values.items():
    z=snow[f];station[f].extend([z[1],z[2]])
    v['snow']=z[0] if z[2]<=150 else None
    v['wiSalt']=wi.get(f,[None])[0]
    v['rugged']=rugged[f]
    gg=gradeLocal.get(f)
    v['gradeLocal']=gg[0] if gg and gg[1]>=10 and gg[3]>=3 else None
    v['roadPM10']=roadDust.get(f,{}).get('tons_per_sqmi')
    v['gradeMi']=gg[1] if gg else None
    v['gradeN']=gg[3] if gg else None
terrain=read('geodata/terrain_lookup.json')
IMS=src('NOAA / NSIDC IMS snow maps','https://nsidc.org/data/g02156/versions/1')
NCLIM=src('NOAA nClimGrid','https://www.drought.gov/data-maps-tools/gridded-climate-datasets-noaas-nclimgrid-monthly')
DEM=src('USGS 3DEP elevation','https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer')
metric('winter','snowCover','Monthly snow-cover frequency','% of observed days',[1,10,30,55,80],'cool','County point · ~24 km','2006–2025','Share of observed land days classified as snow-covered in the selected month. This records snow persistence around the county reference point. Road plowing changes the surface a car encounters.','Reuses the terrain atlas IMS 24 km snow series on its 0.25° overview grid. Sample the cell containing the county reference point, with no gap filling. Average 20 month-year frequencies, each with at least 80% observed calendar days. Zero and missing are distinct.',[IMS],seasonal=True,note='The month selector changes the snow-cover map.')
movefirst('winter','snowCover')
for g,k,title,bins,pal,rev in [('heat','monthlyHigh','Monthly average daily high',[35,50,65,80,90],'hot',False),('cold','monthlyLow','Monthly average daily low',[15,25,35,45,60],'cool',True)]:
    metric(g,k,title,'°F',bins,pal,'County point · ~9 km','2006–2025','Average daily '+('high' if g=='heat' else 'low')+' for the selected month. The calendar month is averaged over 20 historical years.','Reuses the terrain atlas monthly nClimGrid climate grids. Its 2 × 2 native-cell aggregation requires 20 years for each contributing cell. Sample the overview cell at each county reference point without filling missing coverage; convert Celsius to Fahrenheit.',[NCLIM],seasonal=True,reverse=rev,note='Typical daily temperature for the selected month.')
metric('grade','landSlope','Regional land-surface slope','degrees',[.5,1,2,4,8],'earth','County point · 0.05° cell','Static terrain','Mean slope of the surrounding land in the cell containing the county reference point. Compare it with road-only ruggedness and measured road grades.','Reuses the terrain atlas USGS 3DEP processing. Horn 3 × 3 gradients on 500 m elevation samples were averaged into 0.05° display cells. Approximate cell height 5.6 km. This measures regional topography and cannot describe the grade or direction of a vehicle’s route.',[DEM],digits=2)
for f in values:values[f]['landSlope']=terrain[f]['landSlope']
