import React, { createContext, useContext, useState } from 'react';
import { TR } from './i18n-tr.js';

// English text is the key; Turkish comes from i18n-tr.js. Missing entries fall back to English.
export const LANGS = { tr: 'TR', en: 'EN' };
let current = 'tr';
export const locale = () => (current === 'tr' ? 'tr-TR' : 'en-GB');

function loadLang() {
  try { const saved = localStorage.getItem('carbonqueue-lang'); if (saved in LANGS) return saved; } catch { /* storage unavailable */ }
  return 'tr';
}

export function translate(text, vars) {
  let out = current === 'tr' ? (TR[text] ?? text) : text;
  if (vars) for (const [k, v] of Object.entries(vars)) out = out.replaceAll(`{${k}}`, v);
  return out;
}

const LangContext = createContext({ lang: 'tr', setLang: () => {}, t: translate });
export const useT = () => useContext(LangContext);

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(() => { current = loadLang(); return current; });
  const setLang = next => {
    current = next; setLangState(next);
    try { localStorage.setItem('carbonqueue-lang', next); } catch { /* storage unavailable */ }
    document.documentElement.lang = next;
  };
  document.documentElement.lang = lang;
  return <LangContext.Provider value={{ lang, setLang, t: translate }}>{children}</LangContext.Provider>;
}

export function LangSwitch() {
  const { lang, setLang, t } = useT();
  return <div className="lang-switch" role="group" aria-label={t('Language')}>
    {Object.entries(LANGS).map(([code, label]) => <button key={code} type="button" aria-pressed={lang === code} onClick={() => setLang(code)}>{label}</button>)}
  </div>;
}
