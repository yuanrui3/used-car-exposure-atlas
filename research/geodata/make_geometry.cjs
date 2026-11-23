const fs=require('fs'), path=require('path')
const d3=require('./tools/d3.cjs'), topo=require('./tools/topo.cjs')
const raw=JSON.parse(fs.readFileSync(__dirname+'/counties.topo.json','utf8'))
const rows=d3.csvParse(fs.readFileSync(__dirname+'/counties.csv','utf8'))
const rowById=new Map(rows.map(r=>[r.fips,r]))
const counties=topo.feature(raw,raw.objects.counties).features.filter(f=>rowById.has(f.id))
const tiny=JSON.parse(fs.readFileSync(__dirname+'/falls_church.geojson')).features[0];
if(d3.geoArea(tiny)>2*Math.PI) {
  const polygons=tiny.geometry.type==='MultiPolygon'?tiny.geometry.coordinates:[tiny.geometry.coordinates];
  polygons.forEach(poly=>poly.forEach(ring=>ring.reverse()));
}
counties.find(f=>f.id==='51610').geometry=tiny.geometry;
const states=topo.feature(raw,raw.objects.states).features.filter(f=>rows.some(r=>r.fips.startsWith(f.id)))
const proj=d3.geoAlbers().fitExtent([[22,16],[966,587]],{type:'FeatureCollection',features:states})
const draw=d3.geoPath(proj).digits(1)
const rnd=v=>Math.round(v*10)/10
const data={
  counties: counties.map(f=>{const r=rowById.get(f.id),pt=proj([+r.lon,+r.lat]);return [f.id,r.county,r.state,...pt.map(rnd),draw(f)]}),
  states:states.map(f=>{const ab=rows.find(r=>r.fips.startsWith(f.id)).state;return [ab,f.properties.name,draw(f),draw.bounds(f).flat().map(rnd)]}),
  projection:{translate:proj.translate(),scale:proj.scale()}
}
fs.writeFileSync(__dirname+'/../../dist/assets/geography.js','const GEO='+JSON.stringify(data)+';\n')
console.log(counties.length,states.length,fs.statSync(__dirname+'/../../dist/assets/geography.js').size)
