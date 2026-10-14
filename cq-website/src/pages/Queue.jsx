import React, { useState } from 'react';
import { useApp, QueueRows } from '../state.jsx';
import { queueSortLabels } from '../queue-sort.js';
function SortHeading({ sortKey, children }) {
  const ctx = useApp();
  const active = ctx.sort?.key === sortKey;
  return <th scope="col" className="queue-column-heading" aria-sort={active ? (ctx.sort.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
    <button type="button" className="sort-heading" onClick={() => ctx.toggleSort(sortKey)}>{children || queueSortLabels[sortKey]}<span aria-hidden="true">{active ? (ctx.sort.direction === 'asc' ? '↑' : '↓') : '↕'}</span></button>
    {sortKey === 'compliant' && <small className="block normal-case font-normal">Demo status</small>}
  </th>;
}

export default function Queue() { const ctx = useApp(); const [policyOpen,setPolicyOpen]=useState(false), [whyOpen,setWhyOpen]=useState(false); return (<div className="flex flex-col w-full text-on-surface antialiased pb-space-xl">
  <div className="px-gutter-desktop pt-space-lg pb-space-md flex flex-col gap-space-md border-b border-outline-variant/30 bg-surface-container-lowest">
    <div className="flex flex-wrap items-center justify-between gap-y-space-md">
      <div>
        <div className="flex items-center gap-space-sm mb-0.5">
          <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">Review Queue</h1>
          <span className="inline-flex items-center gap-1.5 px-space-sm py-0.5 rounded-full bg-surface-container-high text-on-surface-variant font-label-xs text-label-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
            42 applications waiting
          </span>
        </div>
        <p className="font-body-md text-body-md text-on-surface-variant">
          Prioritize low-carbon project applications using available review capacity.
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-space-lg">
        <div className="bg-surface-container-low px-space-md py-space-sm rounded-lg flex flex-col min-w-[210px] gap-1 shadow-xs">
          <div className="flex justify-between items-center font-label-xs text-label-xs">
            <span className="text-on-surface-variant font-medium">Weekly Capacity</span>
            <span className="font-semibold text-on-surface">238 h / 320 h (74%)</span>
          </div>
          <div className="w-full bg-surface-container-highest rounded-full h-1.5 overflow-hidden">
            <div className="bg-secondary h-full rounded-full transition-all duration-500" style={{width: '74.3%'}} />
          </div>
          <span className="font-label-xs text-[10px] leading-3 text-on-surface-variant/80">82 reviewer hours unallocated</span>
        </div>
        <div className="flex items-center gap-space-sm">
          <button className="inline-flex items-center gap-space-xs px-space-md py-space-sm rounded bg-surface-container hover:bg-surface-container-high text-on-surface font-label-md text-label-md transition-colors shadow-xs" type="button">
            <span className="material-symbols-outlined text-[18px]">file_download</span>
            Export Queue Audit (CSV)
          </button>
          <button className="inline-flex items-center gap-space-xs px-space-md py-space-sm rounded bg-primary text-on-primary hover:bg-primary-container font-label-md text-label-md transition-colors shadow-xs" type="button">
            <span className="material-symbols-outlined text-[18px]">sync</span>
            View Results
          </button>
        </div>
      </div>
    </div>
  </div>
  <div className="px-gutter-desktop flex flex-col gap-space-lg pt-space-lg">
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-md">
      <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="font-label-xs text-label-xs uppercase tracking-wider text-on-surface-variant font-medium">Applications in Queue</span>
          <span className="material-symbols-outlined text-outline text-[18px]">fact_check</span>
        </div>
        <div className="my-space-xs">
          <span className="font-metric-num text-metric-num text-on-surface">42</span>
        </div>
        <div className="flex items-center gap-1 font-body-sm text-body-sm text-on-surface-variant">
          <span className="inline-block w-2 h-2 rounded-full bg-secondary-fixed-dim" />
          <span>18 fast-track eligible (&lt;10h effort)</span>
        </div>
      </div>
      <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="font-label-xs text-label-xs uppercase tracking-wider text-on-surface-variant font-medium">Median Wait</span>
          <span className="material-symbols-outlined text-outline text-[18px]">hourglass_empty</span>
        </div>
        <div className="my-space-xs flex items-baseline gap-2">
          <span className="font-metric-num text-metric-num text-on-surface">51</span>
          <span className="font-label-md text-label-md text-on-surface-variant">days</span>
        </div>
        <div className="inline-flex items-center gap-1 font-label-xs text-label-xs text-secondary font-medium">
          <span className="material-symbols-outlined text-[14px]">arrow_downward</span>
          <span>23 days vs FIFO baseline (74d)</span>
        </div>
      </div>
      <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="font-label-xs text-label-xs uppercase tracking-wider text-on-surface-variant font-medium">P90 Wait</span>
          <span className="material-symbols-outlined text-outline text-[18px]">speed</span>
        </div>
        <div className="my-space-xs flex items-baseline gap-2">
          <span className="font-metric-num text-metric-num text-on-surface">142</span>
          <span className="font-label-md text-label-md text-on-surface-variant">days</span>
        </div>
        <div className="flex items-center gap-1 font-label-xs text-label-xs text-on-surface-variant"><span className="px-2 py-0.5 rounded bg-surface-container font-medium text-on-surface font-label-xs text-label-xs">Maximum-wait policy: 180 days</span><span className="text-secondary font-medium font-label-xs text-label-xs">Compliant</span></div>
      </div>
      <div className="bg-surface-container-lowest p-space-md rounded-lg shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="font-label-xs text-label-xs uppercase tracking-wider text-on-surface-variant font-medium">Modeled Carbon Impact</span>
          <span className="material-symbols-outlined text-outline text-[18px]">eco</span>
        </div>
        <div className="my-space-xs flex items-baseline gap-1.5">
          <span className="font-metric-num text-metric-num text-on-surface">1.2–3.8</span>
          <span className="font-label-md text-label-md text-on-surface-variant">ktCO₂e</span>
        </div>
        <div className="font-label-xs text-[10px] leading-tight text-on-surface-variant">
          <span className="font-medium text-on-surface">Avoided-delay potential</span> · displacement estimates
        </div>
      </div>
    </div>
    <div className="queue-toolbar">
      <div className="queue-toolbar-fields">
        <div className="queue-toolbar-search relative">
          <span className="material-symbols-outlined absolute left-3 top-2 text-outline text-[18px]">search</span>
          <input aria-label="Search projects" value={ctx.search} onChange={e => ctx.setSearch(e.target.value)} className="w-full pl-9 pr-3 py-1.5 bg-surface-container-low focus:bg-surface-container-lowest rounded text-on-surface placeholder:text-outline font-body-sm text-body-sm outline-none transition-all focus:ring-1 focus:ring-on-surface/40" placeholder="Search projects by name, ID, or developer..." type="text" />
        </div>
        <div className="queue-filter-pair"><div className="relative inline-block">
          <select value={ctx.filters[0]} aria-label="Technology" onChange={e => ctx.setFilter(0, Number(e.target.value))} className="appearance-none bg-surface-container-low text-on-surface px-space-md py-1.5 pr-8 rounded font-label-md text-label-md outline-none cursor-pointer hover:bg-surface-container transition-colors">
            <option value={0}>All Technologies</option>
            <option value={3}>Battery Storage (BESS)</option>
            <option value={4}>EV Fleet Infrastructure</option>
            <option value={6}>Hydro</option>
            <option value={5}>Industrial Heat Pump</option>
            <option value={1}>Solar Photovoltaic</option>
            <option value={2}>Wind Energy</option>
          </select>
          <span className="material-symbols-outlined absolute right-2 top-2 pointer-events-none text-outline text-[16px]">expand_more</span>
        </div>
        <button className="queue-control" aria-label="Sort technologies alphabetically" aria-pressed={ctx.sort?.key==='tech'} onClick={()=>ctx.toggleSort('tech')}>A–Z <span className="material-symbols-outlined">{ctx.sort?.key==='tech'&&ctx.sort.direction==='desc'?'arrow_downward':'arrow_upward'}</span></button></div>
        <div className="queue-filter-pair"><div className="relative inline-block">
          <select value={ctx.filters[1]} aria-label="Capacity" onChange={e => ctx.setFilter(1, Number(e.target.value))} className="appearance-none bg-surface-container-low text-on-surface px-space-md py-1.5 pr-8 rounded font-label-md text-label-md outline-none cursor-pointer hover:bg-surface-container transition-colors">
            <option value={0}>Capacity: All Sizes</option>
            <option value={1}>&lt; 5 MW (Small)</option>
            <option value={2}>5 – 25 MW (Medium)</option>
            <option value={3}>&gt; 25 MW (Utility Scale)</option>
          </select>
          <span className="material-symbols-outlined absolute right-2 top-2 pointer-events-none text-outline text-[16px]">expand_more</span>
        </div>
        <button className="queue-control" aria-label="Sort by capacity" aria-pressed={ctx.sort?.key==='capacity'} onClick={()=>ctx.toggleSort('capacity')}>Capacity <span className="material-symbols-outlined">{ctx.sort?.key==='capacity'&&ctx.sort.direction==='asc'?'arrow_upward':'arrow_downward'}</span></button></div>
        <div className="relative inline-block">
          <select value={ctx.filters[2]} aria-label="Waiting time" onChange={e => ctx.setFilter(2, Number(e.target.value))} className="appearance-none bg-surface-container-low text-on-surface px-space-md py-1.5 pr-8 rounded font-label-md text-label-md outline-none cursor-pointer hover:bg-surface-container transition-colors">
            <option value={0}>Wait: All Durations</option>
            <option value={1}>&gt; 90 Days (Late Stage)</option>
            <option value={2}>&gt; 120 Days (Priority Protection)</option>
          </select>
          <span className="material-symbols-outlined absolute right-2 top-2 pointer-events-none text-outline text-[16px]">expand_more</span>
        </div>
      </div>
      <div className="queue-toolbar-actions"><button className="queue-control" aria-expanded={policyOpen} aria-controls="policy-options" onClick={()=>setPolicyOpen(!policyOpen)}><span className="material-symbols-outlined">tune</span>Policy Optimization<span className="material-symbols-outlined">{policyOpen?'expand_less':'expand_more'}</span></button>
      <div className="flex items-center gap-1 bg-surface-container-low p-1 rounded">
        <button type="button" aria-pressed={ctx.view==='table'} className={"px-space-sm py-1 rounded font-label-xs text-label-xs flex items-center gap-1 "+(ctx.view==='table'?'bg-white shadow-xs text-on-surface font-semibold':'text-on-surface-variant hover:text-on-surface font-medium')}>
          <span className="material-symbols-outlined text-[16px]">table_rows</span>
          Table View
        </button>
        <button type="button" aria-pressed={ctx.view==='gantt'} className={"px-space-sm py-1 rounded font-label-xs text-label-xs flex items-center gap-1 "+(ctx.view==='gantt'?'bg-white shadow-xs text-on-surface font-semibold':'text-on-surface-variant hover:text-on-surface font-medium')}>
          <span className="material-symbols-outlined text-[16px]">timeline</span>
          Queue Gantt
        </button>
      </div>
      </div>
    </div>
    {policyOpen && (<div id="policy-options" className="bg-surface-container-lowest rounded-xl shadow-sm p-space-lg flex flex-col gap-space-md">
      <div className="flex flex-wrap items-center justify-between gap-space-sm pb-space-xs"><div className="flex flex-col"><div className="font-title-sm text-[17px] font-semibold text-on-surface">Policy Optimization Engine</div><p className="font-body-md text-body-md text-on-surface-variant">Queue ordering adjusts dynamically according to the selected review policy.</p></div></div>
      <div className="bg-surface-container-low p-1 rounded-lg flex flex-wrap gap-1"><button  className={"policy-tab flex-1 min-w-[120px] px-space-md py-space-sm rounded text-label-md " + (ctx.policy === 0 ? "bg-white shadow-sm font-semibold" : "text-on-surface-variant")} type="button">1. FIFO</button><button  className={"policy-tab flex-1 min-w-[120px] px-space-md py-space-sm rounded text-label-md " + (ctx.policy === 1 ? "bg-white shadow-sm font-semibold" : "text-on-surface-variant")} type="button">2. Carbon Only</button><button  className={"policy-tab flex-1 min-w-[120px] px-space-md py-space-sm rounded text-label-md " + (ctx.policy === 2 ? "bg-white shadow-sm font-semibold" : "text-on-surface-variant")} type="button">3. + Withdrawal Risk</button><button  className={"policy-tab flex-1 min-w-[120px] px-space-md py-space-sm rounded text-label-md " + (ctx.policy === 3 ? "bg-white shadow-sm font-semibold" : "text-on-surface-variant")} type="button">4. + Effort</button><button  className={"policy-tab flex-1 min-w-[120px] px-space-md py-space-sm rounded text-label-md " + (ctx.policy === 4 ? "bg-white shadow-sm font-semibold" : "text-on-surface-variant")} type="button"><span>5. CarbonQueue</span><span className="px-1.5 py-0.5 rounded-full bg-secondary-container text-on-secondary-container font-label-xs text-[10px] uppercase font-bold tracking-wider">Recommended</span></button></div>
      <div className="bg-surface-container-low rounded-lg p-space-md flex items-start gap-space-md shadow-xs"><span className="material-symbols-outlined text-secondary text-[22px] mt-0.5 shrink-0">insights</span><div className="flex flex-col gap-0.5"><div className="font-title-sm text-[14px] font-semibold text-on-surface">Simulation preview</div><p className="font-body-md text-body-md text-on-surface-variant">Compared with FIFO, CarbonQueue changes review order based on modeled carbon impact, withdrawal risk, review effort, and fairness constraints.</p></div></div>
    </div>)}
    <div className="queue-explanation-bar"><span>{ctx.sort ? queueSortLabels[ctx.sort.key]+' · '+(ctx.sort.direction==='desc'?'Descending':'Ascending') : 'Ordered by selected policy'}</span><div>{ctx.sort&&<button className="queue-control" onClick={()=>ctx.setSort(null)}>Reset order</button>}<button className="queue-control" aria-expanded={whyOpen} aria-controls="queue-explanation" onClick={()=>setWhyOpen(!whyOpen)}><span className="material-symbols-outlined">psychology_alt</span>Why this queue?<span className="material-symbols-outlined">{whyOpen?'chevron_right':'chevron_left'}</span></button></div></div>
    <div className={'queue-layout '+(whyOpen?'with-explanation':'')}>
      <div className="min-w-0 bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden flex flex-col">
        <div className="overflow-x-auto">
          <table className="queue-table w-full text-left border-collapse">
            <colgroup>{[4,18,12,9,12,9,6,7,13,10].map((width,index)=><col key={index} style={{width:width+'%'}} />)}</colgroup>
            <thead>
              <tr className="bg-surface-container-low font-label-xs text-label-xs uppercase text-on-surface-variant tracking-wider">
                <th scope="col" className="py-space-sm px-space-md font-semibold text-center w-14">#</th>
                <SortHeading sortKey="name" />
                <SortHeading sortKey="tech" />
                <SortHeading sortKey="capacity" />
                <SortHeading sortKey="carbon" />
                <SortHeading sortKey="risk" />
                <SortHeading sortKey="effort" />
                <SortHeading sortKey="wait" />
                <SortHeading sortKey="reason" />
                <SortHeading sortKey="compliant"><span className="inline-flex items-center gap-1"><span className="material-symbols-outlined" aria-hidden="true">gavel</span>Compliance</span></SortHeading>
              </tr>
            </thead>
            <QueueRows />
          </table>
        </div>
        <div className="px-space-md py-space-sm bg-surface-container-low flex flex-wrap items-center justify-between gap-space-md">
          <div className="font-label-xs text-label-xs text-on-surface-variant">
            Showing <span className="font-semibold text-on-surface">{ctx.visible.length}</span> of <span className="font-semibold text-on-surface">{ctx.projects.length}</span> sample applications · Reference cohort: 42 applications
          </div>
          <div className="flex items-center gap-1">
            <button className="px-2 py-1 rounded bg-surface-container-lowest text-on-surface font-label-xs text-label-xs shadow-xs hover:bg-surface-container transition-colors disabled:opacity-40" disabled>
              Prev
            </button>
            <span className="px-2 py-1 font-label-xs text-label-xs text-on-surface font-semibold">1 / 1</span>
            <button className="px-2 py-1 rounded bg-surface-container-lowest text-on-surface font-label-xs text-label-xs shadow-xs hover:bg-surface-container transition-colors" disabled>Next</button>
          </div>
        </div>
      </div>
      {whyOpen && <aside id="queue-explanation" className="flex flex-col gap-space-md">
        <div className="bg-surface-container-lowest rounded-xl shadow-sm p-space-md flex flex-col gap-space-md"><div className="flex items-center gap-space-xs pb-space-xs border-b border-surface-container"><span className="material-symbols-outlined text-secondary text-[20px]">psychology_alt</span><div className="flex flex-col"><h2 className="font-title-sm text-[15px] font-semibold text-on-surface">Why this queue?</h2><span className="font-label-xs text-[11px] text-on-surface-variant">Decision factor breakdown</span></div></div><div className="flex flex-col gap-2 py-1"><div className="flex items-center gap-2 text-body-sm text-on-surface"><span className="w-2 h-2 rounded-full bg-secondary shrink-0" /><span className="font-medium">Carbon impact</span></div><div className="flex items-center gap-2 text-body-sm text-on-surface"><span className="w-2 h-2 rounded-full bg-primary shrink-0" /><span className="font-medium">Review effort</span></div><div className="flex items-center gap-2 text-body-sm text-on-surface"><span className="w-2 h-2 rounded-full bg-outline shrink-0" /><span className="font-medium">Withdrawal risk</span></div><div className="flex items-center gap-2 text-body-sm text-on-surface"><span className="w-2 h-2 rounded-full bg-tertiary-fixed-dim shrink-0" /><span className="font-medium">Waiting-time protection</span></div><div className="flex items-center gap-2 text-body-sm text-on-surface"><span className="w-2 h-2 rounded-full bg-surface-tint shrink-0" /><span className="font-medium">Fairness protection</span></div></div><div className="bg-surface-container-low p-space-sm rounded text-[13px] leading-relaxed text-on-surface-variant shadow-xs">CarbonQueue combines modeled impact and review efficiency while enforcing waiting-time and fairness protections.</div><div className="pt-space-xs border-t border-surface-container"><a className="inline-flex items-center gap-1 font-label-xs text-label-xs text-on-surface font-semibold hover:text-secondary transition-colors" href="#">View methodology documentation →</a></div></div>
        <div className="bg-surface-container-lowest rounded-xl shadow-sm p-space-md flex flex-col gap-space-xs">
          <div className="flex items-center gap-space-xs">
            <span className="material-symbols-outlined text-secondary text-[18px]">gavel</span>
            <span className="font-label-md text-label-md font-semibold text-on-surface">Statutory Compliance</span>
          </div>
          <p className="font-body-sm text-[12px] leading-snug text-on-surface-variant">Green and red badges show sample filing-compliance statuses only. They are demonstration data, not verified legal determinations.</p>
        </div>
      </aside>}
    </div>
  </div>
</div>); }
