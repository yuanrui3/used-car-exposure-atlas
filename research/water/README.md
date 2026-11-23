# Coastal proximity and winter treatment

## Salt applied by state highway departments

`salt_states.json` maps two-letter state codes to [US short tons of dry salt per state-owned lane-mile, reported short tons of dry salt, state highway agency lane-miles]. The numerator comes from the Clear Roads survey for winter 2021–22. The denominator comes from FHWA Highway Statistics 2022, table HM-81, rural and urban combined. These figures cover 36 states, representing 2,140 of the 3,108 mapped counties or county equivalents. The other 12 states and DC have missing values. A state's entire network shares its reported value. Liquid brine, most municipal streets, roads maintained by private parties, and other seasons can produce substantially different exposures. The two sources can differ in their treatment of contracted routes and plowing beyond state-owned roads.

The reported quantities in `salt_2021_22.csv` were read from the blue state labels on page 7 of the January 18, 2023 Vermont Agency of Transportation presentation. Dashes mean unavailable. Table HM-81 was saved as `hm81.html`. Running `python make_salt.py` reconstructs the JSON. Indiana's 272,977 tons divided by 28,596 lane-miles yields 9.55 tons per lane-mile.

[Clear Roads annual surveys](https://www.clearroads.org/winter-maintenance-survey/) · [Vermont Agency of Transportation, p. 7](https://legislature.vermont.gov/Documents/2024/WorkGroups/House%20Transportation/Agency%20of%20Transportation%20Overview/Agency%20of%20Transportation%20Overview/AOT%20District%20Maintenance%20Division/Witness%20Documents/W~Todd%20Law~AOT%20District%20Maintenance%20and%20Fleet%20Division%20Water%20Quality%2C%20Stormwater%20Management%20and%20Winter%20Road%20Treatment%20Practices~1-18-2023.pdf#page=7) · [FHWA table HM-81](https://www.fhwa.dot.gov/policyinformation/statistics/2022/hm81.cfm)

## Wisconsin county inventories

`wi_salt_counties.json` maps each five-digit Wisconsin county FIPS code to [reported tons of salt used per state-highway lane-mile, same-winter snowfall in inches, reported tons, state-highway lane-miles]. All 72 counties have values. The input is Wisconsin DOT's 2025–26 annual winter maintenance report, table 1.4, with salt quantities from its inventory reporting system. `pdftotext -layout wi-2026.pdf wi-2026.txt` followed by `python make_wi.py` reproduces the fields. The script verifies that the 72 distinct county keys match Census geography and that the reported rate agrees with tons divided by lane-miles to within 0.012 tons per lane-mile. This pilot pertains to one particular winter. It spans 3.77 (Green Lake) to 27.12 (Vilas) tons per lane-mile.

As an exposure cross-check, across the 72 counties the unweighted Spearman rank correlation between same-winter total snowfall and inventoried tons per lane-mile is 0.375. Between the nearest station's long-term number of days with at least one inch of snowfall and the same inventory measure, it is 0.264. This compares winter-weather readings with salt application. It does not use vehicle condition or replacement dates.

[Wisconsin DOT annual report](https://wisconsindot.gov/Documents/doing-bus/local-gov/hwy-mnt/winter-maintenance/winterannualrpt2025-2026.pdf)

## Snow

`snow.json` maps county FIPS to [normal annual number of days with at least 1 inch of new snowfall, station ID, distance between station and county Census representative point in km]. `snow_stations.json` supplies station names. The NOAA variable is ANN-SNOW-AVGNDS-GE010TI from the 1991–2020 U.S. Climate Normals annual station archive v1.0.1. Only standard-completeness (S) stations are used. `python snow.py` uses the archive and county coordinates in the atlas source. Of 3,108 mapped counties and county equivalents, 2,859 have a qualifying station within 75 km and 2,997 within 100 km. Elevation, lake effects and station spacing can change the local snowfall regime. Snowfall counts do not quantify deicer use or the length of a highway agency's treatment season.

[NOAA station normals](https://www.ncei.noaa.gov/access/us-climate-normals/) · [NOAA archive used](https://noaa-normals-pds.s3.amazonaws.com/normals-annualseasonal/1991-2020/archive/us-climate-normals_1991-2020_v1.0.1_annualseasonal_multivariate_by-station_c20230404.tar.gz)

## Proximity to saltwater

`coast_counties.json` maps each county FIPS to [population-weighted mean distance from tract population centers to the ocean coastline in km, share of residents in tracts with population centers within 5 km of that coastline in percent]. The observations comprise all 83,239 populated 2020 Census tracts in the mapped 3,108 county areas. Distances use Natural Earth's 1:10-million ocean coastline, including major islands and mapped bays. Great Lakes shorelines are excluded. `make_coast.py` resamples mapped segments at intervals no greater than 0.5 km and computes shortest spherical distances. The public data inputs are `census_tracts.csv` and `coastline.geojson`. Five km is an illustrative proximity threshold. The distance and population share describe where people live, and cannot resolve individual addresses, garage conditions, winds, sea-salt deposition rates, or driving routes.

[2020 Census centers of population](https://www.census.gov/geographies/reference-files/2020/geo/2020-centers-population.html) · [Census national tract table](https://www2.census.gov/geo/docs/reference/cenpop2020/tract/CenPop2020_Mean_TR.txt) · [Natural Earth coastline](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/) · [GeoJSON input](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_coastline.geojson)

## National road salt raster

USGS publishes annual estimated road salt application at 1 km for 1992–2019. It combines state sales/distribution, roads, land use and snowfall. The primary archives were unavailable in this build (HTTP 403 at ScienceBase). The reproducible next acquisition is the public file 2016_2019.zip attached to ScienceBase item 5b15a50ce4b092d9651e22b9. The older zip is 1992_2015.zip. The corresponding annual .tif files contain estimated pounds per square-kilometer cell. Local and state inventory comparisons should normalize road salt by a common roadway denominator, distinguish years and spatial support, and avoid interpreting a high urban mass per square kilometer as heavier salting per road mile. A legacy national SPARROW GIS service publishes modeled dissolved-solids yields to streams. That endpoint was excluded because its endpoint differs from on-road application.

[USGS catalog and coverage](https://water.usgs.gov/catalog/datasets/adde3501-bf38-474d-95d1-a7e5249ec550/) · [USGS release DOI](https://doi.org/10.5066/P96IX385) · [Published pipeline identifying annual archives](https://github.com/hdugan/episodic-river-salinization-model/blob/v.1.0.0/1_Download.R)
