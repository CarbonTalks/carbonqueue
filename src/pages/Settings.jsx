import React, {useState} from 'react';
import {useApp} from '../state.jsx';

export default function Settings(){
  const ctx=useApp(), [draft,setDraft]=useState(ctx.settings), [message,setMessage]=useState('');
  const update=(key,value)=>{setDraft(s=>({...s,[key]:value}));setMessage('');};
  return <div className="workspace-page px-gutter-desktop py-space-xl">
    <header><span className="results-eyebrow">WORKSPACE</span><h1>Settings</h1><p>Customize your workspace and default queue view.</p></header>
    <form onSubmit={e=>{e.preventDefault();e.stopPropagation();try{ctx.saveSettings({...draft,name:draft.name.trim()||'Demo workspace'});setMessage('Settings saved. Queue defaults applied.');}catch{setMessage('Settings could not be saved in this browser. Please try again.');}}}>
      <section className="results-panel"><h2>Workspace preferences</h2><div className="settings-fields">
        <label>Workspace name<input required maxLength={48} value={draft.name} onChange={e=>update('name',e.target.value)}/></label>
        <label>Default review policy<select value={draft.policy} onChange={e=>update('policy',Number(e.target.value))}><option value={0}>FIFO</option><option value={1}>Carbon Only</option><option value={2}>Carbon + Withdrawal Risk</option><option value={3}>Carbon + Risk + Effort</option><option value={4}>CarbonQueue</option></select></label>
        <label>Default queue view<select value={draft.view} onChange={e=>update('view',e.target.value)}><option value="table">Table View</option><option value="gantt">Queue Gantt</option></select></label>
        <label className="settings-checkbox"><input type="checkbox" checked={draft.compact} onChange={e=>update('compact',e.target.checked)}/><span>Compact table rows</span></label>
      </div><p>Saved in this browser. Saving also applies the selected policy and view to the current queue.</p></section>
      <section className="results-panel"><h2>Demo reference configuration</h2><p>These values belong to the included sample dataset.</p><dl className="settings-reference"><div><dt>Weekly reviewer capacity</dt><dd>320 hours</dd></div><div><dt>Maximum-wait threshold</dt><dd>180 days</dd></div><div><dt>Historical reference cohort</dt><dd>2021</dd></div><div><dt>Data connection</dt><dd>Demo · no live connection</dd></div></dl></section>
      <div className="settings-actions"><span role="status">{message}</span><button type="button" className="queue-control" onClick={()=>{setDraft(ctx.settings);setMessage('Unsaved changes discarded.');}}>Discard changes</button><button type="submit" className="settings-save">Save settings</button></div>
    </form>
  </div>;
}
