"""
Vercel Python Entrypoint for the UTM FCIM Schedule Bot.
Handles both `/` and `/api/webhook` routes.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import bot  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check & automatic webhook registration helper (`?setup=1`)."""
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            self._respond(500, "Missing TELEGRAM_BOT_TOKEN environment variable in Vercel.")
            return

        host = self.headers.get("x-forwarded-host") or self.headers.get("host") or ""
        if "setup=1" in self.path and host:
            webhook_url = f"https://{host}/api/webhook"
            tb = bot.TelegramBot(token)
            res = tb.api_call("setWebhook", {"url": webhook_url})
            tb.register_commands()
            self._respond(200, f"Webhook set to {webhook_url}\nResponse: {json.dumps(res)}")
            return

        self._respond(
            200,
            "UTM FCIM Schedule Bot Webhook is active!\n"
            "To register the Telegram webhook, visit: https://" + host + "/api/webhook?setup=1",
        )

    def do_POST(self):
        """Receive Telegram update via Webhook and process it immediately."""
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            self._respond(500, "Missing TELEGRAM_BOT_TOKEN")
            return

        content_len = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            upd = json.loads(raw_body.decode("utf-8"))
            tb = bot.TelegramBot(token)
            if "message" in upd:
                tb.handle_message(upd["message"])
            elif "callback_query" in upd:
                tb.handle_callback(upd["callback_query"])
        except Exception as exc:
            print(f"[!] Webhook error: {exc}", file=sys.stderr)

        self._respond(200, "OK")

    def _respond(self, status: int, body: str):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
