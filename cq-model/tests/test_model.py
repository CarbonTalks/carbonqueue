"""Hazard birikimi testleri: sentetik veride biriktirilmis olasilik gercek orana esit cikmali.

Calistirma: PYTHONPATH=src python tests/test_model.py
"""
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

from cq.model import accumulate

K = 12


def simulate(h_dec, h_wd, n, rng):
    """Her basvuru icin dilim dilim olay cek; (olay, dilim) dondur. Olay: 0 yok, 1 karar, 2 geri cekilme."""
    event = np.zeros(n, int)
    when = np.full(n, K + 1)
    alive = np.ones(n, bool)
    for k in range(K):
        u = rng.random(n)
        dec = alive & (u < h_dec[:, k])
        wd = alive & ~dec & (u < h_dec[:, k] + h_wd[:, k])
        event[dec], event[wd] = 1, 2
        when[dec | wd] = k + 1
        alive &= ~(dec | wd)
    return event, when


def test_accumulate_matches_simulation():
    rng = np.random.default_rng(0)
    n = 200_000
    h_dec = np.tile(np.linspace(0.02, 0.25, K), (n, 1))  # karar olasiligi zamanla artiyor
    h_wd = np.tile(np.linspace(0.03, 0.005, K), (n, 1))
    p_wd, dist = accumulate(h_dec[:1], h_wd[:1])
    event, when = simulate(h_dec, h_wd, n, rng)
    assert abs(p_wd[0] - (event == 2).mean()) < 0.003
    emp = [((event == 1) & (when == k)).mean() for k in range(1, K + 1)] + [1 - (event == 1).mean()]
    assert np.allclose(dist[0], emp, atol=0.003)
    assert np.isclose(dist.sum(), 1)


def test_naive_sum_would_be_wrong():
    """Hazard'lari dogrudan toplamak olasiligi sisirir; birikimin farki gercek."""
    h_dec, h_wd = np.full((1, K), 0.2), np.full((1, K), 0.05)
    p_wd, _ = accumulate(h_dec, h_wd)
    assert p_wd[0] < 0.6 * h_wd.sum()


def test_model_recovers_rates_on_synthetic_intervals():
    """Uctan uca: dilim satirlariyla egitilen CatBoost + birikim, gercek 12 aylik orani bulmali."""
    rng = np.random.default_rng(1)
    n = 6000
    risky = rng.random(n) < 0.3  # riskli grupta geri cekilme 4 kat
    h_wd = np.where(risky, 0.04, 0.01)[:, None] * np.ones((1, K))
    h_dec = np.full((n, K), 0.12)
    event, when = simulate(h_dec, h_wd, n, rng)
    n_rows = np.minimum(when, K)
    idx = np.repeat(np.arange(n), n_rows)
    k = np.concatenate([np.arange(1, m + 1) for m in n_rows])
    label = np.where(k == when[idx], event[idx], 0)
    x = pd.DataFrame({"risky": risky[idx].astype(int), "bin": k})
    m = CatBoostClassifier(loss_function="MultiClass", iterations=200, depth=3, verbose=False, random_seed=0)
    m.fit(x, label)
    for flag in (0, 1):
        q = pd.DataFrame({"risky": flag, "bin": np.arange(1, K + 1)})
        h = m.predict_proba(q)
        p_wd, _ = accumulate(h[None, :, 1], h[None, :, 2])
        true_p, _ = accumulate(h_dec[:1], h_wd[np.argmax(risky == flag)][None, :])
        assert abs(p_wd[0] - true_p[0]) < 0.03, (flag, p_wd[0], true_p[0])


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
