import importlib.util
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest


def load_server():
    path = Path(__file__).resolve().parents[1] / "integration" / "ml_server.py"
    spec = importlib.util.spec_from_file_location("cq_ml_server", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_separate_process_ml_bridge_uses_predictor_and_checks_output():
    module = load_server()
    seen = []

    def predict(features):
        seen.append(features)
        return {
            "withdrawal_probability_12m": 0.2,
            "decision_distribution": [0.0] * 12 + [1.0],
        }

    server = module.create_server(predict, "127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        request = urllib.request.Request(
            base + "/predict",
            data=json.dumps(
                {
                    "technology": "battery",
                    "capacity_mw": 52,
                    "has_storage": True,
                    "applicant": None,
                    "submission_date": None,
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            assert json.load(response)["withdrawal_probability_12m"] == 0.2
        assert seen[0]["technology"] == "battery"
        assert seen[0]["has_storage"] is True
        with urllib.request.urlopen(base + "/health") as response:
            assert json.load(response) == {"status": "ok"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize(
    "result",
    [
        {"withdrawal_probability_12m": 0.2, "decision_distribution": [1.0]},
        {"withdrawal_probability_12m": 2, "decision_distribution": [0.0] * 12 + [1.0]},
    ],
)
def test_invalid_model_output_fails_without_private_details(result):
    module = load_server()
    server = module.create_server(lambda features: result, "127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/predict",
            data=b'{"technology":"solar","capacity_mw":40}',
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request)
        assert error.value.code == 502
        assert json.load(error.value)["code"] == "ML_INVALID_RESPONSE"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
