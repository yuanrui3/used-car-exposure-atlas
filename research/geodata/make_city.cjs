const fs=require('fs'), d3=require('./tools/d3.cjs'), topo=require('./tools/topo.cjs')
const raw=JSON.parse(fs.readFileSync(__dirname+'/counties.topo.json','utf8'))
const rows=d3.csvParse(fs.readFileSync(__dirname+'/counties.csv','utf8')), ids=new Set(rows.map(r=>r.fips))
const features=topo.feature(raw,raw.objects.counties).features.filter(f=>ids.has(f.id))
const states=topo.feature(raw,raw.objects.states).features.filter(f=>features.some(c=>c.id.startsWith(f.id)))
const proj=d3.geoAlbers().fitExtent([[22,16],[966,587]],{type:'FeatureCollection',features:states})
const cities=JSON.parse(fs.readFileSync(__dirname+'/../braking/city_braking.json','utf8'))
const byState=new Map(rows.map(r=>[r.state,r.fips.slice(0,2)]))
const out=cities.map(c=>{const coords=[c.lon,c.lat],pre=byState.get(c.state),county=features.find(f=>f.id.startsWith(pre)&&d3.geoContains(f,coords)); if(!county) console.log('outside land boundary',c.city,c.state);return {name:c.city,state:c.state,fips:county?.id,x:+proj(coords)[0].toFixed(2),y:+proj(coords)[1].toFixed(2),value:c.hard_brakes_per_1000_miles,geoid:c.place_geoid,lat:c.lat,lon:c.lon}})
fs.writeFileSync(__dirname+'/cities.json',JSON.stringify(out))
console.log(out.length,'cities')
const metros=JSON.parse(fs.readFileSync(__dirname+'/../braking/urban_congestion.json','utf8'))
const urban=metros.map(c=>{
  const override={'Corpus Christi TX':'Corpus Christi','Portland ME':'Portland, ME','Texas City TX':'Texas City'}[c.urban_area];
  const xy=override?JSON.parse(fs.readFileSync(__dirname+'/marine_metro_points.json'))[override]:[c.lon,c.lat],pt=proj(xy),pre=byState.get(c.state)
  const f=features.find(f=>f.id.startsWith(pre)&&d3.geoContains(f,xy))||features.find(f=>d3.geoContains(f,xy));
  if(!f)console.log('unassigned metro',c.urban_area)
  return {name:c.urban_area,state:c.state,fips:f?.id,x:+pt[0].toFixed(2),y:+pt[1].toFixed(2),delay:c.delay_hours_per_auto_commuter,peak:c.peak_vmt_congested_pct,lat:xy[1],lon:xy[0]}
})
fs.writeFileSync(__dirname+'/metros.json',JSON.stringify(urban))
