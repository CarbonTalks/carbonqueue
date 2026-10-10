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


def daily_tco2(category: pd.Series, generation_mw: pd.Series, cfg: dict, scenario: str = "central") -> pd.Series:
    """Gunluk yer degistirilen emisyon: MW x 24 x yuk faktoru x emisyon faktoru. Skorlanamayan dosyada bos."""
    lf = category.map(cfg["carbon"]["load_factor"])
    out = generation_mw * 24 * lf * cfg["carbon"]["emission_factor"][scenario]
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


def build_queue(year: int | str, cfg: dict, data: Path = DATA) -> pd.DataFrame:
    """Y yilinin (ya da "live") kuyrugu; her dosya tek satir.

    arrival : kuyruga giris (basvuru tarihi)
    exit    : dosya incelenmeden kuyruktan kendiliginden ciktigi tarih (geri cekilme ya da redsiz temyiz)
    counts  : incelenirse karbona katkisi var mi (nihai izin almis, terk edilmemis, skorlanabilir)
    """
    apps = pd.read_parquet(data / "applications.parquet")
    pred = pd.read_parquet(data / "predictions" / f"predictions_{year}.parquet")
    q = apps.assign(has_storage=_has_storage(apps)).merge(pred[["app_id", "p_withdraw_12m"]], on="app_id")
    if len(q) != len(pred):
        raise ValueError("tahmin dosyasindaki bazi app_id'ler applications.parquet'te yok")

    out = q[["app_id", "site_name", "authority", "category", "technology", "app_generation_mw",
             "has_storage", "p_withdraw_12m", "event"]].copy()
    out["arrival"] = q.d_submitted
    leaves = (q.event == "withdrawal") | q.decision_via_nondetermination_appeal
    out["exit"] = q.d_event.where(leaves)
    out["daily_tco2"] = daily_tco2(q.category, q.app_generation_mw, cfg)
    out["scored"] = out.daily_tco2.notna()
    out["effort"] = effort_hours(q.app_generation_mw.fillna(0), q.has_storage, cfg)
    out["small"] = out.scored & (q.app_generation_mw < cfg["queue"]["small_project_mw"])
    permitted = q.d_permitted.notna() & ~q.abandoned_or_expired
    out["counts"] = out.scored & permitted & ~leaves
    out["unresolved"] = q.event == "open"
    out["decided_in_year"] = (q.event == "decision") & (q.d_event.dt.year == year) if year != "live" else False
    return out.sort_values(["arrival", "app_id"]).reset_index(drop=True)


def weekly_capacity(q: pd.DataFrame, cfg: dict) -> float:
    """Haftalik uzman kapasitesi (saat): o yil gercekte karar verilen dosyalarin toplam eforu / 52."""
    return float(q.effort[q.decided_in_year].sum() / 52 * cfg["simulation"]["capacity_factor"])


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
