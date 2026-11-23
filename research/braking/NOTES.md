# Stop-and-go driving and validation

## Hard braking in 125 cities

Allstate’s 2019 America’s Best Drivers Report lists absolute hard-braking events per 1,000 miles from volunteer Drivewise customers in 2016–17. Of its 200 listed places, 125 in the contiguous U.S. (including DC) report observations. California, North Carolina, South Carolina and Texas lacked Drivewise data for this edition. Other large cities can lack observations. Each point gives the published city rate at the 2024 Census internal point for the corresponding city or Census-designated place. These are aggregated driving behaviors. A point has no radius of applicability. The figure does not count routine brake use, total stops, time idling, pad wear or damage. The city sample reflects local driving plus participant selection. Preserve missing observations.

- City rate table and definitions: https://www.allstate.com/resources/allstate/attachments/best-drivers/full-americas-best-drivers-report-v2.pdf
- Census place points: https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_place_national.zip
- `city_braking.json` contains city, postal state, seven-character Census place GEOID, latitude/longitude and hard_brakes_per_1000_miles. Knoxville's three-decimal value is as printed.

## County urbanization

`county_urban_population_pct.json` maps county FIPS to percentage of residents who lived in an urban area, from the 2020 Census (county data updated September 2023). Numerator is Census urban population, denominator total county population. This is explicitly a proxy for typical stop-and-go conditions; rural interstates and city freeways are counterexamples. Do not convert directly to stops/mile or interpolate hard braking from the city points. Includes 3,108 contiguous county-equivalents/DC in 2020 geography plus alternative 2022 Connecticut planning regions from the workbook; a map must display only the rows matching its geography.

- Census urban/rural source: https://www.census.gov/programs-surveys/geography/guidance/geo-areas/urban-rural.html
- Source workbook: https://www2.census.gov/geo/docs/reference/ua/2020_UA_COUNTY.xlsx

## Validation

New York DMV releases inspection transactions with inspection type/date, safety PASS/FAIL, make, model, model year, reported odometer and inspecting facility ID. Public, dealer and fleet inspection facilities can be linked by ID to facility county. Vehicle attributes including manually entered model names and odometer readings require cleaning. Initial inspections should be the denominator and reinspections excluded. The public schema has only an overall safety outcome. NY DMV's safety inspection record form does include brake/tires/suspension rejection boxes, making the added fields a possible data request. Shop location is a proxy for exposure and does not give garaging or lifetime history. No publication of VINs is necessary.

- Inspection transactions and schema: https://data.ny.gov/Transportation/Department-of-Motor-Vehicles-Vehicle-Inspections/vezn-fmmk
- Inspection-facility registry: https://data.ny.gov/Transportation/Facilities-Licensed-by-the-Department-of-Motor-Veh/nhjr-rpi2
- State safety inspection record sheet (component categories on form): https://dmv.ny.gov/forms/vs1074s.pdf
- Pennsylvania research with detailed component records from a private partner: https://ppms.cit.cmu.edu/media/project_files/TSET_FY15_Project_99_Final_Report.pdf

Start the substantive test with pre-specified component outcomes and known prior location(s), weights by time vs mileage appropriate to the mechanism. Compare a make/model/year/mileage/dates baseline with a model adding the pre-specified component exposure. Hold out counties and calendar periods; cluster repeated vehicles or retain the first observation in the period. A broken taillamp could produce an overall safety failure, so statewide safety-pass associations cannot validate brake wear specifically. A registry-completeness test is distinct from a predictive validation.

## Urban-area traffic delay

`urban_congestion.json` provides a 2024 travel delay estimate for every one of the 478 urban areas in the contiguous states and DC included in Texas A&M Transportation Institute's 2025 Urban Mobility Report. Each record is an urban area, represented on the map by a Census point at the lead city (or the Census urban-area point for San Francisco–Oakland, since the San Francisco place includes offshore islands). `delay_hours_per_auto_commuter` is **annual hours of extra travel time per auto commuter**. It sums network congestion delay and divides by the estimated number of auto commuters; it is an area-wide per-commuter estimate, not an individual's time at a standstill. `peak_vmt_congested_pct` is the percent of peak-period vehicle-miles traveled under congested conditions, published for 98 of the 478 areas; null means missing. Never infer idle hours, stopped brake applications, or component wear from these numbers.

- 2025 report and methodology: https://mobility.tamu.edu/umr/report/
- Raw workbook (sheet "urban areas", 2024 rows): https://static.tti.tamu.edu/tti.tamu.edu/documents/umr/data/complete-data-2025-umr-by-tti.xlsx
- Urban area point for San Francisco–Oakland: https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_ua_national.zip
