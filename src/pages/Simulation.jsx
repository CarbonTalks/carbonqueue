import React from 'react';
import { useApp, QueueRows } from '../state.jsx';
export default function Simulation({section='summary'}) { const ctx = useApp(); return (<div className="flex flex-col w-full">
  <div className="px-gutter-desktop py-space-xl flex flex-col gap-space-xl max-w-[1600px] mx-auto w-full historical-results">
    <div className="flex flex-wrap items-end justify-end gap-space-lg">
      {section==='setup' && <div className="flex flex-col gap-space-xs mr-auto">
        <div className="flex items-center gap-space-sm">
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant font-label-xs text-label-xs uppercase tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-secondary" />
            Evaluation &amp; Counterfactual Research Module
          </span>
          <span className="font-label-xs text-label-xs text-outline tracking-wider uppercase">SIM-RUN-2021-V4</span>
        </div>
        <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">Historical Analysis</h1>
        <p className="font-body-md text-body-md text-on-surface-variant max-w-3xl">
          Compare review policies under the same historical workload and expert capacity. Evaluates queue reordering impact without statutory pre-commitments.
        </p>
      </div>}
      <div className="flex items-center gap-space-md shrink-0">
        <button className="inline-flex items-center gap-space-sm px-space-lg py-2 rounded bg-surface-container-lowest text-on-surface shadow-sm hover:bg-surface-container transition-colors font-label-md text-label-md" type="button">
          <span className="material-symbols-outlined text-[18px]">download</span>
          Export Results
        </button>
        <button className="inline-flex items-center gap-space-sm px-space-lg py-2 rounded bg-primary text-on-primary shadow-sm hover:opacity-90 transition-opacity font-label-md text-label-md" id="btn-run-sim" type="button">
          <span className="material-symbols-outlined text-[18px]" id="sim-spin-icon">refresh</span>
          <span>Run Simulation</span>
        </button>
      </div>
    </div>
    {section==='setup' && (<div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-wrap items-center justify-between gap-space-md">
      <div className="flex flex-wrap items-center gap-space-sm text-on-surface">
        <div className="flex items-center gap-1.5 bg-surface-container-low px-space-md py-1.5 rounded">
          <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Year:</span>
          <span className="font-label-md text-label-md font-semibold">2021</span>
          <span className="material-symbols-outlined text-[16px] text-on-surface-variant">arrow_drop_down</span>
        </div>
        <div className="flex items-center gap-1.5 bg-surface-container-low px-space-md py-1.5 rounded">
          <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Policy Set:</span>
          <span className="font-label-md text-label-md font-semibold">All Policies</span>
          <span className="material-symbols-outlined text-[16px] text-on-surface-variant">arrow_drop_down</span>
        </div>
        <div className="flex items-center gap-1.5 bg-surface-container px-space-md py-1.5 rounded">
          <span className="material-symbols-outlined text-[15px] text-secondary">speed</span>
          <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Capacity:</span>
          <span className="font-label-md text-label-md font-semibold">320 h / week</span>
        </div>
        <div className="flex items-center gap-1.5 bg-surface-container-low px-space-md py-1.5 rounded">
          <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Stale Records:</span>
          <span className="font-label-md text-label-md font-semibold text-secondary">Included</span>
          <span className="material-symbols-outlined text-[14px] text-secondary">toggle_on</span>
        </div>
        <div className="flex items-center gap-1.5 bg-surface-container-low px-space-md py-1.5 rounded">
          <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Scenario:</span>
          <span className="font-label-md text-label-md font-semibold">Central (Mid)</span>
          <span className="material-symbols-outlined text-[16px] text-on-surface-variant">arrow_drop_down</span>
        </div>
        <div className="flex items-center gap-1.5 bg-surface-container-low px-space-md py-1.5 rounded" title="Strict operational threshold, not a statutory determination">
          <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Max-Wait Policy:</span>
          <span className="font-label-md text-label-md font-semibold">180 days</span>
        </div>
      </div>
      <a className="inline-flex items-center gap-1 text-on-surface-variant hover:text-on-surface font-label-md text-label-md transition-colors" href="#">
        <span className="material-symbols-outlined text-[16px]">tune</span>
        Advanced settings
      </a>
    </div>)}
    {section==='setup' && (<div className="bg-surface-container-low rounded-xl p-space-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-space-lg relative overflow-hidden">
      <div className="flex items-start gap-space-md">
        <div className="p-2 rounded bg-surface-container-highest text-secondary shrink-0">
          <span className="material-symbols-outlined text-[20px]">science</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-space-sm">
            <span className="font-label-xs text-label-xs uppercase font-semibold text-secondary">Historical Evaluation Sandbox</span>
            <span className="text-outline-variant font-label-xs">•</span>
            <span className="font-body-sm text-body-sm text-on-surface font-medium">Cohort-matched counterfactual simulation</span>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            All policies are evaluated using the identical application cohort, review capacity, and simulation rules. 
            The machine learning model for each simulated year is trained <span className="font-medium text-on-surface">strictly on information available prior to that year</span> to prevent temporal leakage.
          </p>
        </div>
      </div>
      <div className="shrink-0 flex items-center gap-space-sm bg-surface-container-lowest px-space-md py-1.5 rounded shadow-sm">
        <span className="material-symbols-outlined text-secondary text-[16px]">lock_clock</span>
        <span className="font-label-xs text-label-xs text-on-surface-variant">Leakage guard active</span>
      </div>
    </div>)}
    {section==='setup' && (<div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-md bg-surface-container-lowest p-space-md rounded-xl shadow-sm">
      <div className="flex items-center gap-space-xs overflow-x-auto pb-1 sm:pb-0">
        <span className="font-label-xs text-label-xs text-on-surface-variant uppercase pr-space-sm shrink-0">Simulated Cohort:</span>
        <button className="px-space-md py-1 rounded text-on-surface-variant hover:bg-surface-container-low font-label-md text-label-md transition-colors">2019</button>
        <button className="px-space-md py-1 rounded text-on-surface-variant hover:bg-surface-container-low font-label-md text-label-md transition-colors flex items-center gap-1">
          2020
          <span className="font-label-xs text-[10px] text-outline">(COVID context)</span>
        </button>
        <button className="px-space-md py-1 rounded bg-primary text-on-primary font-label-md text-label-md shadow-sm font-semibold flex items-center gap-1.5">
          <span>2021</span>
          <span className="w-1.5 h-1.5 rounded-full bg-secondary-container" />
          <span className="font-label-xs text-label-xs text-on-primary/80">Active</span>
        </button>
        <button className="px-space-md py-1 rounded text-on-surface-variant hover:bg-surface-container-low font-label-md text-label-md transition-colors">2022</button>
        <button className="px-space-md py-1 rounded text-on-surface-variant hover:bg-surface-container-low font-label-md text-label-md transition-colors">2023</button>
      </div>
      <p className="font-label-xs text-label-xs text-on-surface-variant italic">
        Each simulated year is evaluated independently without conflating historical cohorts or multi-year state carryovers.
      </p>
    </div>)}
    {section==='summary' && (<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-space-md">
      <div className="bg-surface-container-lowest rounded-xl p-space-lg shadow-sm flex flex-col justify-between gap-space-md hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <span className="font-label-xs text-label-xs uppercase tracking-wider text-on-surface-variant">Median Wait</span>
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-secondary-container text-on-secondary-fixed-variant font-label-xs text-label-xs font-semibold">
            -23 days
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex items-baseline gap-space-sm">
            <span className="font-metric-num text-metric-num text-on-surface">51</span>
            <span className="font-body-md text-body-md text-on-surface-variant">days</span>
          </div>
          <div className="flex items-center gap-space-sm font-body-sm text-body-sm">
            <span className="text-on-surface-variant">FIFO baseline:</span>
            <span className="font-medium text-on-surface">74 days</span>
          </div>
        </div>
        <div className="pt-space-sm flex items-center justify-between font-label-xs text-label-xs text-on-surface-variant bg-surface-container-low/60 -mx-space-lg -mb-space-lg p-space-sm px-space-lg rounded-b-xl">
          <span>Simulated review cycle</span>
          <span className="material-symbols-outlined text-[14px]">calendar_month</span>
        </div>
      </div>
      <div className="bg-surface-container-lowest rounded-xl p-space-lg shadow-sm flex flex-col justify-between gap-space-md hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <span className="font-label-xs text-label-xs uppercase tracking-wider text-on-surface-variant">P90 Tail Wait</span>
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-secondary-container text-on-secondary-fixed-variant font-label-xs text-label-xs font-semibold">
            -46 days
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex items-baseline gap-space-sm">
            <span className="font-metric-num text-metric-num text-on-surface">142</span>
            <span className="font-body-md text-body-md text-on-surface-variant">days</span>
          </div>
          <div className="flex items-center gap-space-sm font-body-sm text-body-sm">
            <span className="text-on-surface-variant">FIFO baseline:</span>
            <span className="font-medium text-on-surface">188 days</span>
          </div>
        </div>
        <div className="pt-space-sm flex items-center justify-between font-label-xs text-label-xs text-on-surface-variant bg-surface-container-low/60 -mx-space-lg -mb-space-lg p-space-sm px-space-lg rounded-b-xl">
          <span>Cap threshold: 180 d</span>
          <span className="material-symbols-outlined text-[14px]">timer</span>
        </div>
      </div>
      <div className="bg-surface-container-lowest rounded-xl p-space-lg shadow-sm flex flex-col justify-between gap-space-md hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <span className="font-label-xs text-label-xs uppercase tracking-wider text-on-surface-variant">Avoided-Delay CO₂e</span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-surface-container text-secondary font-label-xs text-label-xs font-semibold">
            Modeled
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex items-baseline gap-1">
            <span className="font-metric-num text-metric-num text-secondary">1.2–3.8</span>
            <span className="font-body-sm text-body-sm text-on-surface-variant">ktCO₂e</span>
          </div>
          <div className="flex items-center gap-space-sm font-body-sm text-body-sm">
            <span className="text-on-surface-variant">FIFO baseline:</span>
            <span className="font-medium text-on-surface">0.0 (Ref)</span>
          </div>
        </div>
        <div className="pt-space-sm flex items-center justify-between font-label-xs text-label-xs text-on-surface-variant bg-surface-container-low/60 -mx-space-lg -mb-space-lg p-space-sm px-space-lg rounded-b-xl" title="Modeled displacement potential under dispatch constraints; not guaranteed real-world savings.">
          <span className="truncate">Central scenario range</span>
          <span className="material-symbols-outlined text-[14px]">eco</span>
        </div>
      </div>
      <div className="bg-surface-container-lowest rounded-xl p-space-lg shadow-sm flex flex-col justify-between gap-space-md hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <span className="font-label-xs text-label-xs uppercase tracking-wider text-on-surface-variant">Max-Wait Violations</span>
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-secondary-container text-on-secondary-fixed-variant font-label-xs text-label-xs font-semibold">
            -5 apps
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex items-baseline gap-space-sm">
            <span className="font-metric-num text-metric-num text-on-surface">2</span>
            <span className="font-body-md text-body-md text-on-surface-variant">cases</span>
          </div>
          <div className="flex items-center gap-space-sm font-body-sm text-body-sm">
            <span className="text-on-surface-variant">FIFO baseline:</span>
            <span className="font-medium text-error">7 cases</span>
          </div>
        </div>
        <div className="pt-space-sm flex items-center justify-between font-label-xs text-label-xs text-on-surface-variant bg-surface-container-low/60 -mx-space-lg -mb-space-lg p-space-sm px-space-lg rounded-b-xl">
          <span>Exceeding &gt;180 days</span>
          <span className="material-symbols-outlined text-[14px]">rule</span>
        </div>
      </div>
      <div className="bg-surface-container-lowest rounded-xl p-space-lg shadow-sm flex flex-col justify-between gap-space-md hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <span className="font-label-xs text-label-xs uppercase tracking-wider text-on-surface-variant">Wasted Review Effort</span>
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-secondary-container text-on-secondary-fixed-variant font-label-xs text-label-xs font-semibold">
            -35 h (-36%)
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex items-baseline gap-space-sm">
            <span className="font-metric-num text-metric-num text-on-surface">61</span>
            <span className="font-body-md text-body-md text-on-surface-variant">hours</span>
          </div>
          <div className="flex items-center gap-space-sm font-body-sm text-body-sm">
            <span className="text-on-surface-variant">FIFO baseline:</span>
            <span className="font-medium text-on-surface">96 hours</span>
          </div>
        </div>
        <div className="pt-space-sm flex items-center justify-between font-label-xs text-label-xs text-on-surface-variant bg-surface-container-low/60 -mx-space-lg -mb-space-lg p-space-sm px-space-lg rounded-b-xl">
          <span className="truncate">On later-withdrawn apps</span>
          <span className="material-symbols-outlined text-[14px]">hourglass_disabled</span>
        </div>
      </div>
    </div>)}
    {section==='comparison' && (<div className="bg-surface-container-lowest rounded-xl shadow-sm p-space-lg flex flex-col gap-space-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm">
        <div>
          <div className="flex items-center gap-space-sm">
            <h2 className="font-headline-md text-headline-md text-on-surface">What changes as policy components are added?</h2>
            <span className="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant font-label-xs text-label-xs font-medium">Illustrative simulation values</span>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant">Incremental contribution of each policy constraint under identical 320 h/week reviewer capacity.</p>
        </div>
        <div className="flex items-center gap-space-sm">
          <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Comparator Mode:</span>
          <span className="font-label-md text-label-md font-semibold text-on-surface">Stepwise Progression</span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-low text-on-surface-variant font-label-md text-label-md uppercase">
              <th className="py-space-md px-space-lg rounded-l">Metric</th>
              <th className="py-space-md px-space-md text-right">FIFO (Baseline)</th>
              <th className="py-space-md px-space-md text-right">+ Carbon Only</th>
              <th className="py-space-md px-space-md text-right">+ Withdrawal Risk</th>
              <th className="py-space-md px-space-md text-right">+ Review Effort</th>
              <th className="py-space-md px-space-lg text-right rounded-r bg-surface-container font-semibold text-on-surface">
                <span className="inline-flex items-center gap-1.5">
                  CarbonQueue
                  <span className="px-1.5 py-0.5 rounded bg-primary text-on-primary font-label-xs text-[10px] uppercase font-normal">Recommended</span>
                </span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y-0 text-on-surface font-body-md text-body-md">
            <tr className="hover:bg-surface-container-low/50 transition-colors">
              <td className="py-3 px-space-lg font-medium">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px] text-on-surface-variant">speed</span>
                  <span>Median Wait Time</span>
                </div>
              </td>
              <td className="py-3 px-space-md text-right font-medium">74 d</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">68 d</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">64 d</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">58 d</td>
              <td className="py-3 px-space-lg text-right font-semibold bg-surface-container-low text-secondary">51 d (-31%)</td>
            </tr>
            <tr className="hover:bg-surface-container-low/50 transition-colors">
              <td className="py-3 px-space-lg font-medium">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px] text-on-surface-variant">hourglass_top</span>
                  <span>P90 Tail Wait</span>
                </div>
              </td>
              <td className="py-3 px-space-md text-right font-medium">188 d</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">176 d</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">168 d</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">154 d</td>
              <td className="py-3 px-space-lg text-right font-semibold bg-surface-container-low text-secondary">142 d (-24%)</td>
            </tr>
            <tr className="hover:bg-surface-container-low/50 transition-colors">
              <td className="py-3 px-space-lg font-medium">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px] text-on-surface-variant">warning</span>
                  <span>Max-Wait Exceedances (&gt;180 d)</span>
                </div>
              </td>
              <td className="py-3 px-space-md text-right font-medium text-error">7 apps</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">6 apps</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">5 apps</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">4 apps</td>
              <td className="py-3 px-space-lg text-right font-semibold bg-surface-container-low text-secondary">2 apps (-71%)</td>
            </tr>
            <tr className="hover:bg-surface-container-low/50 transition-colors">
              <td className="py-3 px-space-lg font-medium">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px] text-on-surface-variant">work_history</span>
                  <span>Wasted Review Effort</span>
                </div>
              </td>
              <td className="py-3 px-space-md text-right font-medium">96 h</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">94 h</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">76 h</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">64 h</td>
              <td className="py-3 px-space-lg text-right font-semibold bg-surface-container-low text-secondary">61 h (-36%)</td>
            </tr>
            <tr className="hover:bg-surface-container-low/50 transition-colors">
              <td className="py-3 px-space-lg font-medium">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px] text-on-surface-variant">cloud_sync</span>
                  <span>Modeled Avoided-Delay Carbon</span>
                </div>
              </td>
              <td className="py-3 px-space-md text-right font-medium text-on-surface-variant">Baseline (0.0)</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">+1.9 kt</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">+2.2 kt</td>
              <td className="py-3 px-space-md text-right text-on-surface-variant">+2.8 kt</td>
              <td className="py-3 px-space-lg text-right font-semibold bg-surface-container-low text-secondary">+3.1 ktCO₂e</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>)}
    {section==='distribution' && (<div className="bg-surface-container-lowest rounded-xl p-space-lg shadow-sm flex flex-col justify-between gap-space-lg">
        <div className="flex flex-col gap-1">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-headline-md text-headline-md text-on-surface">Waiting Time Distribution</h3>
            <span className="font-label-xs text-label-xs text-on-surface-variant bg-surface-container px-2 py-0.5 rounded">Percentile Spread</span>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Comparison of P10, P25, Median (P50), P75, and P90 review durations against the 180-day Maximum-Wait Policy threshold.
          </p>
        </div>
        <div className="waiting-distribution-chart w-full bg-surface-container-low rounded-lg p-space-md">
          <svg className="w-full h-auto text-on-surface" preserveAspectRatio="xMidYMid meet" viewBox="-30 0 560 180" role="img" aria-label="Waiting time distribution: FIFO median 74 days, P90 188 days; CarbonQueue median 51 days, P90 142 days. Maximum-wait threshold 180 days.">
            <line stroke="currentColor" strokeDasharray="2 2" strokeOpacity="0.1" x1={70} x2={70} y1={20} y2={135} />
            <line stroke="currentColor" strokeDasharray="2 2" strokeOpacity="0.1" x1={190} x2={190} y1={20} y2={135} />
            <line stroke="currentColor" strokeDasharray="2 2" strokeOpacity="0.1" x1={310} x2={310} y1={20} y2={135} />
            <line stroke="#ba1a1a" strokeDasharray="4 2" strokeOpacity="0.4" strokeWidth="1.5" x1={430} x2={430} y1={20} y2={135} />
            <line stroke="currentColor" strokeDasharray="2 2" strokeOpacity="0.1" x1={490} x2={490} y1={20} y2={135} />
            <text fill="#76777d" fontFamily="Inter" fontSize={10} textAnchor="middle" x={70} y={152}>0 d</text>
            <text fill="#76777d" fontFamily="Inter" fontSize={10} textAnchor="middle" x={190} y={152}>60 d</text>
            <text fill="#76777d" fontFamily="Inter" fontSize={10} textAnchor="middle" x={310} y={152}>120 d</text>
            <text fill="#ba1a1a" fontFamily="Inter" fontSize={10} fontWeight={600} textAnchor="middle" x={430} y={152}>180 d<tspan x={430} dy={13} fontSize={8}>(Max-Wait)</tspan></text>
            <text fill="#76777d" fontFamily="Inter" fontSize={10} textAnchor="middle" x={490} y={152}>210 d</text>
            <text fill="#0b1c30" fontFamily="Inter" fontSize={11} fontWeight={600} textAnchor="end" x={60} y={55}>FIFO</text>
            <rect fill="#cbd5e1" fillOpacity="0.4" height={18} rx={3} width={312} x={134} y={44} />
            <rect fill="#64748b" fillOpacity="0.3" height={26} rx={4} width={128} x={166} y={40} />
            <line stroke="#0b1c30" strokeWidth="2.5" x1={218} x2={218} y1={36} y2={70} />
            <circle cx={218} cy={53} fill="#0b1c30" r="3.5" />
            <line stroke="#ba1a1a" strokeWidth={2} x1={446} x2={446} y1={40} y2={66} />
            <text fill="#ba1a1a" fontFamily="Inter" fontSize={9} textAnchor="middle" x={446} y={34}>188d (tail breach)</text>
            <text fill="#006c4e" fontFamily="Inter" fontSize={11} fontWeight={600} textAnchor="end" x={60} y={105}>CarbonQueue</text>
            <rect fill="#97f5cc" fillOpacity="0.4" height={18} rx={3} width={236} x={118} y={94} />
            <rect fill="#006c4e" fillOpacity="0.25" height={26} rx={4} width={96} x={142} y={90} />
            <line stroke="#006c4e" strokeWidth="2.5" x1={172} x2={172} y1={86} y2={120} />
            <circle cx={172} cy={103} fill="#006c4e" r="3.5" />
            <line stroke="#006c4e" strokeWidth={2} x1={354} x2={354} y1={90} y2={116} />
            <text fill="#006c4e" fontFamily="Inter" fontSize={9} fontWeight={600} textAnchor="middle" x={354} y={84}>142d (compliant)</text>
          </svg>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 text-on-surface-variant font-label-xs text-label-xs">
          <div className="flex flex-wrap items-center gap-space-md">
            <span className="inline-flex items-center gap-1.5"><span className="w-3 h-3 bg-slate-300 rounded-sm" /> Interquartile Range (IQR)</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-0.5 bg-on-surface" /> Median P50</span>
          </div>
          <span className="text-error font-medium">Vertical red dashed: 180 d Policy Cap</span>
        </div>
      </div>)}
    {section==='carbon' && (<div className="bg-surface-container-lowest rounded-xl p-space-lg shadow-sm flex flex-col justify-between gap-space-lg">
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <h3 className="font-headline-md text-headline-md text-on-surface">Modeled Carbon Potential Ranges</h3>
            <span className="font-label-xs text-label-xs text-secondary bg-surface-container px-2 py-0.5 rounded">Central Scenario</span>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Uncertainty intervals across policies. Modeled displacement potential under dispatch constraints; not guaranteed real-world savings.
          </p>
        </div>
        <div className="w-full bg-surface-container-low rounded-lg p-space-md">
          <svg className="w-full h-auto text-on-surface" preserveAspectRatio="xMidYMid meet" viewBox="0 0 520 180">
            <line stroke="currentColor" strokeDasharray="2 2" strokeOpacity="0.1" x1={100} x2={100} y1={15} y2={140} />
            <line stroke="currentColor" strokeDasharray="2 2" strokeOpacity="0.1" x1={190} x2={190} y1={15} y2={140} />
            <line stroke="currentColor" strokeDasharray="2 2" strokeOpacity="0.1" x1={280} x2={280} y1={15} y2={140} />
            <line stroke="currentColor" strokeDasharray="2 2" strokeOpacity="0.1" x1={370} x2={370} y1={15} y2={140} />
            <line stroke="currentColor" strokeDasharray="2 2" strokeOpacity="0.1" x1={460} x2={460} y1={15} y2={140} />
            <text fill="#76777d" fontFamily="Inter" fontSize={10} textAnchor="middle" x={100} y={155}>0 kt</text>
            <text fill="#76777d" fontFamily="Inter" fontSize={10} textAnchor="middle" x={190} y={155}>1.0 kt</text>
            <text fill="#76777d" fontFamily="Inter" fontSize={10} textAnchor="middle" x={280} y={155}>2.0 kt</text>
            <text fill="#76777d" fontFamily="Inter" fontSize={10} textAnchor="middle" x={370} y={155}>3.0 kt</text>
            <text fill="#76777d" fontFamily="Inter" fontSize={10} textAnchor="middle" x={460} y={155}>4.0 kt</text>
            <text fill="#45464d" fontFamily="Inter" fontSize={10} textAnchor="end" x={90} y={36}>FIFO</text>
            <circle cx={100} cy={32} fill="#76777d" r={4} />
            <text fill="#76777d" fontFamily="Inter" fontSize={9} x={112} y={36}>Baseline (0.0)</text>
            <text fill="#45464d" fontFamily="Inter" fontSize={10} textAnchor="end" x={90} y={62}>Carbon Only</text>
            <line stroke="#76777d" strokeWidth={2} x1={172} x2={334} y1={58} y2={58} />
            <rect fill="#d3e4fe" height={12} rx={2} width={60} x={235} y={52} />
            <circle cx={271} cy={58} fill="#131b2e" r="3.5" />
            <text fill="#45464d" fontFamily="Inter" fontSize={10} textAnchor="end" x={90} y={88}>+ Withdrawal</text>
            <line stroke="#76777d" strokeWidth={2} x1={190} x2={370} y1={84} y2={84} />
            <rect fill="#d3e4fe" height={12} rx={2} width={65} x={260} y={78} />
            <circle cx={298} cy={84} fill="#131b2e" r="3.5" />
            <text fill="#45464d" fontFamily="Inter" fontSize={10} textAnchor="end" x={90} y={114}>+ Effort</text>
            <line stroke="#76777d" strokeWidth={2} x1={199} x2={406} y1={110} y2={110} />
            <rect fill="#bec6e0" height={12} rx={2} width={70} x={310} y={104} />
            <circle cx={352} cy={110} fill="#131b2e" r="3.5" />
            <text fill="#006c4e" fontFamily="Inter" fontSize={10} fontWeight={600} textAnchor="end" x={90} y={140}>CarbonQueue</text>
            <line stroke="#006c4e" strokeWidth="2.5" x1={208} x2={442} y1={136} y2={136} />
            <rect fill="#97f5cc" height={13} rx={2} width={85} x={330} y={130} />
            <circle cx={379} cy="136.5" fill="#006c4e" r={4} />
            <text fill="#006c4e" fontFamily="Inter" fontSize={10} fontWeight={600} x={450} y={139}>+3.1 kt</text>
          </svg>
        </div>
        <div className="flex items-center justify-between text-on-surface-variant font-label-xs text-label-xs">
          <span>Whisker: 10th–90th percentile modeled variance</span>
          <span className="text-on-surface font-medium">Box &amp; Point: Interquartile mass &amp; Median</span>
        </div>
      </div>)}
    {section==='sensitivity' && (<div className="flex flex-col gap-space-lg">
        <div className="bg-surface-container-lowest rounded-xl p-space-lg shadow-sm flex flex-col gap-space-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-space-sm">
              <div className="p-1.5 rounded bg-surface-container-low text-on-surface">
                <span className="material-symbols-outlined text-[18px]">find_replace</span>
              </div>
              <h3 className="font-headline-md text-headline-md text-on-surface">Stale Record Sensitivity</h3>
            </div>
            <span className="font-label-xs text-label-xs text-on-surface-variant bg-surface-container px-2 py-0.5 rounded">Robustness Check</span>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Long-waiting or uncertain historical submissions are flagged rather than silently excluded. Reporting both conditions confirms whether tail results hinge on dormant files.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md">
            <div className="p-space-md rounded-lg bg-surface-container-low flex flex-col gap-space-sm">
              <div className="flex items-center justify-between">
                <span className="font-label-md text-label-md font-semibold text-on-surface">Stale Records Included</span>
                <span className="font-label-xs text-label-xs bg-surface-container px-1.5 py-0.5 rounded text-on-surface-variant">Default</span>
              </div>
              <div className="flex flex-col gap-1 text-on-surface-variant font-body-sm text-body-sm">
                <div className="flex justify-between"><span>Median Wait:</span> <span className="font-medium text-on-surface">51 days</span></div>
                <div className="flex justify-between"><span>P90 Tail Wait:</span> <span className="font-medium text-on-surface">142 days</span></div>
                <div className="flex justify-between"><span>Modeled Carbon:</span> <span className="font-medium text-secondary">1.2–3.8 ktCO₂e</span></div>
              </div>
            </div>
            <div className="p-space-md rounded-lg bg-surface-container-low flex flex-col gap-space-sm">
              <div className="flex items-center justify-between">
                <span className="font-label-md text-label-md font-semibold text-on-surface">Stale Records Excluded</span>
                <span className="font-label-xs text-label-xs bg-surface-container px-1.5 py-0.5 rounded text-on-surface-variant">Filtered</span>
              </div>
              <div className="flex flex-col gap-1 text-on-surface-variant font-body-sm text-body-sm">
                <div className="flex justify-between"><span>Median Wait:</span> <span className="font-medium text-on-surface">48 days</span></div>
                <div className="flex justify-between"><span>P90 Tail Wait:</span> <span className="font-medium text-on-surface">136 days</span></div>
                <div className="flex justify-between"><span>Modeled Carbon:</span> <span className="font-medium text-secondary">1.1–3.5 ktCO₂e</span></div>
              </div>
            </div>
          </div>
          <p className="font-label-xs text-label-xs text-on-surface-variant italic">
            Delta is minor (+3 days median, +6 days P90), showing policy performance is robust against historical administrative backlog artifacts.
          </p>
        </div>
      </div>)}
    {section==='performance' && (<div className="bg-surface-container-lowest rounded-xl p-space-lg shadow-sm flex flex-col justify-between gap-space-md">
        <div className="flex flex-col gap-space-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm">
            <h3 className="font-headline-md text-headline-md text-on-surface">Performance Breakdown</h3>
            <div className="inline-flex p-0.5 bg-surface-container rounded-lg self-start">
              <button className={"px-space-md py-1 rounded font-label-md text-label-md " + (ctx.breakdown === 'tech' ? 'bg-white shadow-sm font-semibold' : 'text-on-surface-variant')} aria-pressed={ctx.breakdown === 'tech'} id="tab-btn-tech">Technology</button>
              <button className={"px-space-md py-1 rounded font-label-md text-label-md " + (ctx.breakdown === 'size' ? 'bg-white shadow-sm font-semibold' : 'text-on-surface-variant')} aria-pressed={ctx.breakdown === 'size'} id="tab-btn-size">Project Size</button>
            </div>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant">Cohort performance across technical categories under the CarbonQueue schedule.</p>
        </div>
        <div className="flex flex-col gap-space-sm" id="view-tech" style={{display: ctx.breakdown === "tech" ? "flex" : "none"}}>
          <div className="p-space-md rounded-lg bg-surface-container-low flex items-center justify-between hover:bg-surface-container transition-colors">
            <div className="flex items-center gap-space-md">
              <div className="p-2 rounded bg-surface-container-lowest text-on-surface">
                <span className="material-symbols-outlined text-[20px]">solar_power</span>
              </div>
              <div className="flex flex-col">
                <span className="font-label-md text-label-md font-semibold text-on-surface">Solar PV</span>
                <span className="font-label-xs text-label-xs text-on-surface-variant">18 active applications</span>
              </div>
            </div>
            <div className="flex items-center gap-space-xl text-right">
              <div className="flex flex-col">
                <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Median Wait</span>
                <span className="font-body-md text-body-md font-semibold text-on-surface">49 days</span>
              </div>
              <div className="flex flex-col min-w-[110px]">
                <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Modeled CO₂e</span>
                <span className="font-body-md text-body-md font-semibold text-secondary">0.8–1.6 kt</span>
              </div>
            </div>
          </div>
          <div className="p-space-md rounded-lg bg-surface-container-low flex items-center justify-between hover:bg-surface-container transition-colors">
            <div className="flex items-center gap-space-md">
              <div className="p-2 rounded bg-surface-container-lowest text-on-surface">
                <span className="material-symbols-outlined text-[20px]">mode_fan</span>
              </div>
              <div className="flex flex-col">
                <span className="font-label-md text-label-md font-semibold text-on-surface">Onshore &amp; Offshore Wind</span>
                <span className="font-label-xs text-label-xs text-on-surface-variant">8 active applications</span>
              </div>
            </div>
            <div className="flex items-center gap-space-xl text-right">
              <div className="flex flex-col">
                <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Median Wait</span>
                <span className="font-body-md text-body-md font-semibold text-on-surface">46 days</span>
              </div>
              <div className="flex flex-col min-w-[110px]">
                <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Modeled CO₂e</span>
                <span className="font-body-md text-body-md font-semibold text-secondary">0.9–1.8 kt</span>
              </div>
            </div>
          </div>
          <div className="p-space-md rounded-lg bg-surface-container-low flex items-center justify-between hover:bg-surface-container transition-colors">
            <div className="flex items-center gap-space-md">
              <div className="p-2 rounded bg-surface-container-lowest text-on-surface">
                <span className="material-symbols-outlined text-[20px]">battery_charging_full</span>
              </div>
              <div className="flex flex-col">
                <span className="font-label-md text-label-md font-semibold text-on-surface">Battery Energy Storage</span>
                <span className="font-label-xs text-label-xs text-on-surface-variant">7 active applications</span>
              </div>
            </div>
            <div className="flex items-center gap-space-xl text-right">
              <div className="flex flex-col">
                <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Median Wait</span>
                <span className="font-body-md text-body-md font-semibold text-on-surface">53 days</span>
              </div>
              <div className="flex flex-col min-w-[110px]">
                <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Modeled CO₂e</span>
                <span className="font-body-md text-body-md font-semibold text-secondary">0.4–0.7 kt</span>
              </div>
            </div>
          </div>
          <div className="p-space-md rounded-lg bg-surface-container-low flex items-center justify-between hover:bg-surface-container transition-colors">
            <div className="flex items-center gap-space-md">
              <div className="p-2 rounded bg-surface-container-lowest text-on-surface">
                <span className="material-symbols-outlined text-[20px]">ev_station</span>
              </div>
              <div className="flex flex-col">
                <span className="font-label-md text-label-md font-semibold text-on-surface">Commercial EV Fleet Hubs</span>
                <span className="font-label-xs text-label-xs text-on-surface-variant">5 active applications</span>
              </div>
            </div>
            <div className="flex items-center gap-space-xl text-right">
              <div className="flex flex-col">
                <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Median Wait</span>
                <span className="font-body-md text-body-md font-semibold text-on-surface">57 days</span>
              </div>
              <div className="flex flex-col min-w-[110px]">
                <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Modeled CO₂e</span>
                <span className="font-body-md text-body-md font-semibold text-secondary">0.2–0.5 kt</span>
              </div>
            </div>
          </div>
          <div className="p-space-md rounded-lg bg-surface-container-low flex items-center justify-between hover:bg-surface-container transition-colors">
            <div className="flex items-center gap-space-md">
              <div className="p-2 rounded bg-surface-container-lowest text-on-surface">
                <span className="material-symbols-outlined text-[20px]">heat_pump</span>
              </div>
              <div className="flex flex-col">
                <span className="font-label-md text-label-md font-semibold text-on-surface">Industrial Heat Pump Cluster</span>
                <span className="font-label-xs text-label-xs text-on-surface-variant">4 active applications</span>
              </div>
            </div>
            <div className="flex items-center gap-space-xl text-right">
              <div className="flex flex-col">
                <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Median Wait</span>
                <span className="font-body-md text-body-md font-semibold text-on-surface">62 days</span>
              </div>
              <div className="flex flex-col min-w-[110px]">
                <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">Modeled CO₂e</span>
                <span className="font-body-md text-body-md font-semibold text-secondary">0.3–0.6 kt</span>
              </div>
            </div>
          </div>
        </div>
        <div className="hidden flex-col gap-space-sm" id="view-size" style={{display: ctx.breakdown === "size" ? "flex" : "none"}}>
          <div className="p-space-md rounded-lg bg-surface-container-low flex items-center justify-between">
            <div className="flex flex-col">
              <span className="font-label-md text-label-md font-semibold text-on-surface">Small Projects (&lt; 5 MW)</span>
              <span className="font-label-xs text-label-xs text-on-surface-variant">14 applications</span>
            </div>
            <div className="flex items-center gap-space-lg text-right">
              <div><span className="font-label-xs text-label-xs text-on-surface-variant">Median:</span> <span className="font-body-md text-body-md font-semibold">58 d</span></div>
              <div><span className="font-label-xs text-label-xs text-on-surface-variant">P90:</span> <span className="font-body-md text-body-md font-semibold">146 d</span></div>
            </div>
          </div>
          <div className="p-space-md rounded-lg bg-surface-container-low flex items-center justify-between">
            <div className="flex flex-col">
              <span className="font-label-md text-label-md font-semibold text-on-surface">Medium Projects (5–50 MW)</span>
              <span className="font-label-xs text-label-xs text-on-surface-variant">20 applications</span>
            </div>
            <div className="flex items-center gap-space-lg text-right">
              <div><span className="font-label-xs text-label-xs text-on-surface-variant">Median:</span> <span className="font-body-md text-body-md font-semibold">50 d</span></div>
              <div><span className="font-label-xs text-label-xs text-on-surface-variant">P90:</span> <span className="font-body-md text-body-md font-semibold">138 d</span></div>
            </div>
          </div>
          <div className="p-space-md rounded-lg bg-surface-container-low flex items-center justify-between">
            <div className="flex flex-col">
              <span className="font-label-md text-label-md font-semibold text-on-surface">Large Utility (&gt; 50 MW)</span>
              <span className="font-label-xs text-label-xs text-on-surface-variant">8 applications</span>
            </div>
            <div className="flex items-center gap-space-lg text-right">
              <div><span className="font-label-xs text-label-xs text-on-surface-variant">Median:</span> <span className="font-body-md text-body-md font-semibold">44 d</span></div>
              <div><span className="font-label-xs text-label-xs text-on-surface-variant">P90:</span> <span className="font-body-md text-body-md font-semibold">132 d</span></div>
            </div>
          </div>
        </div>
        <div className="pt-space-sm border-t-0 flex items-center justify-between font-label-xs text-label-xs text-on-surface-variant">
          <span>Total simulated projects: 42</span>
          <span>Aggregated capacity: 418 MW</span>
        </div>
      </div>)}
    {section==='setup' && (<div className="grid grid-cols-1 md:grid-cols-2 gap-space-lg">
      <div className="bg-surface-container-lowest rounded-xl p-space-lg shadow-sm flex flex-col gap-space-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-space-sm">
            <div className="p-1.5 rounded bg-surface-container-low text-on-surface">
              <span className="material-symbols-outlined text-[18px]">model_training</span>
            </div>
            <h3 className="font-headline-md text-headline-md text-on-surface">Historical Model Setup</h3>
          </div>
          <span className="font-label-xs text-label-xs text-on-surface-variant bg-surface-container px-2 py-0.5 rounded">CatBoost v1.2</span>
        </div>
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          Each simulation year strictly utilizes a model trained on data registered before that year to avoid temporal leakage.
        </p>
        <div className="grid grid-cols-2 gap-space-sm text-on-surface font-body-sm text-body-sm">
          <div className="bg-surface-container-low p-space-sm rounded">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase block">Simulated Year</span>
            <span className="font-semibold">2021 Cohort</span>
          </div>
          <div className="bg-surface-container-low p-space-sm rounded">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase block">Training Cutoff</span>
            <span className="font-semibold">31 Dec 2020</span>
          </div>
          <div className="bg-surface-container-low p-space-sm rounded">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase block">Window Interval</span>
            <span className="font-semibold">30-day Batches</span>
          </div>
          <div className="bg-surface-container-low p-space-sm rounded">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase block">Hyperparameters</span>
            <span className="font-semibold">Fixed Pre-Run</span>
          </div>
        </div>
        <div className="pt-space-xs">
          <span className="font-label-xs text-label-xs text-outline">Validation Strategy: Expanding historical window without post-period leakage.</span>
        </div>
      </div>
      <div className="bg-surface-container-lowest rounded-xl p-space-lg shadow-sm flex flex-col justify-between gap-space-md">
        <div className="flex flex-col gap-space-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-space-sm">
              <div className="p-1.5 rounded bg-surface-container-low text-on-surface">
                <span className="material-symbols-outlined text-[18px]">rule_folder</span>
              </div>
              <h3 className="font-headline-md text-headline-md text-on-surface">Simulation Assumptions</h3>
            </div>
            <a className="font-label-md text-label-md text-secondary hover:underline flex items-center gap-0.5" href="#">
              Full methodology
              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </a>
          </div>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-x-space-md gap-y-1.5 text-on-surface font-body-sm text-body-sm">
            <li className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-secondary">check</span>
              <span>Identical cohort across policies</span>
            </li>
            <li className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-secondary">check</span>
              <span>Fixed capacity (320 h/wk)</span>
            </li>
            <li className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-secondary">check</span>
              <span>Identical review-effort models</span>
            </li>
            <li className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-secondary">check</span>
              <span>Shared carbon grid scenarios</span>
            </li>
            <li className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-secondary">check</span>
              <span>Max-wait protection enabled</span>
            </li>
            <li className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-secondary">check</span>
              <span>Fairness constraint active</span>
            </li>
            <li className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-secondary">check</span>
              <span>Withdrawn = 0 carbon benefit</span>
            </li>
            <li className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-secondary">check</span>
              <span>Exits queue upon drop date</span>
            </li>
          </ul>
        </div>
        <div className="bg-surface-container-low p-space-sm rounded font-label-xs text-label-xs text-on-surface-variant flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px] text-outline">info</span>
          <span>Historical outcomes are not used to determine simulated queue order (ex-ante scoring only).</span>
        </div>
      </div>
    </div>)}
  </div>
</div>); }
