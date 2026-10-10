"""Simulasyon sonucundan metrikler. Karbon kazanci FIFO simulasyonuna gore hesaplanir, gercek tarihlere gore degil."""
import numpy as np
import pandas as pd


def _waits(days: pd.Series) -> dict:
    if days.empty:
        return {"n": 0}
    return {"n": int(len(days)), "median": float(days.median()), "p90": round(float(days.quantile(0.9)), 1),
            "max": float(days.max())}


def summarize(q: pd.DataFrame, res: pd.DataFrame, fifo: pd.DataFrame, cfg: dict) -> dict:
    """q ve iki simulasyon sonucu ayni sirada olmalidir (build_queue sirasi)."""
    wait = (res.done - q.arrival).dt.days
    reviewed = res.done.notna()
    max_wait = cfg["queue"]["max_wait_days"]

    # Karbon: yalnizca nihai izin almis, terk edilmemis, skorlanabilir dosyalar. Digerlerinin katkisi sifir.
    c = q.counts.to_numpy()
    gain_days = (fifo.done - res.done).dt.days[c]
    daily = q.daily_tco2[c]
    central = cfg["carbon"]["emission_factor"]["central"]
    base_t = float((daily * gain_days).sum())  # merkezi faktor, alpha = 1
    carbon = {
        f"alpha_{a}": {name: round(base_t * a * ef / central, 1) for name, ef in cfg["carbon"]["emission_factor"].items()}
        for a in cfg["carbon"]["alpha"]
    }
    left = q.exit.notna().to_numpy()
    return {
        "files": int(len(q)),
        "reviewed": int(reviewed.sum()),
        "left_before_review": int((~reviewed).sum()),
        "unresolved_files": int(q.unresolved.sum()),  # gercek sonucu belli degil; karbon katkisi sifir sayildi
        "carbon_files": int(c.sum()),
        "weeks_to_clear": int((res.done.max() - q.arrival.clip(lower=res.done.min()).min()).days // 7),
        "wait_days": {
            "all": _waits(wait[reviewed]),
            "small_scored": _waits(wait[reviewed & q.small]),
            "large_scored": _waits(wait[reviewed & q.scored & ~q.small]),
            "unscored": _waits(wait[reviewed & ~q.scored]),
        },
        "over_max_wait_share": round(float((wait[reviewed] > max_wait).mean()), 4),
        "carbon_weighted_wait_days": round(float(np.average(wait[c], weights=daily)), 1) if c.any() else None,
        "carbon_gain_days_median": float(gain_days.median()) if c.any() else None,
        "carbon_gain_tco2_vs_fifo": carbon,
        "wasted_hours_on_withdrawn": round(float(res.spent[left].sum()), 1),
        "hours_on_unresolved": round(float(res.spent[q.unresolved.to_numpy()].sum()), 1),
    }
