"""Ayrik zamanli model icin 30 gunluk dilimler, bolme ve bilgi kesim tarihi.

Sira her zaman: basvuruyu bolume ata -> kesim tarihini uygula -> dilimleri uret.
Etiketler: 0 = hicbir sey, 1 = ilk karar, 2 = geri cekilme (izin/red ayrimi yok).
"""
import numpy as np
import pandas as pd

BIN_DAYS = 30
HORIZON_BINS = 12  # 12 x 30 = 360 gun ("12 ay")
LABEL = {"decision": 1, "withdrawal": 2}


def eligible(apps: pd.DataFrame) -> pd.DataFrame:
    """Modelin gorebilecegi basvurular: ana bilesen, gecerli tarih, kapsam ici."""
    return apps[apps.model_eligible].copy()


def assign_split(apps: pd.DataFrame, cutoff: pd.Timestamp, eval_end: pd.Timestamp | None = None) -> pd.Series:
    """Basvuruyu bolume atar. Zincirler bolunmez: zincir, ilk basvurusunun tarihine gore atanir.

    train: zincirin ilk basvurusu <= cutoff ve basvurunun kendisi <= cutoff
    eval : zincirin ilk basvurusu (cutoff, eval_end] araliginda
    Zinciri egitimde olup kendisi cutoff'tan sonra gelen yeniden basvurular hicbir bolume girmez.
    """
    chain_start = apps.groupby("chain_id").d_submitted.transform("min")
    split = pd.Series(pd.NA, index=apps.index, dtype="string")
    split[(chain_start <= cutoff) & (apps.d_submitted <= cutoff)] = "train"
    if eval_end is not None:
        split[(chain_start > cutoff) & (chain_start <= eval_end) & (apps.d_submitted <= eval_end)] = "eval"
    return split


def expand(apps: pd.DataFrame, observe_until: pd.Timestamp) -> pd.DataFrame:
    """Her basvuruyu observe_until'e kadar gorulebilen 30 gunluk dilimlere acar.

    Olay observe_until'den sonraysa gorunmez; basvuru o anda acik (sansurlu) sayilir ve
    yalnizca tamamlanmis dilimleri uretilir. Olay satiri, olayin oldugu dilimdir.
    """
    a = apps[apps.d_submitted <= observe_until]
    seen = a.d_event.notna() & (a.d_event <= observe_until)
    event_days = (a.d_event - a.d_submitted).dt.days
    censor_days = (observe_until - a.d_submitted).dt.days
    n_bins = np.where(seen, event_days // BIN_DAYS + 1, censor_days // BIN_DAYS).astype(int)
    label_last = np.where(seen, a.event.map(LABEL).fillna(0), 0).astype(int)

    rows = np.repeat(np.arange(len(a)), n_bins)
    k = np.concatenate([np.arange(1, n + 1) for n in n_bins]) if len(rows) else np.array([], int)
    last = np.r_[np.cumsum(n_bins)] - 1
    label = np.zeros(len(rows), int)
    label[last[n_bins > 0]] = label_last[n_bins > 0]

    out = pd.DataFrame({
        "app_id": a.app_id.values[rows],
        "bin": k,
        "label": label,
    })
    start = a.d_submitted.values[rows] + pd.to_timedelta((k - 1) * BIN_DAYS, "D")
    out["bin_start"] = start
    out["bin_end"] = start + pd.Timedelta(days=BIN_DAYS)
    # Satirin bilgisi ne zaman kesinlesti: olay satirinda olay tarihi, digerlerinde dilim sonu.
    ev = a.d_event.values[rows]
    out["info_date"] = np.where(label > 0, ev, out.bin_end.values)
    out["info_date"] = pd.to_datetime(out.info_date)
    return out


def training_table(apps: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    """cutoff kesimli model icin egitim dilimleri, has_time icin bilgi tarihine gore sirali."""
    apps = eligible(apps)
    train = apps[assign_split(apps, cutoff) == "train"]
    return expand(train, cutoff).sort_values(["info_date", "app_id", "bin"], kind="stable").reset_index(drop=True)


def app_labels(apps: pd.DataFrame, observe_until: pd.Timestamp, horizon_bins: int = HORIZON_BINS) -> pd.DataFrame:
    """Basvuru duzeyinde degerlendirme etiketleri (360 gun ufku).

    withdraw_12m: 1/0; ufuk dolmadan sansurlenip olay gormeyenlerde bos.
    decision_bin: ilk kararin dilimi (1..horizon) ya da horizon+1 = "ufuk icinde karar yok"; bilinmiyorsa bos.
    """
    horizon = horizon_bins * BIN_DAYS
    seen = apps.d_event.notna() & (apps.d_event <= observe_until)
    days = (apps.d_event - apps.d_submitted).dt.days.where(seen)
    followed = (observe_until - apps.d_submitted).dt.days >= horizon
    known = (days < horizon) | followed
    in_h = days < horizon
    withdraw = ((apps.event == "withdrawal") & in_h).astype(float).where(known)
    dec_bin = np.where((apps.event == "decision") & in_h, days // BIN_DAYS + 1, horizon_bins + 1)
    return pd.DataFrame({
        "app_id": apps.app_id.values,
        "withdraw_12m": withdraw.values,
        "decision_bin": pd.Series(dec_bin, index=apps.index).where(known).values,
    })
