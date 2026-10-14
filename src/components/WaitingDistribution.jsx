import React from 'react';

const policies = [
  {name:'FIFO', values:[32,48,74,112,188], color:'#64748b', fill:'#bfcbdc'},
  {name:'CarbonQueue', values:[24,36,51,84,142], color:'#00785b', fill:'#9ed7c5'},
];
const x = days => 164 + days / 210 * 760;

export default function WaitingDistribution() {
  return <div className="waiting-distribution-chart range-chart-surface">
    <svg viewBox="0 0 1000 280" role="img" aria-labelledby="waiting-chart-title waiting-chart-description">
      <title id="waiting-chart-title">Waiting time distribution by review policy</title>
      <desc id="waiting-chart-description">FIFO: P10 32, P25 48, median 74, P75 112, P90 188 days. CarbonQueue: P10 24, P25 36, median 51, P75 84, P90 142 days. Policy threshold: 180 days.</desc>
      <rect x={x(180)} y="48" width={x(210)-x(180)} height="164" fill="#fff6f5" rx="4" />
      {[0,30,60,90,120,150,180,210].map(day=><g key={day}>
        <line x1={x(day)} x2={x(day)} y1="48" y2="212" stroke={day===180?'#c66b64':'#ccd6e5'} strokeDasharray={day===180?'5 5':undefined}/>
        <text x={x(day)} y="238" textAnchor="middle" fill="#718096" fontSize="14">{day}</text>
      </g>)}
      <text x={x(180)} y="28" textAnchor="middle" fill="#a94740" fontSize="12" fontWeight="600">180-day limit</text>
      {policies.map((policy,index)=>{
        const [p10,p25,median,p75,p90]=policy.values, y=92+index*88;
        return <g key={policy.name}>
          <text x="140" y={y+4} textAnchor="end" fill={policy.color} fontSize="15" fontWeight="600">{policy.name}</text>
          <rect x={x(p10)} y={y-11} width={x(p90)-x(p10)} height="22" rx="4" fill={index===0?'#dfe6f0':'#c1f0df'} />
          {[p10,p90].map(day=><line key={day} x1={x(day)} x2={x(day)} y1={y-9} y2={y+9} stroke={policy.color} strokeWidth="2"/>)}
          <rect x={x(p25)} y={y-17} width={x(p75)-x(p25)} height="34" rx="5" fill={policy.fill} stroke={policy.color} strokeOpacity=".35"/>
          <line x1={x(median)} x2={x(median)} y1={y-17} y2={y+17} stroke={policy.color} strokeWidth="3"/>
          <text x={x(median)} y={y+38} textAnchor="middle" fill={policy.color} fontSize="12" fontWeight="600">Median {median} d</text>
          <text x={x(p90)} y={y-21} textAnchor="middle" fill={p90>180?'#a94740':policy.color} fontSize="12" fontWeight="600">P90 · {p90} d</text>
        </g>;
      })}
      <text x="924" y="267" textAnchor="end" fill="#718096" fontSize="12">Waiting time · days</text>
    </svg>
    <div className="waiting-chart-legend"><span><i className="waiting-range"/>P10–P90 range</span><span><i className="waiting-box"/>P25–P75 range</span><span><i className="waiting-median"/>Median</span></div>
  </div>;
}
