"""K2/K4 icin SAHTE tahmin dosyalari: gercek modelle ayni sema, sabit taban oranlar.

Herkese ayni olasilik verildigi icin bu dosyalarla kurulan siralama "sadece karbon"
ablasyonuna denk gelir. Gercek dosyalar ayni yollara ayni kolonlarla yazilacak.

Calistirma: PYTHONPATH=src python scripts/make_fake_predictions.py
"""
import numpy as np
import pandas as pd

from cq.dataset import OUT as APPLICATIONS
from cq.repd import ROOT

OUT_DIR = ROOT / "data" / "processed" / "predictions"
BIN_DAYS, N_BINS = 30, 12  # 12 x 30 gun; son eleman "360 gun icinde karar yok"
SIM_YEARS = range(2019, 2024)

apps = pd.read_parquet(APPLICATIONS)
sim = apps[apps.sim_eligible]

# Taban oranlar: 2015-2022 basvurulari (neredeyse hepsi sonuclanmis)
base = apps[apps.model_eligible & apps.d_submitted.dt.year.between(2015, 2022)]
within = base.duration_days < BIN_DAYS * N_BINS
p_withdraw = float(((base.event == "withdrawal") & within).mean())
dec = base[(base.event == "decision") & within]
counts = np.bincount((dec.duration_days // BIN_DAYS).astype(int), minlength=N_BINS)
dist = list(counts / len(base)) + [1 - counts.sum() / len(base)]


def frame(rows: pd.DataFrame, cutoff_year: int, as_of: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({
        "app_id": rows.app_id.values,
        "cutoff_year": cutoff_year,
        "as_of_date": as_of.values,
        "p_withdraw_12m": p_withdraw,
        "decision_dist": [dist] * len(rows),
        "is_fake": True,
    })


OUT_DIR.mkdir(parents=True, exist_ok=True)
for year in SIM_YEARS:
    start, end = pd.Timestamp(year, 1, 1), pd.Timestamp(year, 12, 31)
    # Y yilinda kuyrukta bulunan her dosya: Y sonuna kadar basvurmus, Y basindan once sonuclanmamis
    q = sim[(sim.d_submitted <= end) & (sim.d_event.isna() | (sim.d_event >= start))]
    frame(q, year - 1, q.d_submitted.clip(lower=start)).to_parquet(OUT_DIR / f"predictions_{year}.parquet", index=False)
    print(year, len(q))

live = apps[apps.live_queue]
frame(live, 2026, live.d_submitted).to_parquet(OUT_DIR / "predictions_live.parquet", index=False)
print("live", len(live), "| p_withdraw_12m =", round(p_withdraw, 4), "| dist =", [round(x, 3) for x in dist])
