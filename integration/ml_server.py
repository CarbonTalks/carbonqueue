"""cq-model tahmin fonksiyonunu backend'in HTTP sozlesmesiyle sunar: POST /predict (ProjectFeatures JSON).

Backend Python 3.14 ile calisir; model ise catboost/pandas kurulu herhangi bir Python ortaminda ayri surec olarak
calisir. Backend'e CQ_ML_URL=http://127.0.0.1:9001 ile baglanir.

Calistirma: python integration/ml_server.py
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cq-model" / "src"))
from cq.serve import load_predictor  # noqa: E402

PORT = 9001
PREDICT = load_predictor()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200, {"status": "ok"})

    def do_POST(self):
        if self.path != "/predict":
            return self._send(404, {"error": "not found"})
        try:
            project = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            self._send(200, PREDICT(project))
        except ValueError as error:  # desteklenmeyen teknoloji ya da bozuk girdi
            self._send(422, {"error": str(error)})


if __name__ == "__main__":
    print(f"ml server: http://127.0.0.1:{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
