import React, { createContext, useContext } from 'react';
export const AppContext = createContext(null);
export const useApp = () => useContext(AppContext);
export const projects = [
  { name:'Riverside Solar', developer:'West Valley', id:'APP-2024-1842', tech:'Solar PV', icon:'wb_sunny', capacity:24.5, carbon:[22.4,31.7], risk:6, effort:14, wait:126, compliant:true, shift:14 },
  { name:'Northfield Wind', developer:'Ridge District', id:'APP-2024-912', tech:'Wind', icon:'air', capacity:42, carbon:[38.2,51.4], risk:4, effort:18, wait:63, compliant:true, shift:4 },
  { name:'School Roof Portfolio', developer:'Municipal Unified', id:'APP-2024-741', tech:'Solar PV', icon:'wb_sunny', capacity:3.2, carbon:[4.1,6.8], risk:8, effort:5, wait:94, compliant:true, shift:9 },
  { name:'GreenCharge Network', developer:'Metro Transit Hub', id:'APP-2024-933', tech:'EV Depot', icon:'bolt', capacity:0, carbon:[8.2,12.6], risk:11, effort:8, wait:48, compliant:false, shift:-2 },
  { name:'Industrial Heat Pump', developer:'BioFoods Plant', id:'APP-2024-955', tech:'Heat Pump', icon:'heat_pump', capacity:8.4, carbon:[18.1,24.3], risk:15, effort:12, wait:32, compliant:true, shift:1 },
  { name:'Highline Community Storage', developer:'East Substation', id:'APP-2024-890', tech:'Battery BESS', icon:'battery_charging_full', capacity:15, carbon:[12,17.5], risk:5, effort:10, wait:76, compliant:true, shift:6 },
  { name:'Pine Creek Hydro Retrofit', developer:'Cascade Basin', id:'APP-2024-699', tech:'Hydro', icon:'water_drop', capacity:6.5, carbon:[9.4,13.1], risk:18, effort:22, wait:108, compliant:false, shift:-5 },
];
export function Icon({children}) { return <span aria-hidden="true" className="material-symbols-outlined">{children}</span>; }
export function QueueRows() {
  const ctx = useApp();
  return <tbody className="divide-y divide-surface-container text-body-sm">
    {!ctx.visible.length && <tr><td colSpan="10" className="p-10 text-center">No matching projects. Try another search or filter.</td></tr>}
    {ctx.visible.map((p, index) => <tr key={p.id} className="hover:bg-surface-container-low">
      <td className="p-3 text-center"><strong className="text-headline-md">{index+1}</strong><div className={p.shift>0?'text-secondary':'text-error'}>{p.shift>0?'▲ +':'▼ '}{p.shift}</div></td>
      <td className="p-3 min-w-[200px]"><button className="text-left font-semibold text-[15px] hover:underline" onClick={() => ctx.openProject(p)}>{p.name}</button><div className="text-on-surface-variant font-mono text-xs mt-1">{p.id} · {p.developer}</div>{ctx.view==='gantt' && <div className="mt-2 h-2 rounded bg-surface-container"><div className="h-2 rounded bg-secondary" style={{width:`${p.wait/180*100}%`}} /></div>}</td>
      <td className="px-3 whitespace-nowrap"><span className="inline-flex items-center gap-1 bg-surface-container px-2 py-1 rounded"><Icon>{p.icon}</Icon>{p.tech}</span></td>
      <td className="px-3 whitespace-nowrap text-right font-mono">{p.capacity ? `${p.capacity.toFixed(1)} MW` : '—'}</td>
      <td className="px-3 whitespace-nowrap text-right"><strong className="font-mono">{p.carbon.map(n=>n.toFixed(1)).join('–')}</strong> <small>tCO₂e/day</small></td>
      <td className="px-3 text-center"><strong>{p.risk}%</strong><div className="h-1.5 bg-surface-container-highest rounded w-10 mx-auto mt-1"><div className="bg-secondary h-full rounded" style={{width:`${p.risk}%`}} /></div></td>
      <td className="px-3 whitespace-nowrap">{p.effort} h</td><td className="px-3 whitespace-nowrap">{p.wait} days</td><td className="px-3 whitespace-nowrap">{p.wait>120?'Maximum-wait protection':'Carbon impact / reviewer hour'}</td>
      <td className="px-3 whitespace-nowrap"><span className={'compliance-badge '+(p.compliant?'compliant':'non-compliant')} title="Sample filing status — demonstration data"><Icon>gavel</Icon>{p.compliant?'Compliant':'Non-compliant'}</span></td>
    </tr>)}
  </tbody>;
}
