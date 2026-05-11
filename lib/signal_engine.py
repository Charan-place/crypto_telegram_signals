from dataclasses import dataclass
import pandas as pd
import ta
from lib.config import MIN_SCORE, MIN_RR, ATR_PERIOD, SL_ATR_MULT, TP1_ATR_MULT, TP2_ATR_MULT


@dataclass
class Signal:
    symbol: str
    direction: str
    entry: float
    sl: float
    tp1: float
    tp2: float
    rr: float
    score: int
    strategies: dict
    timeframe: str


# ─── Indicators ───────────────────────────────────────────────────────────────

def _indicators_15m(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    c, h, lo, v = df["close"], df["high"], df["low"], df["volume"]
    df["rsi"]         = ta.momentum.RSIIndicator(c, window=14).rsi()
    # Stochastic RSI for fast scalp confirmation
    stoch             = ta.momentum.StochRSIIndicator(c, window=14, smooth1=3, smooth2=3)
    df["stoch_k"]     = stoch.stochrsi_k()
    df["stoch_d"]     = stoch.stochrsi_d()
    macd              = ta.trend.MACD(c, window_fast=12, window_slow=26, window_sign=9)
    df["macd"]        = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["ema9"]        = ta.trend.EMAIndicator(c, window=9).ema_indicator()
    df["ema21"]       = ta.trend.EMAIndicator(c, window=21).ema_indicator()
    df["ema50"]       = ta.trend.EMAIndicator(c, window=50).ema_indicator()
    bb                = ta.volatility.BollingerBands(c, window=20, window_dev=2)
    df["bb_pct"]      = bb.bollinger_pband()
    df["bb_width"]    = bb.bollinger_wband()   # volatility squeeze detection
    df["atr"]         = ta.volatility.AverageTrueRange(h, lo, c, window=ATR_PERIOD).average_true_range()
    df["vol_ma20"]    = v.rolling(20).mean()
    return df


def _indicators_1h(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    c = df["close"]
    df["ema20"] = ta.trend.EMAIndicator(c, window=20).ema_indicator()
    df["ema50"] = ta.trend.EMAIndicator(c, window=50).ema_indicator()
    df["rsi"]   = ta.momentum.RSIIndicator(c, window=14).rsi()
    return df


# ─── Strategies ───────────────────────────────────────────────────────────────

def _rsi_macd(df: pd.DataFrame) -> int:
    """RSI + MACD momentum — tuned tight for 15m scalp."""
    try:
        r, r1 = df["rsi"].iloc[-1], df["rsi"].iloc[-2]
        m, m1 = df["macd"].iloc[-1], df["macd"].iloc[-2]
        s, s1 = df["macd_signal"].iloc[-1], df["macd_signal"].iloc[-2]

        # Strong: RSI exits extreme + fresh MACD cross
        if r1 < 38 and r > 38 and m > s and m1 <= s1:
            return 1
        if r1 > 62 and r < 62 and m < s and m1 >= s1:
            return -1
        # Softer: zone + direction agree
        if r < 45 and m > s:
            return 1
        if r > 55 and m < s:
            return -1
    except (KeyError, IndexError):
        pass
    return 0


def _stoch_rsi(df: pd.DataFrame) -> int:
    """Stochastic RSI crossover — best for fast 15m reversals."""
    try:
        k, k1 = df["stoch_k"].iloc[-1], df["stoch_k"].iloc[-2]
        d, d1 = df["stoch_d"].iloc[-1], df["stoch_d"].iloc[-2]

        # K crosses above D from oversold
        if k1 < d1 and k > d and k < 0.4:
            return 1
        # K crosses below D from overbought
        if k1 > d1 and k < d and k > 0.6:
            return -1
    except (KeyError, IndexError):
        pass
    return 0


def _ema_stack(df: pd.DataFrame) -> int:
    """EMA 9/21/50 alignment."""
    try:
        e9, e21, e50 = df["ema9"].iloc[-1], df["ema21"].iloc[-1], df["ema50"].iloc[-1]
        if e9 > e21 > e50:
            return 1
        if e9 < e21 < e50:
            return -1
    except (KeyError, IndexError):
        pass
    return 0


def _bollinger(df: pd.DataFrame) -> int:
    """BB squeeze + extreme bands for meme/alt volatility."""
    try:
        bp  = df["bb_pct"].iloc[-1]
        rsi = df["rsi"].iloc[-1]
        if bp < 0.15 and rsi < 48:
            return 1
        if bp > 0.85 and rsi > 52:
            return -1
    except (KeyError, IndexError):
        pass
    return 0


def _trend_1h(df_1h: pd.DataFrame) -> int:
    """1H structure — price vs EMA20/50 for trend bias."""
    try:
        close = df_1h["close"].iloc[-1]
        e20   = df_1h["ema20"].iloc[-1]
        e50   = df_1h["ema50"].iloc[-1]
        rsi   = df_1h["rsi"].iloc[-1]
        if close > e20 > e50 and rsi > 45:
            return 1
        if close < e20 < e50 and rsi < 55:
            return -1
    except (KeyError, IndexError):
        pass
    return 0


def _volume_surge(df: pd.DataFrame) -> int:
    """Volume 2× MA confirms breakout direction."""
    try:
        vol    = df["volume"].iloc[-1]
        vol_ma = df["vol_ma20"].iloc[-1]
        if vol > vol_ma * 1.3:   # 1.3x — meme coins spike hard
            c, o = df["close"].iloc[-1], df["open"].iloc[-1]
            return 1 if c > o else -1
    except (KeyError, IndexError):
        pass
    return 0


# ─── SL / TP ──────────────────────────────────────────────────────────────────

def _calc_levels(df: pd.DataFrame, direction: str):
    atr   = df["atr"].iloc[-1]
    entry = df["close"].iloc[-1]
    if direction == "LONG":
        sl  = entry - atr * SL_ATR_MULT
        tp1 = entry + atr * TP1_ATR_MULT
        tp2 = entry + atr * TP2_ATR_MULT
    else:
        sl  = entry + atr * SL_ATR_MULT
        tp1 = entry - atr * TP1_ATR_MULT
        tp2 = entry - atr * TP2_ATR_MULT
    rr = abs(tp1 - entry) / abs(entry - sl) if abs(entry - sl) > 0 else 0
    return entry, sl, tp1, tp2, round(rr, 2)


# ─── Main ─────────────────────────────────────────────────────────────────────

def analyze(symbol: str, df_15m: pd.DataFrame, df_1h: pd.DataFrame) -> Signal | None:
    df_15m = _indicators_15m(df_15m)
    df_1h  = _indicators_1h(df_1h)

    strategies = {
        "RSI + MACD":    _rsi_macd(df_15m),
        "Stoch RSI":     _stoch_rsi(df_15m),
        "EMA Stack":     _ema_stack(df_15m),
        "Bollinger":     _bollinger(df_15m),
        "1H Trend":      _trend_1h(df_1h),
    }

    score = sum(strategies.values())
    if abs(score) < MIN_SCORE:
        return None

    direction = "LONG" if score > 0 else "SHORT"
    entry, sl, tp1, tp2, rr = _calc_levels(df_15m, direction)

    if rr < MIN_RR:
        return None

    return Signal(
        symbol=symbol, direction=direction,
        entry=entry, sl=sl, tp1=tp1, tp2=tp2,
        rr=rr, score=abs(score),
        strategies=strategies, timeframe="15M + 1H",
    )
