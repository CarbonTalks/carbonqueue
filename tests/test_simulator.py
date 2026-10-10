import copy

import numpy as np
import pandas as pd
import pytest

from cqsim.metrics import summarize
from cqsim import live
from cqsim.prepare import DATA, daily_tco2, effort_hours, load_config
from cqsim.simulator import POLICIES, simulate

CFG = load_config()
START = pd.Timestamp(2022, 1, 1)


def queue(rows):
    """rows: (basvuru gunu, MW, kategori, cikis gunu ya da None). Efor sabit 10 saat."""
    q = pd.DataFrame(rows, columns=["day", "app_generation_mw", "category", "exit_day"])
    q["app_id"] = np.arange(len(q))
    q["arrival"] = START + pd.to_timedelta(q.day, "D")
    q["exit"] = START + pd.to_timedelta(q.exit_day, "D")
    q["daily_tco2"] = daily_tco2(q.category, q.app_generation_mw, CFG)
    q["scored"] = q.daily_tco2.notna()
    q["effort"] = 10.0
    q["small"] = q.scored & (q.app_generation_mw < 1)
    q["p_withdraw_12m"] = 0.03
    q["counts"] = q.scored & q.exit.isna()
    q["unresolved"] = False
    return q.sort_values(["arrival", "app_id"]).reset_index(drop=True)


MIXED = queue([(0, 0.5, "solar", None), (0, 40, "solar", None), (0, None, "storage", None),
               (0, 5, "onshore_wind", None), (7, 20, "solar", None), (7, 0.3, "solar", None)])


def test_carbon_and_effort_rules():
    cat, mw = pd.Series(["solar", "onshore_wind", "storage"]), pd.Series([10.0, 10.0, 10.0])
    d = daily_tco2(cat, mw, CFG)
    assert d[0] == pytest.approx(10 * 24 * 0.10 * 0.207) and d[1] > d[0] and np.isnan(d[2])
    e = effort_hours(pd.Series([0.5, 5.0, 30.0]), pd.Series([False, False, True]), CFG)
    assert list(e) == [8, 12, 20]


def test_fifo_follows_arrival_order():
    res = simulate(MIXED, "fifo", CFG, START, capacity=10)
    assert res.done.is_monotonic_increasing and res.done.notna().all()


@pytest.mark.parametrize("policy", POLICIES)
def test_every_file_is_fully_reviewed_within_capacity(policy):
    res = simulate(MIXED, policy, CFG, START, capacity=10)
    assert np.allclose(res.spent, MIXED.effort)
    weeks = (res.done.max() - START).days / 7
    assert res.spent.sum() <= 10 * weeks + 1e-6


def test_carbon_puts_large_project_first_and_fifo_gain_is_zero():
    fifo = simulate(MIXED, "fifo", CFG, START, capacity=10)
    res = simulate(MIXED, "carbon", CFG, START, capacity=10)
    assert res.done[1] < res.done[0]  # 40 MW, 0,5 MW'in onune gecer
    assert summarize(MIXED, fifo, fifo, CFG)["carbon_gain_tco2_vs_fifo"]["alpha_1.0"]["central"] == 0
    assert summarize(MIXED, res, fifo, CFG)["carbon_gain_tco2_vs_fifo"]["alpha_1.0"]["central"] > 0


def test_unscored_lane_is_not_starved():
    q = queue([(0, None, "storage", None)] * 5 + [(0, 30, "solar", None)] * 20)
    res = simulate(q, "carbon", CFG, START, capacity=10)
    # skorsuz yol efor payi kadar kapasite alir: ilk skorsuz dosya kuyrugun ilk beste birinde biter
    assert (res.done[0] - START).days <= 7 * 6 and (res.done.max() - START).days == 7 * 25


def test_withdrawn_file_leaves_unreviewed_or_wastes_effort():
    q = queue([(0, 30, "solar", None), (0, 30, "solar", None), (0, 1, "solar", 10)])
    late = simulate(q, "carbon", CFG, START, capacity=10)  # sirasi gelmeden geri cekilir
    assert pd.isna(late.done[2]) and late.spent[2] == 0
    early = simulate(q, "fifo", CFG, START, capacity=100)  # sirasi once gelir: efor bosa gider, katki sifir
    assert early.spent[2] == 10
    assert summarize(q, early, early, CFG)["wasted_hours_on_withdrawn"] == 10


def test_max_wait_tier_bounds_small_project_wait():
    q = queue([(0, 0.2, "solar", None)] + [(d, 40, "solar", None) for d in range(0, 700, 7) for _ in range(2)])
    plain = simulate(q, "carbon_withdrawal_effort", CFG, START, capacity=20)
    fair = simulate(q, "carbonqueue", CFG, START, capacity=20)
    assert fair.done[0] < plain.done[0]


def test_overloaded_max_wait_tier_collapses_to_fifo_unless_capped():
    q = queue([(-800 + d, mw, "solar", None) for d in range(0, 350, 7) for mw in (0.5, 10 + d)])  # hepsi suresini asmis; yeni dosyalar daha buyuk
    fifo = simulate(q, "fifo", CFG, START, capacity=10)
    full = simulate(q, "carbonqueue", CFG, START, capacity=10)
    assert (full.order == fifo.order).all()
    capped = copy.deepcopy(CFG)
    capped["queue"]["max_wait_capacity_share"] = 0.5
    res = simulate(q, "carbonqueue", capped, START, capacity=10)
    assert summarize(q, res, fifo, capped)["carbon_gain_tco2_vs_fifo"]["alpha_1.0"]["central"] > 0


@pytest.mark.skipif(not (DATA / "predictions" / "predictions_live.parquet").exists(), reason="cq-model ciktilari yok")
def test_live_rank_is_a_complete_ordering():
    r = live.rank(CFG)
    for policy in live.TOGGLE:
        assert sorted(f["position"][policy] for f in r["files"]) == list(range(1, len(r["files"]) + 1))
    assert all(f["reason"] for f in r["files"]) and not any(f["stale"] for f in r["files"])
    assert all((f["daily_tco2"] is None) == (f["lane"] == "unscored") for f in r["files"] if f["lane"] != "max_wait")
