"""Typical-year used-car exposure, with fixed category weights across counties."""
from bisect import bisect_left, bisect_right
from statistics import mean

# The indicators for each category share that category's weight equally.
COMPONENTS = {
    'winter': ['snowYear', 'salt'],
    'coast': ['seaSalt'],
    'wet': ['wet', 'hh'],
    'heat': ['hot90', 'solar'],
    'cold': ['ft', 'cold0'],
    'grade': ['rugged'],
    'traffic': ['urban'],
    'rough': ['roughLocal'],
    'dust': ['dust', 'roadPM10'],
    'flood': ['floodYear'],
    'hail': ['hailYear'],
}

# Calendar days per month averaged over 2006–2025, including five leap years.
MONTH_DAYS = (31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def annual_measures(values, terrain):
    for fips, row in values.items():
        snow = terrain[fips]['snowCover']
        if len(snow) == 12 and all(value is not None for value in snow):
            snow_days = sum(days * pct / 100 for days, pct in zip(MONTH_DAYS, snow))
            row['snowYear'] = round(snow_days, 4)
        else:
            row['snowYear'] = None
        for key in ('flood', 'hail'):
            count = row[key]
            row[key + 'Year'] = None if count is None else count / 10


def build_annual(values, terrain):
    annual_measures(values, terrain)
    inputs = [key for keys in COMPONENTS.values() for key in keys]
    ranks = {}
    for key in inputs:
        observations = sorted(row[key] for row in values.values() if row[key] is not None)
        ranks[key] = {
            value: 50 * (bisect_left(observations, value) + bisect_right(observations, value)) / len(observations)
            for value in set(observations)
        }

    records = {}
    for fips, row in values.items():
        scores = {}
        missing_weight = 0
        observed = 0
        for group, keys in COMPONENTS.items():
            points = [ranks[key][row[key]] for key in keys if row[key] is not None]
            missing = len(keys) - len(points)
            observed += len(points)
            missing_weight += missing / len(keys) / len(COMPONENTS)
            scores[group] = (sum(points) + 50 * missing) / len(keys)
        score = mean(scores.values())
        margin = 50 * missing_weight
        row['annualExposure'] = round(score, 4) if observed else None
        records[fips] = {
            'categories': {key: round(value, 4) for key, value in scores.items()},
            'observed': observed,
            'low': round(score - margin, 4),
            'high': round(score + margin, 4),
        }
    return {'components': COMPONENTS, 'inputCount': len(inputs), 'records': records}
