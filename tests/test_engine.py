import pytest

from cqsim import engine
from cqsim.prepare import load_config

CFG = load_config()


def app(i, tech, mw, submitted="2026-01-05", p_wd=0.03):
    return {"application_id": f"app-{i}", "created_at": "2026-10-01T00:00:00Z",
            "project_features": {"technology": tech, "capacity_mw": mw, "submission_date": submitted},
            "prediction": {"withdrawal_probability_12m": p_wd, "decision_distribution": [1 / 13] * 13}}


def test_carbon_returns_daily_band():
    r = engine.carbon(app(1, "solar", 40.0), {"name": "default", "parameters": {}}, CFG, year=2026)
    assert set(r) == {"daily_tco2", "methodology_reference"}
    b = r["daily_tco2"]
    assert b["central"] == pytest.approx(40 * 24 * 0.105 * 0.13276, rel=1e-3)  # 2026 + 2 yil = 2028 faktoru
    assert 0 <= b["low"] <= b["central"] <= b["high"]


def test_battery_is_unscored_not_invented():
    r = engine.carbon(app(1, "battery", 50.0), None, CFG, year=2026)
    assert set(r) == {"unscored_reason", "methodology_reference"} and "depolama" in r["unscored_reason"]


def test_effort_uses_rule_and_has_storage():
    assert engine.effort(app(1, "solar", 0.5), CFG)["reviewer_hours"] == 8
    assert engine.effort(app(1, "solar", 40.0), CFG)["reviewer_hours"] == 16
    assert engine.effort(app(1, "battery", 40.0), CFG)["reviewer_hours"] == 20
    hybrid = app(1, "solar", 40.0)
    hybrid["project_features"]["has_storage"] = True  # gunes + batarya ortak basvuru
    assert engine.effort(hybrid, CFG)["reviewer_hours"] == 20


def test_schedule_returns_unique_positions_for_every_project():
    projects = [app(1, "solar", 0.5), app(2, "solar", 40.0), app(3, "battery", 20.0), app(4, "onshore_wind", 10.0)]
    for policy in ("FIFO", "carbon", "carbonqueue"):
        entries = engine.schedule(projects, {"name": policy, "parameters": {}}, 20, CFG)["entries"]
        assert sorted(e["position"] for e in entries) == [1, 2, 3, 4]
        assert {e["application_id"] for e in entries} == {p["application_id"] for p in projects}
    carbon = {e["application_id"]: e for e in engine.schedule(projects, {"name": "carbon"}, 20, CFG)["entries"]}
    assert carbon["app-2"]["position"] < carbon["app-1"]["position"]  # 40 MW, 0,5 MW'in onune gecer
    assert carbon["app-3"]["score"] is None  # batarya skorsuz
    assert carbon["app-3"]["lane"] == "unscored" and "Skorsuz yol" in carbon["app-3"]["reason"]
    assert all(e["planned_week"] >= 1 and e["reason"] for e in carbon.values())


def test_unknown_inputs_are_rejected():
    with pytest.raises(engine.EngineError):
        engine.schedule([app(1, "solar", 1.0)], {"name": "best"}, 10, CFG)
    with pytest.raises(engine.EngineError):
        engine.carbon(app(1, "offshore_wind", 100.0), None, CFG)


def test_simulate_returns_flat_metrics_from_results():
    r = engine.simulate_results({"application_ids": [], "parameters": {"year": 2023}, "projects": []}, CFG)
    assert r["metrics"]["gain_tco2_alpha_0.5_central"] == pytest.approx(44689.3)
    assert all(isinstance(v, float) for v in r["metrics"].values())
