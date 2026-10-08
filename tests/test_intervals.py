"""Dilimleme ve sizinti testleri. Calistirma: PYTHONPATH=src python tests/test_intervals.py (ya da pytest)."""
import pandas as pd

from cq.dataset import OUT as APPLICATIONS
from cq.intervals import BIN_DAYS, app_labels, assign_split, eligible, expand, training_table

T = pd.Timestamp


def toy():
    return pd.DataFrame({
        "app_id": [1, 2, 3, 4, 5],
        "chain_id": [1, 2, 3, 4, 4],
        "d_submitted": [T("2022-01-01"), T("2022-01-01"), T("2022-11-01"), T("2022-06-01"), T("2023-03-01")],
        "event": ["decision", "withdrawal", "decision", "open", "decision"],
        "d_event": [T("2022-04-05"), T("2022-01-20"), T("2023-02-01"), pd.NaT, T("2023-05-01")],
        "model_eligible": True,
    })


def test_event_row_and_labels():
    rows = expand(toy().iloc[:2], T("2022-12-31"))
    a = rows[rows.app_id == 1]
    assert list(a.label) == [0, 0, 0, 1]  # 94. gun -> 4. dilim
    b = rows[rows.app_id == 2]
    assert list(b.label) == [2]  # 19. gun -> 1. dilim, geri cekilme


def test_event_after_cutoff_is_invisible():
    rows = expand(toy().iloc[[2]], T("2022-12-31"))  # karar 2023'te
    assert (rows.label == 0).all()
    assert len(rows) == (T("2022-12-31") - T("2022-11-01")).days // BIN_DAYS
    assert (rows.info_date <= T("2022-12-31")).all()


def test_chain_not_split():
    s = assign_split(toy(), T("2022-12-31"), T("2023-12-31"))
    assert s[3] == "train"
    assert pd.isna(s[4])  # ayni zincirin cutoff sonrasi basvurusu: hicbir bolume girmez


def test_app_labels_censoring():
    lab = app_labels(toy(), T("2022-12-31")).set_index("app_id")
    assert lab.loc[2, "withdraw_12m"] == 1
    assert lab.loc[1, "withdraw_12m"] == 0 and lab.loc[1, "decision_bin"] == 4
    assert pd.isna(lab.loc[4, "withdraw_12m"])  # 360 gun dolmadi, olay yok


def test_real_data_no_leakage():
    apps = pd.read_parquet(APPLICATIONS)
    cutoff = T("2022-12-31")
    rows = training_table(apps, cutoff)
    assert (rows.info_date <= cutoff).all()
    assert rows.info_date.is_monotonic_increasing
    assert (rows[rows.label > 0].groupby("app_id").size() == 1).all()
    last_bin = rows.groupby("app_id").bin.transform("max")
    assert (rows[rows.label > 0].bin == last_bin[rows.label > 0]).all()  # olaydan sonra satir yok
    e = eligible(apps)
    s = assign_split(e, cutoff, T("2023-12-31"))
    assert e.groupby("chain_id").apply(lambda g: s[g.index].dropna().nunique() <= 1).all()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
