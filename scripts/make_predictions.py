"""Gercek tahmin dosyalari (docs/data_contract.md, bolum 2).

Y yili kuyrugu: Y-1 sonunda kesilmis veriyle egitilen modelle tahmin (kayan baslangicli egitim).
Canli kuyruk: veri kesim tarihine (24.07.2026) kadar egitilen modelle tahmin.
Hiperparametreler sabittir (cq.model.PARAMS); hicbir yilda ayarlanmaz.

Calistirma: PYTHONPATH=src python scripts/make_predictions.py
"""
import sys

import pandas as pd

from cq.dataset import OUT as APPLICATIONS
from cq.features import build_features
from cq.model import elapsed_bins, predict, train
from cq.repd import ROOT, SNAPSHOT

OUT_DIR = ROOT / "data" / "processed" / "predictions"
MODEL_DIR = ROOT / "data" / "models"
SIM_YEARS = range(2019, 2024)


def queue_for_year(apps: pd.DataFrame, year: int) -> pd.DataFrame:
    """Y yilinda kuyrukta bulunan her simulasyon dosyasi: Y sonuna kadar basvurmus, Y basindan once sonuclanmamis."""
    start, end = pd.Timestamp(year, 1, 1), pd.Timestamp(year, 12, 31)
    sim = apps[apps.sim_eligible]
    return sim[(sim.d_submitted <= end) & (sim.d_event.isna() | (sim.d_event >= start))]


def write(model, feats, q, as_of, cutoff_year, path):
    pred = predict(model, feats, q.app_id.values, elapsed_bins(q.d_submitted, as_of) if len(q) else 0)
    pred.insert(1, "cutoff_year", cutoff_year)
    pred.insert(2, "as_of_date", as_of.values if isinstance(as_of, pd.Series) else pd.Timestamp(as_of))
    pred["is_fake"] = False
    pred.to_parquet(path, index=False)
    print(f"{path.name}: n={len(pred)}  ort. p_withdraw_12m={pred.p_withdraw_12m.mean():.4f}", flush=True)


if __name__ == "__main__":
    apps = pd.read_parquet(APPLICATIONS)
    feats = build_features(apps)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for year in [] if "--live-only" in sys.argv else SIM_YEARS:
        cutoff = pd.Timestamp(year - 1, 12, 31)
        model = train(apps, cutoff, feats)
        model.save_model(MODEL_DIR / f"model_{year - 1}.cbm")
        q = queue_for_year(apps, year)
        as_of = q.d_submitted.clip(lower=pd.Timestamp(year, 1, 1))  # yil basinda ya da kuyruga girdigi an
        write(model, feats, q, as_of, year - 1, OUT_DIR / f"predictions_{year}.parquet")

    model = train(apps, SNAPSHOT, feats)
    model.save_model(MODEL_DIR / "model_live.cbm")
    live = apps[apps.live_queue]
    write(model, feats, live, SNAPSHOT, SNAPSHOT.year, OUT_DIR / "predictions_live.parquet")
