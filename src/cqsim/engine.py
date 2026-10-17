"""cq-backend icin kuyruk motoru: backend'in QueueEngine sozlesmesindeki dort cagri (carbon, effort, schedule, simulate).

Girdi ve cikti backend'in JSON sozlesmesidir (cq-backend/src/cq_backend/domain, 15 Ekim surumu):
karbon gunluk bant (daily_tco2) ya da skorsuz nedeni (unscored_reason), kuyruk girdisinde lane / reason / planned_week.
Hesaplar cq-sim'in geri kalaniyla aynidir: ayni karbon formulu, efor kurali, simulator ve gerekce metinleri.
"""
import csv
import json
from datetime import date
from functools import lru_cache

import numpy as np
import pandas as pd

from cqsim.live import _reason
from cqsim.prepare import ROOT, effort_hours, emission_factors, score
from cqsim.simulator import POLICIES, simulate

# backend teknolojisi -> cq-sim kategorisi (cq-model/src/cq/serve.py ile ayni esleme)
CATEGORY = {
    "solar": "solar",
    "onshore_wind": "onshore_wind",
    "battery": "storage",
    "hydro": "other_renewable",
    "biomass": "bioenergy_waste",
    "tidal": "other_renewable",
    "wave": "other_renewable",
}
UNSCORED_WHY = {"storage": "depolama", "bioenergy_waste": "biyoenerji / atik", "other_renewable": "diger yenilenebilir"}
POLICY_ALIASES = {"FIFO": "fifo", "CARBONQUEUE": "carbonqueue"}
# REPD disindaki her karbon azaltim projesi (isi pompasi, verimlilik, elektrifikasyon...) bu kategoriyle girer:
# etkisi MW'tan degil, basvurunun kendi beyanindan (yillik tCO2e ya da yillik MWh) gelir.
CLAIM = "claim_based"
CLAIM_FIELDS = ("annual_co2e_reduction_t", "annual_energy_mwh")
# project_features.country (ISO 3166-1 alfa-2); bos ise Ingiltere: gecmis veri ve canli kuyruk Ingiltere'dir.
DEFAULT_COUNTRY = "GB"
COUNTRY_ALIASES = {"UK": "GB"}
FACTOR_SOURCES = {
    "GB": "dusuk sebeke ortalamasi, merkezi uzun donem marjinal (Green Book tablo 1), yuksek gaz santrali (DUKES 5.14)",
    "TR": "dusuk Turkiye geneli elektrik uretimi (ETKB 2023), merkezi birlesik marj (ETKB 2021, UNFCCC Tool 07), "
          "yuksek faaliyet temelli marj (ETKB 2021)",
}
IFI_SOURCE = ("merkezi birlesik marj, yuksek faaliyet temelli marj: Harmonized IFI Default Grid Factors 2021 v3.2 "
              "(UNFCCC, CDM Tool 07)")
LEVELS = ("low", "central", "high")
# Kesintili uretim; digerleri (verimlilik, isi pompasi, hidro...) kesintisiz/verimlilik marjini kullanir.
INTERMITTENT = {"solar", "onshore_wind", "offshore_wind", "tidal", "wave"}


class EngineError(ValueError):
    """Gecersiz istek: sunucu 422 doner."""


def _positive(value) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0 else None


def _country(f: dict) -> str:
    code = str(f.get("country") or DEFAULT_COUNTRY).strip().upper()
    return COUNTRY_ALIASES.get(code, code)


@lru_cache(maxsize=4)
def _ifi_table(path: str) -> dict:
    with open(path, encoding="utf-8", newline="") as f:
        return {row["iso2"]: row for row in csv.DictReader(f)}


def country_factors(cfg: dict, country: str, year: int, kind: str = "intermittent") -> dict | None:
    """Ulkenin yuk faktorleri, {low, central, high} emisyon faktoru (tCO2e/MWh) ve kaynagi; bilinmeyen ulkede None.
    Once ulkenin resmi faktorleri (assumptions.toml), yoksa BM'deki IFI veri seti. kind: intermittent | firm."""
    c = cfg["carbon"]
    src = c if country == DEFAULT_COUNTRY else c.get("country", {}).get(country)
    if src is not None:
        lag = {"operation_lag_years": c["operation_lag_years"]}
        ef = emission_factors({"carbon": {"emission_factor": src["emission_factor"], **lag}}, year)
        if kind == "firm" and "emission_factor_firm" in src:
            ef |= emission_factors({"carbon": {"emission_factor": src["emission_factor_firm"], **lag}}, year)
        return {"load_factor": src.get("load_factor", {}), "ef": ef, "source": FACTOR_SOURCES.get(country, country)}
    row = _ifi_table(str(ROOT / c["ifi"]["file"])).get(country) if "ifi" in c else None
    if row is None:
        return None
    central = float(row["cm_intermittent" if kind == "intermittent" else "cm_energy_efficiency"]) / 1000
    high = max(float(row["om"]) / 1000, central)
    return {"load_factor": {}, "ef": {"low": central, "central": central, "high": high},
            "source": f"{row['name']}: {IFI_SOURCE}"}


