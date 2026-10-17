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


def claim(i, tech, tonnes=None, mwh=None, submitted="2026-01-05"):
    p = app(i, tech, None, submitted)
    p["project_features"].update(annual_co2e_reduction_t=tonnes, annual_energy_mwh=mwh)
    p["prediction"] = None  # REPD disi projede gecmis model yok: geri cekilme bilinmiyor
    return p


def test_claim_in_tonnes_gives_daily_rate():
    r = engine.carbon(claim(1, "heat_pump", tonnes=730), None, CFG, year=2026)
    assert r["daily_tco2"] == {"low": 2.0, "central": 2.0, "high": 2.0}
    assert "beyan" in r["methodology_reference"]


def test_claim_in_mwh_uses_emission_factor_band():
    b = engine.carbon(claim(1, "energy_efficiency", mwh=3650), None, CFG, year=2026)["daily_tco2"]
    assert b["central"] == pytest.approx(10 * 0.13276, rel=1e-3)  # 3650 MWh / 365 x 2028 merkezi faktor
    assert b["low"] < b["central"] < b["high"]


def test_tonnes_claim_wins_over_mwh_and_capacity_formula_wins_over_claim():
    assert engine.carbon(claim(1, "ev_charging", tonnes=365, mwh=10_000), None, CFG, year=2026)["daily_tco2"]["central"] == 1.0
    solar = app(1, "solar", 40.0)
    solar["project_features"]["annual_co2e_reduction_t"] = 1_000_000  # dogrulanmis MW formulu beyandan once gelir
    assert engine.carbon(solar, None, CFG, year=2026)["daily_tco2"]["central"] == pytest.approx(40 * 24 * 0.105 * 0.13276, rel=1e-3)


def test_unscored_technology_with_claim_is_scored_from_claim():
    battery = app(1, "battery", 50.0)
    battery["project_features"]["annual_co2e_reduction_t"] = 3650
    assert engine.carbon(battery, None, CFG, year=2026)["daily_tco2"]["central"] == 10.0


def test_claim_projects_join_the_same_queue_and_effort_rule():
    assert engine.effort(claim(1, "heat_pump", tonnes=100), CFG)["reviewer_hours"] == 8  # MW yok: taban puan
    projects = [claim(1, "heat_pump", tonnes=50), claim(2, "industrial_electrification", tonnes=20_000),
                app(3, "solar", 40.0), app(4, "battery", 20.0)]
    entries = {e["application_id"]: e for e in engine.schedule(projects, {"name": "carbon"}, 20, CFG)["entries"]}
    assert entries["app-2"]["position"] < entries["app-3"]["position"] < entries["app-1"]["position"]
    assert entries["app-2"]["lane"] == "carbon" and entries["app-2"]["score"] > 0
    assert entries["app-4"]["lane"] == "unscored"


def test_claim_project_without_any_claim_is_rejected():
    with pytest.raises(engine.EngineError):
        engine.carbon(claim(1, "heat_pump"), None, CFG)
    with pytest.raises(engine.EngineError):
        engine.carbon(claim(1, "heat_pump", tonnes=0), None, CFG)


def in_country(project, country):
    project["project_features"]["country"] = country
    return project


def test_turkish_energy_claim_uses_turkish_grid_factors():
    b = engine.carbon(in_country(claim(1, "energy_efficiency", mwh=3650), "TR"), None, CFG, year=2026)
    # verimlilik: birlesik marj "diger yenilenebilir"; gunes/ruzgar: birlesik marj gunes/ruzgar
    assert b["daily_tco2"] == {"low": pytest.approx(10 * 0.434), "central": pytest.approx(10 * 0.5410), "high": pytest.approx(10 * 0.7279)}
    assert "ETKB" in b["methodology_reference"]
    solar = in_country(claim(1, "solar", mwh=3650), "TR")
    solar["project_features"]["capacity_mw"] = 2.0
    assert engine.carbon(solar, None, CFG, year=2026)["daily_tco2"]["central"] == pytest.approx(10 * 0.6345)


def test_turkish_solar_without_load_factor_needs_an_energy_claim():
    solar = in_country(app(1, "solar", 10.0), "TR")
    r = engine.carbon(solar, None, CFG, year=2026)
    assert "yuk faktoru" in r["unscored_reason"]
    solar["project_features"]["annual_energy_mwh"] = 18_250  # belgedeki yillik uretim
    assert engine.carbon(solar, None, CFG, year=2026)["daily_tco2"]["central"] == pytest.approx(50 * 0.6345)


def test_country_aliases_and_default_are_great_britain():
    gb = engine.carbon(app(1, "solar", 40.0), None, CFG, year=2026)
    assert engine.carbon(in_country(app(1, "solar", 40.0), "uk"), None, CFG, year=2026) == gb
    assert engine.carbon(in_country(app(1, "solar", 40.0), "GB"), None, CFG, year=2026) == gb


def test_unknown_country_keeps_tonnes_claims_but_not_energy_claims():
    assert engine.carbon(in_country(claim(1, "heat_pump", tonnes=365), "ZZ"), None, CFG, year=2026)["daily_tco2"]["central"] == 1.0
    r = engine.carbon(in_country(claim(1, "heat_pump", mwh=1000), "ZZ"), None, CFG, year=2026)
    assert "emisyon faktoru tanimli degil" in r["unscored_reason"]


def test_same_project_ranks_higher_on_the_turkish_grid():
    gb, tr = claim(1, "energy_efficiency", mwh=3650), in_country(claim(2, "energy_efficiency", mwh=3650), "TR")
    entries = {e["application_id"]: e for e in engine.schedule([gb, tr], {"name": "carbon"}, 20, CFG)["entries"]}
    assert entries["app-2"]["score"] > entries["app-1"]["score"]


def test_other_countries_use_the_un_ifi_dataset():
    # Almanya, IFI v3.2: verimlilik birlesik marji 312,88; kesintili 523,39; faaliyet temelli marj 649,69 gCO2/kWh
    eff = engine.carbon(in_country(claim(1, "energy_efficiency", mwh=3650), "DE"), None, CFG, year=2026)
    assert eff["daily_tco2"] == {k: pytest.approx(v, abs=1e-3) for k, v in {"low": 3.1288, "central": 3.1288, "high": 6.4969}.items()}
    assert "IFI" in eff["methodology_reference"] and "Germany" in eff["methodology_reference"]
    wind = in_country(claim(2, "onshore_wind", mwh=3650), "DE")
    wind["project_features"]["capacity_mw"] = 5.0
    assert engine.carbon(wind, None, CFG, year=2026)["daily_tco2"]["central"] == pytest.approx(5.2339, abs=1e-3)


def test_ifi_dataset_covers_many_countries():
    from cqsim.engine import _ifi_table
    table = _ifi_table(str(engine.ROOT / CFG["carbon"]["ifi"]["file"]))
    assert len(table) > 200 and {"KE", "IN", "BR", "US", "DE"} <= set(table)
