import React, {useState} from 'react';
import {useApp} from '../state.jsx';
import {API_URL} from '../api.js';
import {LIVE_POLICIES, fmt} from '../live-data.js';

export default function Settings(){
  const ctx=useApp(), [draft,setDraft]=useState(ctx.settings), [message,setMessage]=useState('');
  const update=(key,value)=>{setDraft(s=>({...s,[key]:value}));setMessage('');};
  const live=ctx.live.status==='ready'?ctx.live.data:null;
  return <div className="workspace-page px-gutter-desktop py-space-xl">
    <header><span className="results-eyebrow">WORKSPACE</span><h1>Settings</h1><p>Customize your workspace and default queue view.</p></header>
    <form onSubmit={e=>{e.preventDefault();try{ctx.saveSettings({...draft,name:draft.name.trim()||'Demo workspace'});setMessage('Settings saved. Queue defaults applied.');}catch{setMessage('Settings could not be saved in this browser. Please try again.');}}}>
      <section className="results-panel"><h2>Workspace preferences</h2><div className="settings-fields">
        <label>Workspace name<input required maxLength={48} value={draft.name} onChange={e=>update('name',e.target.value)}/></label>
        <label>Default review policy<select value={draft.policy} onChange={e=>update('policy',Number(e.target.value))}>{LIVE_POLICIES.map((p,i)=><option key={p.key} value={i}>{p.label}</option>)}</select></label>
        <label>Default queue view<select value={draft.view} onChange={e=>update('view',e.target.value)}><option value="table">Table view</option><option value="gantt">Planned weeks</option></select></label>
        <label className="settings-checkbox"><input type="checkbox" checked={draft.compact} onChange={e=>update('compact',e.target.checked)}/><span>Compact table rows</span></label>
      </div><p>Saved in this browser.</p></section>
      <section className="results-panel"><h2>Data connection</h2><dl className="settings-reference">
        <div><dt>Backend</dt><dd>{API_URL} · {ctx.live.status==='ready'?'connected':ctx.live.status==='loading'?'connecting':'unavailable'}</dd></div>
        <div><dt>Live queue snapshot</dt><dd>{live?`${live.as_of} · ${live.files.length} ranked, ${live.needs_confirmation.length} awaiting confirmation`:'—'}</dd></div>
        <div><dt>Weekly reviewer capacity</dt><dd>{live?`${fmt(live.calibration.capacity_hours_per_week,0)} hours (calibration year ${live.calibration.calibration_year})`:'—'}</dd></div>
        <div><dt>Emission factors used (tCO₂e/MWh)</dt><dd>{live?Object.entries(live.emission_factor_tco2_per_mwh).map(([k,v])=>`${k} ${v}`).join(' · '):'—'}</dd></div>
      </dl></section>
      <div className="settings-actions"><span role="status">{message}</span><button type="button" className="queue-control" onClick={()=>{setDraft(ctx.settings);setMessage('Unsaved changes discarded.');}}>Discard changes</button><button type="submit" className="settings-save">Save settings</button></div>
    </form>
  </div>;
}
