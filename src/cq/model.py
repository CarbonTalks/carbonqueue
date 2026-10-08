"""Ayrik zamanli CatBoost modeli: 30 gunluk dilimde 0 hicbir sey / 1 ilk karar / 2 geri cekilme.

Model dilim basina kosullu olasilik (hazard) verir; accumulate() bunlari
12 aylik geri cekilme olasiligina ve karar suresi dagilimina cevirir.
"""
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool

from cq.features import CATEGORICAL, FEATURES, build_features
from cq.intervals import BIN_DAYS, HORIZON_BINS, training_table

MAX_BIN = 37  # 36 dilimden (3 yil) sonrasi tek grup: cok eski "bekliyor" kayitlari ayrintiya bolunmesin
PARAMS = dict(  # bir kez sabitlendi; dogrulama setine gore ayarlanmaz
    loss_function="MultiClass", iterations=600, learning_rate=0.05, depth=6,
    l2_leaf_reg=3, random_seed=0, has_time=True, verbose=False, thread_count=-1,
)
X_COLS = FEATURES + ["bin"]


def _x(feats: pd.DataFrame, app_ids, bins) -> pd.DataFrame:
    x = feats.loc[app_ids].reset_index(drop=True)
    x["bin"] = np.minimum(np.asarray(bins), MAX_BIN)
    return x[X_COLS]


def train(apps: pd.DataFrame, cutoff: pd.Timestamp, feats: pd.DataFrame | None = None) -> CatBoostClassifier:
    feats = build_features(apps) if feats is None else feats
    rows = training_table(apps, cutoff)  # info_date'e gore sirali (has_time)
    pool = Pool(_x(feats, rows.app_id, rows.bin), rows.label, cat_features=CATEGORICAL)
    return CatBoostClassifier(**PARAMS).fit(pool)


def accumulate(h_dec: np.ndarray, h_wd: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Hazard -> olasilik. Girdi (n, K): her dilimde, o dilime kadar olay yoksa olay olasiligi.

    S(k)        = prod_{j<=k} (1 - h_dec(j) - h_wd(j))
    P(wd <= K)  = sum_k S(k-1) * h_wd(k)
    P(dec in k) = S(k-1) * h_dec(k);  son eleman = 1 - sum_k P(dec in k)  ("K dilimde karar yok")
    """
    surv = np.cumprod(1 - h_dec - h_wd, axis=1)
    before = np.hstack([np.ones((len(surv), 1)), surv[:, :-1]])  # S(k-1)
    p_wd = (before * h_wd).sum(axis=1)
    p_dec = before * h_dec
    dist = np.hstack([p_dec, 1 - p_dec.sum(axis=1, keepdims=True)])
    return p_wd, dist


def predict(model: CatBoostClassifier, feats: pd.DataFrame, app_ids, elapsed_bins=0,
            horizon: int = HORIZON_BINS) -> pd.DataFrame:
    """as_of anindaki tahmin. elapsed_bins: basvurudan as_of'a kadar gecen tam dilim sayisi
    (dosya o ana kadar sonuclanmamis kabul edilir; sonraki 12 dilim tahmin edilir)."""
    app_ids = np.asarray(app_ids)
    elapsed = np.broadcast_to(np.asarray(elapsed_bins), app_ids.shape)
    k = elapsed[:, None] + np.arange(1, horizon + 1)[None, :]
    proba = model.predict_proba(_x(feats, np.repeat(app_ids, horizon), k.ravel()))
    h = proba.reshape(len(app_ids), horizon, 3)
    p_wd, dist = accumulate(h[:, :, 1], h[:, :, 2])
    return pd.DataFrame({"app_id": app_ids, "p_withdraw_12m": p_wd, "decision_dist": list(dist)})


def elapsed_bins(d_submitted: pd.Series, as_of) -> np.ndarray:
    return np.maximum((pd.to_datetime(as_of) - d_submitted).dt.days.values // BIN_DAYS, 0)
