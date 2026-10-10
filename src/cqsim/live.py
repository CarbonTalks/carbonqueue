"""Canli kuyruk siralamasi (dashboard icin).

Sira, canli kuyrugun bugunku kapasiteyle simule edilmesinden cikar (son 365 gunun kararlari x son
simulasyon yilinin kalibrasyon katsayisi): her dosyanin hangi hafta ve hangi
kademeden incelenecegi. Canli kuyrukta gercek sonuc bilinmedigi icin karbon kazanci raporlanmaz.
"""
from pathlib import Path

import pandas as pd

from cqsim.prepare import DATA, build_queue, emission_factors, live_capacity
from cqsim.simulator import calibrate, simulate

CALIBRATION_YEAR = 2023  # canli kuyrukta gercek sonuc olmadigi icin katsayi en son simulasyon yilindan alinir
TOGGLE = ("fifo", "carbon", "carbonqueue")  # dashboard'daki politika secici
UNSCORED_WHY = {"storage": "depolama", "bioenergy_waste": "biyoenerji / atık", "other_renewable": "diğer yenilenebilir"}
STALE_REASON = "5 yıldan uzun süredir bekliyor: durumu kurumla teyit edilmeli"


def _tr(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def _reason(r) -> str:
    if r.lane == "max_wait":
        return f"Azami bekleme koruması: {r.wait_days} gündür bekliyor"
    if r.lane == "small_quota":
        return f"Küçük proje kotası: {_tr(r.app_generation_mw, 2)} MW"
    if r.lane == "carbon":
        return f"Uzman saati başına yüksek karbon etkisi: {_tr(r.daily_tco2)} tCO₂/gün ÷ {r.effort:.0f} saat"
    why = UNSCORED_WHY.get(r.category, "kapasite bilgisi eksik") if r.category != "solar" and r.category != "onshore_wind" \
        else "kapasite bilgisi eksik"
    return f"Skorsuz yol ({why}): başvuru sırasına göre"


def rank(cfg: dict, data: Path = DATA, include_stale: bool = False) -> dict:
    q = build_queue("live", cfg, data)
    as_of = pd.read_parquet(data / "predictions" / "predictions_live.parquet").as_of_date.max()
    year = CALIBRATION_YEAR
    factor = calibrate(build_queue(year, cfg, data), cfg, pd.Timestamp(year, 1, 1))["calibration_factor"]
    naive = live_capacity(cfg, as_of, data)
    capacity = naive * factor * cfg["simulation"]["capacity_factor"]
    stale = q[q.stale]
    if not include_stale:
        q = q[~q.stale].reset_index(drop=True)
    q["exit"] = pd.NaT  # canli kuyrukta kimin geri cekilecegi bilinmiyor
    runs = {p: simulate(q, p, cfg, as_of, capacity) for p in TOGGLE}
    main = runs["carbonqueue"]
    q["lane"] = main.lane.values
    q["wait_days"] = (as_of - q.arrival).dt.days
    ef = emission_factors(cfg, as_of.year)

    def row(r, i):
        band = None if pd.isna(r.daily_tco2) else {k: round(r.daily_tco2 * v / ef["central"], 2) for k, v in ef.items()}
        return {
            "app_id": int(r.app_id), "site_name": r.site_name, "authority": r.authority,
            "category": r.category, "technology": r.technology,
            "generation_mw": None if pd.isna(r.app_generation_mw) else float(r.app_generation_mw),
            "has_storage": bool(r.has_storage), "submitted": str(r.arrival.date()), "wait_days": int(r.wait_days),
            "position": {p: int(runs[p].order[i]) for p in TOGGLE},
            "planned_week": {p: int((runs[p].done[i] - as_of).days // 7) for p in TOGGLE},
            "lane": r.lane, "reason": _reason(r),
            "daily_tco2": band, "effort_hours": float(r.effort), "p_withdraw_12m": round(float(r.p_withdraw_12m), 4),
            "stale": bool(r.stale),
        }

    files = [row(r, i) for i, r in enumerate(q.itertuples(index=False))]
    files.sort(key=lambda f: f["position"]["carbonqueue"])
    return {
        "as_of": str(as_of.date()),
        "emission_factor_tco2_per_mwh": ef,
        "calibration": {"capacity_hours_per_week": round(capacity, 1), "naive_capacity_hours_per_week": round(naive, 1),
                        "calibration_factor": factor, "calibration_year": year},
        "files": files,
        "needs_confirmation": [] if include_stale else [
            {"app_id": int(r.app_id), "site_name": r.site_name, "authority": r.authority, "category": r.category,
             "submitted": str(r.arrival.date()), "wait_days": int((as_of - r.arrival).days), "reason": STALE_REASON}
            for r in stale.itertuples(index=False)],
        "lane_counts": {k: int(v) for k, v in q.lane.value_counts().items()},
    }
