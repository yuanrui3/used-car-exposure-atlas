"""Find connected low/high county groups and dissolve their interior boundaries."""
from collections import defaultdict
from math import ceil, cos, radians
from statistics import mean

TAIL_FRACTION = 0.2
MIN_COUNTIES = 5


def build_clusters(values, geography, edges):
    scores = {f: row['annualExposure'] for f, row in values.items() if row['annualExposure'] is not None}
    ordered = sorted(scores.values())
    tail_size = ceil(len(ordered) * TAIL_FRACTION)
    lower, higher = ordered[tail_size - 1], ordered[-tail_size]
    if lower >= higher:
        raise ValueError('The upper and lower score cutoffs must be distinct.')
    sides = {f: 'low' if v <= lower else 'high' for f, v in scores.items() if v <= lower or v >= higher}
    locations = {row['fips']: row for row in geography}
    neighbors = defaultdict(set)
    for a, b, _ in edges:
        if b and a in sides and sides[a] == sides.get(b):
            neighbors[a].add(b)
            neighbors[b].add(a)

    membership, regions = {}, {}
    seen = set()
    for seed in sorted(sides):
        if seed in seen:
            continue
        stack = [seed]
        seen.add(seed)
        members = []
        while stack:
            f = stack.pop()
            members.append(f)
            adjacent = neighbors[f] - seen
            seen.update(adjacent)
            stack.extend(sorted(adjacent))
        if len(members) < MIN_COUNTIES:
            continue
        lat = mean(float(locations[f]['lat']) for f in members)
        lon = mean(float(locations[f]['lon']) for f in members)
        def center_distance(f):
            row = locations[f]
            return (float(row['lat'])-lat)**2 + ((float(row['lon'])-lon)*cos(radians(lat)))**2
        anchor = min(members, key=lambda f: (center_distance(f), f))
        rid = sides[seed] + '-' + seed
        membership.update((f, rid) for f in members)
        regions[rid] = dict(kind=sides[seed], count=len(members), anchor=anchor,
                            states=sorted({locations[f]['state'] for f in members}),
                            mean=round(mean(scores[f] for f in members), 2))
    outlines = defaultdict(list)
    for a, b, geometry in edges:
        left, right = membership.get(a), membership.get(b)
        if left != right:
            if left:
                outlines[left].append(geometry)
            if right:
                outlines[right].append(geometry)
    for rid, region in regions.items():
        region['path'] = ''.join(outlines[rid])
    return dict(lower=lower, higher=higher, minCount=MIN_COUNTIES, fraction=TAIL_FRACTION,
                membership=membership, regions=regions)
