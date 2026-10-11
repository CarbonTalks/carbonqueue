"""Backend tahmin fonksiyonu: cikti backend'in Prediction sozlesmesine uymali.

Calistirma: PYTHONPATH=src python tests/test_serve.py  (data/models/model_live.cbm gerekir)
"""
import time

import numpy as np

from cq.serve import load_predictor

P = load_predictor()
HANWELL = {"technology": "solar", "capacity_mw": 40.0, "planning_authority": "Cherwell District Council",
           "applicant": "Elgin Energy", "submission_date": "2025-07-25"}


def check(out):
    assert set(out) == {"withdrawal_probability_12m", "decision_distribution"}
    assert 0 <= out["withdrawal_probability_12m"] <= 1
    d = out["decision_distribution"]
    assert len(d) == 13 and all(0 <= x <= 1 for x in d) and abs(sum(d) - 1) < 1e-6


def test_contract_and_speed():
    t = time.perf_counter()
    check(P(HANWELL))
    assert time.perf_counter() - t < 5  # backend 30 sn bekliyor


def test_authority_matching():
    assert P.authority("Cherwell District Council") == "Cherwell"
    assert P.authority("cherwell") == "Cherwell"
    assert P.authority("Nowhere Council") is None


def test_unknown_inputs_still_predict():
    check(P({"technology": "battery", "capacity_mw": 52.0}))  # kurum, sahip, tarih yok
    check(P({"technology": "onshore_wind", "capacity_mw": 12.6, "planning_authority": "Nowhere Council"}))


def test_object_input():
    class Obj:  # backend ProjectFeatures nesnesi gibi
        technology, capacity_mw, planning_authority, applicant, submission_date = "solar", 0.4, "Cherwell", None, None
    check(P(Obj()))


def test_unsupported_technology():
    try:
        P({"technology": "heat_pump", "capacity_mw": 1.0})
    except ValueError:
        return
    raise AssertionError("kapsam disi teknoloji hata vermeli")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    out = P(HANWELL)
    print("Hanwell:", round(out["withdrawal_probability_12m"], 4), np.round(out["decision_distribution"], 3).tolist())
