'use strict';
(function () {
  const $ = id => document.getElementById(id);
  const ns = 'http://www.w3.org/2000/svg';
  const county = new Map(GEO.counties.map(r => [r[0],r]));
  const state = new Map(GEO.states.map(r => [r[0],r[1]]));
  const metrics = DATA.metrics;
  const groups = DATA.groups;
  const colorSets = {
    earth:['#e7eee1','#c8d8ad','#abc58d','#dbbc74','#cb8555','#a34830'],
    cool:['#ebf1ed','#d0e4dc','#a1cebd','#66b0a4','#31878b','#245968'],
    hot:['#f5edda','#eddaa8','#ecc181','#e69b65','#ce7052','#a94738'],
    violet:['#e9ecf0','#d1dbe5','#aebed4','#91a2c0','#707fa4','#515c81']
  };
  const cities=[...DATA.cities.map(c=>({...c,kind:'brake'})),...DATA.metros.map(c=>({...c,kind:'metro'}))];
  const pointValue=(c,k)=>k==='brake'?c.value:c[k];
  const asPoint=(c,k)=>metrics[k].point===c.kind&&pointValue(c,k)!=null;
  const citiesByCounty=new Map();
  cities.forEach(c=>{if(!citiesByCounty.has(c.fips))citiesByCounty.set(c.fips,[]);citiesByCounty.get(c.fips).push(c)});
  let mode=groups[0].mode, group=groups[0].id, key=groups[0].keys[0], a='18157', b=null, active='A', waiting=false;
  const annualView=()=>mode==='annual'||mode==='clusters';
  const clusterFor=id=>CLUSTERS.regions[CLUSTERS.membership[id]];
  const clusterType=region=>region.kind==='low'?'Lower exposure':'Higher exposure';
  const clusterLocation=region=>{
    const anchor=county.get(region.anchor);
    return anchor[1]+', '+anchor[2];
  };
  const clusterColors={low:['#87c8b5','#145e52'],high:['#e7a18a','#923d2c'],outside:['#e3e7e5','#c4cecb']};
  const preferred=new Map();
  const citySelected={A:null,B:null};
  const monthNames=['January','February','March','April','May','June','July','August','September','October','November','December'];
  let month=0;
  const rawValue=(id,k)=>metrics[k].seasonal?DATA.seasons[id]?.[k]?.[month]:DATA.values[id]?.[k];
  const dated=m=>(m.seasonal?monthNames[month]+' · ':'')+m.period;
  let view=[0,0,990,605], drag=null, dragged=false;
  const paths=new Map();
  const urbanCities=cities.filter(c=>c.fips).map(c=>({id:c.fips,label:c.name+(c.kind==='brake'?', '+c.state+' · city braking':' · urban-area delay'),city:c}));
  const countyOptions=GEO.counties.map(r=>({id:r[0],label:r[1]+', '+r[2],search:r[1]+' '+r[2]+' '+state.get(r[2])+' '+r[0]})).sort((x,y)=>x.label.localeCompare(y.label));
  const mainPlace=()=>active==='B'&&b?b:a;
  function svg(tag,attrs){const el=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v));return el}
  function opt(value,title){const o=document.createElement('option');o.value=value;o.textContent=title;return o}
  function setOpts(el,items,current){el.replaceChildren(...items.map(o=>opt(o[0],o[1])));el.value=current}
  function fmt(v,d=1){return Number(v).toLocaleString('en-US',{minimumFractionDigits:0,maximumFractionDigits:d})}
  function paint(v,m){if(v==null)return 'url(#missing)';const index=m.bins.filter(c=>v>=c).length;return colorSets[m.palette][m.reverse?5-index:index]}
  function vals(id,k,slot){
    const m=metrics[k];
    if(m.point){
      let cs=(citiesByCounty.get(id)||[]).filter(c=>asPoint(c,k));
      if(slot&&citySelected[slot]&&cs.includes(citySelected[slot]))cs=[citySelected[slot]];
      return cs.map(c=>({v:pointValue(c,k),s:c.name}));
    }
    const v=rawValue(id,k);return v==null?[]:[{v}];
  }
  function readingText(id,k,slot){
    const m=metrics[k],v=vals(id,k,slot);
    if(!v.length)return m.point?'No sampled place':'No data';
    return v.map(x=>fmt(x.v,m.digits)+' '+m.unit+(x.s?' · '+x.s:'')).join(' / ');
  }
  function makeMap(){
    const cf=document.createDocumentFragment(),sf=document.createDocumentFragment(),lf=document.createDocumentFragment();
    for(const [id,,,x,y,d] of GEO.counties){const p=svg('path',{d,'data-id':id});cf.append(p);paths.set(id,p)}
    for(const [ab,,d,bounds] of GEO.states){
      sf.append(svg('path',{d}));
      if(['DC','RI','DE','MA','CT','NH','VT','MD','NJ'].includes(ab))continue;
      const rr=GEO.counties.filter(r=>r[2]===ab),x=rr.reduce((s,r)=>s+r[3],0)/rr.length,y=rr.reduce((s,r)=>s+r[4],0)/rr.length;
      const t=svg('text',{x,y});t.textContent=ab;lf.append(t);
    }
    $('countyPaths').append(cf);$('statePaths').append(sf);$('labels').append(lf);
  }
  function setupClusters(){
    const selector=$('clusterFinder');
    selector.append(opt('','National view'));
    const counts=[];
    for(const kind of ['low','high']){
      const regions=Object.entries(CLUSTERS.regions).filter(([,r])=>r.kind===kind)
        .sort((x,y)=>y[1].count-x[1].count || x[0].localeCompare(y[0]));
      const section=document.createElement('optgroup');
      section.label=kind==='low'?'Lower exposure':'Higher exposure';
      counts.push(regions.length+' '+(kind==='low'?'lower':'higher'));
      for(const [id,r] of regions){
        section.append(opt(id,'Near '+clusterLocation(r)+' · '+r.count+' counties'));
        $('clusterOutlines').append(svg('path',{id:'outline-'+id,d:r.path,stroke:clusterColors[kind][1]}));
      }
      selector.append(section);
    }
    $('clusterCounts').textContent=counts.join(' · ')+' exposure clusters';
    selector.onchange=()=>{
      const id=selector.value;
      if(!id){setView([0,0,990,605]);return}
      const r=CLUSTERS.regions[id];
      pick(r.anchor);
      const box=$('outline-'+id).getBBox(),ratio=990/605;
      const w=Math.min(990,Math.max(120,box.width*1.3,box.height*ratio*1.3));
      setView([box.x+box.width/2-w/2,box.y+box.height/2-w/(2*ratio),w,w/ratio]);
    };
  }
  function drawClusterMap(){
    for(const [id,path] of paths){
      const kind=clusterFor(id)?.kind || 'outside';
      path.setAttribute('fill',clusterColors[kind][0]);
    }
    $('points').replaceChildren();
    $('legendTitle').textContent='Typical-year used-car exposure';
    const items=[['low','Lower exposure'],['high','Higher exposure'],['outside','Outside a cluster']];
    $('swatches').replaceChildren(...items.map(([kind,label])=>{
      const tag=document.createElement('span');tag.className='swatch';
      const chip=document.createElement('i');chip.className='chip clusterChip';
      chip.style.background=clusterColors[kind][0];chip.style.borderColor=clusterColors[kind][1];
      tag.append(chip,label);return tag;
    }));
    $('legendNote').textContent='Outlines join at least '+CLUSTERS.minCount+' neighboring counties in the bottom or top 20% of annual scores (cutoffs about '+fmt(CLUSTERS.lower,2)+' and '+fmt(CLUSTERS.higher,2)+'). Gray also includes isolated high- or low-scoring counties.';
  }
  function clusterStatus(id){
    const region=clusterFor(id);
    if(region)return clusterType(region)+' cluster · near '+clusterLocation(region);
    const value=rawValue(id,'annualExposure');
    if(value==null)return 'Annual score unavailable';
    if(value<=CLUSTERS.lower||value>=CLUSTERS.higher)return (value<=CLUSTERS.lower?'Low':'High')+' score · fewer than '+CLUSTERS.minCount+' connected counties';
    return 'Outside a cluster · middle 60% of annual scores';
  }
  function showMembership(id){
    const region=clusterFor(id),box=$('clusterMembership');
    box.className=region?region.kind:'outside';
    const label=document.createElement('strong');label.textContent=clusterStatus(id);
    box.replaceChildren(label);
    if(region){
      const detail=document.createElement('span');
      detail.textContent=region.count+' counties · average score '+fmt(region.mean)+' / 100 · '+region.states.join(', ');
      box.append(detail);
    }
  }
  function drawMapColors(){
    $('clusterOutlines').style.display=mode==='clusters'?'':'none';
    if(mode==='clusters'){drawClusterMap();return}
    const m=metrics[key];
    const ff=document.createDocumentFragment();
    for(const [id,p] of paths)p.setAttribute('fill',m.point?'#dce5e2':paint(rawValue(id,key),m));
    if(m.point) cities.forEach((c,i)=>{
      if(!asPoint(c,key))return;
      const dot=svg('circle',{cx:c.x,cy:c.y,r:key==='brake'?4.2:3.5,fill:paint(pointValue(c,key),m),stroke:'#29444c','stroke-width':.8,'data-city':i,'data-id':c.fips});
      dot.style.cursor='pointer';ff.append(dot)
    });
    $('points').replaceChildren(ff);
    $('legendTitle').textContent=mode==='annual'?'Annual exposure · lower to higher':m.title+' · '+m.unit;
    const starts=[null,...m.bins],format=x=>fmt(x,m.binDigits??m.digits);
    const marks=starts.map((low,i)=>{
      const el=document.createElement('span');el.className='swatch';
      const chip=document.createElement('i');chip.className='chip';chip.style.background=colorSets[m.palette][m.reverse?5-i:i];el.append(chip);
      const high=m.bins[i];el.append(low===null?'< '+format(high):high===undefined?'≥ '+format(low):format(low)+'–<'+format(high));return el
    });
    const miss=document.createElement('span');miss.className='swatch';miss.innerHTML=m.point?'<i class="chip" style="background:#dce5e2"></i>Outside point sample':'<i class="chip" style="background:repeating-linear-gradient(135deg,#e2e5e4,#e2e5e4 2px,#c1c7c6 2px,#c1c7c6 3px)"></i>No data';
    $('swatches').replaceChildren(...marks,miss);
    $('legendNote').textContent=m.scale+' · '+dated(m)+'. '+(m.note||'');
  }
  function drawMarks(){
    const g=$('selectionMarks');g.replaceChildren();
    const z=view[2]/990;
    for(const [slot,id] of [['B',b],['A',a]]){
      if(!id)continue;
      const r=county.get(id),c=citySelected[slot]&&asPoint(citySelected[slot],key)?citySelected[slot]:null,x=c?c.x:r[3],y=c?c.y:r[4],color=slot==='A'?'#174f53':'#9c4828';
      g.append(svg('path',{d:r[5],fill:'none',stroke:color,'stroke-width':1.8,'vector-effect':'non-scaling-stroke'}));
      const flag=svg('g',{transform:'translate('+x+' '+y+') scale('+z+')'});flag.append(svg('path',{d:'M0 0L7 -11H-7Z',fill:color}),svg('circle',{cx:0,cy:-14,r:8.5,fill:color,stroke:'white','stroke-width':1.4}));
      const t=svg('text',{x:0,y:-10.5,'text-anchor':'middle','font-size':10,'font-weight':700,fill:'white'});t.textContent=slot;flag.append(t);g.append(flag)
    }
  }
  function updateGroup(){
    const gs=groups.filter(g=>g.mode===(mode==='clusters'?'annual':mode));if(!gs.some(g=>g.id===group))group=gs[0].id;
    const gg=gs.find(g=>g.id===group);if(!gg.keys.includes(key))key=preferred.get(group)||gg.keys[0];
    setOpts($('group'),gs.map(g=>[g.id,g.title]),group);
    setOpts($('metric'),gg.keys.map(k=>[k,metrics[k].title]),key);
    $('metric').disabled=gg.keys.length===1;
    $('monthLabel').hidden=!metrics[key].seasonal;$('month').value=String(month);
    $('annualMapHead').hidden=mode!=='annual';
    $('clusterMapHead').hidden=mode!=='clusters';
    $('layerControls').hidden=annualView();
    $('tabClusters').setAttribute('aria-pressed',String(mode==='clusters'));
    $('tabAnnual').setAttribute('aria-pressed',String(mode==='annual'));
    $('tabExposure').setAttribute('aria-pressed',String(mode==='exposure'));$('tabEvents').setAttribute('aria-pressed',String(mode==='events'));
  }
  function sourceLinks(node,src){
    src.forEach(([name,url],i)=>{if(i)node.append(' · ');const a=document.createElement('a');a.textContent=name;a.href=url;if(!url.startsWith('#')){a.target='_blank';a.rel='noopener'}node.append(a)})
  }
  function restoreLink(){
    const p=new URLSearchParams(location.search);const parsed=Number(p.get('month'));if(parsed>=1&&parsed<=12&&Number.isInteger(parsed))month=parsed-1;const k=p.get('layer'),id=p.get('a'),other=p.get('b');
    if(county.has(id))a=id;
    if(county.has(other))b=other;
    if(k==='clusters'){mode='clusters';group='overall';key='annualExposure';return}
    if(Object.hasOwn(metrics,k)){key=k;const g=groups.find(g=>g.keys.includes(k));group=g.id;mode=g.mode;preferred.set(group,key)}
  }
  function writeLink(){
    if(!/^https?:$/.test(location.protocol))return;
    const u=new URL(location.href);
    u.searchParams.set('a',a);if(b)u.searchParams.set('b',b);else u.searchParams.delete('b');
    u.searchParams.set('layer',mode==='clusters'?'clusters':key);if(metrics[key].seasonal)u.searchParams.set('month',String(month+1));else u.searchParams.delete('month');history.replaceState(null,'',u);
  }
  function renderDetails(){
    const id=mainPlace(),slot=active==='B'&&b?'B':'A',c=county.get(id),m=metrics[key],v=vals(id,key,slot);
    document.querySelector('.place .pin').textContent=slot;document.querySelector('.place .pin').classList.toggle('b',slot==='B');
    $('placeName').textContent=c[1];$('placeState').textContent=state.get(c[2])+' · FIPS '+id;
    if(!v.length){$('number').textContent='—';$('unit').textContent=m.point?'No sampled place':'No data'}
    else if(v.length>1){$('number').textContent=fmt(Math.min(...v.map(x=>x.v)),m.digits)+'–'+fmt(Math.max(...v.map(x=>x.v)),m.digits);$('unit').textContent=m.unit}
    else{$('number').textContent=fmt(v[0].v,m.digits);$('unit').textContent=m.unit}
    $('readingName').textContent=m.title;$('meta').textContent=m.scale+' · '+dated(m);
    let desc=m.desc;const ext=DATA.stationInfo?.[id];
    if(m.station&&ext){const i=m.station==='noaa'?0:m.station==='snow'?4:2;if(ext[i]!=null)desc+=' Station '+ext[i]+', '+fmt(ext[i+1],0)+' km from the county reference point.'}
    if(key==='gradeLocal'&&DATA.values[id]?.gradeMi!=null)desc+=' Accepted sample: '+fmt(DATA.values[id].gradeMi,1)+' miles across '+fmt(DATA.values[id].gradeN,0)+' intervals.';
    if(key==='rough'&&DATA.values[id]?.roughcov!=null)desc+=' Reporting covers '+fmt(DATA.values[id].roughcov,1)+'% of this state’s federal-aid network.';
    if(key==='roughLocal'&&DATA.values[id]?.ratedMi!=null)desc+=' Sample length: '+fmt(DATA.values[id].ratedMi,0)+' miles.';
    if(m.point&&v.length)desc+=' '+v.map(x=>x.s+' '+fmt(x.v,m.digits)).join(' · ')+'.';
    $('sideDesc').textContent=desc;$('datasource').href=m.src[0][1];$('datasource').textContent=m.src[0][0];
    $('datasource').target=annualView()?'_self':'_blank';
    $('annualGauge').hidden=!annualView();
    $('annualDrivers').hidden=!annualView();
    if(annualView())renderAnnualDetails(id);
    $('clusterMembership').hidden=mode!=='clusters';
    if(mode==='clusters'){
      showMembership(id);
      $('datasource').href='#cluster-method';$('datasource').textContent='How cluster boundaries are drawn';
    }
    $('compareBtn').textContent=waiting?'Cancel county selection':b?(active==='A'?'Edit county B':'Edit county A'):'Add comparison county';
    $('compareHint').textContent=waiting?'Click the map or search above to choose county B.':b?'Click the map or search to change county '+active+'.':'Click the map or search to change county A.';
    $('swap').hidden=!b;$('clearB').hidden=!b;drawMarks();renderTable();writeLink();
  }
  function smallText(parent,value){
    const el=document.createElement('div');el.className='tblsmall';el.textContent=value;parent.append(el);
  }
  function renderAnnualDetails(id){
    const rec=DATA.annual.records[id],score=rawValue(id,'annualExposure'),gauge=$('annualGauge');
    gauge.querySelector('.marker').style.left=score+'%';
    const range=gauge.querySelector('.range');
    range.style.left=rec.low+'%';range.style.width=(rec.high-rec.low)+'%';
    $('readingName').textContent='Annual exposure score';
    $('meta').textContent=rec.observed+' of '+DATA.annual.inputCount+' indicators available';
    const missing=Object.values(DATA.annual.components).flat().filter(k=>rawValue(id,k)==null);
    $('sideDesc').textContent=missing.length
      ? 'Missing-data range '+fmt(rec.low)+'–'+fmt(rec.high)+' if the missing readings fall at either end of the scale. Missing: '+missing.map(k=>metrics[k].title).join(', ')+'.'
      : 'All 11 categories have complete inputs. Higher scores indicate more exposure across the selected indicators.';
    const drivers=groups.filter(g=>DATA.annual.components[g.id]?.every(k=>rawValue(id,k)!=null))
      .sort((x,y)=>rec.categories[y.id]-rec.categories[x.id]).slice(0,2);
    const parent=$('annualDrivers');parent.replaceChildren();
    if(drivers.length){
      const title=document.createElement('strong');title.textContent='Highest categories with complete inputs';parent.append(title);
      for(const g of drivers){
        const line=document.createElement('div'),value=document.createElement('b');
        value.textContent=fmt(rec.categories[g.id]);line.append(g.title,value);parent.append(line);
      }
    }
  }
  function annualCell(row,id,category){
    const cell=row.insertCell();if(!id){cell.textContent='—';return}
    const rec=DATA.annual.records[id],inputs=DATA.annual.components[category];
    if(!inputs){
      cell.className='overallScore';cell.textContent=fmt(rawValue(id,'annualExposure'))+' / 100';
      const info=rec.observed+' of '+DATA.annual.inputCount+' inputs';
      smallText(cell,info+(rec.observed<DATA.annual.inputCount?' · range '+fmt(rec.low)+'–'+fmt(rec.high):''));return;
    }
    const score=document.createElement('strong');score.textContent=fmt(rec.categories[category])+' / 100';cell.append(score);
    for(const k of inputs){
      const value=rawValue(id,k),m=metrics[k];
      smallText(cell,m.title+' · '+(value==null?'Missing (rank 50 used)':fmt(value,m.digits)+' '+m.unit));
    }
  }
  function renderAnnualTable(body){
    const total=body.insertRow();total.className='totalRow';total.insertCell().textContent='Annual exposure score';
    annualCell(total,a);annualCell(total,b);
    if(mode==='clusters'){
      const row=body.insertRow();row.insertCell().textContent='Regional cluster';
      row.insertCell().textContent=clusterStatus(a);row.insertCell().textContent=b?clusterStatus(b):'—';
    }
    for(const g of groups.filter(g=>DATA.annual.components[g.id])){
      const row=body.insertRow(),cell=row.insertCell();cell.textContent=g.title;
      const nav=document.createElement('div');nav.className='inputLinks';
      for(const k of DATA.annual.components[g.id]){
        const button=document.createElement('button');button.textContent=metrics[k].title;
        button.onclick=()=>{mode=g.mode;group=g.id;key=k;preferred.set(group,k);refresh();$('explorer').scrollIntoView({block:'start'})};
        nav.append(button);
      }
      cell.append(nav);annualCell(row,a,g.id);annualCell(row,b,g.id);
    }
  }
  function renderTable(){
    const table=$('profile');table.replaceChildren();
    const thr=table.createTHead().insertRow();
    [annualView()?'Exposure category':'Reading','A · '+county.get(a)[1]+', '+county.get(a)[2],b?'B · '+county.get(b)[1]+', '+county.get(b)[2]:'B · Select a county'].forEach(x=>{const th=document.createElement('th');th.textContent=x;thr.append(th)});
    const body=table.createTBody();
    $('profileTitle').textContent=annualView()?'What drives the annual score?':'County profiles';
    $('profileDesc').textContent=annualView()?'Compare the 11 equally weighted categories. Each score is on the same 0–100 scale. Select an indicator to see its map.':'Compare the readings in their original units. Select a reading to display it on the map.';
    if(annualView()){renderAnnualTable(body);return}
    for(const g of groups){
      const k=g.id===group?key:preferred.get(g.id)||g.keys[0],m=metrics[k],row=body.insertRow(),td=row.insertCell(),btn=document.createElement('button');btn.textContent=m.title;btn.onclick=()=>{mode=g.mode;group=g.id;key=k;refresh();$('explorer').scrollIntoView({block:'start'})};td.append(btn);
      const meta=document.createElement('div');meta.className='tblsmall';meta.textContent=m.scale+' · '+dated(m);td.append(meta);
      row.insertCell().textContent=readingText(a,k,'A');row.insertCell().textContent=b?readingText(b,k,'B'):'—';
    }
  }
  function refresh(){updateGroup();drawMapColors();renderDetails();$('tip').hidden=true}
  function pick(id,city=null){
    if(!county.has(id))return;
    const slot=waiting?'B':active;if(slot==='B')b=id;else a=id;active=slot;citySelected[slot]=city;waiting=false;
    if(city&&!annualView()&&!asPoint(city,key)){const g=groups.find(o=>o.keys.includes('brake'));mode=g.mode;group=g.id;key=city.kind==='brake'?'brake':'delay';preferred.set(group,key);updateGroup();drawMapColors()}
    $('finder').value='';$('matches').hidden=true;renderDetails();
  }
  function showMatches(){
    const q=$('finder').value.trim().toLowerCase();if(!q){$('matches').hidden=true;return}
    const tokens=q.replaceAll(',',' ').split(/\s+/).filter(Boolean);
    const options=[...countyOptions,...urbanCities].filter(o=>tokens.every(t=>(o.search||o.label).toLowerCase().includes(t))).slice(0,15);
    $('matches').replaceChildren(...options.map(o=>{const b=document.createElement('button');b.textContent=o.label;b.onclick=()=>{pick(o.id,o.city);let c=county.get(o.id);if(view[2]<990&&!inside(c[3],c[4]))setView([0,0,990,605])};return b}));
    if(!options.length){const t=document.createElement('span');t.textContent='No matching county or sampled city.';$('matches').append(t)}$('matches').hidden=false
  }
  function setView(v){
    const w=Math.min(990,Math.max(120,v[2])),h=w*605/990,x=Math.max(0,Math.min(990-w,v[0])),y=Math.max(0,Math.min(605-h,v[1]));view=[x,y,w,h];
    $('map').setAttribute('viewBox',view.join(' '));$('map').classList.toggle('zoomed',w<989);$('zoomOut').disabled=w>=989;$('zoomIn').disabled=w<=120.1;drawMarks();
  }
  function inside(x,y){return x>=view[0]&&x<=view[0]+view[2]&&y>=view[1]&&y<=view[1]+view[3]}
  function zoom(f){let c=county.get(mainPlace()),cx=c[3],cy=c[4];if(!inside(cx,cy)){cx=view[0]+view[2]/2;cy=view[1]+view[3]/2}let w=Math.max(120,Math.min(990,view[2]*f)),h=w*605/990;setView([cx-w/2,cy-h/2,w,h])}
  function buildMethods(){
    for(const g of groups){
      const a=document.createElement('article'),h=document.createElement('h3');h.textContent=g.title;a.append(h);
      for(const k of g.keys){const m=metrics[k],p=document.createElement('p'),b=document.createElement('b');b.textContent=m.title+'. ';p.append(b,m.method+' ');sourceLinks(p,m.src);a.append(p)}
      $('methodList').append(a)
    }
    $('coverageText').innerHTML=DATA.coverageHtml;$('validationText').innerHTML=DATA.validationHtml;
  }
  function setup(){
    setOpts($('month'),monthNames.map((name,i)=>[i,name]),'0');
    $('month').onchange=()=>{month=Number($('month').value);refresh()};
    makeMap();setupClusters();const cb=document.createElement('button');cb.id='clearB';cb.textContent='Clear B';cb.style.cssText='margin-left:8px;background:white;color:var(--teal)';$('compareBtn').after(cb);
    $('compareBtn').onclick=()=>{if(waiting)waiting=false;else if(b)active=active==='A'?'B':'A';else{waiting=true;$('finder').focus()}renderDetails()};
    cb.onclick=()=>{b=null;active='A';waiting=false;citySelected.B=null;renderDetails()};
    $('swap').onclick=()=>{[a,b]=[b,a];[citySelected.A,citySelected.B]=[citySelected.B,citySelected.A];renderDetails()};
    $('finder').oninput=showMatches;$('finder').onfocus=showMatches;
    $('finder').onkeydown=e=>{if(e.key==='Escape')$('matches').hidden=true;else if(['Enter','ArrowDown'].includes(e.key)&&!$('matches').hidden){const el=$('matches').querySelector('button');if(el){e.preventDefault();if(e.key==='Enter')el.click();else el.focus()}}};
    $('matches').onkeydown=e=>{if(e.key==='ArrowDown')e.target.nextElementSibling?.focus();if(e.key==='ArrowUp')e.target.previousElementSibling?.focus();if(e.key==='Escape'){$('finder').focus();$('matches').hidden=true}};
    document.addEventListener('click',e=>{if(!e.target.closest('.pickers'))$('matches').hidden=true});
    $('group').onchange=()=>{group=$('group').value;key=preferred.get(group)||groups.find(g=>g.id===group).keys[0];refresh()};
    $('metric').onchange=()=>{key=$('metric').value;preferred.set(group,key);refresh()};
    $('tabClusters').onclick=()=>{mode='clusters';refresh()};
    $('tabAnnual').onclick=()=>{mode='annual';refresh()};
    $('tabExposure').onclick=()=>{mode='exposure';refresh()};$('tabEvents').onclick=()=>{mode='events';refresh()};
    $('zoomIn').onclick=()=>zoom(.62);$('zoomOut').onclick=()=>zoom(1.65);$('reset').onclick=()=>{$('clusterFinder').value='';setView([0,0,990,605])};
    const map=$('map'),tip=$('tip');
    map.onpointerdown=e=>{drag={x:e.clientX,y:e.clientY,view:[...view]};dragged=false};
    map.onpointermove=e=>{
      if(drag&&e.buttons&&view[2]<989){
        const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.hypot(dx,dy)>3){dragged=true;const scale=map.getScreenCTM().a;setView([drag.view[0]-dx/scale,drag.view[1]-dy/scale,drag.view[2],drag.view[3]]);tip.hidden=true;return}
      }
      const el=e.target.closest('[data-id]');if(!el||e.pointerType==='touch'){tip.hidden=true;return}
      const id=el.dataset.id,c=county.get(id),idx=el.dataset.city,city=idx!==undefined?cities[+idx]:null;
      tip.textContent=city?city.name+', '+city.state+' · '+fmt(pointValue(city,key),metrics[key].digits)+' '+metrics[key].unit:c[1]+', '+c[2]+' · '+readingText(id,key);
      if(mode==='clusters')tip.textContent+=' · '+clusterStatus(id);
      const rect=map.parentElement.getBoundingClientRect();tip.hidden=false;
      tip.style.left=Math.max(2,Math.min(rect.width-tip.offsetWidth-2,e.clientX-rect.left+10))+'px';
      tip.style.top=Math.max(2,Math.min(rect.height-tip.offsetHeight-2,e.clientY-rect.top+10))+'px';
    };
    window.addEventListener('pointerup',()=>drag=null);map.onpointerleave=()=>tip.hidden=true;
    map.onclick=e=>{if(dragged){dragged=false;return}const el=e.target.closest('[data-id]');if(el)pick(el.dataset.id,el.dataset.city!==undefined?cities[+el.dataset.city]:null)};
    restoreLink();buildMethods();refresh();setView(view);$('loading').hidden=true;$('explorer').hidden=false;
  }
  setup();
})();
