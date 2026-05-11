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


def _indicators_1h(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    c, h, lo, v = df["close"], df["high"], df["low"], df["volume"]
    df["rsi"]         = ta.momentum.RSIIndicator(c, window=14).rsi()
    macd              = ta.trend.MACD(c, window_fast=12, window_slow=26, window_sign=9)
    df["macd"]        = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["ema9"]        = ta.trend.EMAIndicator(c, window=9).ema_indicator()
    df["ema21"]       = ta.trend.EMAIndicator(c, window=21).ema_indicator()
    df["ema50"]       = ta.trend.EMAIndicator(c, window=50).ema_indicator()
    bb                = ta.volatility.BollingerBands(c, window=20, window_dev=2)
    df["bb_pct"]      = bb.bollinger_pband()
    df["atr"]         = ta.volatility.AverageTrueRange(h, lo, c, window=ATR_PERIOD).average_true_range()
    df["vol_ma20"]    = v.rolling(20).mean()
    return df


def _indicators_4h(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    c = df["close"]
    df["ema20"] = ta.trend.EMAIndicator(c, window=20).ema_indicator()
    df["ema50"] = ta.trend.EMAIndicator(c, window=50).ema_indicator()
    return df


def _rsi_macd(df: pd.DataFrame) -> int:
    try:
        r, r1 = df["rsi"].iloc[-1], df["rsi"].iloc[-2]
        m, m1 = df["macd"].iloc[-1], df["macd"].iloc[-2]
        s, s1 = df["macd_signal"].iloc[-1], df["macd_signal"].iloc[-2]
        if r1 < 35 and r > 35 and m > s and m1 <= s1:
            return 1
        if r1 > 65 and r < 65 and m < s and m1 >= s1:
            return -1
        if r < 42 and m > s:
            return 1
        if r > 58 and m < s:
            return -1
    except (KeyError, IndexError):
        pass
    return 0


def _ema_stack(df: pd.DataFrame) -> int:
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
    try:
        bp  = df["bb_pct"].iloc[-1]
        rsi = df["rsi"].iloc[-1]
        if bp < 0.1 and rsi < 42:
            return 1
        if bp > 0.9 and rsi > 58:
            return -1
    except (KeyError, IndexError):
        pass
    return 0


def _trend_4h(df_4h: pd.DataFrame) -> int:
    try:
        close = df_4h["close"].iloc[-1]
        e20   = df_4h["ema20"].iloc[-1]
        e50   = df_4h["ema50"].iloc[-1]
        if close > e20 > e50:
            return 1
        if close < e20 < e50:
            return -1
    except (KeyError, IndexError):
        pass
    return 0


def _volume_surge(df: pd.DataFrame) -> int:
    try:
        vol    = df["volume"].iloc[-1]
        vol_ma = df["vol_ma20"].iloc[-1]
        if vol > vol_ma * 1.5:
            c, o = df["close"].iloc[-1], df["open"].iloc[-1]
            return 1 if c > o else -1
    except (KeyError, IndexError):
        pass
    return 0


def _calc_levels(df: pd.DataFrame, direction: str):
    atr   = df["atr"].iloc[-1]
    entry = df["close"].iloc[-1]
    if direction == "LONG":
        sl, tp1, tp2 = entry - atr * SL_ATR_MULT, entry + atr * TP1_ATR_MULT, entry + atr * TP2_ATR_MULT
    else:
        sl, tp1, tp2 = entry + atr * SL_ATR_MULT, entry - atr * TP1_ATR_MULT, entry - atr * TP2_ATR_MULT
    rr = abs(tp1 - entry) / abs(entry - sl) if abs(entry - sl) > 0 else 0
    return entry, sl, tp1, tp2, round(rr, 2)


def analyze(symbol: str, df_1h: pd.DataFrame, df_4h: pd.DataFrame) -> Signal | None:
    df_1h = _indicators_1h(df_1h)
    df_4h = _indicators_4h(df_4h)

    strategies = {
        "RSI + MACD":   _rsi_macd(df_1h),
        "EMA Stack":    _ema_stack(df_1h),
        "Bollinger":    _bollinger(df_1h),
        "4H Structure": _trend_4h(df_4h),
        "Volume Surge": _volume_surge(df_1h),
    }

    score = sum(strategies.values())
    if abs(score) < MIN_SCORE:
        return None

    direction = "LONG" if score > 0 else "SHORT"
    entry, sl, tp1, tp2, rr = _calc_levels(df_1h, direction)

    if rr < MIN_RR:
        return None

    return Signal(
        symbol=symbol, direction=direction,
        entry=entry, sl=sl, tp1=tp1, tp2=tp2,
        rr=rr, score=abs(score),
        strategies=strategies, timeframe="1H + 4H",
    )
