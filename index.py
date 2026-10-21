"""
Vercel Python Entrypoint for the UTM FCIM Schedule Bot.
Handles both `/` and `/api/webhook` routes.
"""

import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import bot  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check, webhook info (`?info=1`), & webhook registration (`?setup=1`)."""
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            self._respond(500, "Missing TELEGRAM_BOT_TOKEN environment variable in Vercel.")
            return

        host = self.headers.get("x-forwarded-host") or self.headers.get("host") or ""
        tb = bot.TelegramBot(token)

        if "setup=1" in self.path and host:
            webhook_url = f"https://{host}/api/webhook"
            res = tb.api_call("setWebhook", {"url": webhook_url, "drop_pending_updates": False})
            tb.register_commands()
            info = tb.api_call("getWebhookInfo")
            self._respond(200, f"Webhook set to {webhook_url}\nsetWebhook: {json.dumps(res)}\ngetWebhookInfo: {json.dumps(info, indent=2)}")
            return

        if "info=1" in self.path:
            info = tb.api_call("getWebhookInfo")
            me = tb.api_call("getMe")
            self._respond(200, json.dumps({"bot": me.get("result"), "webhook": info.get("result")}, indent=2))
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

        content_len_str = self.headers.get("Content-Length") or self.headers.get("content-length")
        if content_len_str:
            raw_body = self.rfile.read(int(content_len_str))
        else:
            raw_body = self.rfile.read()

        try:
            upd = json.loads(raw_body.decode("utf-8") if raw_body else "{}")
            tb = bot.TelegramBot(token)
            if "message" in upd:
                tb.handle_message(upd["message"])
            elif "callback_query" in upd:
                tb.handle_callback(upd["callback_query"])
        except Exception:
            err = traceback.format_exc()
            print(f"[!] Webhook error:\n{err}", file=sys.stderr)
            self._respond(200, f"ERR: {err}")
            return

        self._respond(200, "OK")

    def _respond(self, status: int, body: str):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
