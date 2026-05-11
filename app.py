import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from flask import Flask, request, jsonify

from lib.config import SYMBOLS, TF_PRIMARY, TF_TREND, SCAN_INTERVAL, MIN_SCORE, MIN_RR
from lib.fetcher import fetch_ohlcv
from lib.signal_engine import analyze
from lib.store import is_cooldown, set_cooldown
from lib.notifier import send_signal, send_message

app = Flask(__name__)


# ─── Scanner ──────────────────────────────────────────────────────────────────

async def _scan() -> list:
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


@app.route("/api/scan", methods=["GET", "POST"])
def scan():
    try:
        fired = asyncio.run(_scan())
        return jsonify({"ok": True, "signals": fired})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ─── Telegram Webhook ─────────────────────────────────────────────────────────

@app.route("/api/webhook", methods=["POST"])
def webhook():
    body    = request.get_json(silent=True) or {}
    message = body.get("message", {})
    text    = message.get("text", "").strip().split("@")[0]
    chat_id = str(message.get("chat", {}).get("id", ""))

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

    return "OK", 200


# ─── Health check ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({"status": "ok", "coins": SYMBOLS})
