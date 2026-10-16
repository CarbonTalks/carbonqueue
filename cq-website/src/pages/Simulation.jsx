import React, { useState } from 'react';
import { useHistorical, HISTORICAL_POLICIES } from '../api.js';
import { fmt } from '../live-data.js';
import { Chart } from '../chart.jsx';
import { useT } from '../i18n.jsx';

const YEARS = [2019, 2020, 2021, 2022, 2023];
const NAMES = { fifo: 'FIFO', carbon: 'Carbon only', carbon_withdrawal: '+ Withdrawal risk', carbon_withdrawal_effort: '+ Effort', carbonqueue: 'CarbonQueue' };
const GROUPS = [['all', 'All files'], ['small_scored', 'Small (<1 MW)'], ['large_scored', 'Large scored'], ['unscored', 'Unscored']];
const kt = v => fmt(v / 1000, 1);

function Kpi({ label, value, unit, note }) {
  return <div className="results-kpi"><div className="results-kpi-label"><span>{label}</span></div><div className="results-kpi-value">{value}<small>{unit}</small></div><div className="results-kpi-bottom"><span>{note}</span></div></div>;
}
function Panel({ title, children }) { return <section className="results-panel"><h2>{title}</h2>{children}</section>; }

export default function Simulation({ section = 'summary' }) {
  const { t } = useT();
  const [year, setYear] = useState(2023);
  const history = useHistorical(year);
  const d = history.data;
  const cq = d?.carbonqueue, fifo = d?.fifo;
  const days = t('days'), d_ = t('d');
  return <div className="flex flex-col gap-space-lg">
    <div className="results-archive-note"><span className="material-symbols-outlined" aria-hidden="true">history</span>
      <span>{t('Replay of a real English queue with each policy, same calibrated capacity and effort rules. Carbon counts only applications that were actually permitted.')}</span>
      <label className="results-week ml-auto">{t('Queue year')}<select value={year} onChange={e => setYear(Number(e.target.value))}>{YEARS.map(y => <option key={y} value={y}>{y}{y < 2021 ? ` (${t('small queue')})` : ''}</option>)}</select></label>
    </div>
    {history.status === 'loading' && <Panel title={t('Loading')}>{t('Loading {y} results…', { y: year })}</Panel>}
    {history.status === 'error' && <Panel title={t('Historical results unavailable')}><p>{t(history.error.message)}. {t('Set CQ_SIMULATION_RESULTS_DIR in the backend (see README).')}</p></Panel>}
    {d && section === 'summary' && <>
      <div className="results-kpis">
        <Kpi label={t('Carbon gain vs FIFO')} value={kt(cq.carbon_gain_tco2_vs_fifo['alpha_0.5'].central)} unit="ktCO₂e" note={t('Range {a}–{b} kt', { a: kt(cq.carbon_gain_tco2_vs_fifo['alpha_0.2'].low), b: kt(cq.carbon_gain_tco2_vs_fifo['alpha_1.0'].high) })} />
        <Kpi label={t('Median wait')} value={fmt(cq.wait_days.all.median, 0)} unit={days} note={t('FIFO {d} days', { d: fmt(fifo.wait_days.all.median, 0) })} />
        <Kpi label={t('P90 wait')} value={fmt(cq.wait_days.all.p90, 0)} unit={days} note={t('FIFO {d} days', { d: fmt(fifo.wait_days.all.p90, 0) })} />
        <Kpi label={t('Small projects, P90 wait')} value={fmt(cq.wait_days.small_scored.p90, 0)} unit={days} note={t('FIFO {a} · carbon only {b}', { a: fmt(fifo.wait_days.small_scored.p90, 0), b: fmt(d.carbon.wait_days.small_scored.p90, 0) })} />
      </div>
      <Panel title={t('Reading the result')}>
        <p>{t('CarbonQueue reviews high-impact projects earlier without adding reviewers: across the {n} files of the {y} queue, earlier permissions shift about {g} kt of displaced emissions forward (central emission factor, 50% of earlier permission passed through to earlier operation).', { n: fmt(cq.files, 0), y: year, g: kt(cq.carbon_gain_tco2_vs_fifo['alpha_0.5'].central) })}</p>
        <p>{t('Fairness protections cost part of the gain: carbon-only ordering reaches {g} kt but pushes the slowest small projects to {p} days.', { g: kt(d.carbon.carbon_gain_tco2_vs_fifo['alpha_0.5'].central), p: fmt(d.carbon.wait_days.small_scored.p90, 0) })}</p>
      </Panel>
    </>}
    {d && section === 'comparison' && <Panel title={t('What changes as policy components are added?')}>
      <div className="overflow-x-auto"><table className="w-full text-left text-body-sm">
        <thead><tr className="uppercase font-label-xs text-label-xs text-on-surface-variant"><th className="py-2 pr-3">{t('Policy')}</th><th className="pr-3 text-right">{t('Carbon gain (kt)')}</th><th className="pr-3 text-right">{t('Median wait')}</th><th className="pr-3 text-right">{t('P90 wait')}</th><th className="pr-3 text-right">{t('Small P90')}</th><th className="pr-3 text-right">{t('Over 365 days')}</th><th className="text-right">{t('Hours on withdrawn files')}</th></tr></thead>
        <tbody className="divide-y divide-surface-container">{HISTORICAL_POLICIES.map(p => { const r = d[p]; return <tr key={p} className={p === 'carbonqueue' ? 'font-semibold' : ''}>
          <td className="py-2 pr-3">{t(NAMES[p])}</td>
          <td className="pr-3 text-right">{p === 'fifo' ? '—' : kt(r.carbon_gain_tco2_vs_fifo['alpha_0.5'].central)}</td>
          <td className="pr-3 text-right">{fmt(r.wait_days.all.median, 0)} {d_}</td>
          <td className="pr-3 text-right">{fmt(r.wait_days.all.p90, 0)} {d_}</td>
          <td className="pr-3 text-right">{fmt(r.wait_days.small_scored.p90, 0)} {d_}</td>
          <td className="pr-3 text-right">{fmt(r.over_max_wait_share * 100)}%</td>
          <td className="text-right">{fmt(r.wasted_hours_on_withdrawn, 0)} {t('h')}</td>
        </tr>; })}</tbody>
      </table></div>
      <p>{t('Almost all of the gain comes from ordering by carbon impact. The withdrawal-risk and effort terms change it by less than 2%; the fairness tiers trade part of the gain for shorter tails for small projects.')}</p>
    </Panel>}
    {d && section === 'distribution' && <div className="results-chart-grid">
      <Chart title={t('Median wait by group')} subtitle={t('{y} queue, simulated', { y: year })} unit={days} labels={GROUPS.map(g => t(g[1]))} series={[{ name: 'FIFO', values: GROUPS.map(g => fifo.wait_days[g[0]].median || 0), color: '#b6c9df' }, { name: 'CarbonQueue', values: GROUPS.map(g => cq.wait_days[g[0]].median || 0), color: '#00785b' }]} />
      <Chart title={t('P90 wait by group')} subtitle={t('The slowest 10% of each group')} unit={days} labels={GROUPS.map(g => t(g[1]))} series={[{ name: 'FIFO', values: GROUPS.map(g => fifo.wait_days[g[0]].p90 || 0), color: '#b6c9df' }, { name: 'CarbonQueue', values: GROUPS.map(g => cq.wait_days[g[0]].p90 || 0), color: '#00785b' }]} />
    </div>}
    {d && section === 'carbon' && <Panel title={t('Carbon gain vs FIFO, {y} (ktCO₂e)', { y: year })}>
      <div className="overflow-x-auto"><table className="w-full text-left text-body-sm">
        <thead><tr className="uppercase font-label-xs text-label-xs text-on-surface-variant"><th className="py-2 pr-3">{t('Pass-through (α)')}</th><th className="pr-3 text-right">{t('Low factor')}</th><th className="pr-3 text-right">{t('Central factor')}</th><th className="text-right">{t('High factor')}</th></tr></thead>
        <tbody className="divide-y divide-surface-container">{Object.entries(cq.carbon_gain_tco2_vs_fifo).map(([alpha, v]) => <tr key={alpha}><td className="py-2 pr-3">{Number(alpha.split('_')[1]) * 100}%</td><td className="pr-3 text-right">{kt(v.low)}</td><td className="pr-3 text-right font-semibold">{kt(v.central)}</td><td className="text-right">{kt(v.high)}</td></tr>)}</tbody>
      </table></div>
      <p>{t('Emission factors (tCO₂e/MWh): low {l} (grid average), central {c} (long-run marginal), high {h} (gas-fired). α is the share of an earlier permission that turns into earlier operation; it is an assumption, reported separately from the emission-factor uncertainty.', { l: cq.emission_factor_tco2_per_mwh.low, c: cq.emission_factor_tco2_per_mwh.central, h: cq.emission_factor_tco2_per_mwh.high })}</p>
    </Panel>}
    {d && section === 'setup' && <div className="results-chart-grid">
      <Panel title={t('Calibration')}>
        <dl className="settings-reference">
          <div><dt>{t('Weekly reviewer capacity')}</dt><dd>{fmt(cq.calibration.capacity_hours_per_week, 0)} {t('h')} (×{cq.calibration.calibration_factor})</dd></div>
          <div><dt>{t('Median decision time, real vs simulated FIFO')}</dt><dd>{fmt(cq.calibration.real_wait_median, 0)} / {fmt(cq.calibration.fifo_wait_median, 0)} {days}</dd></div>
          <div><dt>{t('P90 decision time, real vs simulated FIFO')}</dt><dd>{fmt(cq.calibration.real_wait_p90, 0)} / {fmt(cq.calibration.fifo_wait_p90, 0)} {days} ({t('not calibrated; a known limitation')})</dd></div>
          <div><dt>{t('Files · counted for carbon · outcome unknown')}</dt><dd>{cq.files} · {cq.carbon_files} · {cq.unresolved_files}</dd></div>
          <div><dt>{t('Capacity share: unscored lane · small-project quota')}</dt><dd>{fmt(cq.lane_share.unscored * 100)}% · {fmt(cq.lane_share.small_quota * 100)}%</dd></div>
        </dl>
      </Panel>
      <Panel title={t('Assumptions')}>
        <dl className="settings-reference">
          <div><dt>{t('Load factor (DUKES 2026, 2021–2025 mean)')}</dt><dd>{t('Solar {s} · onshore wind {w}', { s: cq.assumptions.carbon.load_factor.solar, w: cq.assumptions.carbon.load_factor.onshore_wind })}</dd></div>
          <div><dt>{t('Emission factor year')}</dt><dd>{t('Queue year + {n} years', { n: cq.assumptions.carbon.operation_lag_years })}</dd></div>
          <div><dt>{t('Effort rule')}</dt><dd>{t('{b} points base, +{s} storage, MW steps {m}; 1 point = {h} h', { b: cq.assumptions.effort.base, s: cq.assumptions.effort.storage_component, m: cq.assumptions.effort.mw_steps.map(([mw, pts]) => `≥${mw} MW +${pts}`).join(', '), h: cq.assumptions.effort.hours_per_point })}</dd></div>
          <div><dt>{t('Maximum wait')}</dt><dd>{t('{d} days, up to {s}% of capacity', { d: cq.assumptions.queue.max_wait_days, s: cq.assumptions.queue.max_wait_capacity_share * 100 })}</dd></div>
          <div><dt>{t('Small-project quota')}</dt><dd>{t('Below {mw} MW, {f}% of their effort share', { mw: cq.assumptions.queue.small_project_mw, f: cq.assumptions.queue.small_quota_factor * 100 })}</dd></div>
          <div><dt>{t('Single pool')}</dt><dd>{t('One England-wide reviewer pool; authorities receive too few renewable files to reorder individually.')}</dd></div>
        </dl>
      </Panel>
    </div>}
  </div>;
}
