import React, { useState } from 'react';
function MetricInfo({id,label,children}) {
  const [open,setOpen]=useState(false);
  return <span className="metric-info" onMouseEnter={()=>setOpen(true)} onMouseLeave={()=>setOpen(false)}>
    <button type="button" className="metric-info-button" aria-label={label+' information'} aria-describedby={open?'metric-help-'+id:undefined} onFocus={()=>setOpen(true)} onBlur={()=>setOpen(false)} onClick={()=>setOpen(true)} onKeyDown={e=>{if(e.key==='Escape'){setOpen(false);e.stopPropagation();}}}>i</button>
    {open&&<span role="tooltip" id={'metric-help-'+id} className="metric-tooltip">{children}</span>}
  </span>;
}
export default function Project() { return (<div className="flex flex-col w-full">
  <div className="px-gutter-desktop py-space-xl max-w-[1520px] mx-auto w-full space-y-space-xl">
    <div className="flex flex-col gap-space-md">
      <div className="flex flex-wrap items-center justify-between gap-space-md">
        <div className="flex items-center gap-space-sm font-label-md text-label-md">
          <a className="inline-flex items-center gap-1 px-space-sm py-1 rounded bg-surface-container-low text-on-surface hover:bg-surface-container text-label-md transition-colors" href="#">
            <span className="material-symbols-outlined text-[16px]">arrow_back</span>
            Back to Queue
          </a>
          <span className="text-on-surface-variant/40">/</span>
          <span className="text-on-surface-variant">Queue</span>
          <span className="text-on-surface-variant/40">/</span>
          <span className="font-semibold text-on-surface">Riverside Solar</span>
        </div>
        <div className="flex items-center gap-space-sm">
          <button className="inline-flex items-center gap-space-xs px-space-md py-1.5 rounded bg-surface-container-lowest text-on-surface shadow-sm hover:bg-surface-container-low transition-colors font-label-md text-label-md" type="button">
            <span className="material-symbols-outlined text-[16px] text-on-surface-variant">description</span>
            View source documents
          </button>
          <button className="inline-flex items-center gap-space-xs px-space-md py-1.5 rounded bg-surface-container-lowest text-on-surface shadow-sm hover:bg-surface-container-low transition-colors font-label-md text-label-md" type="button">
            <span className="material-symbols-outlined text-[16px] text-on-surface-variant">history</span>
            Audit log
          </button>
        </div>
      </div>
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-lg bg-surface-container-lowest p-space-xl rounded-xl shadow-sm">
        <div className="space-y-space-sm">
          <div className="flex flex-wrap items-center gap-space-sm">
            <h1 className="font-display-lg text-display-lg text-on-surface tracking-tight">Riverside Solar</h1>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-secondary-container/30 text-on-secondary-container font-label-xs text-label-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-secondary" />
              Ready for review
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-space-xs font-label-md text-label-md">
            <span className="px-2.5 py-0.5 rounded bg-surface-container text-on-surface-variant font-medium">Solar PV</span>
            <span className="text-on-surface-variant/30">•</span>
            <span className="px-2.5 py-0.5 rounded bg-surface-container text-on-surface-variant font-medium">24.5 MW</span>
            <span className="text-on-surface-variant/30">•</span>
            <span className="px-2.5 py-0.5 rounded bg-surface-container text-on-surface-variant font-medium">West Valley Substation</span>
            <span className="text-on-surface-variant/30">•</span>
            <span className="px-2 py-0.5 rounded bg-surface-container-high text-on-surface font-mono text-label-xs tracking-wider">APP-2024-1842</span>
          </div>
        </div>
        <div className="flex items-center gap-space-lg px-space-xl py-space-md bg-surface-container-low rounded-xl">
          <div className="flex flex-col text-right">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-wider">Current Priority</span>
            <span className="font-display-lg text-display-lg font-bold text-on-surface">Queue Position #1</span>
            <span className="font-label-md text-label-md text-on-surface-variant">of 42 applications pending</span>
          </div>
          <div className="w-12 h-12 rounded-lg bg-primary text-on-primary flex items-center justify-center shadow">
            <span className="material-symbols-outlined text-[28px]">vertical_align_top</span>
          </div>
        </div>
      </div>
    </div>
    <div className="bg-surface-container-lowest p-space-xl rounded-xl shadow-sm space-y-space-md">
          <div className="flex items-center justify-between">
            <h2 className="font-headline-md text-headline-md text-on-surface">Data Quality &amp; Integrity Flags</h2>
            <span className="px-2 py-0.5 rounded bg-secondary-container/40 text-on-secondary-container font-label-xs text-label-xs font-semibold">
              All checks passing
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-sm pt-1">
            <div className="flex items-center justify-between p-space-sm rounded bg-surface-container-low">
              <span className="font-body-sm text-body-sm text-on-surface">Missing information</span>
              <div className="flex items-center gap-1 text-secondary font-label-xs text-label-xs font-semibold">
                <span className="material-symbols-outlined text-[16px]">check_circle</span>
                None
              </div>
            </div>
            <div className="flex items-center justify-between p-space-sm rounded bg-surface-container-low">
              <span className="font-body-sm text-body-sm text-on-surface">Extraction conflicts</span>
              <div className="flex items-center gap-1 text-secondary font-label-xs text-label-xs font-semibold">
                <span className="material-symbols-outlined text-[16px]">check_circle</span>
                None
              </div>
            </div>
            <div className="flex items-center justify-between p-space-sm rounded bg-surface-container-low">
              <span className="font-body-sm text-body-sm text-on-surface">Stale or uncertain record</span>
              <div className="flex items-center gap-1 text-secondary font-label-xs text-label-xs font-semibold">
                <span className="material-symbols-outlined text-[16px]">check_circle</span>
                No
              </div>
            </div>
            <div className="flex items-center justify-between p-space-sm rounded bg-surface-container-low">
              <span className="font-body-sm text-body-sm text-on-surface">Ready for review</span>
              <div className="flex items-center gap-1 text-secondary font-label-xs text-label-xs font-semibold">
                <span className="material-symbols-outlined text-[16px]">check_circle</span>
                Yes
              </div>
            </div>
          </div>
        </div>
    <div className="relative overflow-hidden bg-surface-container-lowest p-space-xl rounded-xl shadow-sm">
      <div className="absolute top-0 left-0 bottom-0 w-1.5 bg-secondary" />
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-space-lg pl-space-sm">
        <div className="space-y-space-sm max-w-4xl">
          <div className="flex flex-wrap items-center gap-space-sm">
            <span className="font-headline-md text-headline-md text-on-surface">Why is this project #1?</span>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-secondary-fixed text-on-secondary-fixed-variant font-label-xs text-label-xs font-semibold uppercase tracking-wider">
              <span className="material-symbols-outlined text-[14px]">format_image_left</span>
              Maximum-wait protection
            </span>
          </div>
          <p className="font-title-sm text-title-sm text-on-surface leading-relaxed">
            This application is approaching the configured maximum waiting period. CarbonQueue protects it from further delay regardless of its optimization score.
          </p>
          <p className="font-body-md text-body-md text-on-surface-variant">
            It also demonstrates high modeled carbon displacement relative to its estimated reviewer effort. Under statutory review protocols, queue-time bounds strictly prevent starvation while accelerating decarbonization throughput.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start bg-surface-container-low px-space-md py-space-sm rounded text-on-surface-variant font-label-xs text-label-xs">
          <span className="material-symbols-outlined text-[16px] text-secondary">verified</span>
          <span>Deterministic Audit Rule #CQ-180D</span>
        </div>
      </div>
    </div>
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-md">
      {[
        {id:'carbon',label:'Modeled Carbon Impact',value:'22.4–31.7',unit:'tCO₂e / day',description:'Estimated displacement range. Modeled bounded carbon impact potential, not guaranteed emissions savings.'},
        {id:'withdrawal',label:'Withdrawal Within 12 Mo',value:'6%',unit:'Low risk',description:'Model probability estimate of developer withdrawal within 12 months. Low risk: P < 0.10.',progress:6},
        {id:'effort',label:'Estimated Review Effort',value:'14 h',description:'Expected expert analyst time, based on the standard utility study model.'},
        {id:'waiting',label:'Waiting Time',value:'126 days',description:'70% of the 180-day maximum waiting target. 54 days remain before the policy threshold.',progress:70}
      ].map(metric=><div key={metric.id} className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm space-y-2">
        <div className="flex items-start justify-between gap-2"><span className="font-label-xs text-label-xs uppercase tracking-wider text-on-surface-variant">{metric.label}</span><MetricInfo id={metric.id} label={metric.label}>{metric.description}</MetricInfo></div>
        <div className="font-metric-num text-metric-num text-on-surface">{metric.value}</div>
        {metric.unit&&<div className="font-label-md text-label-md text-secondary font-medium">{metric.unit}</div>}
        {metric.progress&&<div className="w-full bg-surface-container h-1.5 rounded-full overflow-hidden"><div className={metric.id==='waiting'?'bg-tertiary-fixed-dim h-full rounded-full':'bg-secondary h-full rounded-full'} style={{width:metric.progress+'%'}} /></div>}
      </div>)}
    </div>
    <div className="bg-surface-container-lowest p-space-xl rounded-xl shadow-sm space-y-space-lg">
          <div className="flex items-center justify-between">
            <h2 className="font-headline-md text-headline-md text-on-surface">Carbon Impact Details</h2>
            <span className="px-2.5 py-0.5 rounded bg-secondary-container/30 text-on-secondary-container font-label-xs text-label-xs font-semibold">
              Modeled Range
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-space-md">
            <div className="p-space-md bg-surface-container-low rounded-lg space-y-1">
              <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Technology &amp; Capacity</span>
              <div className="font-title-sm text-title-sm text-on-surface">Solar PV · 24.5 MW</div>
              <span className="font-label-xs text-label-xs text-on-surface-variant">Single-axis horizontal tracking</span>
            </div>
            <div className="p-space-md bg-surface-container-low rounded-lg space-y-1">
              <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Daily Displacement</span>
              <div className="font-title-sm text-title-sm text-secondary font-semibold">22.4–31.7 tCO₂e/day</div>
              <span className="font-label-xs text-label-xs text-on-surface-variant">Substation nodal marginal factor</span>
            </div>
            <div className="p-space-md bg-surface-container-low rounded-lg space-y-1">
              <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Annualized Estimate</span>
              <div className="font-title-sm text-title-sm text-on-surface">8.2–11.6 ktCO₂e/year</div>
              <span className="font-label-xs text-label-xs text-on-surface-variant">Based on 8,760h irradiance profile</span>
            </div>
            <div className="p-space-md bg-surface-container-low rounded-lg space-y-1">
              <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Baseline Grid Scenario</span>
              <div className="font-title-sm text-title-sm text-on-surface">Central Emission Factor</div>
              <span className="font-label-xs text-label-xs text-on-surface-variant">NREL Cambium 2024 Mid-Case</span>
            </div>
          </div>
          <div className="p-space-md bg-surface-container-low rounded-lg flex items-start gap-space-sm text-on-surface-variant">
            <span className="material-symbols-outlined text-[18px] text-on-surface-variant mt-0.5">info</span>
            <div className="flex-1 font-body-sm text-body-sm">
              <span>Carbon estimates represent modeled displacement potential and are not guaranteed emissions savings. Actual avoided carbon is governed by dispatch conditions.</span>
              <a className="inline-flex items-center gap-0.5 font-semibold text-on-surface hover:underline ml-1" href="#">
                View assumptions →
              </a>
            </div>
          </div>
        </div>
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-xl items-start">
      <div className="lg:col-span-6 space-y-space-xl">
        <div className="bg-surface-container-lowest p-space-xl rounded-xl shadow-sm space-y-space-lg">
          <div className="flex items-center justify-between">
            <h2 className="font-headline-md text-headline-md text-on-surface">Queue Position &amp; Policy Shift</h2>
            <span className="font-label-xs text-label-xs uppercase text-on-surface-variant">Algorithmic Shift</span>
          </div>
          <div className="bg-surface-container-low p-space-md rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-space-md">
              <div className="flex flex-col">
                <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Prior FIFO</span>
                <span className="font-metric-num text-metric-num text-on-surface-variant line-through">#7</span>
              </div>
              <span className="material-symbols-outlined text-secondary text-[24px]">trending_flat</span>
              <div className="flex flex-col">
                <span className="font-label-xs text-label-xs text-secondary uppercase font-semibold">CarbonQueue</span>
                <span className="font-metric-num text-metric-num text-secondary">#1</span>
              </div>
            </div>
            <div className="text-right">
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-secondary-container/40 text-on-secondary-container font-label-xs text-label-xs font-semibold">
                +6 positions gained
              </span>
            </div>
          </div>
          <div className="space-y-space-sm font-body-md text-body-md">
            <div className="flex justify-between py-1.5 border-b border-surface-container">
              <span className="text-on-surface-variant">Current Position</span>
              <span className="font-semibold text-on-surface">#1</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-surface-container">
              <span className="text-on-surface-variant">Baseline FIFO Position</span>
              <span className="text-on-surface">#7</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-surface-container">
              <span className="text-on-surface-variant">Active Prioritization Policy</span>
              <span className="font-semibold text-on-surface">CarbonQueue Hybrid v2.4</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-surface-container">
              <span className="text-on-surface-variant">Elapsed Waiting Time</span>
              <span className="text-on-surface">126 days (Submitted Oct 14, 2024)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-surface-container">
              <span className="text-on-surface-variant">Primary Escalation Trigger</span>
              <span className="font-semibold text-on-tertiary-container">Maximum-wait protection (&gt;120d)</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-on-surface-variant">Secondary Optimization Factor</span>
              <span className="text-on-surface">High carbon impact / reviewer hour</span>
            </div>
          </div>
        </div>
        <div className="bg-surface-container-lowest p-space-xl rounded-xl shadow-sm space-y-space-md">
          <div className="flex items-center justify-between">
            <h2 className="font-headline-md text-headline-md text-on-surface">Priority Factors</h2>
            <span className="font-label-xs text-label-xs text-on-surface-variant">Human-readable Criteria</span>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Evaluated deterministically according to jurisdictional dispatch weights without arbitrary percentage scores.
          </p>
          <div className="space-y-2 pt-2">
            <div className="flex items-center justify-between p-space-md rounded-lg bg-surface-container-low">
              <div className="flex items-center gap-space-sm">
                <span className="material-symbols-outlined text-secondary text-[20px]">bolt</span>
                <span className="font-label-md text-label-md font-semibold text-on-surface">Carbon impact potential</span>
              </div>
              <span className="px-2.5 py-0.5 rounded bg-secondary-container/50 text-on-secondary-container font-label-xs text-label-xs font-semibold">High</span>
            </div>
            <div className="flex items-center justify-between p-space-md rounded-lg bg-surface-container-low">
              <div className="flex items-center gap-space-sm">
                <span className="material-symbols-outlined text-on-surface-variant text-[20px]">engineering</span>
                <span className="font-label-md text-label-md font-semibold text-on-surface">Estimated review effort</span>
              </div>
              <span className="px-2.5 py-0.5 rounded bg-surface-container-highest text-on-surface-variant font-label-xs text-label-xs font-semibold">Moderate</span>
            </div>
            <div className="flex items-center justify-between p-space-md rounded-lg bg-surface-container-low">
              <div className="flex items-center gap-space-sm">
                <span className="material-symbols-outlined text-secondary text-[20px]">verified</span>
                <span className="font-label-md text-label-md font-semibold text-on-surface">Project withdrawal risk</span>
              </div>
              <span className="px-2.5 py-0.5 rounded bg-secondary-fixed text-on-secondary-fixed-variant font-label-xs text-label-xs font-semibold">Low</span>
            </div>
            <div className="flex items-center justify-between p-space-md rounded-lg bg-surface-container-low">
              <div className="flex items-center gap-space-sm">
                <span className="material-symbols-outlined text-tertiary-fixed-dim text-[20px]">hourglass_top</span>
                <span className="font-label-md text-label-md font-semibold text-on-surface">Waiting-time protection</span>
              </div>
              <span className="px-2.5 py-0.5 rounded bg-tertiary-fixed text-on-tertiary-fixed-variant font-label-xs text-label-xs font-semibold">Active</span>
            </div>
            <div className="flex items-center justify-between p-space-md rounded-lg bg-surface-container-low">
              <div className="flex items-center gap-space-sm">
                <span className="material-symbols-outlined text-outline text-[20px]">balance</span>
                <span className="font-label-md text-label-md font-semibold text-on-surface">Fairness protection</span>
              </div>
              <span className="px-2.5 py-0.5 rounded bg-surface-container text-outline font-label-xs text-label-xs font-semibold">Not triggered</span>
            </div>
          </div>
        </div>
        
      </div>
      <div className="lg:col-span-6 space-y-space-xl">
        
        <div className="bg-surface-container-lowest p-space-xl rounded-xl shadow-sm space-y-space-md">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="font-headline-md text-headline-md text-on-surface">Source Evidence</h2>
              <span className="font-label-xs text-label-xs text-on-surface-variant">AI Transparency &amp; Lineage</span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
              Values extracted from application documents and used by the decision-support system.
            </p>
          </div>
          <div className="space-y-space-sm pt-2">
            <div className="p-space-md rounded-lg bg-surface-container-low space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-space-sm">
                  <span className="font-label-xs text-label-xs uppercase text-on-surface-variant">Field:</span>
                  <span className="font-label-md text-label-md font-semibold text-on-surface">Technology</span>
                  <span className="px-2 py-0.5 rounded bg-surface-container text-on-surface font-mono text-label-xs font-semibold">Solar PV</span>
                </div>
                <div className="flex items-center gap-space-sm">
                  <button className="inline-flex items-center gap-1 px-2 py-1 rounded bg-surface-container-lowest text-on-surface font-label-xs text-label-xs shadow-sm hover:bg-surface-container transition-colors" type="button">
                    <span className="material-symbols-outlined text-[12px]">open_in_new</span>
                    View source
                  </button>
                </div>
              </div>
              <div className="font-label-xs text-label-xs text-on-surface-variant">
                Document: <span className="font-mono text-on-surface">Technical Report.pdf · p.12</span>
              </div>
              <div className="font-body-sm text-body-sm italic text-on-surface-variant/90 pl-space-sm border-l-2 border-outline-variant/40">
                “Ground-mounted photovoltaic generation facility with single-axis tracking and bifacial modules...”
              </div>
            </div>
            <div className="p-space-md rounded-lg bg-surface-container-low space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-space-sm">
                  <span className="font-label-xs text-label-xs uppercase text-on-surface-variant">Field:</span>
                  <span className="font-label-md text-label-md font-semibold text-on-surface">Installed Capacity</span>
                  <span className="px-2 py-0.5 rounded bg-surface-container text-on-surface font-mono text-label-xs font-semibold">24.5 MW</span>
                </div>
                <div className="flex items-center gap-space-sm">
                  <button className="inline-flex items-center gap-1 px-2 py-1 rounded bg-surface-container-lowest text-on-surface font-label-xs text-label-xs shadow-sm hover:bg-surface-container transition-colors" type="button">
                    <span className="material-symbols-outlined text-[12px]">open_in_new</span>
                    View source
                  </button>
                </div>
              </div>
              <div className="font-label-xs text-label-xs text-on-surface-variant">
                Document: <span className="font-mono text-on-surface">Technical Report.pdf · p.17</span>
              </div>
              <div className="font-body-sm text-body-sm italic text-on-surface-variant/90 pl-space-sm border-l-2 border-outline-variant/40">
                “Installed generating capacity: 24.5 MW AC rated interconnection at 115 kV delivery bus...”
              </div>
            </div>
            <div className="p-space-md rounded-lg bg-surface-container-low space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-space-sm">
                  <span className="font-label-xs text-label-xs uppercase text-on-surface-variant">Field:</span>
                  <span className="font-label-md text-label-md font-semibold text-on-surface">Location</span>
                  <span className="px-2 py-0.5 rounded bg-surface-container text-on-surface font-mono text-label-xs font-semibold">West Valley</span>
                </div>
                <div className="flex items-center gap-space-sm">
                  <button className="inline-flex items-center gap-1 px-2 py-1 rounded bg-surface-container-lowest text-on-surface font-label-xs text-label-xs shadow-sm hover:bg-surface-container transition-colors" type="button">
                    <span className="material-symbols-outlined text-[12px]">open_in_new</span>
                    View source
                  </button>
                </div>
              </div>
              <div className="font-label-xs text-label-xs text-on-surface-variant">
                Document: <span className="font-mono text-on-surface">Application Form.pdf · p.3</span>
              </div>
              <div className="font-body-sm text-body-sm italic text-on-surface-variant/90 pl-space-sm border-l-2 border-outline-variant/40">
                “Project site coordinates within West Valley Substation utility corridor, Parcel ID 841-A2...”
              </div>
            </div>
          </div>
        </div>
        
      </div>
    </div>
  </div>
</div>); }

