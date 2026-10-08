"""Model degerlendirmesi: kesim 2022 -> dogrulama 2023 basvurulari, kesim 2023 -> test 2024 basvurulari.

Basvuru duzeyinde, basvuru anindaki tahminle: 12 aylik geri cekilme (PR-AUC, ROC-AUC, Brier, kalibrasyon)
ve karar suresi dagilimi (13 sinifli Brier). Taban cizgi: egitim verisindeki sabit oranlar.

Calistirma: PYTHONPATH=src python scripts/evaluate.py
"""
import json

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from cq.dataset import OUT as APPLICATIONS
from cq.features import build_features
from cq.intervals import HORIZON_BINS, app_labels, assign_split, eligible
from cq.model import predict, train
from cq.repd import ROOT, SNAPSHOT

REPORT = ROOT / "reports" / "model_metrics.json"


def baseline(apps, cutoff):
    """Kesim tarihine kadar 360 gunu dolmus egitim basvurularindan sabit oranlar."""
    e = eligible(apps)
    tr = e[assign_split(e, cutoff) == "train"]
    lab = app_labels(tr, cutoff).dropna()
    p = lab.withdraw_12m.mean()
    dist = np.bincount(lab.decision_bin.astype(int) - 1, minlength=HORIZON_BINS + 1) / len(lab)
    return p, dist


def multiclass_brier(dist, bins):
    onehot = np.eye(dist.shape[1])[bins - 1]
    return float(((dist - onehot) ** 2).sum(axis=1).mean())


def evaluate(apps, feats, cutoff, eval_end, name):
    model = train(apps, cutoff, feats)
    e = eligible(apps)
    ev = e[assign_split(e, cutoff, eval_end) == "eval"]
    lab = app_labels(ev, SNAPSHOT).dropna()
    pred = predict(model, feats, lab.app_id).set_index("app_id").loc[lab.app_id]
    y, p = lab.withdraw_12m.values, pred.p_withdraw_12m.values
    dist = np.stack(pred.decision_dist.values)
    bins = lab.decision_bin.astype(int).values
    b_p, b_dist = baseline(apps, cutoff)
    deciles = pd.qcut(p, 5, duplicates="drop")
    calib = pd.DataFrame({"pred": p, "obs": y}).groupby(deciles, observed=True).mean()
    pred_median = (np.cumsum(dist, axis=1) >= 0.5).argmax(axis=1) + 1
    res = {
        "set": name, "cutoff": str(cutoff.date()), "n": int(len(y)), "withdrawals": int(y.sum()),
        "base_rate": round(float(y.mean()), 4),
        "pr_auc": round(average_precision_score(y, p), 4),
        "roc_auc": round(roc_auc_score(y, p), 4),
        "brier": round(brier_score_loss(y, p), 5),
        "brier_baseline": round(brier_score_loss(y, np.full_like(p, b_p)), 5),
        "mean_pred": round(float(p.mean()), 4),
        "decision_brier": round(multiclass_brier(dist, bins), 4),
        "decision_brier_baseline": round(multiclass_brier(np.tile(b_dist, (len(bins), 1)), bins), 4),
        "decision_bin_mae": round(float(np.abs(pred_median - bins).mean()), 2),
        "calibration_quintiles": [[round(a, 4), round(b, 4)] for a, b in calib.values],
        "feature_importance_top10": model.get_feature_importance(prettified=True).head(10).values.tolist(),
    }
    return res, model, ev, pred


if __name__ == "__main__":
    apps = pd.read_parquet(APPLICATIONS)
    feats = build_features(apps)
    out = []
    for cut, end, name in [(2022, 2023, "dogrulama_2023"), (2023, 2024, "test_2024")]:
        res, *_ = evaluate(apps, feats, pd.Timestamp(cut, 12, 31), pd.Timestamp(end, 12, 31), name)
        out.append(res)
        print(json.dumps(res, ensure_ascii=False, indent=1))
    REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
