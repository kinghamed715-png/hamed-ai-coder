import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from dotenv import load_dotenv

from main import ask_ai

load_dotenv()

HOST = "127.0.0.1"
PORT = 8765
APP_KEY = "HAMED-LOCAL-APP-2026"
MAX_BODY = 20000


class Handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/health":
            return self.send_json(404, {"error": "مسیر نامعتبر است."})

        configured = bool(
            os.getenv("AI_API_KEY")
            and os.getenv("AI_PROVIDER", "").lower() == "groq"
        )

        self.send_json(200, {
            "ok": True,
            "provider_configured": configured
        })

    def do_POST(self):
        if self.path != "/chat":
            return self.send_json(404, {"error": "مسیر نامعتبر است."})

        if self.headers.get("X-Local-App-Key") != APP_KEY:
            return self.send_json(401, {"error": "دسترسی غیرمجاز."})

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.send_json(400, {"error": "درخواست نامعتبر است."})

        if length < 1 or length > MAX_BODY:
            return self.send_json(413, {"error": "حجم درخواست نامعتبر است."})

        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self.send_json(400, {"error": "JSON نامعتبر است."})

        if not isinstance(data, dict):
            return self.send_json(400, {"error": "ساختار پیام نامعتبر است."})

        message = data.get("message", "")
        session_id = data.get("session_id")

        if not isinstance(message, str) or not message.strip():
            return self.send_json(400, {"error": "پیام خالی است."})

        if len(message) > 8000:
            return self.send_json(413, {"error": "پیام بیش از حد طولانی است."})

        if session_id is not None:
            if not isinstance(session_id, str) or not re.fullmatch(
                r"[A-Za-z0-9_-]{8,80}", session_id
            ):
                return self.send_json(400, {"error": "شناسه گفتگو نامعتبر است."})

        try:
            answer, new_session, error = ask_ai(message.strip(), session_id)

            if error:
                return self.send_json(502, {"error": str(error)[:2000]})

            self.send_json(200, {
                "reply": answer or "",
                "session_id": new_session
            })

        except Exception:
            self.send_json(500, {"error": "خطای داخلی سرور."})

    def log_message(self, fmt, *args):
        print("[mobile-api]", fmt % args)


if __name__ == "__main__":
    print(f"HAMED AI CODER API: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
