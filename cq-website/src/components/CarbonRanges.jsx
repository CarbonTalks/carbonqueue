import React from 'react';

// Preserve the supplied chart's interval endpoints and median positions.
const rows = [
  {name:'Carbon Only', low:172, high:334, box:235, width:60, median:271, fill:'#d3e4fe'},
  {name:'+ Withdrawal', low:190, high:370, box:260, width:65, median:298, fill:'#d3e4fe'},
  {name:'+ Effort', low:199, high:406, box:310, width:70, median:352, fill:'#bec6e0'},
  {name:'CarbonQueue', low:208, high:442, box:330, width:85, median:379, fill:'#97f5cc'},
];
const x = original => 170 + (original-100)*1.9;

export default function CarbonRanges() {
  return <div className="range-chart-surface">
    <svg viewBox="0 0 1000 340" role="img" aria-labelledby="carbon-range-title carbon-range-description">
      <title id="carbon-range-title">Modeled Carbon Potential Ranges</title>
      <desc id="carbon-range-description">FIFO baseline: zero. Median modeled carbon potential: Carbon Only 1.9, plus Withdrawal 2.2, plus Effort 2.8, CarbonQueue 3.1 kt. Lines show P10 to P90; boxes show interquartile ranges.</desc>
      {[0,1,2,3,4].map(value=><g key={value}>
        <line x1={x(100+value*90)} x2={x(100+value*90)} y1="28" y2="284" stroke="#ccd6e5" strokeDasharray="4 5"/>
        <text x={x(100+value*90)} y="311" textAnchor="middle" fill="#526277" fontSize="14">{value.toFixed(1)} kt</text>
      </g>)}
      <text x="148" y="56" textAnchor="end" fill="#344256" fontSize="15">FIFO</text>
      <circle cx={x(100)} cy="51" r="5" fill="#64748b"/>
      <text x={x(100)+18} y="56" fill="#526277" fontSize="14">Baseline (0.0)</text>
      {rows.map((row,index)=>{
        const y=104+index*54, highlighted=index===3, color=highlighted?'#006c4e':'#64748b';
        return <g key={row.name}>
          <text x="148" y={y+5} textAnchor="end" fill={highlighted?color:'#344256'} fontSize="15" fontWeight={highlighted?600:400}>{row.name}</text>
          <line x1={x(row.low)} x2={x(row.high)} y1={y} y2={y} stroke={color} strokeWidth="2.5"/>
          <rect x={x(row.box)} y={y-11} width={row.width*1.9} height="22" rx="4" fill={row.fill}/>
          <circle cx={x(row.median)} cy={y} r="5" fill={highlighted?color:'#131b2e'}/>
          {highlighted&&<text x={x(row.high)+16} y={y+5} fill={color} fontSize="15" fontWeight="600">+3.1 kt</text>}
        </g>;
      })}
    </svg>
  </div>;
}
