import React, {useState, useRef} from 'react';
import Simulation from './Simulation.jsx';
import {useApp} from '../state.jsx';
import {historicalSections} from '../results-navigation.js';
import {weeks,days,summarize} from '../results-data.js';

const tabs=[['overview','Overview','space_dashboard'],['throughput','Applications','bar_chart'],['waiting','Waiting time','show_chart'],['capacity','Capacity & ratios','donut_large'],['historical','Historical analysis','history']];
const round=value=>Number(value.toFixed(1));

function Chart({title,subtitle,labels,series,line=false,unit}) {
  const max=Math.max(1,...series.flatMap(s=>s.values));
  const ceiling=Math.ceil(max/4)*4;
  const x=i=>58+(i+.5)*560/labels.length;
  const y=value=>224-value/ceiling*174;
  return <section className="results-panel">
    <div className="results-chart-heading"><h2>{title}</h2><span>{unit}</span></div><p>{subtitle}</p>
    <div className="results-legend">{series.map(s=><span key={s.name}><i style={{background:s.color}}/>{s.name}</span>)}</div>
    <svg viewBox="0 0 650 270" role="img" aria-label={title+'. '+series.map(s=>s.name+': '+s.values.map((v,i)=>labels[i]+' '+round(v)+' '+unit).join(', ')).join('; ')}>
      {[0,1,2,3,4].map(i=><g key={i}><line x1="58" y1={y(ceiling*i/4)} x2="618" y2={y(ceiling*i/4)} stroke="#e8edf1"/><text x="46" y={y(ceiling*i/4)+4} textAnchor="end" fill="#748091" fontSize="11">{round(ceiling*i/4)}</text></g>)}
      {labels.map((label,i)=><text key={label} x={x(i)} y="248" textAnchor="middle" fill="#748091" fontSize="11">{label}</text>)}
      {series.map((s,si)=><g key={s.name}>
        {line&&<polyline points={s.values.map((v,i)=>`${x(i)},${y(v)}`).join(' ')} fill="none" stroke={s.color} strokeWidth="3" strokeLinejoin="round"/>}
        {s.values.map((value,i)=>line?<g key={i}><circle cx={x(i)} cy={y(value)} r="4" fill="white" stroke={s.color} strokeWidth="2"><title>{labels[i]} · {s.name}: {round(value)} {unit}</title></circle><text x={x(i)} y={y(value)-12} textAnchor="middle" fill={s.color} fontSize="11">{round(value)}</text></g>:<g key={i}><rect x={x(i)+(si-series.length/2)*25} y={y(value)} width="20" height={224-y(value)} rx="4" fill={s.color}><title>{labels[i]} · {s.name}: {round(value)} {unit}</title></rect><text x={x(i)+(si-series.length/2)*25+10} y={y(value)-7} textAnchor="middle" fill={s.color} fontSize="10">{round(value)}</text></g>)}
      </g>)}
    </svg>
    <details className="chart-values"><summary>View chart data</summary><div className="overflow-x-auto"><table><thead><tr><th>Period</th>{series.map(s=><th key={s.name}>{s.name} ({unit})</th>)}</tr></thead><tbody>{labels.map((label,i)=><tr key={label}><th>{label}</th>{series.map(s=><td key={s.name}>{round(s.values[i])}</td>)}</tr>)}</tbody></table></div></details>
  </section>;
}

function Ratio({label,value,detail}) {
  return <div className="results-ratio"><div className="results-ring" style={{background:`conic-gradient(#00785b ${Math.min(value,100)}%, #eaf0f3 0)`}} role="img" aria-label={`${label}: ${round(value)}%`}><span>{round(value)}<small>%</small></span></div><div><h3>{label}</h3><p>{detail}</p></div></div>;
}

