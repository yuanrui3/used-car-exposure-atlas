// Rebuild the shared boundaries in the same Albers projection as the county map.
const fs = require('node:fs');
const path = require('node:path');
const source = path.resolve(process.argv[2] || __dirname);
const d3 = require(path.join(source, 'tools/d3.cjs'));
const topo = require(path.join(source, 'tools/topo.cjs'));
const raw = JSON.parse(fs.readFileSync(path.join(source, 'counties.topo.json'), 'utf8'));
const rows = d3.csvParse(fs.readFileSync(path.join(__dirname, 'counties.csv'), 'utf8'));
const included = new Set(rows.map(row => row.fips));
const stateCodes = new Set(rows.map(row => row.fips.slice(0, 2)));
const states = topo.feature(raw, raw.objects.states).features.filter(s => stateCodes.has(s.id));
const projection = d3.geoAlbers().fitExtent([[22,16],[966,587]], {type:'FeatureCollection', features:states});
const draw = d3.geoPath(projection).digits(1);
const owners = new Map();
for (const county of raw.objects.counties.geometries) {
  if (!included.has(county.id)) continue;
  for (const ref of county.arcs.flat(Infinity)) {
    const arc = ref < 0 ? ~ref : ref;
    if (!owners.has(arc)) owners.set(arc, new Set());
    owners.get(arc).add(county.id);
  }
}
const edges = [];
for (const [arc, ids] of owners) {
  // Four short junction arcs have three owners in the generalized source.
  // They supply no unambiguous two-county boundary.
  if (ids.size > 2) continue;
  const line = topo.feature(raw, {type:'LineString', arcs:[arc]});
  const coords = line.geometry.coordinates;
  if (!coords.some(([x,y]) => x !== coords[0][0] || y !== coords[0][1])) continue;
  const pair = [...ids].sort();
  edges.push([pair[0], pair[1] || null, draw(line)]);
}
fs.writeFileSync(path.join(__dirname, 'county_edges.json'), JSON.stringify(edges));
console.log(edges.length + ' boundary arcs');
