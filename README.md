# Used Car Exposure Atlas

[Open the interactive map](https://yuanrui3.github.io/used-car-exposure-atlas/)

An interactive map for the contiguous 48 states and the District of Columbia. The default annual overview compares the combined exposure of two counties. Individual layers retain their physical units. Nine everyday conditions appear alongside two event histories. Look up a county, independent city, parish, five-digit FIPS, sampled braking city or traffic-study urban area. A location point identifies where a published city or urban-area value belongs. Source periods vary by layer.

## Run the site

The browser entry is docs/index.html. It loads bundled JavaScript and local assets. The map can also be served over HTTP from docs. It initially opens on Tippecanoe County in Indiana. A shared URL can retain A, B, the selected metric and the month of a seasonal layer.

## Annual exposure score

The default map equally weights nine everyday exposure categories and the two historical storm categories. The score is the average of 11 category scores on a 0–100 scale. Each indicator uses its county midrank, calculated as 100 × (number strictly below + half the number tied) / number observed. Indicators within a category share the category weight. A missing indicator takes a neutral rank of 50, with sensitivity bounds computed by substituting 0 or 100 for every missing indicator. The national county mean is 50. The score describes a typical year assembled from mixed source periods. It has not been calibrated against actual damage, depreciation or repair costs.

| Category | Inputs |
|---|---|
| Winter | Annual snow-covered days from all twelve monthly frequencies, plus state-agency dry salt use per state-owned lane-mile |
| Coastal salt | Fine sea salt concentration |
| Moisture | Atmospheric wetness hours and humid-heat hours |
| Heat and sun | Days reaching 90°F and mean daily solar energy |
| Cold | Freeze–thaw days and nights at or below 0°F |
| Hills | Mean road terrain ruggedness |
| Traffic | Share of county population in urban areas |
| Pavement | Share of measured major-road miles with rough pavement |
| Dust | Fine mineral dust concentration and unpaved-road PM₁₀ emissions per land area |
| Flood | Annualized county flood report days |
| Hail | Annualized county hail report days |

Snow frequency is weighted by calendar days, including leap days across the 2006–2025 baseline. Annual flood and hail counts divide 2015–2024 county report days by ten. Annual heat and cold frequencies preserve summer and winter extremes. Alternative measures, city/urban-area point observations, and coverage fields remain available as context. County populations do not weight the national reference distribution.

The annual-exposure.csv file includes the composite, sensitivity bounds, observed-indicator count and all eleven category scores. The county-readings.csv file includes the physical inputs. The regeneration command below also rebuilds the downloadable research ZIP.

## Research data

The CSV files use the 2017 Census county definitions. Read FIPS as strings to retain leading zeros. county-readings.csv provides the static county/state/station indicators. seasonal-readings.csv stores 12 calendar months by county. point-readings.csv gives city and urban-area observations with reference locations and their original geographic scope. metric-definitions.json provides definitions, periods, units, color breaks, interpretation and links. Empty cells are missing. The download includes the input snapshot for recreating these summaries.

Run python research/pipeline/assemble.py to regenerate the browser data and CSVs from the included summaries. Python 3 is sufficient for that step. The scripts next to the summaries document source-specific calculations. Some optional upstream rebuilds require external downloads, Python packages or GDAL; some use manual source transcriptions. NOAA event reconstruction expects the ten listed NOAA gzipped detail files in research/water/raw/. County and metro outlines came from us-atlas 3.0.1 (Census boundaries). To rebuild drawing paths, download counties-10m.json from that package and the CommonJS distributions of d3 7.9.0 and topojson-client 3.1.0 as geodata/tools/d3.cjs and geodata/tools/topo.cjs within research. Then run node research/geodata/make_geometry.cjs. The small Falls Church polygon uses the Census 2017 1:500,000 cartographic boundary instead of the heavily simplified polygon.

## Reused terrain atlas data

The original project archive is conus-monthly-atlas-github-pages.zip. Within that archive, docs/data/climate.json supplies November and docs/data/climate_months/ supplies the other eleven monthly NOAA nClimGrid summaries. docs/data/seasonal_snow.json.gz supplies the NOAA/NSIDC IMS frequencies. docs/data/regional_slope.json.gz supplies regional USGS 3DEP land slope. The 20-year climate and snow products cover 2006–2025. Sampling uses the grid cell at the county internal point. Missing cells stay missing. terrain-provenance.json records the byte-level hashes. Rebuild the lookup using python research/geodata/terrain_context.py /path/to/conus-monthly-atlas-github-pages.zip. Regional land slope and actual road grades are selectable as different measurements.

## Outcome validation

New York DMV inspection records establish feasibility of finding comparable passenger cars and testing overall safety pass/fail. The downloadable pilot code only requests the fields needed for these checks. Specific rejected components, maintenance history and prior garaging are missing from the public transaction file. Held-out, component-specific validation remains open. A Wisconsin exposure check uses all 72 county records in winter 2025–26, with Spearman correlation 0.375 between season snowfall and state-highway salt use per lane-mile.

## Attribution

USGS, NOAA, NSIDC, FHWA, Census, USDA ERS, EPA, Clear Roads, WisDOT, Texas A&M Transportation Institute, Allstate, NREL and NY DMV are credited with each applicable source in metric-definitions.json or the notes. SatPM V6.NA.01 fine sea salt and dust are derived from Siyuan Shen et al., Washington University Atmospheric Composition Analysis Group, CC BY 4.0, modified by averaging into 2017 counties and across the five years 2019–2023. The font is Inter under the SIL Open Font License. Original data-source terms apply.
