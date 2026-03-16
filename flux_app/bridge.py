import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from .config import BRIDGE_PORT
from .embeddings import embed_text
from .utils import json_dumps


class BridgeHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, code: int = 200) -> None:
        body = json_dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/health"):
            self._send_json({"status": "ok", "service": "bridge"})
            return
        self._send_json({"error": "not found"}, code=404)

    def do_POST(self):
        if self.path.startswith("/embed"):
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8", errors="ignore")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {}
            text = payload.get("text", "")
            dim = int(payload.get("dim", 200))
            vec = embed_text(text, dim=dim)
            self._send_json({"vector": vec})
            return
        self._send_json({"error": "not found"}, code=404)


def run() -> None:
    server = HTTPServer(("", BRIDGE_PORT), BridgeHandler)
    print(f"Bridge listening on :{BRIDGE_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
