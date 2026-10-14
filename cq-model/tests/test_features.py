"""Ozelliklerin basvuru tarihi itibariyla hesaplandigini test eder. Calistirma: PYTHONPATH=src python tests/test_features.py"""
import numpy as np
import pandas as pd

from cq.dataset import OUT as APPLICATIONS
from cq.features import NUMERIC, build_features


def truncate(apps: pd.DataFrame, d: pd.Timestamp) -> pd.DataFrame:
    """Veriyi d tarihinde gorundugu hale getirir: sonraki basvurular yok, sonraki olaylar olmamis."""
    a = apps[apps.d_submitted.isna() | (apps.d_submitted <= d)].copy()
    late = a.d_event > d
    a.loc[late, ["d_event", "duration_days"]] = np.nan
    a.loc[late, "event"] = "open"
    return a


def test_features_do_not_see_the_future():
    apps = pd.read_parquet(APPLICATIONS)
    d = pd.Timestamp("2019-06-30")
    full = build_features(apps)
    cut = build_features(truncate(apps, d))
    ids = apps.loc[apps.d_submitted <= d, "app_id"]
    pd.testing.assert_frame_equal(full.loc[ids, NUMERIC], cut.loc[ids, NUMERIC], check_dtype=False)


if __name__ == "__main__":
    test_features_do_not_see_the_future()
    print("ok test_features_do_not_see_the_future")
