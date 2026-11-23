# County shopping comparisons

The buying page compares written quotes and the costs of collecting and repairing an individual car. The county map uses the seller’s location to help buyers find listings. Exposure belongs to the places in the individual car’s history. The exposure index is a screening measure, with no validated conversion to repair dollars, crash probability or vehicle life.

## Data and reproduction

The [public vehicle listing snapshot](https://www.kaggle.com/datasets/austinreese/craigslist-carstrucks-data/versions/11) contains 295,451 Craigslist ads posted September 29–November 2, 2026. The county polygons come from [US Atlas](https://github.com/topojson/us-atlas). The download script checks both SHA-256 digests. When the listings change, reproduce with the matching archived zip in the local cache. The published tables contain county aggregates. The two Macan prices cited on the page correspond to October 16 (Washington) and October 24 (Oregon).

With Python 3.11+ and pandas, NumPy, SciPy, Shapely 2 and scikit-learn installed, run these commands from this directory. Intermediate files go into cache/.

```sh
python sources.py
python read.py
python flags.py
python compare.py
python pricemodel.py
python routes.py
python audit_routes.py
python export.py
```

## What passed the comparisons

- County assignment uses the coordinates of the ad inside a county polygon. Retain 2006–2025 vehicles with a reported clean title, usable model and vehicle attributes, 10,000–200,000 miles and asking prices of $3,500–$75,000. Screen explicit deposit prices and branded-title contradictions. Deduplicate VINs or listing fingerprints and drop conflicting county assignments.
- Among 49,307 eligible cars, require the same make, normalized full model description, year, fuel, transmission, drive, seller type and stated condition. Search within 5,000 miles on the odometer. Only 125 listings have at least three reference vehicles from two other counties. No county clears the release threshold of 15 matched vehicles across five strata with no stratum above 40%.
- For broader coverage, fit ridge regression with a second robust reweighting pass to log asking price. Covariates include manufacturer, model family, full model text, available VIN prefix, family/year and trim-text/year, age, mileage, drivetrain, body, condition and seller type. Five folds hold out entire counties. Require at least five training vehicles in the same model family within two model years. The resulting 46,497 predictions have a median absolute percentage error of 13.8% per car, compared with 43.8% for the training-fold median. Split-period county ordering has Spearman correlation 0.76 across 220 markets.
- The county estimate is its median log-price residual centered on the national supported-listing median and transformed to percent. The published 249 counties each have at least 40 supported listings and eight model families, with no family above 25%. The central 95% interval resamples families 400 times within the county. It omits model fitting uncertainty, unobserved condition, seller selection and geographic search multiplicity.
- The four featured routes have at least 100 supported cars at each end, non-overlapping county bootstrap intervals, a cheaper destination in both periods and after dropping each county’s most frequent rounded ad location, and a same-direction median among at least three disjoint near-pairs. The near-pairs match model family, seller type, reported condition, drive, fuel and transmission, at most one model year and 10,000 odometer miles apart. Ties are resolved using year difference and mileage before looking at price. The destination’s price discount is one minus the ratio of its adjusted price level to the origin’s.
- Start with higher-exposure origins (65th percentile or above) and below-median destinations. Check the atlas’s 11 categories, dropping one at a time, increasing winter to 25%, its missing-data intervals, and the average of winter, moisture, heat, cold, dust, flood and hail. Route times are for the named towns and exclude traffic delays. The file [featured-routes.csv](featured-routes.csv) records the comparisons. Three origins share a single destination market.
- Results describe the listed asking prices during this snapshot. Actual transactions, maintenance histories, confirmed condition, household income, negotiation and remaining repair life are unobserved. County price differences combine market and selection effects. A private inspection and the VIN’s actual registration and service records determine how comparable two individual cars are.

## Tax and out-the-door comparisons

Use the same registration address for both dealer quotes. Include tax still due at home, registration and mandatory fees exactly once, plus travel for every visit, the buyer’s value of time, financing charges and comparable independent repair estimates. For Pacific Northwest trips, consult [Washington’s nonresident sale statute](https://app.leg.wa.gov/RCW/default.aspx?cite=82.08.0264) and [Oregon’s vehicle use tax instructions](https://www.oregon.gov/dor/forms/FormsPubs/form-or-591-c-instructions_612-004-1.pdf). The [FTC buyer guide](https://consumer.ftc.gov/articles/buying-used-car-dealer) describes independent inspections and written out-the-door prices.
