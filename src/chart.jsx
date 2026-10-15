import React from 'react';

const round=value=>Number(value.toFixed(1));

export function Chart({title,subtitle,labels,series,line=false,unit}) {
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

