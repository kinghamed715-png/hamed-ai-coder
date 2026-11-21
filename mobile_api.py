import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

from main import ask_ai
from core.workspace import list_files, read_file, write_file

load_dotenv()

HOST = "127.0.0.1"
PORT = 8765
APP_KEY = "HAMED-LOCAL-APP-2026"
MAX_BODY = 1_100_000


class Handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        return self.headers.get("X-Local-App-Key") == APP_KEY

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("طول درخواست نامعتبر است.")

        if length < 1 or length > MAX_BODY:
            raise ValueError("حجم درخواست نامعتبر است.")

        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("JSON نامعتبر است.")

        if not isinstance(data, dict):
            raise ValueError("ساختار درخواست نامعتبر است.")

        return data

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            configured = bool(
                os.getenv("AI_API_KEY")
                and os.getenv("AI_PROVIDER", "").lower() == "groq"
            )
            return self.send_json(200, {
                "ok": True,
                "provider_configured": configured
            })

        if not self.authorized():
            return self.send_json(401, {"error": "دسترسی غیرمجاز."})

        if parsed.path == "/workspace/files":
            try:
                return self.send_json(200, {"files": list_files()})
            except Exception:
                return self.send_json(500, {"error": "خطا در فهرست فایل‌ها."})

        if parsed.path == "/workspace/file":
            path = parse_qs(parsed.query).get("path", [""])[0].strip()

            if not path:
                return self.send_json(400, {"error": "مسیر فایل وارد نشده است."})

            try:
                content = read_file(path)
                return self.send_json(200, {
                    "path": path,
                    "content": content
                })
            except FileNotFoundError as error:
                return self.send_json(404, {"error": str(error)})
            except (ValueError, OSError) as error:
                return self.send_json(400, {"error": str(error)})
            except Exception:
                return self.send_json(500, {"error": "خطا در خواندن فایل."})

        return self.send_json(404, {"error": "مسیر نامعتبر است."})

    def do_POST(self):
        if not self.authorized():
            return self.send_json(401, {"error": "دسترسی غیرمجاز."})

        try:
            data = self.read_json()
        except ValueError as error:
            return self.send_json(400, {"error": str(error)})

        if self.path == "/chat":
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

                return self.send_json(200, {
                    "reply": answer or "",
                    "session_id": new_session
                })
            except Exception:
                return self.send_json(500, {"error": "خطای داخلی سرور."})

        if self.path == "/workspace/write":
            path = data.get("path")
            content = data.get("content")
            confirmed = data.get("confirm")

            if not isinstance(path, str) or not path.strip():
                return self.send_json(400, {"error": "مسیر فایل نامعتبر است."})

            if not isinstance(content, str):
                return self.send_json(400, {"error": "محتوای فایل باید متن باشد."})

            if confirmed is not True:
                return self.send_json(403, {
                    "error": "ذخیره‌سازی نیازمند تأیید صریح است."
                })

            try:
                saved = write_file(path, content)
                return self.send_json(200, {
                    "saved": True,
                    "path": saved,
                    "backup_created": True
                })
            except (ValueError, TypeError, OSError) as error:
                return self.send_json(400, {"error": str(error)})
            except Exception:
                return self.send_json(500, {"error": "خطا در ذخیره فایل."})

        return self.send_json(404, {"error": "مسیر نامعتبر است."})

    def log_message(self, fmt, *args):
        print("[mobile-api]", fmt % args)


if __name__ == "__main__":
    print(f"HAMED AI CODER API: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
