"""cq-backend icin kuyruk motoru: backend'in QueueEngine sozlesmesindeki dort cagri (carbon, effort, schedule, simulate).

Girdi ve cikti backend'in JSON sozlesmesidir (cq-backend/src/cq_backend/domain, 15 Ekim surumu):
karbon gunluk bant (daily_tco2) ya da skorsuz nedeni (unscored_reason), kuyruk girdisinde lane / reason / planned_week.
Hesaplar cq-sim'in geri kalaniyla aynidir: ayni karbon formulu, efor kurali, simulator ve gerekce metinleri.
"""
import json
from datetime import date

import numpy as np
import pandas as pd

from cqsim.live import _reason
from cqsim.prepare import ROOT, daily_tco2, effort_hours, emission_factors, score
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


class EngineError(ValueError):
    """Gecersiz istek: sunucu 422 doner."""


def _features(project: dict) -> dict:
    f = project.get("project_features")
    if not f or f.get("technology") is None or f.get("capacity_mw") is None:
        raise EngineError("project_features.technology ve capacity_mw gerekli")
    if f["technology"] not in CATEGORY:
        raise EngineError(f"desteklenmeyen teknoloji: {f['technology']}")
    return f


def frame(projects: list[dict], cfg: dict, year: int) -> pd.DataFrame:
    """Backend uygulamalarini simulatorun kuyruk tablosuna cevirir (build_queue ile ayni kolonlar)."""
    rows = []
    for p in projects:
        f = _features(p)
        submitted = f.get("submission_date") or p.get("created_at", str(date.today()))[:10]
        prediction = p.get("prediction") or {}
        rows.append({
            "application_id": p.get("application_id"), "category": CATEGORY[f["technology"]],
            "has_storage_field": f.get("has_storage"),
            "app_generation_mw": float(f["capacity_mw"]), "arrival": pd.Timestamp(submitted),
            "p_withdraw_12m": float(prediction.get("withdrawal_probability_12m", 0.0)),
        })
    q = pd.DataFrame(rows)
    gen = q.app_generation_mw.where(q.category.isin(cfg["carbon"]["load_factor"]))
    # has_storage bos (bilinmiyor) ise yalnizca bataryanin kendisi depolama sayilir
    q["has_storage"] = (q.category == "storage") | q.has_storage_field.eq(True)
    q["daily_tco2"] = daily_tco2(q.category, gen, cfg, year)
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
        return {"unscored_reason": (
            f"Skorsuz yol ({UNSCORED_WHY.get(q.category, q.category)}): bu teknoloji icin uretim karbonu hesaplanmiyor; "
            "kuyrukta efor payi kadar kapasiteyle basvuru sirasina gore ilerler"),
            "methodology_reference": "cq-sim docs/carbon_sources.md"}
    ef = emission_factors(cfg, year)
    band = {k: round(float(q.daily_tco2 * v / ef["central"]), 3) for k, v in ef.items()}
    return {"daily_tco2": band, "methodology_reference": (
        f"tCO2e/gun = MW x 24 x yuk faktoru (DUKES 2026 tablo 6.3) x yer degistirme emisyon faktoru "
        f"{year + cfg['carbon']['operation_lag_years']}: dusuk sebeke ortalamasi, merkezi uzun donem marjinal "
        "(Green Book tablo 1), yuksek gaz santrali (DUKES 5.14). cq-sim docs/carbon_sources.md")}


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
