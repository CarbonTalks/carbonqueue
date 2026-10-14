"""M9: global model ile kategoriye ozel (uzman) modellerin kiyasi.

Her kesim icin (2022 -> 2023 dogrulama, 2023 -> 2024 test) global model bir kez egitilir; gunes, kara
ruzgari ve batarya icin yalnizca o kategorinin basvurularindan uzman modeller egitilir. Ozellikler
(kurum yuku, basvuru sahibi gecmisi) her iki durumda da tum veriden hesaplanir. Ayni basvurular uzerinde
karsilastirilir. Hiperparametreler ayni ve sabit.

Calistirma: PYTHONPATH="src:scripts" python scripts/compare_specialists.py  (Windows: $env:PYTHONPATH="src;scripts")
"""
import json

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score

from cq.dataset import OUT as APPLICATIONS
from cq.features import build_features
from cq.intervals import app_labels, assign_split, eligible
from cq.model import predict, train
from cq.repd import ROOT, SNAPSHOT
from evaluate import bin_mae, multiclass_brier

REPORT = ROOT / "reports" / "specialist_comparison.json"
CATEGORIES = ["solar", "onshore_wind", "storage"]


def metrics(lab, pred):
    y, p = lab.withdraw_12m.values, pred.p_withdraw_12m.values
    dist, bins = np.stack(pred.decision_dist.values), lab.decision_bin.astype(int).values
    return {
        "decision_brier": round(multiclass_brier(dist, bins), 4),
        "decision_bin_mae": round(bin_mae(dist, bins), 2),
        "withdraw_brier": round(brier_score_loss(y, p), 5),
        "withdraw_roc_auc": round(roc_auc_score(y, p), 3) if 0 < y.sum() < len(y) else None,
    }


if __name__ == "__main__":
    apps = pd.read_parquet(APPLICATIONS)
    feats = build_features(apps)
    out = []
    for cut, end, name in [(2022, 2023, "dogrulama_2023"), (2023, 2024, "test_2024")]:
        cutoff, eval_end = pd.Timestamp(cut, 12, 31), pd.Timestamp(end, 12, 31)
        e = eligible(apps)
        ev = e[assign_split(e, cutoff, eval_end) == "eval"]
        lab = app_labels(ev, SNAPSHOT).assign(category=ev.category.values).dropna()
        glob = train(apps, cutoff, feats)
        for cat in CATEGORIES:
            l = lab[lab.category == cat]
            spec = train(apps[apps.category == cat], cutoff, feats)
            g = metrics(l, predict(glob, feats, l.app_id))
            s = metrics(l, predict(spec, feats, l.app_id))
            row = {"set": name, "category": cat, "n": len(l), "withdrawals": int(l.withdraw_12m.sum()), "global": g, "specialist": s}
            out.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
