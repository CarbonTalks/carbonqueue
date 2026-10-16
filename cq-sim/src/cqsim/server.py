"""Kuyruk motoru HTTP sunucusu: cq-backend'in HTTPQueueEngine sozlesmesi.

  POST /carbon    {"project": Application, "scenario": CarbonScenario} -> {"tonnes_co2e", "methodology_reference"}
  POST /effort    {"project": Application}                             -> {"reviewer_hours"}
  POST /schedule  {"projects": [Application], "policy", "capacity"}    -> {"entries": [{application_id, position, score}]}
  POST /simulate  {"application_ids", "parameters", "projects"}        -> {"metrics": {...}, "references": [...]}

Backend'de: CQ_QUEUE_ENGINE_URL=http://127.0.0.1:9002
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from cqsim import engine
from cqsim.prepare import load_config

PORT = 9002


def handle(path: str, body: dict, cfg: dict) -> dict:
    if path == "/carbon":
        return engine.carbon(body["project"], body.get("scenario"), cfg)
    if path == "/effort":
        return engine.effort(body["project"], cfg)
    if path == "/schedule":
        return engine.schedule(body["projects"], body["policy"], body["capacity"], cfg)
    if path == "/simulate":
        return engine.simulate_results(body, cfg)
    raise LookupError(path)


def serve(port: int = PORT, cfg: dict | None = None) -> None:
    cfg = cfg or load_config()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, body):
            data = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self._send(200, {"status": "ok"})

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                self._send(200, handle(self.path, body, cfg))
            except LookupError:
                self._send(404, {"error": f"bilinmeyen uc: {self.path}"})
            except (engine.EngineError, KeyError, TypeError, ValueError) as error:
                self._send(422, {"error": str(error)})

    print(f"kuyruk motoru: http://127.0.0.1:{port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
