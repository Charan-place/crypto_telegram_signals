import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
import hmac
import hashlib
from flask import Flask, request, jsonify

from lib.config import SYMBOLS, TF_PRIMARY, TF_TREND, SCAN_INTERVAL, MIN_SCORE, MIN_RR
from lib.fetcher import fetch_ohlcv
from lib.signal_engine import analyze
from lib.store import is_cooldown, set_cooldown
from lib.notifier import send_signal, send_message

app = Flask(__name__)

_CRON_SECRET    = os.getenv("CRON_SECRET", "")
_WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
_CHAT_ID        = os.getenv("TELEGRAM_CHAT_ID", "")


# ─── Auth guards ──────────────────────────────────────────────────────────────

def _valid_cron() -> bool:
    """Check cron-job.org sends correct secret header."""
    if not _CRON_SECRET:
        return True  # secret not configured → open (warn in logs)
    return request.headers.get("X-Cron-Secret", "") == _CRON_SECRET


def _valid_webhook() -> bool:
    """Validate request is genuinely from Telegram."""
    if not _WEBHOOK_SECRET:
        return True
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    return hmac.compare_digest(token, _WEBHOOK_SECRET)


def _authorized_chat(chat_id: str) -> bool:
    """Only respond to commands from the configured chat."""
    return not _CHAT_ID or chat_id == _CHAT_ID


# ─── Scanner ──────────────────────────────────────────────────────────────────

async def _scan() -> list:
    tasks = []
    for symbol in SYMBOLS:
        tasks.append(fetch_ohlcv(symbol, TF_PRIMARY))
        tasks.append(fetch_ohlcv(symbol, TF_TREND))

    results = await asyncio.gather(*tasks)
    fired = []

    for i, symbol in enumerate(SYMBOLS):
        df_15m = results[i * 2]
        df_1h  = results[i * 2 + 1]
        if df_15m is None or df_1h is None:
            continue
        signal = analyze(symbol, df_15m, df_1h)
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
    if not _valid_cron():
        return jsonify({"error": "unauthorized"}), 401
    try:
        fired = asyncio.run(_scan())
        return jsonify({"ok": True, "signals": fired})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ─── Telegram Webhook ─────────────────────────────────────────────────────────

@app.route("/api/webhook", methods=["POST"])
def webhook():
    if not _valid_webhook():
        return "Forbidden", 403

    body    = request.get_json(silent=True) or {}
    message = body.get("message", {})
    text    = message.get("text", "").strip().split("@")[0]
    chat_id = str(message.get("chat", {}).get("id", ""))

    # Ignore messages from unknown chats
    if not _authorized_chat(chat_id):
        return "OK", 200

    if text == "/start":
        send_message(
            f"🤖 <b>Crypto Signals Bot</b>\n\n"
            f"Your chat ID: <code>{chat_id}</code>\n\n"
            f"Bot runs 24/7 on Vercel. Signals fire automatically.\n"
            f"Use /status to see current config.",
            chat_id,
        )
    elif text == "/status":
        display = [s.split(":")[0] + " PERP" if ":" in s else s for s in SYMBOLS]
        coins   = "\n".join(f"  • {s}" for s in display)
        send_message(
            f"<b>Bot Status</b> ✅\n\n"
            f"<b>Market:</b> Binance Futures\n"
            f"<b>Scanning:</b>\n{coins}\n\n"
            f"<b>Timeframe:</b> {TF_PRIMARY} + {TF_TREND}\n"
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


# ─── Health check (no sensitive info) ────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({"status": "ok"})
