"""Model ozellikleri. Gecmise dayali her ozellik basvuru tarihi itibariyla hesaplanir:
yalnizca o tarihten ONCE olmus basvuru ve olaylar kullanilir.

Calistirma (kontrol): PYTHONPATH=src python -m cq.features
"""
import re

import numpy as np
import pandas as pd

WINDOW = pd.Timedelta(days=3 * 365)  # kurumun "son 3 yil" karar suresi penceresi
STALE = pd.Timedelta(days=5 * 365)  # 5 yildan uzun acik kalan kayit artik kuyruk yuku sayilmaz
CATEGORICAL = ["category", "technology", "solar_mounting", "storage_type", "country", "region", "authority"]
NUMERIC = [
    "log_capacity_mw", "log_generation_mw", "n_components", "submit_year", "submit_month",
    "post_2021", "small_project", "special_route", "is_resubmission",
    "auth_prior_apps", "auth_pending", "auth_median_decision_days", "auth_withdraw_rate",
    "op_prior_apps", "op_prior_withdrawn", "op_prior_resolved", "op_withdraw_rate",
    "uk_pending", "uk_median_decision_days",
]
FEATURES = CATEGORICAL + NUMERIC


_OP_NOISE = r"\b(ltd|limited|plc|llp|llc|inc|co|company|uk|gb|the|group|holdings?|developments?|dev)\b"


def operator_key(name: str) -> str:
    """Ayni sirketin farkli yazilislarini birlestirir: "RES Ltd (formerly X)" ve "RES Limited" -> "res"."""
    s = re.sub(r"\(.*?\)", "", name.lower()).replace("&", " and ")
    s = re.sub(_OP_NOISE, " ", re.sub(r"[^a-z0-9 ]", " ", s))
    return re.sub(r"\s+", " ", s).strip() or name.lower()


def _history(apps: pd.DataFrame) -> pd.DataFrame:
    """Gecmis istatistiklerinin kaynagi: mukerrer olmayan ana bilesenler (kapsam disi dahil, kurum yukune sayilir)."""
    h = apps[apps.is_primary_component & apps.d_submitted.notna()]
    # Sonucu tarihsiz kayitlar disarida: ne zaman bittikleri bilinmedigi icin sonsuza dek "bekliyor" sayilirlardi
    h = h[h.exclude_reason.isna() | h.exclude_reason.isin(["out_of_scope_technology", "pre2021_below_1mw"])]
    return h[["app_id", "authority", "operator", "d_submitted", "d_event", "event", "duration_days"]]


def _asof_group(hist: pd.DataFrame, query: pd.DataFrame) -> pd.DataFrame:
    """Tek bir grup (kurum / basvuru sahibi / UK) icin, her sorgu tarihinden ONCEKI kayitlarla istatistik."""
    t = query.d_submitted.values
    sub = np.sort(hist.d_submitted.values)
    ev = hist[hist.d_event.notna()]
    ev_dates = np.sort(ev.d_event.values)
    dec = ev[ev.event == "decision"].sort_values("d_event")
    dec_dates, dec_days = dec.d_event.values, dec.duration_days.values
    wd_dates = np.sort(ev[ev.event == "withdrawal"].d_event.values)

    prior = np.searchsorted(sub, t, side="left")  # t'den once basvuran
    # t aninda bekleyen: basvuru < t <= bitis; bitis = min(olay tarihi, basvuru + 5 yil).
    # 5 yil kurali olay tarihinden bagimsiz uygulanir; yoksa gelecekteki olay "hala bekliyor" bilgisini sizdirirdi.
    stale_at = hist.d_submitted.values + STALE.to_timedelta64()
    end = np.sort(np.where(hist.d_event.notna(), np.minimum(hist.d_event.values, stale_at), stale_at))
    pending = prior - np.searchsorted(end, t, side="left")
    resolved = np.searchsorted(ev_dates, t, side="left")  # t'den once sonuclanan
    withdrawn = np.searchsorted(wd_dates, t, side="left")
    lo = np.searchsorted(dec_dates, t - WINDOW.to_timedelta64(), side="left")
    hi = np.searchsorted(dec_dates, t, side="left")
    med = np.array([np.median(dec_days[a:b]) if b - a >= 3 else np.nan for a, b in zip(lo, hi)])
    return pd.DataFrame({
        "prior": prior,
        "pending": pending,
        "resolved": resolved,
        "withdrawn": withdrawn,
        "median_days": med,
    }, index=query.index)


def _asof(hist: pd.DataFrame, query: pd.DataFrame, key: str | None) -> pd.DataFrame:
    if key is None:
        return _asof_group(hist, query)
    parts = []
    h_groups = dict(tuple(hist.groupby(key)))
    for k, q in query[query[key].notna()].groupby(key):
        parts.append(_asof_group(h_groups.get(k, hist.iloc[:0]), q))
    return pd.concat(parts).reindex(query.index) if parts else pd.DataFrame(index=query.index)


def build_features(apps: pd.DataFrame, normalize_operators: bool = True) -> pd.DataFrame:
    """Her basvuru icin (basvuru tarihi itibariyla) ozellik satiri; index = app_id."""
    if normalize_operators:
        apps = apps.assign(operator=apps.operator.map(operator_key, na_action="ignore"))
    hist = _history(apps)
    q = apps[apps.d_submitted.notna()].copy()
    f = pd.DataFrame(index=q.index)
    for c in CATEGORICAL:
        f[c] = q[c].fillna("NA").astype(str)
    f["log_capacity_mw"] = np.log1p(q.capacity_mw)
    f["log_generation_mw"] = np.log1p(q.app_generation_mw)
    f["n_components"] = q.n_components
    f["submit_year"] = q.d_submitted.dt.year
    f["submit_month"] = q.d_submitted.dt.month
    for c in ["post_2021", "small_project", "special_route"]:
        f[c] = q[c].astype(float)
    chain_first = apps.groupby("chain_id").d_submitted.transform("min").reindex(q.index)
    f["is_resubmission"] = (q.d_submitted > chain_first).astype(float)

    a = _asof(hist, q, "authority")
    f["auth_prior_apps"] = a.prior
    f["auth_pending"] = a.pending
    f["auth_median_decision_days"] = a.median_days
    f["auth_withdraw_rate"] = (a.withdrawn + 0.5) / (a.resolved + 10)  # 10 sozde gozlemle duzlestirilmis

    o = _asof(hist, q, "operator")
    f["op_prior_apps"] = o.prior
    f["op_prior_withdrawn"] = o.withdrawn
    f["op_prior_resolved"] = o.resolved
    f["op_withdraw_rate"] = (o.withdrawn + 0.5) / (o.resolved + 10)

    u = _asof(hist, q, None)
    f["uk_pending"] = u.pending
    f["uk_median_decision_days"] = u.median_days

    f.index = q.app_id.values
    f.index.name = "app_id"
    return f[FEATURES]


if __name__ == "__main__":
    from cq.dataset import OUT

    apps = pd.read_parquet(OUT)
    f = build_features(apps)
    print(f.shape)
    print(f.describe().T[["count", "mean", "50%", "max"]].round(2).to_string())
