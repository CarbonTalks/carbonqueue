import React from 'react';
import { useApp } from '../state.jsx';
export default function Upload() { const ctx = useApp();
  return (<div className="flex flex-col w-full">
  <div className="px-gutter-desktop py-space-xl max-w-[1600px] mx-auto w-full flex flex-col gap-space-xl">
    <div className="flex flex-col gap-space-lg">
      <div className="flex flex-col gap-space-xs">
        <div className="flex items-center gap-space-sm">
          <span className="font-headline-lg text-headline-lg text-on-surface">Application Intake</span>
          <span className="bg-secondary-container text-on-secondary-container font-label-xs text-label-xs px-2.5 py-0.5 rounded-full uppercase tracking-wider font-semibold">AI-Assisted Document Inspection</span>
        </div>
        <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
          Extract, verify, and cross-reference structured project parameters from application dossiers against statutory intake schemas.
        </p>
      </div>
      <nav className="intake-progress" aria-label="Application progress">
        <ol>
          <li className="complete"><span className="intake-step-icon material-symbols-outlined" aria-hidden="true">check</span><div><span className="intake-step-label">Step 01 · Complete</span><strong>Documents</strong></div></li>
          <li className="complete"><span className="intake-step-icon material-symbols-outlined" aria-hidden="true">check</span><div><span className="intake-step-label">Step 02 · Complete</span><strong>Extraction</strong></div></li>
          <li className="current" aria-current="step"><span className="intake-step-icon" aria-hidden="true">3</span><div><span className="intake-step-label">Step 03 · Current</span><strong>Review &amp; Confirm</strong></div></li>
        </ol>
      </nav>
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg items-stretch">
      <div className="lg:col-span-4 bg-surface-container-lowest p-space-lg rounded-xl shadow-sm flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-space-sm">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-wider font-semibold">Intake Docket</span>
            <span className="font-label-xs text-label-xs text-secondary font-semibold">3 Files Synced</span>
          </div>
          <div className="bg-surface-container-low hover:bg-surface-container transition-colors rounded-lg p-space-md flex flex-col items-center justify-center text-center cursor-pointer group">
            <div className="w-10 h-10 rounded-full bg-surface-container-highest flex items-center justify-center text-primary mb-2 group-hover:scale-105 transition-transform">
              <span className="material-symbols-outlined text-[20px]">upload_file</span>
            </div>
            <p className="font-label-md text-label-md text-on-surface font-semibold">Drop application documents here</p>
            <p className="font-label-xs text-label-xs text-on-surface-variant mt-0.5">PDF, XLSX, or DOCX (Max 60MB)</p>
            <button className="mt-2.5 px-3 py-1 bg-surface-container-lowest text-on-surface font-label-md text-label-md font-medium rounded shadow-sm hover:bg-surface transition-colors">
              Browse files
            </button>
          </div>
        </div>
        <div className="flex flex-col gap-1.5 mt-space-md pt-space-sm">
          <div className="flex items-center justify-between text-body-sm font-body-sm bg-surface-container-low px-2.5 py-1.5 rounded">
            <div className="flex items-center gap-2 truncate">
              <span className="material-symbols-outlined text-[16px] text-error">picture_as_pdf</span>
              <span className="truncate font-medium text-on-surface">Technical Report.pdf</span>
              <span className="text-on-surface-variant text-[11px]">2.4 MB</span>
            </div>
            <span className="bg-secondary-container text-on-secondary-container text-[10px] px-1.5 py-0.5 rounded font-semibold uppercase shrink-0">Processed</span>
          </div>
          <div className="flex items-center justify-between text-body-sm font-body-sm bg-surface-container-low px-2.5 py-1.5 rounded">
            <div className="flex items-center gap-2 truncate">
              <span className="material-symbols-outlined text-[16px] text-error">picture_as_pdf</span>
              <span className="truncate font-medium text-on-surface">Application Form.pdf</span>
              <span className="text-on-surface-variant text-[11px]">840 KB</span>
            </div>
            <span className="bg-secondary-container text-on-secondary-container text-[10px] px-1.5 py-0.5 rounded font-semibold uppercase shrink-0">Processed</span>
          </div>
          <div className="flex items-center justify-between text-body-sm font-body-sm bg-surface-container-low px-2.5 py-1.5 rounded">
            <div className="flex items-center gap-2 truncate">
              <span className="material-symbols-outlined text-[16px] text-secondary">table_view</span>
              <span className="truncate font-medium text-on-surface">Project Timeline.xlsx</span>
              <span className="text-on-surface-variant text-[11px]">126 KB</span>
            </div>
            <span className="bg-secondary-container text-on-secondary-container text-[10px] px-1.5 py-0.5 rounded font-semibold uppercase shrink-0">Processed</span>
          </div>
        </div>
      </div>
      <div className="lg:col-span-8 bg-surface-container-lowest p-space-lg rounded-xl shadow-sm flex flex-col justify-between">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm pb-space-md">
          <div className="flex items-center gap-space-sm">
            <div className="w-8 h-8 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center">
              <span className="material-symbols-outlined text-[18px]">done_all</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-title-sm text-title-sm text-on-surface">Extraction Run Complete</span>
                <span className="bg-secondary-container text-on-secondary-container font-label-xs text-label-xs px-2 py-0.5 rounded-full font-semibold">Ready for review</span>
              </div>
              <p className="font-label-xs text-label-xs text-on-surface-variant">All required schema fields mapped to source citations in submitted dossier.</p>
            </div>
          </div>
          <span className="font-label-xs text-label-xs text-on-surface-variant bg-surface-container px-2.5 py-1 rounded">Model: CQ-GridParser v2.4 (Deterministic)</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-space-sm mt-space-sm">
          <div className="bg-surface-container-low p-space-md rounded-lg flex flex-col">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-wider">Documents Analyzed</span>
            <span className="font-metric-num text-metric-num text-on-surface mt-1">3</span>
            <span className="font-label-xs text-label-xs text-secondary mt-0.5 flex items-center gap-1">
              <span className="material-symbols-outlined text-[12px]">check</span> Parsed
            </span>
          </div>
          <div className="bg-surface-container-low p-space-md rounded-lg flex flex-col">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-wider">Fields Extracted</span>
            <span className="font-metric-num text-metric-num text-on-surface mt-1">{ctx.fieldValues['Site Area']?8:7}</span>
            <span className="font-label-xs text-label-xs text-on-surface-variant mt-0.5">7 required fields</span>
          </div>
          <div className="bg-surface-container-low p-space-md rounded-lg flex flex-col">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-wider">Citation Conflicts</span>
            <span className="font-metric-num text-metric-num text-secondary mt-1">0</span>
            <span className="font-label-xs text-label-xs text-secondary mt-0.5 flex items-center gap-1">
              <span className="material-symbols-outlined text-[12px]">verified</span> Zero Divergence
            </span>
          </div>
          <div className="bg-surface-container-low p-space-md rounded-lg flex flex-col">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-wider">Missing Optional</span>
            <span className="font-metric-num text-metric-num text-on-surface mt-1">{ctx.fieldValues['Site Area']?0:1}</span>
            <span className="font-label-xs text-label-xs text-on-surface-variant mt-0.5">Site Area (Optional)</span>
          </div>
        </div>
        <div className="mt-space-md pt-space-sm flex items-center justify-between text-label-xs font-label-xs text-on-surface-variant">
          <div className="flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[15px] text-secondary">info</span>
            <span>Ready for analyst review</span>
          </div>
          <span className="hidden md:inline">Run ID: <code className="font-mono text-on-surface">EXT-2024-0514-88A</code></span>
        </div>
      </div>
    </div>

    <div className="sticky bottom-4 z-30 bg-surface-container-lowest/95 backdrop-blur-md p-space-md rounded-xl shadow-xl flex flex-col sm:flex-row items-center justify-end gap-space-md">
      <div className="flex items-center gap-space-sm w-full sm:w-auto justify-end">
        <button className="px-space-md py-2 text-on-surface-variant hover:text-on-surface font-label-md text-label-md font-medium transition-colors">
          Cancel
        </button>
        <button className="px-space-md py-2 bg-surface-container-highest hover:bg-surface-container text-on-surface font-label-md text-label-md font-semibold rounded shadow-sm transition-colors">
          Save for Review
        </button>
        <button className="px-space-lg py-2 bg-primary hover:bg-primary-container text-on-primary font-label-md text-label-md font-semibold rounded shadow-md transition-all flex items-center gap-2" id="queue-btn" disabled={ctx.queued}>
          <span className="material-symbols-outlined text-[18px]">playlist_add_check</span>
          <span>Confirm &amp; Add to Queue</span>
        </button>
      </div>
    </div>
  </div>
</div>); }
