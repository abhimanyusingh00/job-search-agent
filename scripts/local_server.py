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

Run: python -m scripts.local_server
Serves on http://localhost:8787
"""

import base64
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

from storage import db
from tailor.resume_parser import parse_resume_bytes

PORT = 8787


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
    print(f"Local server (storage backend={db.BACKEND}) on http://localhost:{PORT}")
    HTTPServer(("localhost", PORT), Handler).serve_forever()
