import React, {useRef} from 'react';
import Simulation from './Simulation.jsx';
import {useApp} from '../state.jsx';
import {historicalSections} from '../results-navigation.js';
import {LIVE_POLICIES, fmt} from '../live-data.js';
import {Chart} from '../chart.jsx';

const tabs=[['overview','Planned workload','space_dashboard'],['historical','Historical analysis','history']];
const WEEKS=8;
function Workload() {
  const ctx=useApp();
  if(ctx.live.status!=='ready') return <section className="results-panel"><h2>Planned workload</h2><p>{ctx.live.status==='loading'?'Loading live queue…':'Live queue unavailable.'}</p></section>;
  const key=LIVE_POLICIES[ctx.policy].key, rows=ctx.rows, capacity=ctx.live.data.calibration.capacity_hours_per_week;
  const labels=Array.from({length:WEEKS},(_,i)=>'W'+(i+1));
  const inWeek=w=>rows.filter(r=>r.plannedWeek[key]===w+1);
  const reviews=labels.map((_,w)=>inWeek(w).length), carbonReviews=labels.map((_,w)=>inWeek(w).filter(r=>r.lane==='carbon').length);
  const hours=labels.map((_,w)=>inWeek(w).reduce((s,r)=>s+r.effort,0));
  const lastWeek=Math.max(...rows.map(r=>r.plannedWeek[key]||0));
  const firstMonth=rows.filter(r=>r.plannedWeek[key]<=4);
  const tCO2=firstMonth.reduce((s,r)=>s+(r.carbon?.[1]||0),0);
  const cards=[
    {title:'Weeks to clear queue',value:lastWeek,unit:'weeks',note:`${rows.length} applications at ${fmt(capacity,0)} h/week`},
    {title:'Reviews in the next 4 weeks',value:firstMonth.length,unit:'files',note:`${firstMonth.filter(r=>r.lane==='max_wait').length} under maximum-wait protection`},
    {title:'Daily displacement reviewed first',value:fmt(tCO2,0),unit:'tCO₂e/day',note:'Central estimate of files planned in the next 4 weeks'},
  ];
  return <>
    <div className="results-kpis results-kpis-overview">{cards.map(card=><div className="results-kpi" key={card.title}><div className="results-kpi-label"><span>{card.title}</span></div><div className="results-kpi-value">{card.value}<small>{card.unit}</small></div><div className="results-kpi-bottom"><span>{card.note}</span></div></div>)}</div>
    <div className="results-chart-grid">
      <Chart title="Planned reviews per week" subtitle={`${LIVE_POLICIES[ctx.policy].label} order, live queue of ${ctx.live.data.as_of}`} labels={labels} unit="applications" series={[{name:'All lanes',values:reviews,color:'#b6c9df'},{name:'Carbon lane',values:carbonReviews,color:'#00785b'}]}/>
      <Chart title="Reviewer hours per week" subtitle="Planned effort against calibrated weekly capacity" labels={labels} unit="hours" series={[{name:'Capacity',values:labels.map(()=>capacity),color:'#b6c9df'},{name:'Planned',values:hours,color:'#00785b'}]}/>
    </div>
    <section className="results-panel"><h2>How the plan is built</h2><p>The live queue is simulated forward with the calibrated weekly capacity (observed decisions of the last 365 days × the 2023 calibration factor). Each week, capacity goes first to files over the maximum wait (up to half), then to the unscored lane and the small-project quota, then by carbon score. Change the policy on the Queue page to compare orders.</p></section>
  </>;
}

export default function Results() {
  const {resultsLocation}=useApp();
  const active=resultsLocation.section;
  const setActive=id=>{location.hash='/results?section='+id;};
  const panel=useRef(null), tabRefs=useRef([]);
  return <div className="results-page px-gutter-desktop py-space-xl">
    <header className="results-header"><div><span className="results-eyebrow">RESULTS</span><h1>Performance overview</h1><p>Planned workload for the live queue and the historical queue simulation.</p></div></header>
    <div className="results-toolbar"><div className="results-tabs" role="tablist" aria-label="Results sections">{tabs.map(([id,label,icon],index)=><button key={id} ref={el=>tabRefs.current[index]=el} id={'results-tab-'+id} role="tab" aria-selected={active===id} aria-controls="results-panel" tabIndex={active===id?0:-1} onClick={()=>setActive(id)} onKeyDown={e=>{let next;if(e.key==='ArrowRight')next=(index+1)%tabs.length;else if(e.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;else return;e.preventDefault();setActive(tabs[next][0]);tabRefs.current[next]?.focus();}}><span className="material-symbols-outlined" aria-hidden="true">{icon}</span>{label}</button>)}</div></div>
    <div id="results-panel" ref={panel} role="tabpanel" aria-labelledby={'results-tab-'+active} tabIndex={0} className="results-content">
      {active==='overview'&&<Workload/>}
      {active==='historical'&&<><nav className="historical-section-picker" aria-label="Historical analysis sections">{historicalSections.map(([id,label])=><a key={id} href={'#/results?section=historical&detail='+id} aria-current={resultsLocation.detail===id?'page':undefined}>{label}</a>)}</nav><Simulation section={resultsLocation.detail}/></>}
    </div>
  </div>;
}
