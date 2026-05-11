# Crypto Signals Bot

A bot that watches crypto futures markets 24/7 and sends trading signals to Telegram automatically.

---

## What It Does

Scans 14 coins on Binance Futures every 2 minutes. Runs 5 strategies on each coin. Fires a signal to Telegram only when 3+ strategies agree AND risk:reward ≥ 2:1.

---

## Architecture

```
cron-job.org          Vercel               Telegram
(every 2 min)  →  (signal engine)  →  (signal lands here)
                        ↑
                   Binance API
                  (live price data)
```

---

## Services Used & Why

| Service | Role | Why |
|---|---|---|
| **Telegram Bot** | Delivers signals to your phone | Free, instant, no app to build |
| **Binance API** | Live candle/volume data for 14 coins | Free public API, no account needed |
| **Vercel** | Hosts the bot code 24/7 | Free, no laptop needed |
| **cron-job.org** | Triggers scan every 2 minutes | Vercel Hobby only allows daily crons — external trigger bypasses this |
| **Upstash Redis** | Remembers recently sent signals | Prevents duplicate signals (2h cooldown per coin) |

---

## Coins Monitored (Binance Perpetual Futures)

| Type | Coins |
|---|---|
| Majors | BTC, ETH, SOL, BNB |
| Alts | LINK, AVAX, INJ, SUI, ARB, APT |
| Meme | DOGE, PEPE, WIF, SHIB |

---

## Signal Engine — 5 Strategies

Each strategy votes +1 (bullish), -1 (bearish), or 0 (neutral).

| Strategy | What It Checks |
|---|---|
| RSI + MACD | Momentum recovering from oversold/overbought zone |
| Stochastic RSI | Fast reversal crossover — best for 15m scalps |
| EMA Stack | 9/21/50 EMAs aligned bullish or bearish |
| Bollinger Bands | Price at extreme bands ready to bounce |
| 1H Trend | Bigger timeframe agrees with signal direction |

**Signal fires only when:**
- Score ≥ 3/5 strategies agree
- R:R ≥ 2:1 (reward at least 2× the risk)
- No signal sent for same coin in last 2 hours

---

## How It Works — Every 2 Minutes

```
1. cron-job.org pings → https://crypto-telegram-signals.vercel.app/api/scan

2. Vercel fetches 15m + 1H candles for all 14 coins from Binance

3. Runs 5 strategies on each coin

4. Score < 3  →  skip

5. Score ≥ 3  →  check R:R
   R:R < 2.0  →  skip

6. Signal sent recently?  →  skip (Redis cooldown)

7. All passed  →  send signal to Telegram

8. Record in Redis, start 2h cooldown

9. Repeat next cycle
```

---

## Signal Format

```
🟢 FUTURES LONG — PEPE/USDT PERP 📈
━━━━━━━━━━━━━━━━━━━━━━
Entry:        $0.00001234
Stop Loss:    $0.00001190  (-3.5%)
TP1 (Quick):  $0.00001392  (+12.8%)
TP2 (Run):    $0.00001720  (+39.4%)
R:R Ratio:    1 : 2.2
Leverage:     5x–10x suggested

Confidence:  80%  [████░]
Timeframe:   15M + 1H

Strategy Votes:
  ✅ RSI + MACD
  ✅ Stoch RSI
  ✅ EMA Stack
  ⬜ Bollinger
  ✅ 1H Trend
━━━━━━━━━━━━━━━━━━━━━━
⚠️ Futures = high risk. Use proper position sizing. DYOR.
```

---

## Bot Commands

| Command | What It Does |
|---|---|
| `/start` | Shows your chat ID |
| `/status` | Current config — coins, interval, thresholds |
| `/help` | Lists all commands |

---

## Project Structure

```
crypto-signals-bot/
├── app.py               — Flask app, all routes (/api/scan + /api/webhook)
├── lib/
│   ├── config.py        — All settings (coins, timeframes, thresholds)
│   ├── fetcher.py       — Pulls candle data from Binance Futures via ccxt
│   ├── signal_engine.py — 5 strategies, scoring, SL/TP calculation
│   ├── store.py         — Upstash Redis cooldown tracking
│   └── notifier.py      — Formats and sends Telegram messages
├── setup_webhook.py     — One-time script to register Telegram webhook
├── requirements.txt
├── vercel.json
└── .env.example
```

---

## Setup (Fresh Install)

### 1. Get Telegram credentials
- Bot token → message **@BotFather** → `/newbot`
- Chat ID → message **@userinfobot**

### 2. Configure environment
```bash
cp .env.example .env
# Fill in TELEGRAM_TOKEN and TELEGRAM_CHAT_ID
```

### 3. Install and deploy
```bash
pip3 install -r requirements.txt
/opt/homebrew/bin/vercel --prod
```

### 4. Register Telegram webhook
```bash
python3 setup_webhook.py https://crypto-telegram-signals.vercel.app
```

### 5. Set up cron trigger
- Go to cron-job.org → Create cronjob
- URL: `https://crypto-telegram-signals.vercel.app/api/scan`
- Schedule: every 2 minutes
- Enable

### 6. Add Upstash Redis (optional but recommended)
- Vercel dashboard → Storage → Upstash → Create Redis → Connect to project
- Env vars auto-added: `KV_REST_API_URL` + `KV_REST_API_TOKEN`

---

## Key Settings (`lib/config.py`)

| Setting | Default | Effect |
|---|---|---|
| `MIN_SCORE` | 3 | Raise to 4 for fewer, higher-quality signals |
| `MIN_RR` | 2.0 | Minimum risk:reward ratio |
| `COOLDOWN_HOURS` | 2 | Hours before same coin+direction repeats |
| `SL_ATR_MULT` | 0.8 | Stop loss = entry ± 0.8 × ATR |
| `TP1_ATR_MULT` | 1.8 | Quick TP = entry ± 1.8 × ATR |
| `TP2_ATR_MULT` | 4.0 | Runner TP = entry ± 4.0 × ATR |
| `LEVERAGE_RANGE` | 5x–10x | Shown in signal (you set actual leverage) |

---

## Problems Hit & How We Fixed Them

| Problem | Cause | Fix |
|---|---|---|
| `pandas-ta` not found | Removed from PyPI | Switched to `ta` library |
| Vercel cron limit | Hobby plan = daily crons only | Used cron-job.org as external trigger |
| `python3.11` runtime error | Wrong format in vercel.json | Removed runtime block, Vercel auto-detects Python |
| `DEPLOYMENT_NOT_FOUND` | Project shell on Vercel, no code deployed | Used `vercel --prod` CLI to deploy |
| "No Python entrypoint" error | Multiple .py files confused Vercel | Merged all routes into single `app.py` |
| Broken `npm` | Two npm installs, wrong one in PATH | Used `/opt/homebrew/bin/npm` directly |
| Space in chat ID | `.env` had `TELEGRAM_CHAT_ID= 6297632513` | Removed leading space |

---

## Live URLs

| URL | Purpose |
|---|---|
| `https://crypto-telegram-signals.vercel.app/api/scan` | Scan endpoint (hit by cron-job.org every 2 min) |
| `https://crypto-telegram-signals.vercel.app/api/webhook` | Telegram webhook (handles bot commands) |
| `https://crypto-telegram-signals.vercel.app/` | Health check |