def _features(project: dict) -> dict:
    f = project.get("project_features")
    if not f or f.get("technology") is None:
        raise EngineError("project_features.technology gerekli")
    if f["technology"] in CATEGORY:
        if f.get("capacity_mw") is None:
            raise EngineError(f"{f['technology']} icin capacity_mw gerekli")
    elif not any(_positive(f.get(name)) for name in CLAIM_FIELDS):
        raise EngineError(f"{f['technology']} icin beyan gerekli: {' ya da '.join(CLAIM_FIELDS)}")
    return f


def _band(category: str, mw: float, claim_t, claim_mwh, factors: dict | None) -> tuple[dict | None, str]:
    """Gunluk tCO2e bandi ve dayanagi. Oncelik: MW formulu (ulkenin yuk faktoru varsa), ton beyani, MWh beyani.
    Bant yoksa ikinci deger skorsuz nedenidir."""
    lf = factors["load_factor"].get(category) if factors else None
    if lf and mw == mw and mw > 0:
        return {k: mw * 24 * lf * factors["ef"][k] for k in LEVELS}, "capacity"
    if claim_t:
        return {k: claim_t / 365 for k in LEVELS}, "claim_t"
    if claim_mwh and factors:
        return {k: claim_mwh / 365 * factors["ef"][k] for k in LEVELS}, "claim_mwh"
    if factors is None:
        return None, "bu ulke icin emisyon faktoru tanimli degil; yillik tCO2e beyani gerekli"
    if category in ("solar", "onshore_wind"):
        return None, "bu ulke icin yuk faktoru tanimli degil; yillik uretim (MWh) beyani gerekli"
    return None, f"{UNSCORED_WHY.get(category, category)}: bu teknoloji icin uretim karbonu hesaplanmiyor"


def frame(projects: list[dict], cfg: dict, year: int) -> pd.DataFrame:
    """Backend uygulamalarini simulatorun kuyruk tablosuna cevirir (build_queue ile ayni kolonlar)."""
    rows = []
    for p in projects:
        f = _features(p)
        submitted = f.get("submission_date") or p.get("created_at", str(date.today()))[:10]
        prediction = p.get("prediction") or {}
        category = CATEGORY.get(f["technology"], CLAIM)
        mw = float(f["capacity_mw"]) if f.get("capacity_mw") is not None else np.nan
        claim_t, claim_mwh = _positive(f.get("annual_co2e_reduction_t")), _positive(f.get("annual_energy_mwh"))
        country = _country(f)
        kind = "intermittent" if f["technology"] in INTERMITTENT else "firm"
        factors = country_factors(cfg, country, year, kind)
        band, basis = _band(category, mw, claim_t, claim_mwh, factors)
        rows.append({
            "application_id": p.get("application_id"), "category": category, "country": country,
            "has_storage_field": f.get("has_storage"), "app_generation_mw": mw, "arrival": pd.Timestamp(submitted),
            "p_withdraw_12m": float(prediction.get("withdrawal_probability_12m", 0.0)),
            "claim_t": claim_t, "claim_mwh": claim_mwh, "band": band, "basis": basis,
            "factor_source": factors["source"] if factors else None,
            "daily_tco2": band["central"] if band else np.nan,
        })
    q = pd.DataFrame(rows)
    q[["claim_t", "claim_mwh", "daily_tco2"]] = q[["claim_t", "claim_mwh", "daily_tco2"]].astype(float)
    # has_storage bos (bilinmiyor) ise yalnizca bataryanin kendisi depolama sayilir
    q["has_storage"] = (q.category == "storage") | q.has_storage_field.eq(True)
    q["from_claim"] = q.basis.isin(["claim_t", "claim_mwh"])
    q["scored"] = q.daily_tco2.notna()
    q["effort"] = effort_hours(q.app_generation_mw, q.has_storage, cfg)
    q["small"] = q.scored & (q.app_generation_mw < cfg["queue"]["small_project_mw"])
    q["exit"] = pd.NaT
    q["app_id"] = np.arange(len(q))
    return q.sort_values(["arrival", "app_id"]).reset_index(drop=True)


