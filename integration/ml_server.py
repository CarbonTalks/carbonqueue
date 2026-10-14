"""Local ML bridge: run with the model's Python environment, not the backend's.

The supplied predictor accepts a ProjectFeatures JSON dictionary and returns the
backend Prediction dictionary. No CatBoost or backend dependencies are imported.
"""

import argparse
import importlib
import json
import math
from http.server import BaseHTTPRequestHandler, HTTPServer


def valid_probability(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


def validate_prediction(result):
    if not isinstance(result, dict):
        raise TypeError("Prediction must be a dictionary")
    probability = result.get("withdrawal_probability_12m")
    bins = result.get("decision_distribution")
    if (
        not valid_probability(probability)
        or not isinstance(bins, list)
        or len(bins) != 13
        or not all(valid_probability(value) for value in bins)
        or abs(sum(bins) - 1) > 1e-6
    ):
        raise ValueError("Invalid prediction")
    return {"withdrawal_probability_12m": probability, "decision_distribution": bins}


def create_server(predict, host="127.0.0.1", port=9001):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(30)

        def log_message(self, format, *args):
            # Do not log feature payloads or model exceptions.
            pass

        def respond(self, status, body):
            payload = json.dumps(body, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path == "/health":
                self.respond(200, {"status": "ok"})
            else:
                self.respond(404, {"code": "NOT_FOUND"})

        def do_POST(self):
            if self.path != "/predict":
                self.respond(404, {"code": "NOT_FOUND"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 65536:
                    self.respond(413, {"code": "INVALID_REQUEST_SIZE"})
                    return
                features = json.loads(self.rfile.read(length))
                if not isinstance(features, dict):
                    raise TypeError("Expected feature object")
            except (ValueError, TypeError, OSError):
                self.respond(400, {"code": "INVALID_FEATURES"})
                return
            try:
                result = predict(features)
            except Exception:  # noqa: BLE001 - model failures must not expose private details
                self.respond(503, {"code": "ML_UNAVAILABLE"})
                return
            try:
                result = validate_prediction(result)
            except (ValueError, TypeError):
                self.respond(502, {"code": "ML_INVALID_RESPONSE"})
                return
            self.respond(200, result)

    return HTTPServer((host, port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--predictor",
        required=True,
        help="Trusted module:function accepting a feature dict",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9001)
    args = parser.parse_args()
    module, function = args.predictor.split(":", 1)
    predict = getattr(importlib.import_module(module), function)
    if not callable(predict):
        parser.error("Predictor must be callable")
    with create_server(predict, args.host, args.port) as server:
        print(f"ML bridge listening on {args.host}:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
