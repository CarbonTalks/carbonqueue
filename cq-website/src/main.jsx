import React, {useState, useEffect, useRef} from 'react';
import {createRoot} from 'react-dom/client';
import {AppContext, projects as sampleProjects, Icon} from './state.jsx';
import Queue from './pages/Queue.jsx';
import Project from './pages/Project.jsx';
import Upload from './pages/Upload.jsx';
import Results from './pages/Results.jsx';
import Settings from './pages/Settings.jsx';
import Methodology from './pages/Methodology.jsx';
import './styles.css';
import { compareQueueProjects } from './queue-sort.js';
import {readResultsLocation} from './results-navigation.js';

const routes = ['queue','project','upload','results','settings','methodology'];
const currentRoute = () => location.hash.slice(2).split('?')[0]==='simulation' ? 'results' : routes.includes(location.hash.slice(2).split('?')[0]) ? location.hash.slice(2).split('?')[0] : 'queue';
const defaultSettings={name:'Demo workspace',policy:4,view:'table',compact:false};
function loadSettings(){try{const saved=JSON.parse(localStorage.getItem('carbonqueue-settings'));return {name:typeof saved?.name==='string'?saved.name.slice(0,48):defaultSettings.name,policy:Number.isInteger(saved?.policy)&&saved.policy>=0&&saved.policy<=4?saved.policy:4,view:saved?.view==='gantt'?'gantt':'table',compact:saved?.compact===true};}catch{return defaultSettings;}}
function App() {
  const [settings,setSettings]=useState(loadSettings);
  function saveSettings(next){localStorage.setItem('carbonqueue-settings',JSON.stringify(next));setSettings(next);setPolicy(next.policy);setView(next.view);setSort(null);}
  const [route,setRoute]=useState(currentRoute), [search,setSearch]=useState(''), [filters,setFilters]=useState([0,0,0]);
  const [policy,setPolicy]=useState(settings.policy), [view,setView]=useState(settings.view), [field,setField]=useState(null), [breakdown,setBreakdown]=useState('tech');
  const [modal,setModal]=useState(null), [notice,setNotice]=useState(''), [mobile,setMobile]=useState(false), [queued,setQueued]=useState(false);
  const [files,setFiles]=useState([]), [editing,setEditing]=useState(null), [editValue,setEditValue]=useState('');
  const [fieldValues,setFieldValues]=useState({});
  const editField=data=>{setEditing(data);setEditValue(data[1]);};
  const [resultsLocation,setResultsLocation]=useState(readResultsLocation);
  const fileInput=useRef(null);
  const [sort,setSort]=useState(null), [navCollapsed,setNavCollapsed]=useState(false);
  const toggleNavigation=()=>window.matchMedia('(max-width:760px)').matches?setMobile(open=>!open):setNavCollapsed(collapsed=>!collapsed);
  const toggleSort=key=>setSort(s=>({key,direction:s?.key===key?(s.direction==='asc'?'desc':'asc'):(key==='capacity'?'desc':'asc')}));
  useEffect(()=> {const cb=()=>{setRoute(currentRoute());setResultsLocation(readResultsLocation());setMobile(false);window.scrollTo(0,0);};window.addEventListener('hashchange',cb);return ()=>window.removeEventListener('hashchange',cb);},[]);
  useEffect(()=>{if(notice){const timer=setTimeout(()=>setNotice(''),4500);return ()=>clearTimeout(timer);}},[notice]);
  const navigate = r => {location.hash='/'+r;};
  const visible=sampleProjects.filter(p=>`${p.name} ${p.id} ${p.developer}`.toLowerCase().includes(search.toLowerCase()) && (!filters[0] || p.tech===['','Solar PV','Wind','Battery BESS','EV Depot','Heat Pump','Hydro'][filters[0]]) && (!filters[1] || (filters[1]===1?p.capacity>0&&p.capacity<5:filters[1]===2?p.capacity>=5&&p.capacity<=25:p.capacity>25)) && (!filters[2] || p.wait>(filters[2]===1?90:120))).sort((a,b)=>policy===0?b.wait-a.wait:policy===1?b.carbon[0]-a.carbon[0]:policy===2?a.risk-b.risk:policy===3?a.effort-b.effort:sampleProjects.indexOf(a)-sampleProjects.indexOf(b));
  function openProject(p) {if(p.name==='Riverside Solar') navigate('project'); else setModal({title:p.name,body:`${p.id} · ${p.developer}\nTechnology: ${p.tech}\nCapacity: ${p.capacity || '—'} MW\nModeled carbon: ${p.carbon.join('–')} tCO₂e/day\nEstimated review: ${p.effort} h\nWaiting: ${p.wait} days\nWithdrawal risk: ${p.risk}%`});}
  function exportCsv() {
    const rows=route==='results'?[['Metric','FIFO','CarbonQueue'],['Median wait (days)',74,51],['P90 wait (days)',188,142],['Review effort (hours)',96,61]]:[['Project','Application','Technology','Capacity MW','Wait days','Review hours'],...visible.map(p=>[p.name,p.id,p.tech,p.capacity,p.wait,p.effort])];
    const blob=new Blob([rows.map(r=>r.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'});
    const url=URL.createObjectURL(blob), a=document.createElement('a');a.href=url;a.download=`carbonqueue-${route}-demo.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);setNotice('CSV exported.');
  }
  function addFiles(list) {
    const accepted=Array.from(list).filter(f=>/\.(pdf|xlsx|docx)$/i.test(f.name)&&f.size<=60*1024*1024);
    setFiles(prev=>[...prev,...accepted]);setNotice(accepted.length?`${accepted.length} file(s) selected locally. Document extraction requires a backend connection.`:'Choose PDF, XLSX or DOCX files up to 60 MB.');
  }
  function handleClick(e) {
    const fieldEl=e.target.closest('[data-field]');
    if(fieldEl) {
      const data=JSON.parse(decodeURIComponent(fieldEl.dataset.field));setField(data);
      if(e.target.closest('button')?.textContent.trim()==='Edit') {setEditing(data);setEditValue(data[1]);}
    }
    const target=e.target.closest('button,a');if(!target)return;
    const label=target.textContent.trim();
    if(target.tagName==='A' && target.getAttribute('href')==='#')e.preventDefault();
    if(target.classList.contains('policy-tab')){setSort(null);setPolicy(Number(label.match(/[1-5]/)?.[0]||5)-1);return;}
    if(label.includes('Export'))exportCsv();
    else if(label.includes('View Results'))navigate('results');
    else if(label.includes('Run Simulation')) {if(route!=='results')navigate('results');else setNotice('Demo results displayed for the 2021 cohort. Live simulation requires a backend connection.');}
    else if(label.includes('Back to Queue')||label==='Cancel')navigate('queue');
    else if(label.includes('Table View'))setView('table');
    else if(label.includes('Queue Gantt'))setView('gantt');
    else if(label.includes('Browse files'))fileInput.current.click();
    else if(target.id==='tab-btn-tech')setBreakdown('tech');
    else if(target.id==='tab-btn-size')setBreakdown('size');
    else if(target.id==='queue-btn') {setQueued(true);setNotice('Riverside Solar is already in the demo queue. Review confirmation saved for this session.');}
    else if(label.includes('Save for Review')){localStorage.setItem('carbonqueue-draft',JSON.stringify({field,fieldValues,files:files.map(f=>f.name)}));setNotice('Draft saved in this browser.');}
    else if(label.includes('View source')||label.includes('View source documents'))navigate('upload');
    else if(label.includes('Audit log'))setModal({title:'Demo audit log',body:'Application imported · 14 May 2024\nSchema validated · 7 required fields\nReview policy · CarbonQueue Hybrid v2.4\nMaximum-wait protection applied · 126 days waiting'});
    else if(/methodology|assumptions/i.test(label)&&target.getAttribute('href')==='#')navigate('methodology');
    else if(label.includes('Advanced settings'))setModal({title:'Simulation configuration',body:'Reference cohort: 2021\nWeekly review capacity: 320 hours\nMaximum wait: 180 days\nScenario: Central\n\nHistorical values in this prototype are fixed reference data.'});
    else if(/Open PDF|Open original|Zoom in/.test(label+' '+target.title))setModal({title:'Source document preview',body:'This preview is included in the supplied design. The original PDF was not included in the design archive. Select your documents with Browse files to attach them locally.'});
    else if(/^20(19|20|21|22|23)/.test(label))setNotice('Only the 2021 reference cohort is included in the supplied demo.');
    else if(label.includes('Add value')){setEditing(['Site Area','']);setEditValue('');}
    else if(target.title?.includes('citation'))setNotice('Select a field in Extracted Project Data to inspect its citation.');
  }
  if(sort) visible.sort((a,b)=>compareQueueProjects(a,b,sort));
  const ctx={settings,saveSettings,resultsLocation,fieldValues,editField,sort,toggleSort,setSort,filters,search,setSearch,setFilter:(i,n)=>setFilters(f=>f.map((v,j)=>i===j?n:v)),policy,visible,view,field,breakdown,queued,projects:sampleProjects,openProject};
  const Page={queue:Queue,project:Project,upload:Upload,results:Results,settings:Settings,methodology:Methodology}[route];
  return <AppContext.Provider value={ctx}>
    <aside id="main-navigation" className={'sidebar '+(mobile?'is-open ':'')+(navCollapsed?'is-collapsed':'')}>
      <button type="button" className="brand" aria-label="Toggle navigation" aria-controls="main-navigation" aria-expanded={mobile || !navCollapsed} onClick={toggleNavigation}><span className="brand-mark"><img src="/carbonqueue-logo.svg" width="36" height="36" alt="" aria-hidden="true" /></span><span className="brand-name"><strong>CarbonQueue</strong><small>PUBLIC ENERGY AUTHORITY</small></span></button>
      <div className="nav-group">{[['queue','format_list_numbered','Queue'],['upload','cloud_upload','Upload'],['results','bar_chart','Results']].map(([r,icon,label])=><a key={r} href={'#/'+r} aria-current={route===r?'page':undefined} className={route===r||r==='queue'&&route==='project'?'active':''}><Icon>{icon}</Icon>{label}</a>)}</div>
      <div className="nav-bottom"><div className="nav-group"><small>DOCUMENTATION & OPS</small>{[['methodology','menu_book','Methodology'],['settings','settings','Settings']].map(([r,icon,label])=><a key={r} href={'#/'+r} className={route===r?'active':''} aria-current={route===r?'page':undefined}><Icon>{icon}</Icon><span>{label}</span></a>)}</div><div className="jurisdiction"><Icon>verified_user</Icon><div><small>JURISDICTION CONTEXT</small><strong>State Energy & Infrastructure Authority</strong></div></div></div>
    </aside>
    {mobile&&<button className="mobile-overlay" aria-label="Close navigation" onClick={()=>setMobile(false)}/>}
    <header className={'topbar '+(navCollapsed?'nav-collapsed':'')}><button type="button" className="mobile-brand-toggle brand-mark" aria-label="Toggle navigation" aria-controls="main-navigation" aria-expanded={mobile} onClick={toggleNavigation}><img src="/carbonqueue-logo.svg" width="36" height="36" alt="" aria-hidden="true" /></button><div className="profile"><div><strong>Dr. Elena Vance</strong><small>Senior Grid Analyst</small></div><span className="avatar">EV</span></div></header>
    <main className={'app-main '+(navCollapsed?'nav-collapsed ':'')+(settings.compact?'compact-tables':'')} onClick={handleClick} onDragOver={e=>{if(route==='upload')e.preventDefault();}} onDrop={e=>{if(route==='upload'){e.preventDefault();addFiles(e.dataTransfer.files);}}}>
      <Page/>
      {route==='upload'&&files.length>0&&<section className="local-files"><h2>Locally selected documents</h2><p>Files are kept in this session; extraction is not connected.</p>{files.map((f,i)=><div key={i}>{f.name} · {(f.size/1024).toFixed(0)} KB <button onClick={()=>setFiles(fs=>fs.filter((_,j)=>j!==i))}>Remove</button></div>)}</section>}
    </main>
    <input ref={fileInput} type="file" accept=".pdf,.xlsx,.docx" multiple hidden onChange={e=>{addFiles(e.target.files);e.target.value='';}}/>
    {notice&&<div className="toast" role="status">{notice}<button onClick={()=>setNotice('')} aria-label="Dismiss">×</button></div>}
    {(modal||editing)&&<div className="modal-overlay" onClick={()=>{setModal(null);setEditing(null);}}><section role="dialog" aria-modal="true" aria-labelledby="dialog-title" className="modal" onClick={e=>e.stopPropagation()} onKeyDown={e=>{if(e.key==='Escape'){setModal(null);setEditing(null);}}}><button autoFocus className="close" aria-label="Close dialog" onClick={()=>{setModal(null);setEditing(null);}}>×</button><h2 id="dialog-title">{editing?`Edit ${editing[0]}`:modal.title}</h2>{editing?<form onSubmit={e=>{e.preventDefault();const changed=[...editing];changed[1]=editValue;setField(changed);setFieldValues(values=>({...values,[changed[0]]:changed[1]}));setEditing(null);setNotice('Inspector value updated for this session.');}}><label>Value<input autoFocus required value={editValue} onChange={e=>setEditValue(e.target.value)}/></label><button className="save">Save value</button></form>:<p>{modal.body}</p>}</section></div>}
  </AppContext.Provider>;
}
createRoot(document.getElementById('root')).render(<App/>);