def carbon(project: dict, scenario: dict | None, cfg: dict, year: int | None = None) -> dict:
    """Gunluk yer degistirilen emisyon bandi (tCO2e/gun) ya da skorsuz nedeni. Senaryo kullanilmaz: bant uc seviyeyi tasir."""
    year = year or date.today().year
    q = frame([project], cfg, year).iloc[0]
    if not q.scored:
        return {"unscored_reason": f"Skorsuz yol ({q.basis}); kuyrukta efor payi kadar kapasiteyle basvuru sirasina gore ilerler",
                "methodology_reference": "cq-sim docs/carbon_sources.md"}
    band = {k: round(float(v), 3) for k, v in q.band.items()}
    factors = f"{q.country} emisyon faktoru {year + cfg['carbon']['operation_lag_years']}: {q.factor_source}"
    if q.basis == "claim_t":
        reference = f"Basvurunun kendi beyani: yillik {q.claim_t:g} tCO2e / 365"
    elif q.basis == "claim_mwh":
        reference = f"Basvurunun kendi beyani: yillik {q.claim_mwh:g} MWh / 365 x {factors}"
    else:
        return {"daily_tco2": band, "methodology_reference": (
            f"tCO2e/gun = MW x 24 x yuk faktoru (DUKES 2026 tablo 6.3) x yer degistirme {factors}. "
            "cq-sim docs/carbon_sources.md")}
    return {"daily_tco2": band, "methodology_reference": (
        f"{reference}. Beyan dogrulanmamistir; kaynagi belge alintisinda, kontrolu uzmandadir.")}


def effort(project: dict, cfg: dict) -> dict:
    q = frame([project], cfg, date.today().year).iloc[0]
    return {"reviewer_hours": float(q.effort)}


def schedule(projects: list[dict], policy: dict, capacity: float, cfg: dict) -> dict:
    """Verilen dosyalari secilen politikayla haftalik kapasite (saat) altinda siralar.

    position: incelemenin bitis sirasi (simulator). score: politikanin karbon skoru; skorsuz ya da FIFO'da bos.
    lane / reason: dosyanin hangi kademeden incelendigi ve gerekcesi (canli kuyruktaki metinlerle ayni).
    planned_week: incelemenin bitmesi planlanan hafta, 1 = bu hafta.
    """
    if not projects:
        return {"entries": []}
    name = POLICY_ALIASES.get(policy.get("name", ""), policy.get("name", ""))
    if name not in POLICIES:
        raise EngineError(f"bilinmeyen politika: {policy.get('name')} ({', '.join(POLICIES)})")
    today = pd.Timestamp(date.today())
    q = frame(projects, cfg, today.year)
    start = max(today, q.arrival.max())
    res = simulate(q, name, cfg, start, float(capacity))
    s = None if name == "fifo" else score(q, *POLICIES[name][:2])
    q["lane"] = res.lane.values
    q["wait_days"] = (start - q.arrival).dt.days
    entries = []
    for i in np.argsort(res.order.to_numpy()):
        sc = None if s is None or np.isnan(s[i]) else round(float(s[i]), 6)
        r = q.iloc[i]
        entries.append({
            "application_id": r.application_id, "position": int(res.order[i]), "score": sc, "lane": r.lane,
            "reason": "Başvuru sırası (FIFO)" if r.lane == "fifo" else _reason(r),
            "planned_week": int((res.done[i] - start).days // 7),  # ilk hafta biten = 1
        })
    return {"entries": entries}


def simulate_results(config: dict, cfg: dict) -> dict:
    """Gecmis kuyruk simulasyonunun hazir sonucu (results/{yil}-{politika}.json).

    Yuklenen yeni dosyalarin gercek sonucu olmadigi icin karbon kazanci onlar uzerinden hesaplanamaz;
    bu cagri cq-sim'in gecmis yil sonuclarini backend'in duz metrik bicimine cevirir.
    """
    params = config.get("parameters") or {}
    year, name = int(params.get("year", 2023)), params.get("policy", "carbonqueue")
    path = ROOT / "results" / f"{year}-{name}.json"
    if not path.exists():
        raise EngineError(f"sonuc yok: {path.name}")
    r = json.loads(path.read_text(encoding="utf-8"))
    metrics = {"files": r["files"], "capacity_hours_per_week": r["calibration"]["capacity_hours_per_week"],
               "over_max_wait_share": r["over_max_wait_share"]}
    for group, w in r["wait_days"].items():
        for k in ("median", "p90"):
            if k in w:
                metrics[f"wait_{group}_{k}_days"] = w[k]
    for alpha, levels in r["carbon_gain_tco2_vs_fifo"].items():
        for level, v in levels.items():
            metrics[f"gain_tco2_{alpha}_{level}"] = v
    return {"metrics": {k: float(v) for k, v in metrics.items()},
            "references": [f"cq-sim results/{path.name}", "cq-sim docs/carbon_sources.md"]}
