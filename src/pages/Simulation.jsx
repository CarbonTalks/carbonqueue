import React, { useState } from 'react';
import { useHistorical, HISTORICAL_POLICIES } from '../api.js';
import { fmt } from '../live-data.js';
import { Chart } from '../chart.jsx';

const YEARS = [2019, 2020, 2021, 2022, 2023];
const NAMES = { fifo: 'FIFO', carbon: 'Carbon only', carbon_withdrawal: '+ Withdrawal risk', carbon_withdrawal_effort: '+ Effort', carbonqueue: 'CarbonQueue' };
const GROUPS = [['all', 'All files'], ['small_scored', 'Small (<1 MW)'], ['large_scored', 'Large scored'], ['unscored', 'Unscored']];
const kt = t => fmt(t / 1000, 1);

function Kpi({ label, value, unit, note }) {
  return <div className="results-kpi"><div className="results-kpi-label"><span>{label}</span></div><div className="results-kpi-value">{value}<small>{unit}</small></div><div className="results-kpi-bottom"><span>{note}</span></div></div>;
}

function Panel({ title, children }) { return <section className="results-panel"><h2>{title}</h2>{children}</section>; }

export default function Simulation({ section = 'summary' }) {
  const [year, setYear] = useState(2023);
  const history = useHistorical(year);
  const d = history.data;
  const cq = d?.carbonqueue, fifo = d?.fifo;
  return <div className="flex flex-col gap-space-lg">
    <div className="results-archive-note"><span className="material-symbols-outlined" aria-hidden="true">history</span>
      <span>Replay of a real English queue with each policy, same calibrated capacity and effort rules. Carbon counts only applications that were actually permitted.</span>
      <label className="results-week ml-auto">Queue year<select value={year} onChange={e => setYear(Number(e.target.value))}>{YEARS.map(y => <option key={y} value={y}>{y}{y < 2021 ? ' (small queue)' : ''}</option>)}</select></label>
    </div>
    {history.status === 'loading' && <Panel title="Loading">Loading {year} results…</Panel>}
    {history.status === 'error' && <Panel title="Historical results unavailable"><p>{history.error.message}. Set CQ_SIMULATION_RESULTS_DIR in the backend (see README).</p></Panel>}
    {d && section === 'summary' && <>
      <div className="results-kpis">
        <Kpi label="Carbon gain vs FIFO" value={kt(cq.carbon_gain_tco2_vs_fifo['alpha_0.5'].central)} unit="ktCO₂e" note={`Range ${kt(cq.carbon_gain_tco2_vs_fifo['alpha_0.2'].low)}–${kt(cq.carbon_gain_tco2_vs_fifo['alpha_1.0'].high)} kt`} />
        <Kpi label="Median wait" value={fmt(cq.wait_days.all.median, 0)} unit="days" note={`FIFO ${fmt(fifo.wait_days.all.median, 0)} days`} />
        <Kpi label="P90 wait" value={fmt(cq.wait_days.all.p90, 0)} unit="days" note={`FIFO ${fmt(fifo.wait_days.all.p90, 0)} days`} />
        <Kpi label="Small projects, P90 wait" value={fmt(cq.wait_days.small_scored.p90, 0)} unit="days" note={`FIFO ${fmt(fifo.wait_days.small_scored.p90, 0)} · carbon only ${fmt(d.carbon.wait_days.small_scored.p90, 0)}`} />
      </div>
      <Panel title="Reading the result">
        <p>CarbonQueue reviews high-impact projects earlier without adding reviewers: across the {fmt(cq.files, 0)} files of the {year} queue, earlier permissions shift about {kt(cq.carbon_gain_tco2_vs_fifo['alpha_0.5'].central)} kt of displaced emissions forward (central emission factor, 50% of earlier permission passed through to earlier operation).</p>
        <p>Fairness protections cost part of the gain: carbon-only ordering reaches {kt(d.carbon.carbon_gain_tco2_vs_fifo['alpha_0.5'].central)} kt but pushes the slowest small projects to {fmt(d.carbon.wait_days.small_scored.p90, 0)} days.</p>
      </Panel>
    </>}
    {d && section === 'comparison' && <Panel title="What changes as policy components are added?">
      <div className="overflow-x-auto"><table className="w-full text-left text-body-sm">
        <thead><tr className="uppercase font-label-xs text-label-xs text-on-surface-variant"><th className="py-2 pr-3">Policy</th><th className="pr-3 text-right">Carbon gain (kt)</th><th className="pr-3 text-right">Median wait</th><th className="pr-3 text-right">P90 wait</th><th className="pr-3 text-right">Small P90</th><th className="pr-3 text-right">Over 365 days</th><th className="text-right">Hours on withdrawn files</th></tr></thead>
        <tbody className="divide-y divide-surface-container">{HISTORICAL_POLICIES.map(p => { const r = d[p]; return <tr key={p} className={p === 'carbonqueue' ? 'font-semibold' : ''}>
          <td className="py-2 pr-3">{NAMES[p]}</td>
          <td className="pr-3 text-right">{p === 'fifo' ? '—' : kt(r.carbon_gain_tco2_vs_fifo['alpha_0.5'].central)}</td>
          <td className="pr-3 text-right">{fmt(r.wait_days.all.median, 0)} d</td>
          <td className="pr-3 text-right">{fmt(r.wait_days.all.p90, 0)} d</td>
          <td className="pr-3 text-right">{fmt(r.wait_days.small_scored.p90, 0)} d</td>
          <td className="pr-3 text-right">{fmt(r.over_max_wait_share * 100)}%</td>
          <td className="text-right">{fmt(r.wasted_hours_on_withdrawn, 0)} h</td>
        </tr>; })}</tbody>
      </table></div>
      <p>Almost all of the gain comes from ordering by carbon impact. The withdrawal-risk and effort terms change it by less than 2%; the fairness tiers trade part of the gain for shorter tails for small projects.</p>
    </Panel>}
    {d && section === 'distribution' && <div className="results-chart-grid">
      <Chart title="Median wait by group" subtitle={`${year} queue, simulated`} unit="days" labels={GROUPS.map(g => g[1])} series={[{ name: 'FIFO', values: GROUPS.map(g => fifo.wait_days[g[0]].median || 0), color: '#b6c9df' }, { name: 'CarbonQueue', values: GROUPS.map(g => cq.wait_days[g[0]].median || 0), color: '#00785b' }]} />
      <Chart title="P90 wait by group" subtitle="The slowest 10% of each group" unit="days" labels={GROUPS.map(g => g[1])} series={[{ name: 'FIFO', values: GROUPS.map(g => fifo.wait_days[g[0]].p90 || 0), color: '#b6c9df' }, { name: 'CarbonQueue', values: GROUPS.map(g => cq.wait_days[g[0]].p90 || 0), color: '#00785b' }]} />
    </div>}
    {d && section === 'carbon' && <Panel title={`Carbon gain vs FIFO, ${year} (ktCO₂e)`}>
      <div className="overflow-x-auto"><table className="w-full text-left text-body-sm">
        <thead><tr className="uppercase font-label-xs text-label-xs text-on-surface-variant"><th className="py-2 pr-3">Pass-through (α)</th><th className="pr-3 text-right">Low factor</th><th className="pr-3 text-right">Central factor</th><th className="text-right">High factor</th></tr></thead>
        <tbody className="divide-y divide-surface-container">{Object.entries(cq.carbon_gain_tco2_vs_fifo).map(([alpha, v]) => <tr key={alpha}><td className="py-2 pr-3">{Number(alpha.split('_')[1]) * 100}%</td><td className="pr-3 text-right">{kt(v.low)}</td><td className="pr-3 text-right font-semibold">{kt(v.central)}</td><td className="text-right">{kt(v.high)}</td></tr>)}</tbody>
      </table></div>
      <p>Emission factors (tCO₂e/MWh): low {cq.emission_factor_tco2_per_mwh.low} (grid average), central {cq.emission_factor_tco2_per_mwh.central} (long-run marginal), high {cq.emission_factor_tco2_per_mwh.high} (gas-fired). α is the share of an earlier permission that turns into earlier operation; it is an assumption, reported separately from the emission-factor uncertainty.</p>
    </Panel>}
    {d && section === 'setup' && <div className="results-chart-grid">
      <Panel title="Calibration">
        <dl className="settings-reference">
          <div><dt>Weekly reviewer capacity</dt><dd>{fmt(cq.calibration.capacity_hours_per_week, 0)} h (factor ×{cq.calibration.calibration_factor})</dd></div>
          <div><dt>Median decision time, real vs simulated FIFO</dt><dd>{fmt(cq.calibration.real_wait_median, 0)} / {fmt(cq.calibration.fifo_wait_median, 0)} days</dd></div>
          <div><dt>P90 decision time, real vs simulated FIFO</dt><dd>{fmt(cq.calibration.real_wait_p90, 0)} / {fmt(cq.calibration.fifo_wait_p90, 0)} days (not calibrated; a known limitation)</dd></div>
          <div><dt>Files · counted for carbon · outcome unknown</dt><dd>{cq.files} · {cq.carbon_files} · {cq.unresolved_files}</dd></div>
          <div><dt>Capacity share: unscored lane · small-project quota</dt><dd>{fmt(cq.lane_share.unscored * 100)}% · {fmt(cq.lane_share.small_quota * 100)}%</dd></div>
        </dl>
      </Panel>
      <Panel title="Assumptions">
        <dl className="settings-reference">
          <div><dt>Load factor (DUKES 2026, 2021–2025 mean)</dt><dd>Solar {cq.assumptions.carbon.load_factor.solar} · onshore wind {cq.assumptions.carbon.load_factor.onshore_wind}</dd></div>
          <div><dt>Emission factor year</dt><dd>Queue year + {cq.assumptions.carbon.operation_lag_years} years</dd></div>
          <div><dt>Effort rule</dt><dd>{cq.assumptions.effort.base} points base, +{cq.assumptions.effort.storage_component} storage, MW steps {cq.assumptions.effort.mw_steps.map(([mw, pts]) => `≥${mw} MW +${pts}`).join(', ')}; 1 point = {cq.assumptions.effort.hours_per_point} h</dd></div>
          <div><dt>Maximum wait</dt><dd>{cq.assumptions.queue.max_wait_days} days, up to {cq.assumptions.queue.max_wait_capacity_share * 100}% of capacity</dd></div>
          <div><dt>Small-project quota</dt><dd>Below {cq.assumptions.queue.small_project_mw} MW, {cq.assumptions.queue.small_quota_factor * 100}% of their effort share</dd></div>
          <div><dt>Single pool</dt><dd>One England-wide reviewer pool; authorities receive too few renewable files to reorder individually.</dd></div>
        </dl>
      </Panel>
    </div>}
  </div>;
}
