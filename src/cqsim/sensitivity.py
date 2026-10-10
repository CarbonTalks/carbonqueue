"""Duyarlilik kosulari: tek bir varsayim degistiginde CarbonQueue sonucu ne kadar degisiyor.

Her varyantta FIFO da ayni varsayimla yeniden kosar; kazanc her zaman ayni kosuldaki FIFO'ya goredir.
"""
import copy
from pathlib import Path

import pandas as pd

from cqsim.metrics import summarize
from cqsim.prepare import DATA, build_queue
from cqsim.simulator import calibrate, simulate

YEARS = (2021, 2022, 2023)  # ana sonuc yillari


def _set(cfg: dict, section: str, **values) -> dict:
    out = copy.deepcopy(cfg)
    out[section].update(values)
    return out


def variants(cfg: dict) -> dict:
    """ad -> (cfg, 5 yildan eski dosyalar cikarilsin mi)"""
    return {
        "temel": (cfg, False),
        "kapasite x0,8": (_set(cfg, "simulation", capacity_factor=0.8), False),
        "kapasite x1,2": (_set(cfg, "simulation", capacity_factor=1.2), False),
        "azami bekleme 180 gun": (_set(cfg, "queue", max_wait_days=180), False),
        "zorunlu kademe sinirsiz": (_set(cfg, "queue", max_wait_capacity_share=1.0), False),
        "azami bekleme 180 gun + sinirsiz": (_set(cfg, "queue", max_wait_days=180, max_wait_capacity_share=1.0), False),
        "sabit efor": (_set(cfg, "effort", storage_component=0, mw_steps=[]), False),
        "kucuk proje kotasi yok": (_set(cfg, "queue", small_quota_factor=0.0), False),
        "kucuk proje kotasi tam pay": (_set(cfg, "queue", small_quota_factor=1.0), False),
        "5 yildan eski dosyalar haric": (cfg, True),
    }


def run(cfg: dict, data: Path = DATA, policy: str = "carbonqueue") -> list[dict]:
    rows = []
    for year in YEARS:
        start = pd.Timestamp(year, 1, 1)
        for name, (c, drop_stale) in variants(cfg).items():
            q = build_queue(year, c, data)
            if drop_stale:
                q = q[~q.stale].reset_index(drop=True)
            capacity = calibrate(q, c, start)["capacity_hours_per_week"]  # capacity_factor dahil
            fifo = simulate(q, "fifo", c, start, capacity)
            m, f = summarize(q, simulate(q, policy, c, start, capacity), fifo, c), summarize(q, fifo, fifo, c)
            rows.append({
                "year": year, "variant": name, "policy": policy, "files": m["files"], "capacity_hours_per_week": capacity,
                "gain_tco2_central_alpha_0.5": m["carbon_gain_tco2_vs_fifo"]["alpha_0.5"]["central"],
                "carbon_weighted_wait_days": m["carbon_weighted_wait_days"],
                "fifo_carbon_weighted_wait_days": f["carbon_weighted_wait_days"],
                "wait_median": m["wait_days"]["all"]["median"], "wait_p90": m["wait_days"]["all"]["p90"],
                "fifo_wait_p90": f["wait_days"]["all"]["p90"],
                "small_wait_p90": m["wait_days"]["small_scored"].get("p90"),
                "fifo_small_wait_p90": f["wait_days"]["small_scored"].get("p90"),
                "unscored_wait_median": m["wait_days"]["unscored"].get("median"),
                "over_max_wait_share": m["over_max_wait_share"],
            })
    return rows


def table(rows: list[dict]) -> str:
    base = {r["year"]: r["gain_tco2_central_alpha_0.5"] for r in rows if r["variant"] == "temel"}
    out = ["| Yıl | Varyant | Kazanç tCO₂ (α=0,5; merkezi) | Temele göre | Karbon ağırlıklı bekleme (FIFO → CQ) "
           "| P90 bekleme (FIFO → CQ) | Küçük proje P90 (FIFO → CQ) |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        g = r["gain_tco2_central_alpha_0.5"]
        out.append(
            f"| {r['year']} | {r['variant']} | {g:,.0f} | %{100 * g / base[r['year']]:.0f} "
            f"| {r['fifo_carbon_weighted_wait_days']:.0f} → {r['carbon_weighted_wait_days']:.0f} "
            f"| {r['fifo_wait_p90']:.0f} → {r['wait_p90']:.0f} | {r['fifo_small_wait_p90']:.0f} → {r['small_wait_p90']:.0f} |")
    return "\n".join(out) + "\n"
