"""Local helper API. Two jobs:

1. Resume upload: always goes through here, in every mode. The resume file
   lives on your machine and structuring it needs GEMINI_API_KEY, which must
   never be shipped to the deployed frontend's JS bundle — so run this
   locally whenever you want to upload or replace your resume, and it writes
   straight to whichever storage backend your .env points at (Supabase in
   production, local SQLite in dev).
2. Local dev shim: when no Supabase project is configured yet, the frontend
   also uses this for browsing/approving the queue (in production it talks
   to Supabase's PostgREST API directly instead).

Serves over HTTPS (self-signed, generated on first run) rather than plain
HTTP: browsers — Safari in particular — block an HTTPS page (the deployed
frontend) from fetching plain http:// content at all, even to localhost,
with no way for the server to opt out via headers. HTTPS-to-HTTPS avoids
that entirely. The first time you use it in a given browser, visit
https://localhost:8787/resume directly once and accept the "not private"
warning — that's expected for a self-signed local-only certificate, not a
sign anything is wrong.

Run: python -m scripts.local_server
Serves on https://localhost:8787
"""

import base64
import json
import re
import ssl
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from storage import db
from tailor.resume_parser import parse_resume_bytes

PORT = 8787
CERT_DIR = Path(__file__).parent / "certs"
CERT_FILE = CERT_DIR / "localhost.pem"
KEY_FILE = CERT_DIR / "localhost-key.pem"


def ensure_cert():
    if CERT_FILE.exists() and KEY_FILE.exists():
        return
    CERT_DIR.mkdir(exist_ok=True)
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", str(KEY_FILE), "-out", str(CERT_FILE), "-days", "3650",
            "-subj", "/CN=localhost",
            "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
        ],
        check=True, capture_output=True,
    )


class Handler(BaseHTTPRequestHandler):
    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        # Required for browsers (Chrome's Private Network Access) to let an
        # HTTPS page (the deployed frontend) call http://localhost at all.
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def _send(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_OPTIONS(self):
        self._send(200, {})

    def do_GET(self):
        if self.path.startswith("/applications"):
            status = None
            if "?" in self.path:
                qs = self.path.split("?", 1)[1]
                for pair in qs.split("&"):
                    if pair.startswith("status="):
                        status = pair.split("=", 1)[1]
            self._send(200, db.list_applications(status=status))
        elif self.path == "/resume":
            resume = db.get_latest_resume()
            self._send(200, resume or {})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/resume":
            try:
                body = self._body()
                filename = body["filename"]
                data = base64.b64decode(body["content_base64"])
                raw_text, structured = parse_resume_bytes(filename, data)
                resume_id = db.save_resume(filename, raw_text, structured, file_bytes=data)
                self._send(200, {"id": resume_id, "structured": structured})
            except Exception as exc:
                self._send(400, {"error": str(exc)})
        else:
            self._send(404, {"error": "not found"})

    def do_PATCH(self):
        match = re.match(r"^/applications/(\d+)$", self.path)
        if not match:
            self._send(404, {"error": "not found"})
            return
        db.update_application_status(int(match.group(1)), self._body()["status"])
        self._send(200, {"ok": True})

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    ensure_cert()
    server = HTTPServer(("localhost", PORT), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=str(CERT_FILE), keyfile=str(KEY_FILE))
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    print(f"Local server (storage backend={db.BACKEND}) on https://localhost:{PORT}")
    print("First time in a given browser: visit that URL once and accept the "
          "self-signed certificate warning (Safari: 'visit this website').")
    server.serve_forever()
