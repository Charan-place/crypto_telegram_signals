"""
Telegram webhook endpoint — receives bot commands from users.
Register URL with: python3 setup_webhook.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
from http.server import BaseHTTPRequestHandler

from lib.config import SYMBOLS, SCAN_INTERVAL, MIN_SCORE, MIN_RR
from lib.notifier import send_message


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = json.loads(self.rfile.read(length)) if length else {}

        message  = body.get("message", {})
        text     = message.get("text", "").strip().split("@")[0]  # strip @botname suffix
        chat_id  = str(message.get("chat", {}).get("id", ""))

        if text == "/start":
            send_message(
                f"🤖 <b>Crypto Signals Bot</b>\n\n"
                f"Your chat ID: <code>{chat_id}</code>\n\n"
                f"Bot runs 24/7 on Vercel. Signals fire automatically.\n"
                f"Use /status to see current config.",
                chat_id,
            )

        elif text == "/status":
            coins = "\n".join(f"  • {s}" for s in SYMBOLS)
            send_message(
                f"<b>Bot Status</b> ✅\n\n"
                f"<b>Scanning:</b>\n{coins}\n\n"
                f"<b>Scan interval:</b> {SCAN_INTERVAL}m\n"
                f"<b>Min strategies:</b> {MIN_SCORE}/5\n"
                f"<b>Min R:R:</b> 1:{MIN_RR}",
                chat_id,
            )

        elif text == "/help":
            send_message(
                "<b>Commands</b>\n\n"
                "/start  — show your chat ID\n"
                "/status — current config\n"
                "/help   — this message\n\n"
                "<b>Signal filter:</b> 3/5 strategies agree + R:R ≥ 2:1",
                chat_id,
            )

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass
