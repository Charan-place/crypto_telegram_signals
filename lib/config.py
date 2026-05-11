import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

EXCHANGE_ID = os.getenv("EXCHANGE", "binance")

# Binance perpetual futures format: COIN/USDT:USDT
SYMBOLS = [s.strip() for s in os.getenv("SYMBOLS", ",".join([
    # Major
    "BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT", "BNB/USDT:USDT",
    # Alts (fast movers)
    "LINK/USDT:USDT", "AVAX/USDT:USDT", "INJ/USDT:USDT", "SUI/USDT:USDT",
    "ARB/USDT:USDT", "APT/USDT:USDT",
    # Meme coins
    "DOGE/USDT:USDT", "PEPE/USDT:USDT", "WIF/USDT:USDT", "SHIB/USDT:USDT",
])).split(",")]

# 15m signals confirmed by 1H trend — fast scalp setup
TF_PRIMARY = "15m"
TF_TREND   = "1h"
CANDLES    = 200

# Signal thresholds
MIN_SCORE = 3       # 3/5 strategies must agree
MIN_RR    = 2.0     # min risk:reward

# ATR — tighter for scalping
ATR_PERIOD   = 14
SL_ATR_MULT  = 0.8   # tight stop
TP1_ATR_MULT = 1.8   # quick first target  → R:R 2.25:1
TP2_ATR_MULT = 4.0   # runner target       → R:R 5:1

SCAN_INTERVAL  = 2
COOLDOWN_HOURS = 2   # shorter cooldown for fast markets

# Suggested leverage range shown in signals (user manages actual leverage)
LEVERAGE_RANGE = "5x–10x"