export default function Results() {
  const {resultsLocation}=useApp();
  const active=resultsLocation.section;
  const setActive=id=>{location.hash='/results?section='+id;};
  const [weekIndex,setWeekIndex]=useState(3);
  const panel=useRef(null), tabRefs=useRef([]);
  const week=weeks[weekIndex], stats=summarize(week), previous=weekIndex?summarize(weeks[weekIndex-1]):null;
  const selectedWeeks=weeks.slice(0,weekIndex+1), summaries=selectedWeeks.map(summarize);
  const change=(key,unit='')=>previous?`${stats[key]-previous[key]>0?'+':''}${round(stats[key]-previous[key])}${unit} vs prior week`:'First sample week';
  function openCard(id){setActive(id);requestAnimationFrame(()=>{panel.current?.focus({preventScroll:true});panel.current?.scrollIntoView({behavior:'smooth',block:'start'});});}
  function exportWeek(e){
    e.stopPropagation();
    const rows=[['Dataset','Illustrative weekly demo'],['Week',week.label],['Day','Received','Completed','Mean wait of completed reviews (days)','Reviewer hours'],...days.map((d,i)=>[d,week.received[i],week.completed[i],week.wait[i],week.hours[i]]),['Total',stats.received,stats.completed,round(stats.wait),stats.hours],['Utilization (%)',round(stats.utilization)],['Completed / received (%)',round(stats.completion)]];
    const blob=new Blob([rows.map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`weekly-results-demo-${weekIndex+1}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  const cards=[
    {id:'throughput',icon:'task_alt',title:'Reviews completed',value:stats.completed,unit:'applications',note:change('completed'),spark:week.completed},
    {id:'waiting',icon:'schedule',title:'Average waiting time',value:round(stats.wait),unit:'days',note:change('wait',' d'),spark:week.wait},
    {id:'capacity',icon:'speed',title:'Capacity utilization',value:round(stats.utilization),unit:'%',note:`${stats.hours} / ${stats.capacity} reviewer hours`,spark:week.hours},
    {id:'throughput',icon:'trending_up',title:'Completed / received',value:round(stats.completion),unit:'%',note:`${stats.completed} completed · ${stats.received} received`,spark:week.completed.map((v,i)=>v/week.received[i]*100)},
  ];
  return <div className="results-page px-gutter-desktop py-space-xl">
    <header className="results-header"><div><span className="results-eyebrow">OPERATIONS · WEEKLY OVERVIEW</span><h1>Weekly Results</h1><p>Applications, waiting times and review capacity at a glance.</p></div><div className="results-actions"><span className="results-demo">Illustrative demo data</span>{active!=='historical'&&<button className="queue-control" onClick={exportWeek}><span className="material-symbols-outlined" aria-hidden="true">download</span>Export week</button>}</div></header>
    <div className="results-toolbar"><div className="results-tabs" role="tablist" aria-label="Results sections">{tabs.map(([id,label,icon],index)=><button key={id} ref={el=>tabRefs.current[index]=el} id={'results-tab-'+id} role="tab" aria-selected={active===id} aria-controls="results-panel" tabIndex={active===id?0:-1} onClick={()=>setActive(id)} onKeyDown={e=>{let next;if(e.key==='ArrowRight')next=(index+1)%tabs.length;else if(e.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;else if(e.key==='Home')next=0;else if(e.key==='End')next=tabs.length-1;else return;e.preventDefault();setActive(tabs[next][0]);tabRefs.current[next]?.focus();}}><span className="material-symbols-outlined" aria-hidden="true">{icon}</span>{label}</button>)}</div>{active!=='historical'&&<label className="results-week">Week<select value={weekIndex} onChange={e=>setWeekIndex(Number(e.target.value))}>{weeks.map((w,i)=><option value={i} key={w.label}>{w.label}</option>)}</select></label>}</div>
    {active!=='historical'&&<><div className="results-context"><span>{week.label} · 5 working days</span><span>Sample operations · not live reporting</span></div><div className="results-kpis">{cards.map((card,i)=><button className="results-kpi" key={i} onClick={()=>openCard(card.id)} aria-label={`${card.title}: ${card.value} ${card.unit}. Open ${tabs.find(t=>t[0]===card.id)[1]}`}><div className="results-kpi-label"><span>{card.title}</span><span className="material-symbols-outlined" aria-hidden="true">{card.icon}</span></div><div className="results-kpi-value">{card.value}<small>{card.unit}</small></div><div className="results-kpi-bottom"><span>{card.note}</span><span className="material-symbols-outlined" aria-hidden="true">arrow_forward</span></div></button>)}</div></>}
    <div id="results-panel" ref={panel} role="tabpanel" aria-labelledby={'results-tab-'+active} tabIndex={0} className="results-content">
      {active==='overview'&&<><div className="results-chart-grid"><Chart title="Weekly application flow" subtitle="Daily received and completed reviews" labels={days} unit="applications" series={[{name:'Received',values:week.received,color:'#b6c9df'},{name:'Completed',values:week.completed,color:'#00785b'}]}/><Chart title="Average wait trend" subtitle="Completed-review weighted mean by week" labels={selectedWeeks.map((_,i)=>'Week '+(i+1))} unit="days" line series={[{name:'Average wait',values:summaries.map(s=>round(s.wait)),color:'#00785b'}]}/></div><section className="results-panel"><div className="results-chart-heading"><h2>Week in numbers</h2><span>{week.label}</span></div><div className="results-summary"><Ratio label="Capacity used" value={stats.utilization} detail={`${stats.capacity-stats.hours} reviewer hours available`}/><div className="results-average"><span>Daily average</span><strong>{round(stats.daily)} <small>reviews</small></strong><p>Completed reviews ÷ 5 working days</p></div><div className="results-average"><span>Hours per review</span><strong>{round(stats.effort)} <small>hours</small></strong><p>Reviewer hours ÷ completed reviews</p></div><div className="results-average"><span>Net queue change</span><strong>+{stats.received-stats.completed} <small>applications</small></strong><p>Received minus completed; no other exits modeled</p></div></div></section></>}
      {active==='throughput'&&<><div className="results-chart-grid"><Chart title="Application flow" subtitle="Daily operations for the selected week" labels={days} unit="applications" series={[{name:'Received',values:week.received,color:'#b6c9df'},{name:'Completed',values:week.completed,color:'#00785b'}]}/><Chart title="Weekly completed reviews" subtitle="Sample weeks up to the selected period" labels={selectedWeeks.map((_,i)=>'Week '+(i+1))} unit="applications" series={[{name:'Completed',values:summaries.map(s=>s.completed),color:'#00785b'}]}/></div><section className="results-panel"><Ratio label="Completed / received" value={stats.completion} detail={`${stats.completed} reviews completed against ${stats.received} new applications. This compares volumes, not the completion rate of a matched cohort.`}/></section></>}
      {active==='waiting'&&<><div className="results-chart-grid"><Chart title="Daily average waiting time" subtitle="Mean waiting time of reviews completed that day" labels={days} unit="days" line series={[{name:'Average wait',values:week.wait,color:'#00785b'}]}/><Chart title="Weekly average waiting time" subtitle="Weighted by the number of completed reviews" labels={selectedWeeks.map((_,i)=>'Week '+(i+1))} unit="days" line series={[{name:'Average wait',values:summaries.map(s=>round(s.wait)),color:'#00785b'}]}/></div><section className="results-panel"><h2>Average for this week: {round(stats.wait)} days</h2><p>Daily mean wait × completed reviews, summed across the week and divided by {stats.completed} completed reviews. Historical median and P90 comparisons remain available in Historical analysis.</p></section></>}
      {active==='capacity'&&<><div className="results-chart-grid"><Chart title="Daily review capacity" subtitle="Used hours against 64 available reviewer hours per day" labels={days} unit="hours" series={[{name:'Available',values:days.map(()=>64),color:'#b6c9df'},{name:'Used',values:week.hours,color:'#00785b'}]}/><section className="results-panel"><h2>Capacity & efficiency</h2><Ratio label="Weekly utilization" value={stats.utilization} detail={`${stats.hours} of ${stats.capacity} hours used`}/><div className="results-detail-row"><span>Available hours remaining</span><strong>{stats.capacity-stats.hours} h</strong></div><div className="results-detail-row"><span>Average hours per working day</span><strong>{round(stats.hours/5)} h</strong></div><div className="results-detail-row"><span>Average hours per completed review</span><strong>{round(stats.effort)} h</strong></div></section></div></>}
      {active==='historical'&&<><div className="results-archive-note"><span className="material-symbols-outlined" aria-hidden="true">history</span>2021 simulation reference · Independent of the weekly demo data. Policy comparisons, carbon ranges, P90, stale-record sensitivity and model assumptions are retained here.</div><nav className="historical-section-picker" aria-label="Historical analysis sections">{historicalSections.map(([id,label])=><a key={id} href={'#/results?section=historical&detail='+id} aria-current={resultsLocation.detail===id?'page':undefined}>{label}</a>)}</nav><Simulation section={resultsLocation.detail}/></>}
    </div>
  </div>;
}
