# Crypto Signals Bot

Telegram bot that scans crypto pairs and fires high-confidence trading signals.

## Signal Logic

5 strategies vote on each coin every 15 minutes:

| Strategy | Criteria |
|---|---|
| RSI + MACD | RSI exits oversold/overbought + MACD confirms |
| EMA Stack | 9 EMA > 21 EMA > 50 EMA (bullish) or inverse |
| Bollinger Bands | Price at extreme bands + RSI confirms |
| 4H Structure | 4H trend aligns with 1H signal direction |
| Volume Surge | Volume > 1.5× 20-period average + candle direction |

**Signal fires only when:** ≥3/5 strategies agree **AND** R:R ≥ 2:1

## Setup

### 1. Get a Telegram Bot Token

1. Message [@BotFather](https://t.me/BotFather) → `/newbot`
2. Copy the token

### 2. Get Your Chat ID

1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy your chat ID

### 3. Configure

```bash
cd crypto-signals-bot
cp .env.example .env
# Edit .env — fill TELEGRAM_TOKEN and TELEGRAM_CHAT_ID
```

### 4. Install & Run

```bash
pip install -r requirements.txt
python main.py
```

## Signal Format

```
🟢 LONG — BTC/USDT 📈
━━━━━━━━━━━━━━━━━━━━━━
📊 Entry:     $43,250.00
⬇️ Stop Loss:  $42,750.00  (-1.16%)
⬆️ TP1:       $44,250.00  (+2.31%)
⬆️ TP2:       $46,250.00  (+6.94%)
⚖️ R:R Ratio:  1 : 2.0

📡 Confidence: 80%  [████░]
⏱ Timeframe:  1H + 4H

Strategy Votes:
  ✅ RSI + MACD
  ✅ EMA Stack
  ✅ Bollinger
  ⬜ 4H Structure
  ✅ Volume Surge
━━━━━━━━━━━━━━━━━━━━━━
⚠️ DYOR. Not financial advice. Manage risk.
```

## Bot Commands

- `/start` — show your chat ID
- `/status` — config + signal count stats
- `/help` — strategy explanation

## Config Options (.env)

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_TOKEN` | — | BotFather token |
| `TELEGRAM_CHAT_ID` | — | Your Telegram chat ID |
| `EXCHANGE` | `binance` | Any ccxt-supported exchange |
| `SYMBOLS` | BTC,ETH,BNB,SOL,XRP,ADA,AVAX | Comma-separated pairs |

## Tune in config.py

| Setting | Default | Effect |
|---|---|---|
| `MIN_SCORE` | 3 | Raise to 4/5 for fewer, higher-quality signals |
| `MIN_RR` | 2.0 | Minimum risk:reward ratio |
| `COOLDOWN_HOURS` | 6 | Hours before same coin+direction repeats |
| `SCAN_INTERVAL` | 15 | Minutes between full scans |
| `SL_ATR_MULT` | 1.0 | Stop loss = entry ± N×ATR |
| `TP1_ATR_MULT` | 2.0 | Take profit 1 = entry ± N×ATR |
| `TP2_ATR_MULT` | 4.0 | Take profit 2 = entry ± N×ATR |
