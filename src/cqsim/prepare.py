"""Kuyruk tablosu: cq-model ciktilarini okur, her dosyaya karbon, efor ve gercek sonucu ekler.

Karbon ve efor deterministiktir; butun sayilar assumptions.toml'dan gelir.
"""
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT.parent / "cq-model" / "data" / "processed"  # varsayilan: yan klasordeki cq-model
SCORED = ("solar", "onshore_wind")  # karbon skoru olan kategoriler; digerleri skorsuz yoldan gider


def load_config(path: Path | None = None) -> dict:
    return tomllib.loads((path or ROOT / "assumptions.toml").read_text(encoding="utf-8"))


def emission_factors(cfg: dict, year: int) -> dict:
    """Kuyruk yili icin {low, central, high} emisyon faktoru (tCO2e/MWh): year + operation_lag_years'in degeri,
    tabloda yoksa en yakin onceki yilin degeri."""
    target = year + cfg["carbon"]["operation_lag_years"]
    out = {}
    for name, by_year in cfg["carbon"]["emission_factor"].items():
        years = sorted(int(y) for y in by_year)
        out[name] = by_year[str(max([y for y in years if y <= target] or years[:1]))]
    return out


def daily_tco2(category: pd.Series, generation_mw: pd.Series, cfg: dict, year: int) -> pd.Series:
    """Gunluk yer degistirilen emisyon (merkezi faktor): MW x 24 x yuk faktoru x emisyon faktoru.
    Skorlanamayan dosyada bos."""
    lf = category.map(cfg["carbon"]["load_factor"])
    out = generation_mw * 24 * lf * emission_factors(cfg, year)["central"]
    return out.where(generation_mw > 0)


def effort_hours(generation_mw: pd.Series, has_storage: pd.Series, cfg: dict) -> pd.Series:
    e = cfg["effort"]
    points = e["base"] + e["storage_component"] * has_storage.astype(int)
    for mw, extra in e["mw_steps"]:
        points = points + extra * (generation_mw >= mw).astype(int)
    return points * e["hours_per_point"]


def _has_storage(apps: pd.DataFrame) -> pd.Series:
    """Ana bilesen satiri icin: basvurunun herhangi bir bileseni depolama mi."""
    comp = apps[~apps.duplicate_record]
    keys = comp.application_key[comp.category == "storage"].unique()
    return apps.application_key.isin(keys)


def _annotate(apps: pd.DataFrame, cfg: dict, year: int) -> pd.DataFrame:
    """Her basvuruya karbon, efor ve gercek sonuc kolonlarini ekler."""
    out = apps[["app_id", "site_name", "authority", "category", "technology", "app_generation_mw", "event"]].copy()
    out["has_storage"] = _has_storage(apps)
    out["arrival"] = apps.d_submitted
    leaves = (apps.event == "withdrawal") | apps.decision_via_nondetermination_appeal
    out["exit"] = apps.d_event.where(leaves)
    out["d_event"] = apps.d_event
    out["daily_tco2"] = daily_tco2(apps.category, apps.app_generation_mw, cfg, year)
    out["scored"] = out.daily_tco2.notna()
    out["effort"] = effort_hours(apps.app_generation_mw.fillna(0), out.has_storage, cfg)
    out["small"] = out.scored & (apps.app_generation_mw < cfg["queue"]["small_project_mw"])
    permitted = apps.d_permitted.notna() & ~apps.abandoned_or_expired
    out["counts"] = out.scored & permitted & ~leaves
    out["unresolved"] = apps.event == "open"
    # Kurumun gercekte karar verdigi dosyalarda basvurudan karara gecen gun (kapasite kalibrasyonu icin)
    out["real_days"] = (apps.d_event - apps.d_submitted).dt.days.where((apps.event == "decision") & ~leaves)
    return out


def build_queue(year: int | str, cfg: dict, data: Path = DATA) -> pd.DataFrame:
    """Y yilinin (ya da "live") kuyrugu; her dosya tek satir.

    arrival : kuyruga giris (basvuru tarihi)
    exit    : dosya incelenmeden kuyruktan kendiliginden ciktigi tarih (geri cekilme ya da redsiz temyiz)
    counts  : incelenirse karbona katkisi var mi (nihai izin almis, terk edilmemis, skorlanabilir)
    stale   : durumu belirsiz eski dosya. Canli kuyrukta tanim cq-model'dedir (stale_or_uncertain kolonu).
              Gecmis yillarda o kolon olmadigi icin yalnizca duyarlilik kosusunda kullanilan yerel kural:
              kuyruk basladiginda simulation.stale_years_historical yildan uzun suredir bekliyor.
    """
    apps = pd.read_parquet(data / "applications.parquet")
    pred = pd.read_parquet(data / "predictions" / f"predictions_{year}.parquet")
    start = pred.as_of_date.max() if year == "live" else pd.Timestamp(year, 1, 1)
    q = _annotate(apps, cfg, start.year).merge(pred[["app_id", "p_withdraw_12m"]], on="app_id")
    if len(q) != len(pred):
        raise ValueError("tahmin dosyasindaki bazi app_id'ler applications.parquet'te yok")
    if year == "live":
        q["stale"] = q.app_id.map(apps.set_index("app_id").stale_or_uncertain).to_numpy(bool)
    else:
        q["stale"] = q.arrival < start - pd.Timedelta(days=365 * cfg["simulation"]["stale_years_historical"])
    q["decided_in_year"] = (q.event == "decision") & (q.d_event.dt.year == year) if year != "live" else False
    return q.sort_values(["arrival", "app_id"]).reset_index(drop=True)


def live_capacity(cfg: dict, as_of: pd.Timestamp, data: Path = DATA) -> float:
    """Canli kuyruk icin kalibre edilmemis kapasite: son 365 gunde karar verilen simulasyon dosyalarinin eforu / 52."""
    apps = pd.read_parquet(data / "applications.parquet")
    a = _annotate(apps, cfg, as_of.year)[apps.sim_eligible.to_numpy()]
    recent = (a.event == "decision") & (a.d_event > as_of - pd.Timedelta(days=365)) & (a.d_event <= as_of)
    return float(a.effort[recent].sum() / 52)


def naive_capacity(q: pd.DataFrame) -> float:
    """Kalibrasyonun baslangic noktasi (saat/hafta): o yil gercekte karar verilen dosyalarin toplam eforu / 52.

    Tek basina kullanilmaz: yil sonuna dogru gelip ertesi yil karara baglanan dosyalari saymadigi icin
    kapasiteyi dusuk gosterir ve kuyrukta yapay birikme yaratir.
    """
    return float(q.effort[q.decided_in_year].sum() / 52)


def lane_shares(q: pd.DataFrame, cfg: dict) -> tuple[float, float]:
    """Skorsuz yolun ve kucuk proje kotasinin kapasite payi (kuyruktaki efor paylarindan)."""
    total = q.effort.sum()
    unscored = q.effort[~q.scored].sum() / total
    small = cfg["queue"]["small_quota_factor"] * q.effort[q.small].sum() / total
    return float(unscored), float(small)


def score(q: pd.DataFrame, use_withdrawal: bool, use_effort: bool) -> np.ndarray:
    s = q.daily_tco2.to_numpy(float)
    if use_withdrawal:
        s = s * (1 - q.p_withdraw_12m.to_numpy(float))
    if use_effort:
        s = s / q.effort.to_numpy(float)
    return s
