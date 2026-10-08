"""Geri cekilme modeli icin sinirli deneme (1 saat kurali).

Varyantlar dogrulama donemi ONCESINDE karsilastirilir: kesim 2020 -> 2021 basvurulari,
kesim 2021 -> 2022 basvurulari. 2023 dogrulama ve 2024 test setine dokunulmaz.
Calistirma: PYTHONPATH=src python scripts/experiment_withdrawal.py
"""
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

import cq.model as M
from cq.dataset import OUT as APPLICATIONS
from cq.features import CATEGORICAL, FEATURES, build_features, operator_key
from cq.intervals import app_labels, assign_split, eligible, training_table
from cq.repd import SNAPSHOT

apps = pd.read_parquet(APPLICATIONS)
F_RAW = build_features(apps, normalize_operators=False)
F_NORM = build_features(apps)
op_key = apps.set_index("app_id").operator.map(operator_key, na_action="ignore").fillna("NA")
F_OPCAT = F_NORM.assign(op_key=op_key.reindex(F_NORM.index).values)

VARIANTS = {
    "A_mevcut": (F_RAW, FEATURES, CATEGORICAL, {}),
    "B_ad_birlestirme": (F_NORM, FEATURES, CATEGORICAL, {}),
    "C_B+sirket_kategorik": (F_OPCAT, FEATURES + ["op_key"], CATEGORICAL + ["op_key"], {}),
    "D_B+derinlik4": (F_NORM, FEATURES, CATEGORICAL, {"depth": 4}),
    "E_B+derinlik8": (F_NORM, FEATURES, CATEGORICAL, {"depth": 8}),
}


def run(feats, cols, cats, params, cutoff, eval_end):
    rows = training_table(apps, cutoff)
    x = feats.loc[rows.app_id].reset_index(drop=True)
    x["bin"] = np.minimum(rows.bin.values, M.MAX_BIN)
    model = CatBoostClassifier(**{**M.PARAMS, **params}).fit(Pool(x[cols + ["bin"]], rows.label, cat_features=cats))
    e = eligible(apps)
    ev = e[assign_split(e, cutoff, eval_end) == "eval"]
    lab = app_labels(ev, SNAPSHOT).dropna()
    old = M.X_COLS
    M.X_COLS = cols + ["bin"]
    try:
        pred = M.predict(model, feats, lab.app_id).p_withdraw_12m.values
    finally:
        M.X_COLS = old
    return lab.withdraw_12m.values, pred


if __name__ == "__main__":
    for name, (feats, cols, cats, params) in VARIANTS.items():
        ys, ps, per = [], [], []
        for cut in (2020, 2021):
            y, p = run(feats, cols, cats, params, pd.Timestamp(cut, 12, 31), pd.Timestamp(cut + 1, 12, 31))
            ys.append(y), ps.append(p), per.append(round(roc_auc_score(y, p), 3))
        y, p = np.concatenate(ys), np.concatenate(ps)
        print(f"{name:24} ROC={roc_auc_score(y, p):.3f} (yillar {per})  PR-AUC={average_precision_score(y, p):.3f}"
              f"  Brier={brier_score_loss(y, p):.5f}  taban={brier_score_loss(y, np.full_like(p, y.mean())):.5f}  n_olay={int(y.sum())}",
              flush=True)
