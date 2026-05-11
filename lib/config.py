import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

EXCHANGE_ID = os.getenv("EXCHANGE", "binance")

# Meme coins only — Binance perpetual futures
SYMBOLS = [s.strip() for s in os.getenv("SYMBOLS", ",".join([
    "DOGE/USDT:USDT",
    "PEPE/USDT:USDT",
    "WIF/USDT:USDT",
    "SHIB/USDT:USDT",
    "BONK/USDT:USDT",
    "FLOKI/USDT:USDT",
    "MEME/USDT:USDT",
    "NEIRO/USDT:USDT",
])).split(",")]

TF_PRIMARY = "15m"
TF_TREND   = "1h"
CANDLES    = 200

# Loosened for meme volatility — fire more signals
MIN_SCORE = 2       # 2/5 strategies must agree (was 3)
MIN_RR    = 1.5     # lower R:R bar (was 2.0)

ATR_PERIOD   = 14
SL_ATR_MULT  = 0.6   # very tight stop for meme pumps
TP1_ATR_MULT = 1.2   # quick scalp TP   → R:R 2:1
TP2_ATR_MULT = 3.0   # runner           → R:R 5:1

SCAN_INTERVAL  = 2
COOLDOWN_HOURS = 1   # 1h cooldown — memes move fast

LEVERAGE_RANGE = "5x–15x"
