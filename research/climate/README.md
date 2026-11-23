# Climate and airborne-particle data

All county keys are five-character 2017 FIPS. The lookup covers the contiguous 48 states and DC. County names and representative coordinates come from the common atlas geography.

## NOAA daily temperature extremes

The fields hot90, hot100 and cold0 are average days per year with a daily maximum ≥90°F, maximum ≥100°F and minimum ≤0°F, respectively. The field ft estimates days with minimum ≤32°F and maximum >32°F by subtracting NOAA's days with maximum ≤32°F from days with minimum ≤32°F. Both use the same station and independent rounded normals. This is an atmospheric freeze–thaw day, a proxy for local conditions.

Source: NOAA NCEI 1991–2020 annual/seasonal U.S. Climate Normals v1.0.1. We retained the 2,206 conterminous stations whose five temperature fields carried NOAA's S (Standard) completeness flag. Each county takes the closest station to its Census interior point using great-circle distance. noaa_site identifies the station, and noaa_km is the separation. The median separation is 23.7 km and the maximum is 138.1 km. Terrain, elevation, coastal microclimates, outdoor parking and driving histories can differ from a nearby station.

[NOAA documentation](https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals) · [NOAA archive](https://noaa-normals-pds.s3.amazonaws.com/normals-annualseasonal/1991-2020/archive/us-climate-normals_1991-2020_v1.0.1_annualseasonal_multivariate_by-station_c20230404.tar.gz)

## Humidity, wetness and sunlight

The source is NREL TMY3 as distributed by DOE's EnergyPlus weather service. At all 925 lower-48 sites we obtained exactly 8,760 valid hourly dry-bulb temperature, relative humidity and horizontal radiation values. Each site has a constructed typical meteorological year assembled from selected months in the station record, spanning either 1976–2005 or 1991–2005. An individual vehicle's trip years may have substantially different conditions. TMY3 should not be used to estimate rare weather extremes.

| Field | Definition |
| --- | --- |
| hh | Hours per typical year with simultaneous air temperature ≥27°C and relative humidity ≥70%. These are project thresholds for comparing humid heat. |
| wet | Hours per typical year with temperature >0°C and relative humidity >80%. This meteorological proxy for atmospheric time of wetness is adapted from ISO 9223. Actual panel wetness depends on moisture, salt contamination and storage conditions. |
| highrh | Hours per typical year with relative humidity >80%, at any temperature. |
| solar | Mean daily incident global horizontal solar irradiation in kWh/m²/day. Yearly sum of hourly EPW global-horizontal Wh/m² divided by 365, then by 1,000. This measures broadband solar energy on an exposed horizontal plane. It does not directly measure UV or paint dose. |
| hoth / coldh | Typical-year hours with temperature ≥35°C or ≤−18°C, respectively. These illustrate the selected historical year. For frequent extreme hot or cold days, prefer the 30-year station normals. |
| tmy_site / tmy_km | NREL/USAF weather station ID and distance to the county representative point. Median distance 40.6 km, maximum 148.6 km. |

[Data archive](https://energyplus-weather.s3.amazonaws.com/?list-type=2&prefix=north_and_central_america_wmo_region_4%2FUSA%2F) · [Wilcox & Marion TMY3 manual](https://www.osti.gov/biblio/928611) · [ISO 9223 time-of-wetness proxy](https://www.npl.co.uk/getattachment/aeb2c3c7-0988-4a7c-9ca3-5e265f5bb436/NPL-guide-Atmospheric_corrosion-LYON_V2-1_TrainingTemplate-%28002%29-Final-update.pdf?lang=en-US)

## Mineral dust and sea-salt aerosol

The dust and seaSalt fields are mean ground-level **PM2.5 component mass concentrations**, in µg/m³. Source is Washington University Atmospheric Composition Analysis Group, SatPM V6.NA.01, Siyuan Shen, Aaron van Donkelaar, Nathan Jacobs, Chi Li and Randall V. Martin. The source combines satellite data, a chemical transport model and ground monitoring. Data are licensed CC BY 4.0. The atlas modification consists of aggregation to five-year county mean concentrations. These are fine-particle regional exposures. Coarse particles, road-level dust clouds, chloride deposition and underbody spray need independent proxies.

We used the annual DUST and SS grids for 2019–2023, masked by the Census 2017 generalized 1:500,000 county boundaries on the source 0.01° grid. For each county-year we computed the mean of finite nonnegative values using cosine-of-latitude cell-area weights and then equally averaged the five annual values. The nominal 0.01° grid spacing exceeds the true resolving power of some input data. Ambient sea salt can be measurable inland and the near-shore gradient of spray is unresolved.

[SatPM data and terms](https://www.satpm.org/v6-na-01) · [Paper](https://doi.org/10.1021/acsestair.5c00251) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [County geometry](https://www2.census.gov/geo/tiger/GENZ2017/shp/cb_2017_us_county_500k.zip)

## Rebuild

Run tmy_fetch.py, then climate_tables.py --tmy. For aerosol data, run aerosol_fetch.py, fetch the linked county geometry to this directory and run aerosol_counties.py with the GDAL Python bindings installed. The original satellite grid keys follow V6NA01/CNN{SS,DUST}/Annual/V6NA01.CNNPM25.{SS,DUST}.YYYY01-YYYY12.nc in the satpmdata public S3 bucket. No archive should be embedded into the user-facing map. climate_counties.json and aerosol_counties.json contain the summarized fields.
