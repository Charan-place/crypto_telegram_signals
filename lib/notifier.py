import os
import requests
from lib.signal_engine import Signal

_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
_API     = f"https://api.telegram.org/bot{_TOKEN}"


def _fmt(p: float) -> str:
    return f"${p:,.6f}".rstrip("0").rstrip(".")


def _pct(a: float, b: float) -> str:
    return f"{abs(a - b) / b * 100:.2f}%"


def format_signal(sig: Signal) -> str:
    is_long      = sig.direction == "LONG"
    head         = "🟢" if is_long else "🔴"
    dir_e        = "📈" if is_long else "📉"
    sl_arrow     = "⬇️" if is_long else "⬆️"
    tp_arrow     = "⬆️" if is_long else "⬇️"
    bar          = "█" * sig.score + "░" * (5 - sig.score)
    confidence   = int(sig.score / 5 * 100)

    votes = []
    for name, vote in sig.strategies.items():
        icon = ("✅" if (vote > 0) == is_long else "🔻" if vote != 0 else "⬜")
        votes.append(f"  {icon} {name}")

    return (
        f"{head} <b>{sig.direction} — {sig.symbol}</b> {dir_e}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Entry:</b>     <code>{_fmt(sig.entry)}</code>\n"
        f"{sl_arrow} <b>Stop Loss:</b>  <code>{_fmt(sig.sl)}</code>  <i>(-{_pct(sig.entry, sig.sl)})</i>\n"
        f"{tp_arrow} <b>TP1:</b>       <code>{_fmt(sig.tp1)}</code>  <i>(+{_pct(sig.tp1, sig.entry)})</i>\n"
        f"{tp_arrow} <b>TP2:</b>       <code>{_fmt(sig.tp2)}</code>  <i>(+{_pct(sig.tp2, sig.entry)})</i>\n"
        f"⚖️ <b>R:R Ratio:</b>  <code>1 : {sig.rr:.1f}</code>\n\n"
        f"📡 <b>Confidence:</b> {confidence}%  <code>[{bar}]</code>\n"
        f"⏱ <b>Timeframe:</b>  {sig.timeframe}\n\n"
        f"<b>Strategy Votes:</b>\n" + "\n".join(votes) + "\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <i>DYOR. Not financial advice. Manage risk.</i>"
    )


def send_signal(signal: Signal, chat_id: str = None) -> bool:
    return send_message(format_signal(signal), chat_id)


def send_message(text: str, chat_id: str = None) -> bool:
    token = os.getenv("TELEGRAM_TOKEN", _TOKEN)
    api   = f"https://api.telegram.org/bot{token}"
    try:
        r = requests.post(
            f"{api}/sendMessage",
            json={"chat_id": chat_id or _CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        return r.ok
    except Exception:
        return False
