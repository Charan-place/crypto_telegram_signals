import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

EXCHANGE_ID = os.getenv("EXCHANGE", "binance")

SYMBOLS = [s.strip() for s in os.getenv(
    "SYMBOLS",
    "BTC/USDT,ETH/USDT,BNB/USDT,SOL/USDT,XRP/USDT,ADA/USDT,AVAX/USDT"
).split(",")]

TF_PRIMARY = "1h"
TF_TREND   = "4h"
CANDLES    = 200

MIN_SCORE = 3
MIN_RR    = 2.0

ATR_PERIOD    = 14
SL_ATR_MULT   = 1.0
TP1_ATR_MULT  = 2.0
TP2_ATR_MULT  = 4.0

SCAN_INTERVAL  = 2   # minutes (matches vercel.json cron)
COOLDOWN_HOURS = 6
