"""
Vercel cron endpoint — triggered every 2 minutes via vercel.json.
Scans all coins concurrently and fires signals when conditions are met.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
import json
from http.server import BaseHTTPRequestHandler

from lib.config import SYMBOLS, TF_PRIMARY, TF_TREND
from lib.fetcher import fetch_ohlcv
from lib.signal_engine import analyze
from lib.store import is_cooldown, set_cooldown
from lib.notifier import send_signal


async def _scan() -> list[str]:
    # Fetch all symbols + timeframes concurrently
    tasks = []
    for symbol in SYMBOLS:
        tasks.append(fetch_ohlcv(symbol, TF_PRIMARY))
        tasks.append(fetch_ohlcv(symbol, TF_TREND))

    results = await asyncio.gather(*tasks)
    fired = []

    for i, symbol in enumerate(SYMBOLS):
        df_1h = results[i * 2]
        df_4h = results[i * 2 + 1]

        if df_1h is None or df_4h is None:
            continue

        signal = analyze(symbol, df_1h, df_4h)
        if signal is None:
            continue

        if is_cooldown(symbol, signal.direction):
            continue

        set_cooldown(symbol, signal.direction)
        send_signal(signal)
        fired.append(f"{symbol} {signal.direction} score={signal.score}/5")

    return fired


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            fired = asyncio.run(_scan())
            body = json.dumps({"ok": True, "signals": fired}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_POST(self):
        self.do_GET()

    def log_message(self, format, *args):
        pass
