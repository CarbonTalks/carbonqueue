import React from 'react';

const go = id => e => { e.preventDefault(); document.getElementById(id).scrollIntoView({behavior:'smooth'}); };

export default function Methodology(){return <div className="workspace-page px-gutter-desktop py-space-xl">
  <header><span className="results-eyebrow">DOCUMENTATION</span><h1>Methodology</h1><p>How the queue is ordered, how carbon is estimated, and what the results mean.</p></header>
  <nav className="historical-section-picker" aria-label="Methodology topics"><a href="#method-queue" onClick={go('method-queue')}>Queue ordering</a><a href="#method-carbon" onClick={go('method-carbon')}>Carbon estimate</a><a href="#method-model" onClick={go('method-model')}>Prediction model</a><a href="#method-evidence" onClick={go('method-evidence')}>Document evidence</a><a href="#method-limits" onClick={go('method-limits')}>Limitations</a></nav>
  <section className="results-panel" id="method-queue"><h2>Queue ordering</h2><p>CarbonQueue is decision support: it orders which application a reviewer opens next. It never approves or refuses an application. Each week the reviewer capacity is spent in this order:</p><dl className="settings-reference">
    <div><dt>1. Maximum-wait protection</dt><dd>Files waiting more than 365 days, oldest first, using at most half of the weekly capacity.</dd></div>
    <div><dt>2. Unscored lane</dt><dd>Storage, bioenergy, other renewables and files without a stated capacity receive their share of effort, in submission order.</dd></div>
    <div><dt>3. Small-project quota</dt><dd>Projects under 1 MW are guaranteed half of their effort share.</dd></div>
    <div><dt>4. Carbon score</dt><dd>(1 − withdrawal probability) × daily tCO₂e displaced ÷ reviewer hours, highest first; ties in submission order.</dd></div>
  </dl><p>FIFO and carbon-only orders are produced by the same simulator with the same capacity, so the queue's position arrows compare like with like.</p></section>
  <section className="results-panel" id="method-carbon"><h2>Carbon estimate</h2><p>Daily tCO₂e = MW × 24 h × load factor × displacement emission factor. Load factors come from DUKES 2026 table 6.3 (2021–2025 mean: solar 0.105, onshore wind 0.248). Three emission factors give the range: grid average and long-run marginal (Green Book supplementary data, table 1) and gas-fired generation (DUKES 2026 table 5.14), read for the queue year + 2 years to reflect time to operation.</p><p>Historical carbon gain compares each policy with FIFO and counts only applications that were actually permitted and not abandoned. The pass-through share α (20 / 50 / 100%) is an assumption: how much of an earlier permission becomes earlier operation.</p></section>
  <section className="results-panel" id="method-model"><h2>Prediction model</h2><p>A discrete-time CatBoost model trained on the UK Renewable Energy Planning Database predicts, from information known at submission, the probability of withdrawal within 12 months and the distribution of the decision date. It does not predict permission or refusal. Withdrawal prediction is weak (ROC-AUC 0.54–0.64) and changes the order by less than 2%; decision-time prediction beats a technology/recent-years baseline by 12–14%.</p></section>
  <section className="results-panel" id="method-evidence"><h2>Document evidence</h2><p>The extraction agent reads planning PDFs and records every value with its document, page and quote. Quotes are checked against the parsed text. Capacities that refer to a neighbouring scheme, an earlier permission or a grid connection are rejected; when no supported value remains, the field is marked missing and a reviewer enters it. Every correction is stored with the original values, actor, time and reason.</p></section>
  <section className="results-panel" id="method-limits"><h2>Limitations</h2><dl className="settings-reference">
    <div><dt>Single reviewer pool</dt><dd>Authorities receive only a few renewable files a year, so the simulation assumes one England-wide pool.</dd></div>
    <div><dt>Calibration</dt><dd>Capacity is calibrated to the observed median decision time; the slowest tail (P90) is not reproduced.</dd></div>
    <div><dt>Sensitivity to capacity</dt><dd>The gain grows when the queue is more congested; results should be read as a range, not a single number.</dd></div>
    <div><dt>Effort</dt><dd>Reviewer hours per file are not public; effort is rule-based.</dd></div>
  </dl></section>
  </div>;}
